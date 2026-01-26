import json
import os


def add_1prefixed_commands():
    """Add the missing 1-sim/ commands that were missed"""

    # Load current database
    db_path = "resources/dataref_database.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_commands = sum(1 for v in data.values() if v.get("type") == "command")
    print(f"Current database has {current_commands} commands")

    # Parse the commands (2).txt file with 1- prefix
    file_path = "XP12 dataref list and commands/commands (2).txt"
    added_count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines, headers, lines with pipes
                if not line or line.startswith("#") or "|" in line or line.isdigit():
                    continue

                # Look for 1- prefix commands
                if line.startswith("1-sim/"):
                    cmd_name = line.strip()

                    # Find first space to separate name from description
                    if " " in cmd_name:
                        first_space = cmd_name.find(" ")
                        name = cmd_name[:first_space].strip()
                        description = cmd_name[first_space:].strip()
                    else:
                        name = cmd_name
                        description = "Command"

                    # Add to database if not already present
                    if name not in data:
                        data[name] = {
                            "name": name,
                            "type": "command",
                            "description": description,
                            "units": "",
                            "writable": False,
                        }
                        added_count += 1
                        print(f"Added: {name}")

        print(f"Added {added_count} 1-prefixed commands from {file_path}")

    except Exception as e:
        print(f"Error parsing command file {file_path}: {e}")
        return 0

    # Save updated database
    print(f"\\nTotal new commands added: {added_count}")
    print("Saving updated database...")

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

    # Check for specific 1-sim commands
    print("\\n=== CHECKING FOR 1-sim/MH COMMANDS ===")
    target_commands = [
        "1-sim/MH/DoubleClickFromXP",
        "1-sim/MH/LeftClickFromXP",
        "1-sim/MH/RightClickFromXP",
        "1-sim/MH/WheelIncDown",
        "1-sim/MH/WheelIncMinus",
        "1-sim/MH/WheelIncPlus",
        "1-sim/MH/WheelIncUp",
        "1-sim/MH/glewMode",
        "1-sim/MH/mainTrigger",
        "1-sim/MH/trimmer",
    ]

    found = 0
    missing = 0
    for cmd in target_commands:
        if cmd in updated_data:
            found += 1
        else:
            missing += 1
            print(f"STILL MISSING: {cmd}")

    print(f"Found {found} of {len(target_commands)} 1-sim/MH commands")
    print(f"Missing {missing} of {len(target_commands)} 1-sim/MH commands")


if __name__ == "__main__":
    add_1prefixed_commands()
