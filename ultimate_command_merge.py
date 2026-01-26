import json


def ultimate_command_merge():
    """Process ALL commands from the file without filtering"""

    # Load current database
    db_path = "resources/dataref_database.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_commands = sum(1 for v in data.values() if v.get("type") == "command")
    print(f"Starting with {current_commands} commands in database")

    # Process ALL commands from the specific file
    file_path = "XP12 dataref list and commands/commands (2).txt"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]

        print(f"Total lines in file: {len(lines)}")

        added_count = 0
        skipped_count = 0

        for line_num, line in enumerate(lines, 1):
            if not line or line.startswith("#") or "|" in line or line.isdigit():
                skipped_count += 1
                continue

            # Process ALL command formats
            if line.startswith("1-sim/"):
                cmd_line = line[2:].strip()  # Remove '1-'
            elif line.startswith("sim/"):
                cmd_line = line.strip()  # sim/ commands
            else:
                skipped_count += 1
                continue

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
            added_count += 1

            if added_count <= 20:  # Show first 20 additions
                print(f"  Added: {name}")

        print(f"\\nProcessed file: {file_path}")
        print(f"Added: {added_count} commands")
        print(f"Skipped: {skipped_count} lines")

    except Exception as e:
        print(f"Error processing command file {file_path}: {e}")
        return 0

    # Save updated database
    print(f"\\nSaving updated database...")

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print("Database updated successfully!")

    # Final verification
    with open(db_path, "r", encoding="utf-8") as f:
        updated_data = json.load(f)

    final_commands = sum(1 for v in updated_data.values() if v.get("type") == "command")
    final_total = len(updated_data)

    print(f"\\n=== ULTIMATE VERIFICATION ===")
    print(f"Total entries: {final_total}")
    print(
        f"Total commands: {final_commands} (was {current_commands}, +{final_commands - current_commands})"
    )

    # Count command types
    sim_1_commands = sum(
        1
        for k in updated_data.keys()
        if k.startswith("1-sim/") and updated_data[k].get("type") == "command"
    )
    sim_commands = sum(
        1
        for k in updated_data.keys()
        if k.startswith("sim/")
        and not k.startswith("1-sim/")
        and updated_data[k].get("type") == "command"
    )

    print(f"\\nCommand breakdown:")
    print(f"  1-sim/ commands: {sim_1_commands}")
    print(f"  sim/ commands: {sim_commands}")

    print(f"\\n=== SUCCESS ===")
    print(f"Comprehensive command database with {final_commands} commands ready!")
    return final_commands


if __name__ == "__main__":
    ultimate_command_merge()
