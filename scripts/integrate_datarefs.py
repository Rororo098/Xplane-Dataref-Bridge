#!/usr/bin/env python3
import json, re, sys, pathlib
from typing import Dict

DB = pathlib.Path(__file__).resolve().parents[1] / 'resources' / 'dataref_database.json'
# Expected input lines (export from DataRefTool or similar):
#   sim/flightmodel2/misc/door_open_ratio[20]    float   rw   Door open ratio per door, 0..1
LINE_RE = re.compile(r"^(?P<name>\S+)\s+(?P<type>\S+)\s+(?P<rw>[rw]{1,2}|-)\s+(?P<desc>.*)$")

PLACEHOLDERS = {"", "custom dataref", "custom datarefs", "unknown", "n/a"}

def normalize_base(name: str) -> str:
    # Strip any array index part(s) to get the base name
    return name.split("[")[0]

def merge_entry(db: Dict[str, Dict], base: str, dtype: str, rw: str, desc: str):
    entry = db.get(base, {})
    # Prefer new description if it's non-placeholder
    new_desc = (desc or "").strip()
    if new_desc.lower() not in PLACEHOLDERS:
        entry['description'] = new_desc
    # Always keep/detect type from source if not set
    if 'type' not in entry or not entry.get('type'):
        entry['type'] = dtype
    # Writable: rw or r (read-only)
    if 'writable' not in entry:
        entry['writable'] = (rw.lower() == 'rw')
    db[base] = entry

def main(inp_path: str):
    db = {}
    if DB.exists():
        try:
            db = json.loads(DB.read_text(encoding='utf-8'))
        except Exception:
            print(f"Warning: failed to parse {DB}, starting with empty DB")
            db = {}

    updates = 0
    with open(inp_path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'): continue
            m = LINE_RE.match(line)
            if not m:
                continue
            name = m.group('name')
            dtype = m.group('type')
            rw = m.group('rw')
            desc = m.group('desc')
            base = normalize_base(name)
            merge_entry(db, base, dtype, rw, desc)
            updates += 1

    DB.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Merged {updates} lines into {DB}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: integrate_datarefs.py <datareftool_export.txt>')
        sys.exit(1)
    main(sys.argv[1])
