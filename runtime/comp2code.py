"""Convert a single component from json to py

Note: does not remove the old json file!

Usage:
    python comp2code.py transformations/components/visualization/timeseries-substitution-plot_100_3160c5a1-
0cfb-7396-739a-a106c2a3e130.json
"""

import json
import sys
from pathlib import Path

path = sys.argv[1]

with open(path) as f:
    trafo_dict = json.load(f)
    code = trafo_dict["content"]
    new_path = Path(path).with_suffix(".py")

    with open(new_path, "w") as py_file:
        py_file.write(code)
