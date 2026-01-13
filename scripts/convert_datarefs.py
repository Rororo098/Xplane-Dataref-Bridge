#!/usr/bin/env python3
"""Convert a DataRefs.txt file into JSON mapping like dataref_databse.json.

Usage:
  python scripts/convert_datarefs.py --input DataRefs.txt --output dataref.txt
"""
import argparse
import json
import os
import re


def parse_line(line):
    s = line.strip()
    if not s:
        return None
    if s.startswith('#'):
        return None
    # Try tab split first
    parts = re.split(r"\t+", s)
    if len(parts) < 2:
        # Fallback: split on whitespace but keep description as last field
        parts = s.split(None, 4)
    # Minimal validation: first token should look like a dataref path
    path = parts[0].strip()
    if '/' not in path:
        return None

    dtype = parts[1].strip() if len(parts) > 1 else "unknown"
    writable = False
    units = ""
    description = ""

    if len(parts) > 2:
        w = parts[2].strip().lower()
        writable = w in ("y", "yes", "true", "1")
    if len(parts) > 3:
        units = parts[3].strip()
    if len(parts) > 4:
        description = parts[4].strip()
    else:
        # If only 4 columns present, it's ambiguous whether col4 is units or description.
        # Heuristic: if col4 contains spaces (or is long) treat as description.
        if units and (" " in units or len(units) > 20):
            description = units
            units = ""

    # Build entry like dataref_databse.json
    entry = {"type": dtype, "writable": writable}
    if units:
        entry["units"] = units
    if description:
        entry["description"] = description
    else:
        entry.setdefault("description", "")

    return path, entry


def convert(input_path, output_path):
    results = {}
    with open(input_path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            parsed = parse_line(ln)
            if not parsed:
                continue
            path, entry = parsed
            # If duplicate path, prefer to merge non-empty fields
            if path in results:
                results[path].update({k: v for k, v in entry.items() if v})
            else:
                results[path] = entry

    # Pretty JSON similar to existing sample
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(results, out, indent=4, sort_keys=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", default="DataRefs.txt", help="Input DataRefs.txt file")
    ap.add_argument("--output", "-o", default="dataref.txt", help="Output JSON file")
    args = ap.parse_args()
    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        return
    convert(args.input, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
