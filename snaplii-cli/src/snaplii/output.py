from __future__ import annotations

import json
import sys


def print_json(data: dict | list) -> None:
    print(json.dumps(data, indent=2))


def print_error(err_dict: dict) -> None:
    print(json.dumps(err_dict, indent=2), file=sys.stderr)
