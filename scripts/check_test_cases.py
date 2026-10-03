import glob
import os
import re
import sys

test_dir = sys.argv[1] if len(sys.argv) > 1 else "test/"
do_output = sys.argv[2] == "-o" if len(sys.argv) > 2 else False

search_pattern = os.path.join(test_dir, "**", "*test*.c")
source_files = glob.glob(search_pattern, recursive=True)

defined_tests = set()
run_tests = set()

for file in source_files:
    with open(file, "r") as f:
        content = f.read()

        content = re.sub(r"//.*", "", content)
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

        defined_tests.update(re.findall(r"\bT\s*\(\s*([a-zA-Z0-9_]+)\s*\)", content))
        run_tests.update(re.findall(r"\bRUN\s*\(\s*([a-zA-Z0-9_]+)\s*\)", content))

forgotten_runs = defined_tests - run_tests
ghost_runs = run_tests - defined_tests

if forgotten_runs or ghost_runs:
    print("❌ TEST SYNCHRONIZATION ERROR!")
    for test in forgotten_runs:
        print(f"   Missing RUN: Has T({test}) but forgot to RUN({test})")
    for test in ghost_runs:
        print(f"   Ghost RUN: Has RUN({test}) but T({test}) doesn't exist")
    sys.exit(1)

print(f"✅ All {len(defined_tests)} tests are properly registered.")

if do_output:
    for t in sorted(run_tests):
        print(t)

sys.exit(0)
