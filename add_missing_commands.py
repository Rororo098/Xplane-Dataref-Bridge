import json
import os


def parse_command_file_with_prefix(file_path: str, data: dict):
    """Parse command file that has numeric prefixes like '1-sim/MH/ClickFromXP'"""
    added_count = 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines, headers, lines with pipes
                if (
                    not line
                    or line.startswith("#")
                    or "|" in line
                    or line.isdigit()
                    or not line.startswith("1-")
                ):
                    continue

                # Remove the '1-' prefix
                if line.startswith("1-"):
                    cmd_name = line[2:].strip()
                else:
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
                    print(f"Added command: {name}")

        print(f"Added {added_count} commands from {file_path}")
        return added_count

    except Exception as e:
        print(f"Error parsing command file {file_path}: {e}")
        return 0


def add_missing_commands():
    """Add missing command files to database"""

    # Load current database
    db_path = "resources/dataref_database.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_commands = sum(1 for v in data.values() if v.get("type") == "command")
    print(f"Current database has {current_commands} commands")

    # Add commands from files with prefix format
    command_files = ["XP12 dataref list and commands/commands (2).txt"]

    total_added = 0
    for file_path in command_files:
        if os.path.exists(file_path):
            added = parse_command_file_with_prefix(file_path, data)
            total_added += added

    # Save updated database
    print(f"\\nTotal new commands added: {total_added}")
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

    print("\\nSample new commands:")
    new_commands = [
        (k, v)
        for k, v in updated_data.items()
        if v.get("type") == "command" and k.startswith("sim/MH/")
    ]

    for name, cmd_info in new_commands[:5]:
        print(f"  {name}: {cmd_info.get('description', 'N/A')[:50]}...")


if __name__ == "__main__":
    add_missing_commands()
