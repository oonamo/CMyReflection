import glob
import os
import re
import sys
from pathlib import Path

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"

test_dir = sys.argv[1] if len(sys.argv) > 1 else "test/"
do_output = sys.argv[2] == "-o" if len(sys.argv) > 2 else False
source_dir = Path(__file__).resolve().parent.parent

search_pattern = os.path.join(test_dir, "**", "*test*.c")
source_files = glob.glob(search_pattern, recursive=True)

defined_tests = {}
run_tests = {}

for file in source_files:
    with open(file, "r") as f:
        content = f.read()

        content = re.sub(r"//.*", "", content)
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        rel_file = Path(f.name).resolve().relative_to(source_dir)

        for match in re.findall(r"\bT\s*\(\s*([a-zA-Z0-9_]+)\s*\)", content):
            defined_tests[match] = rel_file
        for match in re.findall(r"\bRUN\s*\(\s*([a-zA-Z0-9_]+)\s*\)", content):
            run_tests[match] = rel_file

defined_set = set(defined_tests.keys())
run_set = set(run_tests.keys())

forgotten_runs = defined_set - run_set
ghost_runs = run_set - defined_set

if forgotten_runs or ghost_runs:
    print(f"{BOLD}{RED}TEST SYNCHRONIZATION ERROR!{RESET}")
    for test in forgotten_runs:
        file = defined_tests[test]
        print(
            f"   {CYAN}[{file}]{RESET} {BOLD}{YELLOW}Missing RUN:{RESET} Has {BOLD}{GREEN}T({test}){RESET} but forgot to {BOLD}{RED}RUN({test}){RESET}"
        )
    for test in ghost_runs:
        file = run_tests[test]
        print(
            f"   {CYAN}[{file}]{RESET} {BOLD}{YELLOW}Ghost RUN:{RESET} Has {BOLD}{GREEN}RUN({test}){RESET} but {BOLD}{RED}T({test}){RESET} doesn't exist"
        )
    sys.exit(1)

print(
    f"{BOLD}{GREEN}All {len(defined_tests)} Unity tests are properly registered.{RESET}"
)

if do_output:
    for t in sorted(run_tests):
        print(t)

sys.exit(0)
