#!/usr/bin/env python3
import csv, json, sys

file_path = sys.argv[1]

if not file_path.endswith(".csv"):
    print(f"Error: expected a .csv file, got: {file_path}", file=sys.stderr)
    sys.exit(1)

try:
    with open(file_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
except FileNotFoundError:
    print(f"Error: file not found: {file_path}", file=sys.stderr)
    sys.exit(1)

if not rows:
    print("Error: CSV file is empty or has no data rows", file=sys.stderr)
    sys.exit(1)

print(json.dumps(rows, ensure_ascii=False, indent=2))
