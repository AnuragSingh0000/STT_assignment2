import subprocess
import json
import os
import shutil
import tempfile
import pandas as pd
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# ----------------- Configuration -----------------
project = "leveldb"
output_dir = f"vuln_reports_{project}"
os.makedirs(output_dir, exist_ok=True)



# ----------------- Helpers -----------------
def run_cmd(cmd, cwd=None, stdout_path=None, capture_output=False):
    try:
        if stdout_path and not capture_output:
            # stream stdout to file, capture stderr
            with open(stdout_path, "w", encoding="utf-8") as fout:
                proc = subprocess.run(cmd, cwd=cwd, stdout=fout, stderr=subprocess.PIPE, text=True)
            return proc
        elif stdout_path and capture_output:
            # capture both stdout and stderr and write stdout if present, else write stderr
            proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out_text = proc.stdout if proc.stdout else proc.stderr
            with open(stdout_path, "w", encoding="utf-8") as fout:
                fout.write(out_text)
            return proc
        elif capture_output:
            proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return proc
        else:
            proc = subprocess.run(cmd, cwd=cwd)
            return proc
    except FileNotFoundError:
        return None


def safe_json_load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def guess_cwe_from_text(text):
    if not text:
        return None
    t = text.lower()
    if "sql" in t and ("inject" in t or "injection" in t):
        return "CWE-89"
    if "xss" in t or ("cross-site" in t and "scripting" in t):
        return "CWE-79"
    if "eval(" in t or "code injection" in t or "exec(" in t:
        return "CWE-94"
    if "command injection" in t or "os.system" in t or "subprocess" in t:
        return "CWE-78"
    if "path traversal" in t or "directory traversal" in t or ("open(" in t and ("../" in t or "..\\" in t)):
        return "CWE-22"
    if "buffer" in t or "out of bounds" in t or "overflow" in t:
        return "CWE-119"
    if "use after free" in t or "use-after-free" in t:
        return "CWE-416"
    return None

def is_top25(cwe):
    if not isinstance(cwe, str):
        return False
    m = re.search(r"(\d+)", cwe)
    if not m:
        return False
    try:
        return int(m.group(1)) in top25_nums
    except:
        return False



# ----------------- Tool Runners -----------------
def run_cppcheck(project_path):
    out = os.path.join(output_dir, "cppcheck.xml")
    print("Running cppcheck (XML) ...")
    # cppcheck writes XML results to stderr when using --xml
    proc = run_cmd([
        "cppcheck", "--enable=all", "--xml", "--xml-version=2", project_path
    ], capture_output=True)

    if proc is None:
        return None
    # write captured stderr (which contains xml) to file
    if proc.stderr:
        with open(out, "w", encoding="utf-8") as f:
            f.write(proc.stderr)
    else:
        if proc.stdout:
            with open(out, "w", encoding="utf-8") as f:
                f.write(proc.stdout)
    return out if os.path.exists(out) and os.path.getsize(out) > 0 else None


def run_flawfinder(project_path):
    out = os.path.join(output_dir, "flawfinder.sarif")
    print("Running flawfinder (SARIF) ...")
    # newer flawfinder supports --sarif to output SARIF JSON
    proc = run_cmd(["flawfinder", "--minlevel=1", "--sarif", project_path], stdout_path=out)
    # some flawfinder versions print to stdout; run_cmd saved stdout to out
    return out if os.path.exists(out) and os.path.getsize(out) > 0 else None


def run_semgrep(project_path):
    out = os.path.join(output_dir, "semgrep.json")
    print("Running Semgrep (p/cwe-top-25) ...")
    # write JSON output to file
    proc = run_cmd(["semgrep", "--config", "--json", "--output", out, project_path])
    return out if os.path.exists(out) and os.path.getsize(out) > 0 else None


# ----------------- Run Tools -----------------
paths = {}
# Run cppcheck
cpath = run_cppcheck(project)
if cpath:
    paths['cppcheck'] = cpath

# Run flawfinder
fpath = run_flawfinder(project)
if fpath:
    paths['flawfinder'] = fpath

# Run Semgrep
spath = run_semgrep(project)
if spath:
    paths['semgrep'] = spath



