import json
import csv
from pathlib import Path

# Paths
DB_PATH = Path("resources/dataref_database.json")
EXPORT_PATH = Path("datarefs_export.txt")


def update_database():
    # Load existing database
    if DB_PATH.exists():
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {}

    # Read export file (tab-separated)
    with open(EXPORT_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)  # Skip header if present
        for row in reader:
            if len(row) < 5:
                continue
            name, typ, writable, unit, desc = row[:5]
            name = name.strip()
            typ = typ.strip()
            writable = (
                writable.strip().lower() == "y" or writable.strip().lower() == "true"
            )
            desc = desc.strip()

            # Update or add entry
            if name not in db:
                db[name] = {}
            db[name]["description"] = desc
            db[name]["type"] = typ
            db[name]["writable"] = writable

    # Save updated database
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

    print(f"Updated database with {len(db)} entries.")


if __name__ == "__main__":
    update_database()
