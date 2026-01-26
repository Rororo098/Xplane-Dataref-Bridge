import json
import os


def apply_version_prefixes():
    """Apply version prefixes correctly to database"""

    # Load version database
    version_db_path = "C:/Users/Victoria Rafaelle/Downloads/Sample XP11 Dataref to Ard/DREF Extractor/XPLANE_DB_DW.json"
    db_path = "resources/dataref_database.json"

    print("Loading version database...")
    with open(version_db_path, "r", encoding="utf-8") as f:
        version_data = json.load(f)

    # Create version lookup
    version_lookup = {}
    for item in version_data:
        if "path" in item:
            path = item["path"]
            version = item.get("version", "unknown")
            # Clean version format
            if version.startswith("vv"):
                version = version[1:]  # Remove one v
            elif not version.startswith("v"):
                version = "v" + version
            version_lookup[path] = version

    print(f"Loaded {len(version_lookup)} version entries")

    # Load current database
    print("Loading current database...")
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Apply version prefixes
    updated_count = 0
    for name, entry in data.items():
        if name in version_lookup and version_lookup[name] != "unknown":
            version = version_lookup[name]
            current_desc = entry.get("description", "")

            # Only add version if not already present
            if not current_desc.startswith(version):
                entry["description"] = f"{version} - {current_desc}"
                updated_count += 1

    print(f"Applied version prefixes to {updated_count} entries")

    # Save updated database
    print("Saving updated database...")
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print("Database updated successfully!")

    # Verification
    with open(db_path, "r", encoding="utf-8") as f:
        updated_data = json.load(f)

    with_version = sum(
        1
        for v in updated_data.values()
        if "v" in v.get("description", "") and "." in v.get("description", "")
    )
    print(f"\nVERIFICATION:")
    print(f"Total entries: {len(updated_data)}")
    print(f"Entries with version prefixes: {with_version}")

    print("\nSample entries with version prefixes:")
    count = 0
    for name, entry in updated_data.items():
        desc = entry.get("description", "")
        if "v" in desc and "." in desc and len(desc) > 10:
            print(f"  {name}: {desc[:80]}...")
            count += 1
            if count >= 5:
                break


if __name__ == "__main__":
    apply_version_prefixes()
