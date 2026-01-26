import json


def final_force_merge():
    """Final force merge - add ALL commands regardless of format"""

    # Load current database
    db_path = "resources/dataref_database.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_commands = sum(1 for v in data.values() if v.get("type") == "command")
    print(f"Current database has {current_commands} commands")

    # Process commands (2).txt - ALL lines
    file_path = "XP12 dataref list and commands/commands (2).txt"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [
                line.strip()
                for line in f.readlines()
                if line.strip() and not line.startswith("#")
            ]

        print(f"Processing {len(lines)} command lines from {file_path}")
        added = 0

        for line_num, line in enumerate(lines, 1):
            if not line:
                continue

            # Force parse all command lines
            if "1-sim/" in line:
                cmd_line = line[2:].strip()  # Remove '1-'
            elif "sim/" in line:
                cmd_line = line.strip()
            else:
                cmd_line = line.strip()

            # Find first space to separate name from description
            if " " in cmd_line:
                first_space = cmd_line.find(" ")
                name = cmd_line[:first_space].strip()
                description = cmd_line[first_space:].strip()
            else:
                name = cmd_line.strip()
                description = "Command"

            # Add to database (force overwrite)
            data[name] = {
                "name": name,
                "type": "command",
                "description": description,
                "units": "",
                "writable": False,
            }
            added += 1

            if added <= 10:  # Show first 10
                print(f"  {name}: {description[:50]}...")

        print(f"\\nFORCE ADDED {added} commands from {file_path}")

    except Exception as e:
        print(f"Error processing command file {file_path}: {e}")
        return 0

    # Save updated database
    print("\\nSaving updated database...")

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print("Database updated successfully!")

    # Final verification
    with open(db_path, "r", encoding="utf-8") as f:
        updated_data = json.load(f)

    final_commands = sum(1 for v in updated_data.values() if v.get("type") == "command")
    final_total = len(updated_data)

    print(f"\\n=== FINAL RESULTS ===")
    print(f"Total entries: {final_total}")
    print(
        f"Total commands: {final_commands} (was {current_commands}, +{final_commands - current_commands})"
    )

    # Count command types
    mh_commands = sum(1 for k in updated_data.keys() if k.startswith("1-sim/"))
    sim_commands = sum(
        1
        for k in updated_data.keys()
        if k.startswith("sim/")
        and not k.startswith("1-sim/")
        and updated_data[k].get("type") == "command"
    )

    print(f"\\nCommand breakdown:")
    print(f"  1-sim/ commands: {mh_commands}")
    print(f"  sim/ commands: {sim_commands}")
    print(f"  Other commands: {final_commands - mh_commands - sim_commands}")

    print("\\n=== SUCCESS ===")
    print("✅ COMPREHENSIVE COMMAND DATABASE MERGE COMPLETE!")
    print("✅ ALL command types from your file are now included!")
    print("✅ Database ready for immediate use in X-Plane Dataref Bridge!")


if __name__ == "__main__":
    final_force_merge()
