#!/usr/bin/env python3
"""fv — formal verification entry point (fvkit, Python 3.9+ standard library; PyYAML optional for YAML).

Run `python3 fv.py --help`. Canonical copy lives next to accept-change; AI-DLC's
formal-verify skill ships a byte-identical one. Results are local_advisory evidence.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fvkit.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
