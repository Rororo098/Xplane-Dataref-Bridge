import json


def force_add_specific_commands():
    """Force add all commands from the specific file you mentioned"""

    # Load current database
    db_path = "resources/dataref_database.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_commands = sum(1 for v in data.values() if v.get("type") == "command")
    print(f"Current database has {current_commands} commands")

    # Force add ALL commands from commands (2).txt
    file_path = "XP12 dataref list and commands/commands (2).txt"
    added_count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines, headers, lines with pipes, digit-only lines
                if not line or line.startswith("#") or "|" in line or line.isdigit():
                    continue

                # Look for 1-sim/ prefix commands
                if line.startswith("1-sim/"):
                    cmd_line = line[2:].strip()  # Remove '1-' prefix

                    # Find first space to separate name from description
                    if " " in cmd_line:
                        first_space = cmd_line.find(" ")
                        name = cmd_line[:first_space].strip()
                        description = cmd_line[first_space:].strip()
                    else:
                        name = cmd_line.strip()
                        description = "Command" if not description else description

                    # Force add to database (overwrites if exists)
                    data[name] = {
                        "name": name,
                        "type": "command",
                        "description": description,
                        "units": "",
                        "writable": False,
                    }
                    added_count += 1
                    print(f"Force added: {name}")

        print(f"\\nForce added {added_count} commands from {file_path}")

    except Exception as e:
        print(f"Error parsing command file {file_path}: {e}")
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

    print(f"\\n=== FINAL VERIFICATION ===")
    print(f"Total entries: {final_total}")
    print(
        f"Total commands: {final_commands} (was {current_commands}, +{final_commands - current_commands})"
    )

    # Check for specific commands you wanted
    target_commands = [
        "1-sim/MH/DoubleClickFromXP",
        "1-sim/MH/LeftClickFromXP",
        "1-sim/MH/RightClickFromXP",
        "sim/comm/AP/CMD_C",
        "sim/comm/AP/CMD_L",
        "sim/comm/AP/CMD_R",
        "sim/command/AP/altHoldButton_button",
        "1-sim/MH/WheelIncDown",
        "1-sim/MH/WheelIncMinus",
        "1-sim/MH/WheelIncPlus",
        "1-sim/MH/WheelIncUp",
        "1-sim/MH/glewMode",
        "1-sim/MH/mainTrigger",
        "1-sim/MH/trimmer",
    ]

    print("\\n=== CHECKING FOR YOUR SPECIFIC COMMANDS ===")
    found_count = 0
    missing_count = 0

    for cmd in target_commands:
        if cmd in updated_data:
            found_count += 1
            entry = updated_data[cmd]
            print(f"✅ FOUND: {cmd} -> {entry.get('description', 'N/A')}")
        else:
            missing_count += 1
            print(f"❌ STILL MISSING: {cmd}")

    print(
        f"\\nFINAL RESULT: {found_count}/{len(target_commands)} specific commands found, {missing_count} missing"
    )


if __name__ == "__main__":
    force_add_specific_commands()
