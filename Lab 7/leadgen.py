from pycparser import c_parser, c_ast
from graphviz import Digraph
import pandas as pd

input_files = ["bankingsystem.c", "productMan.c", "sortingalgo.c"]  
metrics = []  


for file_idx, filename in enumerate(input_files, start=1):
    print(f"\n{'='*80}\nProcessing {filename}\n{'='*80}")
    # Read and parse code
    with open(filename) as f:
        code = "\n".join([l for l in f if not l.strip().startswith("#")])

    parser = c_parser.CParser()
    ast = parser.parse(code)
    # Build parent map for AST nodes
    parent_map = {}
    def build_parent_map(node, parent=None):
        for _, ch in node.children():
            parent_map[ch] = node
            build_parent_map(ch, ch)
    build_parent_map(ast)
    leaders = set()
    edges = []         
    blocks = []

    def flatten(node):
        if isinstance(node, c_ast.Compound):
            out = []
            for c in node.block_items or []:
                out += flatten(c)
            return out
        return [node]

    def next_stmt(node, parent):
        if not hasattr(parent, "block_items"):
            return None
        stmts = parent.block_items
        if not stmts or node not in stmts:
            return None
        i = stmts.index(node)
        if i + 1 < len(stmts):
            return stmts[i + 1]
        return None

    def last_line_of_region(nodes):
        last = nodes[-1]
        while isinstance(last, c_ast.Compound) and last.block_items:
            last = last.block_items[-1]
        return last.coord.line

    def block_for_line(line):
        return min(blocks, key=lambda b: abs(b[1] - line))[0]

    def loop_exit_blocks(node):
        if isinstance(node, c_ast.Compound):
            if not node.block_items:
                return []
            return loop_exit_blocks(node.block_items[-1])
        elif isinstance(node, c_ast.If):
            exits = []
            exits.extend(loop_exit_blocks(node.iftrue))
            if node.iffalse:
                exits.extend(loop_exit_blocks(node.iffalse))
            return exits
        else:
            return [block_for_line(node.coord.line)]
    # Identify leaders using AST semantics
    def find_leaders(node, parent=None):
        if not node:
            return

        # Entry point (function start)
        if isinstance(node, c_ast.FuncDef):
            body = node.body
            if body.block_items:
                leaders.add(body.block_items[0].coord.line)

        # IF / ELSE IF / ELSE
        if isinstance(node, c_ast.If):
            leaders.add(node.coord.line)
            then_stmts = flatten(node.iftrue)
            if then_stmts:
                leaders.add(then_stmts[0].coord.line)

            if node.iffalse:
                if isinstance(node.iffalse, c_ast.If):  # else-if chain
                    leaders.add(node.iffalse.coord.line)
                else:
                    else_stmts = flatten(node.iffalse)
                    if else_stmts:
                        leaders.add(else_stmts[0].coord.line)

            nxt = next_stmt(node, parent)
            if nxt and hasattr(nxt, "coord"):
                leaders.add(nxt.coord.line)

        # FOR / WHILE / DO-WHILE
        elif isinstance(node, (c_ast.For, c_ast.While, c_ast.DoWhile)):
            leaders.add(node.coord.line)
            body_stmts = flatten(node.stmt)
            if body_stmts:
                leaders.add(body_stmts[0].coord.line)

            nxt = next_stmt(node, parent)
            if nxt and hasattr(nxt, "coord"):
                leaders.add(nxt.coord.line)

        for _, ch in node.children():
            find_leaders(ch, node)

    find_leaders(ast)
    leaders = sorted(leaders)

    # Build basic blocks
    lines = [l.strip() for l in code.splitlines()]
    lines = [(i + 1, l) for i, l in enumerate(lines) if l]

    blocks = []
    for i, leader in enumerate(leaders):
        start = leader
        end = leaders[i + 1] - 1 if i + 1 < len(leaders) else lines[-1][0]
        body = [txt for (n, txt) in lines if start <= n <= end]
        blocks.append((f"B{i}", start, body))

    # Construct edges from AST relationships
    def build_edges(node):
        if not node:
            return

        # --- IF / ELSE IF / ELSE ---
        if isinstance(node, c_ast.If):
            this_block = block_for_line(node.coord.line)
            then_nodes = flatten(node.iftrue)
            if then_nodes:
                then_block = block_for_line(then_nodes[0].coord.line)
                edges.append((this_block, then_block, "true"))

            outer = node
            while True:
                p = parent_map.get(outer)
                if not isinstance(p, c_ast.If) or p.iffalse is not outer:
                    break
                outer = p
            outer_parent = parent_map.get(outer)
            join_stmt = next_stmt(outer, outer_parent)
            join_block = block_for_line(join_stmt.coord.line) if (join_stmt and hasattr(join_stmt, "coord")) else None

            if node.iffalse:
                if isinstance(node.iffalse, c_ast.If):
                    else_if_block = block_for_line(node.iffalse.coord.line)
                    edges.append((this_block, else_if_block, "false"))
                else:
                    else_nodes = flatten(node.iffalse)
                    if else_nodes:
                        else_block = block_for_line(else_nodes[0].coord.line)
                        edges.append((this_block, else_block, "false"))
            else:
                if join_block:
                    edges.append((this_block, join_block, "false"))

            if then_nodes and join_block:
                then_exit_block = block_for_line(last_line_of_region(then_nodes))
                edges.append((then_exit_block, join_block, ""))

            if node.iffalse and not isinstance(node.iffalse, c_ast.If) and join_block:
                else_nodes = flatten(node.iffalse)
                if else_nodes:
                    else_exit_block = block_for_line(last_line_of_region(else_nodes))
                    edges.append((else_exit_block, join_block, ""))

        # --- FOR / WHILE / DO-WHILE ---
        elif isinstance(node, (c_ast.For, c_ast.While, c_ast.DoWhile)):
            this_block = block_for_line(node.coord.line)
            body_nodes = flatten(node.stmt)
            if body_nodes:
                body_block = block_for_line(body_nodes[0].coord.line)
                edges.append((this_block, body_block, "loop body"))

                exit_blocks = loop_exit_blocks(node.stmt)
                for blk in exit_blocks:
                    edges.append((blk, this_block, "back edge"))

            nxt = next_stmt(node, parent_map.get(node))
            if nxt and hasattr(nxt, "coord"):
                exit_block = block_for_line(nxt.coord.line)
                edges.append((this_block, exit_block, "exit"))

        # recurse on children
        for _, ch in node.children():
            build_edges(ch)

    build_edges(ast)

    # Add sequential fallthrough
    for i in range(len(blocks) - 1):
        b1, _, _ = blocks[i]
        b2, _, _ = blocks[i + 1]
        if any(e[0] == b1 and e[1] != b2 for e in edges) or \
        any(e[0] == b1 and e[2] in ("true","false","loop body","back edge") for e in edges):
            continue
        if not any(e[0] == b1 and e[1] == b2 for e in edges):
            edges.append((b1, b2, ""))

    # Print summary
    print("=== Leaders ===")
    for l in leaders:
        txt = next((t for (n, t) in lines if n == l), "")
        print(f"Line {l}: {txt}")

    print("\n=== Blocks ===")
    for name, start, body in blocks:
        print(f"\n{name} (line {start}):")
        for b in body:
            print("   ", b)
    # Draw CFG
    G = Digraph("CFG", format="png")
    G.attr("node", shape="box", style="rounded,filled", fillcolor="lightyellow")

    for name, start, body in blocks:
        label = name + " (" + str(start) + ")\n" + "\n".join(body)
        G.node(name, label)

    for u, v, lbl in edges:
        G.edge(u, v, label=lbl)

    G.render(f"cfg_{filename}", cleanup=True)

    # Compute Cyclomatic Complexity Metrics
    N = len(blocks)
    E = len(edges)
    CC = E - N + 2
    metrics.append([file_idx,N,E,CC])

    # Reaching Definitions Analysis
     
    # Collect all definitions
    definition_counter = 1
    definitions = {}       
    var_definitions = {}   
    def_line_map = {}       
    definitions_set = set() 
    def collect_definitions(node):
        global definition_counter
        if node is None:
            return

        var, line = None, None

        # variable assignment
        if isinstance(node, c_ast.Assignment):
            if isinstance(node.lvalue, c_ast.ID):
                var = node.lvalue.name
                line = node.coord.line
            elif isinstance(node.lvalue, c_ast.ArrayRef):
                if isinstance(node.lvalue.name, c_ast.ID):
                    var = f"{node.lvalue.name.name}[]" 
                    line = node.coord.line

        elif isinstance(node, c_ast.Decl) and node.init:
            var = node.name
            line = node.coord.line

        elif isinstance(node, c_ast.UnaryOp) and node.op in ('p++','p--','++','--'):
            if isinstance(node.expr, c_ast.ID):
                var = node.expr.name
                line = node.coord.line

        elif isinstance(node, c_ast.For) and isinstance(node.init, c_ast.Decl):
            var = node.init.name
            line = node.init.coord.line

        # Add to definitions if not already seen
        if var is not None and (var, line) not in definitions_set:
            definitions_set.add((var, line))
            def_id = f"D{definition_counter}"
            definition_counter += 1
            definitions[def_id] = (var, line)
            var_definitions.setdefault(var, set()).add(def_id)
            def_line_map.setdefault(line, []).append(def_id)

        # Recurse into children
        for attr, ch in node.children():
            if isinstance(node, c_ast.For) and attr == "init":
                continue
            collect_definitions(ch)


    for f in ast.ext:
        if isinstance(f, c_ast.FuncDef):
            collect_definitions(f.body)

    # Compute gen and kill for each block 
    block_gen = {}
    block_kill = {}

    # map variables -> all definitions of that variable
    var_definitions = {}
    for def_id, (var, line) in definitions.items():
        var_definitions.setdefault(var, set()).add(def_id)

    for name, start, body in blocks:
        # get line numbers for this block
        start_line = start
        end_line = start + len(body) - 1  # could also track end_line from your block creation

        gen_set = set()
        vars_in_block = set()

        for line_num, code_line in [(n, t) for (n, t) in lines if start_line <= n <= end_line]:
            for d in def_line_map.get(line_num, []):
                gen_set.add(d)
                var, line = definitions[d]  # unpack fully
                vars_in_block.add(var)

        # kill: all other definitions of the same variables
        kill_set = set()
        for var in vars_in_block:
            kill_set.update(var_definitions[var] - gen_set)

        block_gen[name] = gen_set
        block_kill[name] = kill_set

    # Build predecessors
    preds = {b[0]: set() for b in blocks}
    for u, v, lbl in edges:
        preds[v].add(u)

    # iterative analysis
    in_sets = {b[0]: set() for b in blocks}
    out_sets = {b[0]: set() for b in blocks}

    changed = True
    while changed:
        changed = False
        for name, _, _ in blocks:
            old_in = in_sets[name].copy()
            old_out = out_sets[name].copy()

            # in[B] = union of out[preds]
            in_sets[name] = set()
            for p in preds[name]:
                in_sets[name].update(out_sets[p])

            # out[B] = gen[B] U (in[B] - kill[B])
            out_sets[name] = block_gen[name].union(in_sets[name] - block_kill[name])

            if old_in != in_sets[name] or old_out != out_sets[name]:
                changed = True

    rows = []
    for name, _, _ in blocks:
        rows.append({
            "Block": name,
            "gen[B]": ",".join(sorted(block_gen[name])),
            "kill[B]": ",".join(sorted(block_kill[name])),
            "in[B]": ",".join(sorted(in_sets[name])),
            "out[B]": ",".join(sorted(out_sets[name]))
        })


    df = pd.DataFrame(rows)
    print("\n=== Reaching Definitions Table ===")
    print(df)
    df.to_csv(f"reaching_definitions_{filename}.csv", index=False)
    print("\n Reaching Definitions saved to reaching_definitions.csv")

    # Print all definitions 
    print("\n=== Definitions ===")
    for d, (var, line) in sorted(definitions.items(), key=lambda x: int(x[0][1:])):
        code_line = next((txt for (n, txt) in lines if n == line), "")
        print(f"{d}: {var} = ... (line {line}) -> {code_line}")

columns = ["Program No.", "No. Of Nodes (N)", "No. Of Edges (E)", "Cyclomatic Complexity (CC)"]
df = pd.DataFrame(metrics, columns=columns)
df.to_csv("metrics_table.csv", index=False)
print(df)