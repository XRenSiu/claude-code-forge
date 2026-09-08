#!/usr/bin/env python3
"""Fixture projection script: it renders two files it does not own."""
import json

import yaml

AUDIT = "audit.yaml"
WINDOW = "commit-window.json"


def main():
    rows = yaml.safe_load(open(AUDIT))
    window = json.load(open(WINDOW))
    print(len(rows), window)


if __name__ == "__main__":
    main()
