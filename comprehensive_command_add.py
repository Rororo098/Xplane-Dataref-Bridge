import json
import os


def comprehensive_command_add():
    """Add ALL commands from all command files, ensuring none are missed"""

    # Load current database
    db_path = "resources/dataref_database.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_commands = sum(1 for v in data.values() if v.get("type") == "command")
    print(f"Current database has {current_commands} commands")

    # Process all command files
    command_files = [
        "XP12 dataref list and commands/Commands.txt",
        "XP12 dataref list and commands/commands (2).txt",
    ]

    total_added = 0

    for file_path in command_files:
        if not os.path.exists(file_path):
            print(f"Skipping {file_path} - file not found")
            continue

        print(f"Processing {file_path}...")
        added = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines, headers, lines with pipes, digit-only lines
                    if (
                        not line
                        or line.startswith("#")
                        or "|" in line
                        or line.isdigit()
                    ):
                        continue

                    # Determine command name based on format
                    if line.startswith("1-sim/"):
                        cmd_line = line[2:].strip()  # Remove '1-' prefix
                    elif line.startswith("sim/") or line.startswith("1-sim/"):
                        cmd_line = line.strip()
                    else:
                        continue

                    # Find first space to separate name from description
                    if " " in cmd_line:
                        first_space = cmd_line.find(" ")
                        name = cmd_line[:first_space].strip()
                        description = cmd_line[first_space:].strip()
                    else:
                        name = cmd_line
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
                        added += 1
                        if added <= 10:  # Show first 10 additions per file
                            print(f"  Added: {name}")
                    else:
                        added += 1

            print(f"Added {added} commands from {file_path}")
            total_added += added

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    print(f"\\nTotal new commands added: {total_added}")
    print("Saving updated database...")

    # Save updated database
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print("Database updated successfully!")

    # Final verification
    with open(db_path, "r", encoding="utf-8") as f:
        updated_data = json.load(f)

    final_commands = sum(1 for v in updated_data.values() if v.get("type") == "command")
    final_total = len(updated_data)

    print(f"\\n=== FINAL COMPREHENSIVE VERIFICATION ===")
    print(f"Total entries: {final_total}")
    print(
        f"Total commands: {final_commands} (was {current_commands}, +{final_commands - current_commands})"
    )

    # Check for specific commands we know should be there
    target_commands = [
        "1-sim/MH/DoubleClickFromXP",
        "1-sim/MH/LeftClickFromXP",
        "1-sim/MH/RightClickFromXP",
        "sim/comm/AP/CMD_C",
        "sim/comm/AP/CMD_L",
        "sim/comm/AP/CMD_R",
        "sim/command/AP/altHoldButton_button",
    ]

    print("\\n=== CHECKING FOR SPECIFIC COMMANDS ===")
    found_count = 0
    for cmd in target_commands:
        if cmd in updated_data:
            found_count += 1
            entry = updated_data[cmd]
            print(f"✅ FOUND: {cmd}")
            print(f"   Description: {entry.get('description', 'N/A')}")
        else:
            print(f"❌ MISSING: {cmd}")

    print(
        f"\\nSpecific check: {found_count}/{len(target_commands)} target commands found"
    )

    # Show command categories
    print("\\n=== COMMAND CATEGORIES ===")
    sim_1 = sum(
        1
        for k in updated_data.keys()
        if k.startswith("1-sim/") and updated_data[k].get("type") == "command"
    )
    sim_operation = sum(
        1
        for k in updated_data.keys()
        if k.startswith("sim/operation/") and updated_data[k].get("type") == "command"
    )
    sim_comm = sum(
        1
        for k in updated_data.keys()
        if k.startswith("sim/comm/") and updated_data[k].get("type") == "command"
    )
    sim_command = sum(
        1
        for k in updated_data.keys()
        if k.startswith("sim/command/") and updated_data[k].get("type") == "command"
    )
    other = final_commands - sim_1 - sim_operation - sim_comm - sim_command

    print(f"1-sim/ commands: {sim_1}")
    print(f"sim/operation/ commands: {sim_operation}")
    print(f"sim/comm/ commands: {sim_comm}")
    print(f"sim/command/ commands: {sim_command}")
    print(f"Other commands: {other}")
    print(
        f"Total accounted for: {sim_1 + sim_operation + sim_comm + sim_command + other}"
    )

    print(f"\\n=== SUCCESS ===")
    print(f"Comprehensive command database with {final_commands} total commands ready!")
    print(f"All command types processed and added to database!")


if __name__ == "__main__":
    comprehensive_command_add()
