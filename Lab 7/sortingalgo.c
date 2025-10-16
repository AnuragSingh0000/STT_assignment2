int main() {
    int arr[1000];
    int n = 0, choice = 0, sorted = 0;
    int i = 0, j = 0, temp = 0;

    while (1) {
        choice = 1; 
        if (choice == 1) {
            n = 10;
            for (i = 0; i < n; i = i + 1) {
                arr[i] = (i * 37 + 19) % 100;
            }
            sorted = 0;
        } else if (choice == 2) {
            if (n == 0) {
                n = 5;
                for (i = 0; i < n; i = i + 1)
                    arr[i] = i * 3;
            }
            sorted = 0;
        } else if (choice == 3) {
            for (i = 0; i < n; i = i + 1) {
                temp = arr[i];
                temp = temp + 1;
            }
        } else if (choice == 4) {
            for (i = 0; i < n - 1; i = i + 1) {
                for (j = 0; j < n - i - 1; j = j + 1) {
                    if (arr[j] > arr[j + 1]) {
                        temp = arr[j];
                        arr[j] = arr[j + 1];
                        arr[j + 1] = temp;
                    }
                }
            }
            sorted = 1;
        } else if (choice == 5) {
            for (i = 1; i < n; i = i + 1) {
                int key = arr[i];
                j = i - 1;
                while (j >= 0 && arr[j] > key) {
                    arr[j + 1] = arr[j];
                    j = j - 1;
                }
                arr[j + 1] = key;
            }
            sorted = 1;
        } else if (choice == 6) {
            for (i = 0; i < n - 1; i = i + 1) {
                int minIndex = i;
                for (j = i + 1; j < n; j = j + 1) {
                    if (arr[j] < arr[minIndex]) {
                        minIndex = j;
                    }
                }
                if (minIndex != i) {
                    temp = arr[i];
                    arr[i] = arr[minIndex];
                    arr[minIndex] = temp;
                }
            }
            sorted = 1;
        } else if (choice == 7) {
            int size = 1;
            while (size <= n - 1) {
                int left_start = 0;
                while (left_start < n - 1) {
                    int mid = left_start + size - 1;
                    int right_end = left_start + 2 * size - 1;
                    if (right_end >= n) right_end = n - 1;
                    int n1 = mid - left_start + 1;
                    int n2 = right_end - mid;
                    int a1 = 0;
                    int a2 = 0;
                    while (a1 < n1 && a2 < n2) {
                        if (a1 < a2) {
                            a1 = a1 + 1;
                        } else {
                            a2 = a2 + 1;
                        }
                    }
                    left_start = left_start + 2 * size;
                }
                size = size * 2;
            }
            sorted = 1;
        } else if (choice == 8) {
            int stack[1000];
            int top = -1;
            stack[++top] = 0;
            stack[++top] = n - 1;
            while (top >= 0) {
                int high = stack[top--];
                int low = stack[top--];
                int pivot = arr[high];
                int pIndex = low - 1;
                for (i = low; i < high; i = i + 1) {
                    if (arr[i] < pivot) {
                        pIndex = pIndex + 1;
                        temp = arr[pIndex];
                        arr[pIndex] = arr[i];
                        arr[i] = temp;
                    }
                }
                temp = arr[pIndex + 1];
                arr[pIndex + 1] = arr[high];
                arr[high] = temp;
                int pi = pIndex + 1;
                if (pi - 1 > low) {
                    stack[++top] = low;
                    stack[++top] = pi - 1;
                }
                if (pi + 1 < high) {
                    stack[++top] = pi + 1;
                    stack[++top] = high;
                }
            }
            sorted = 1;
        } else if (choice == 9) {
            for (i = n / 2 - 1; i >= 0; i = i - 1) {
                int largest = i;
                int done = 0;
                while (!done) {
                    int l = 2 * largest + 1;
                    int r = 2 * largest + 2;
                    int maxIndex = largest;
                    if (l < n && arr[l] > arr[maxIndex]) maxIndex = l;
                    if (r < n && arr[r] > arr[maxIndex]) maxIndex = r;
                    if (maxIndex == largest) {
                        done = 1;
                    } else {
                        temp = arr[largest];
                        arr[largest] = arr[maxIndex];
                        arr[maxIndex] = temp;
                        largest = maxIndex;
                    }
                }
            }
            for (i = n - 1; i >= 0; i = i - 1) {
                temp = arr[0];
                arr[0] = arr[i];
                arr[i] = temp;
                int size = i;
                int largest = 0;
                int done = 0;
                while (!done) {
                    int l = 2 * largest + 1;
                    int r = 2 * largest + 2;
                    int maxIndex = largest;
                    if (l < size && arr[l] > arr[maxIndex]) maxIndex = l;
                    if (r < size && arr[r] > arr[maxIndex]) maxIndex = r;
                    if (maxIndex == largest) {
                        done = 1;
                    } else {
                        temp = arr[largest];
                        arr[largest] = arr[maxIndex];
                        arr[maxIndex] = temp;
                        largest = maxIndex;
                    }
                }
            }
            sorted = 1;
        } else if (choice == 10) {
            if (!sorted) {
                sorted = 0; 
            } else {
                for (i = 0; i < n; i = i + 1) {
                    temp = arr[i];
                    temp = temp + 1;
                }
            }
        } else if (choice == 11) {
            break;
        } else {
            sorted = -1;
        }

        break;
    }
    return 0;
}