# ----------------- Collect CWE Findings -----------------
records = []
for tool, path in paths.items():
    if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
        print(f"Skipping {tool}: no output file or empty.")
        continue

    print(f"Parsing output from {tool}: {path}")

    if tool == 'semgrep':
        data = safe_json_load(path)
        if not data:
            print(f"Skipping semgrep: invalid JSON at {path}")
            continue
        for item in data.get('results', []):
            cwe = None
            meta = item.get('extra', {}).get('metadata', {})
            if isinstance(meta, dict):
                val = meta.get('cwe') or meta.get('cwe_id')
                if isinstance(val, list) and val:
                    cwe = val[0]
                elif isinstance(val, str) and val:
                    cwe = val
            if not cwe:
                # check check_id or rule id for CWE
                check_id = item.get('check_id') or item.get('rule', {}).get('id') or ''
                m = re.search(r'CWE[- _]?(\d+)', check_id, re.IGNORECASE)
                if m:
                    cwe = f"CWE-{m.group(1)}"
            if not cwe:
                msg = item.get('extra', {}).get('message') or item.get('extra', {}).get('metadata', {}).get('description') or ''
                guessed = guess_cwe_from_text(msg)
                cwe = guessed or 'Unknown'
            if isinstance(cwe, str) and re.match(r'^\d+$', cwe):
                cwe = f"CWE-{cwe}"
            records.append([project, 'Semgrep', cwe, 1])

    elif tool == 'cppcheck':
        # parse XML
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except Exception as e:
            print(f"Failed to parse cppcheck XML: {e}")
            continue
        # find all <error> elements
        for err in root.findall('.//error'):
            cwe = None
            # cppcheck may expose cwe as attribute
            cwe_attr = err.get('cwe')
            if cwe_attr:
                # some tools provide CWE as e.g. 'CWE-476' or '476'
                if re.match(r'^\d+$', cwe_attr):
                    cwe = f"CWE-{cwe_attr}"
                elif re.match(r'(?i)^cwe-?\d+$', cwe_attr):
                    cwe = cwe_attr.upper().replace('CWE', 'CWE')
            if not cwe:
                # check message text
                msg = err.get('msg') or ''
                m = re.search(r'CWE[- _]?(\d+)', msg, re.IGNORECASE)
                if m:
                    cwe = f"CWE-{m.group(1)}"
            if not cwe:
                # try id attribute mapping (some ids map to known CWEs; heuristic)
                eid = err.get('id') or ''
                guessed = guess_cwe_from_text(eid + ' ' + (err.get('msg') or ''))
                cwe = guessed or 'Unknown'
            records.append([project, 'Cppcheck', cwe, 1])

    elif tool == 'flawfinder':
        # flawfinder SARIF (JSON) or plain text
        data = safe_json_load(path)
        if data:
            # SARIF-like json
            for run in data.get('runs', []):
                for res in run.get('results', []):
                    cwe = None
                    # check properties.tags
                    props = res.get('properties', {})
                    tags = props.get('tags') or []
                    if isinstance(tags, list):
                        for t in tags:
                            m = re.search(r'CWE[- _]?(\d+)', str(t), re.IGNORECASE)
                            if m:
                                cwe = f"CWE-{m.group(1)}"
                                break
                    if not cwe:
                        # check message
                        msg = res.get('message', {}).get('text') or ''
                        m = re.search(r'CWE[- _]?(\d+)', msg, re.IGNORECASE)
                        if m:
                            cwe = f"CWE-{m.group(1)}"
                    if not cwe:
                        # maybe ruleId contains number
                        rid = res.get('ruleId') or ''
                        m = re.search(r'(\d{2,4})', rid)
                        if m:
                            cwe = f"CWE-{m.group(1)}"
                    if not cwe:
                        cwe = guess_cwe_from_text(msg) or 'Unknown'
                    records.append([project, 'Flawfinder', cwe, 1])
        else:
            # fallback: parse plain text lines
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    m = re.search(r'CWE[- _]?(\d+)', line, re.IGNORECASE)
                    if m:
                        records.append([project, 'Flawfinder', f"CWE-{m.group(1)}", 1])



# ----------------- Aggregate & Save -----------------
if records:
    df = pd.DataFrame(records, columns=["Project_name", "Tool_name", "CWE_ID", "Findings"])
    df["CWE_ID"] = df["CWE_ID"].astype(str).str.strip()
    df_agg = df.groupby(["Project_name", "Tool_name", "CWE_ID"], dropna=False).size().reset_index(name="Number_of_Findings")

    top25_nums = {
        79, 89, 78, 20, 125, 22, 787, 416, 190, 352,
        306, 502, 434, 476, 862, 798, 276, 611, 918,
        269, 94, 863, 400, 772
    }
    df_agg["Is_In_CWE_Top_25?"] = df_agg["CWE_ID"].apply(is_top25)

    csv_out = os.path.join(output_dir, f"cpp_vuln_findings_{project}.csv")
    df_agg.to_csv(csv_out, index=False)
    print(f"\n Consolidated CSV saved to: {csv_out}")
    print(df_agg)
else:
    print("No findings detected by any tool.")
