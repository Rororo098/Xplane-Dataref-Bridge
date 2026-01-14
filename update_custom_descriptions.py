import json
from pathlib import Path

# Paths
DB_PATH = Path("resources/dataref_database.json")
CUSTOM_PATH = Path("config/custom_datarefs.json")


def update_custom_descriptions():
    # Load main database
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    # Load custom datarefs
    with open(CUSTOM_PATH, "r", encoding="utf-8") as f:
        custom = json.load(f)

    # Update custom datarefs with descriptions from main database
    updated = 0
    for name, info in custom.items():
        # Get base name (remove array indices)
        base_name = name.split("[")[0] if "[" in name else name

        # Look up in main database
        if base_name in db:
            db_info = db[base_name]
            if "description" in db_info and db_info["description"]:
                info["description"] = db_info["description"]
                updated += 1

    # Save updated custom datarefs
    with open(CUSTOM_PATH, "w", encoding="utf-8") as f:
        json.dump(custom, f, indent=4)

    print(f"Updated {updated} custom dataref descriptions.")


if __name__ == "__main__":
    update_custom_descriptions()
