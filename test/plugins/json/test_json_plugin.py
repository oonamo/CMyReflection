import sys
from pathlib import Path

# test_json_plugin.py -> json/ -> plugins/ -> test/ -> ROOT
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import cmy_reflector

def test_s():
    pass
