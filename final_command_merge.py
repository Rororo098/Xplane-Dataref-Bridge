import json
import os


def final_command_merge():
    """Final comprehensive merge of ALL command files"""

    # Load current database
    db_path = "resources/dataref_database.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_commands = sum(1 for v in data.values() if v.get("type") == "command")
    print(f"Starting with {current_commands} commands in database")

    # Process ALL command files comprehensively
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
        duplicate_count = 0

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
                        or not line.strip()
                    ):
                        continue

                    # Determine command name based on format
                    if line.startswith("1-sim/"):
                        cmd_line = line[2:].strip()  # Remove '1-' prefix
                    elif line.startswith("sim/") or line.startswith("1-sim/"):
                        cmd_line = line.strip()
                    else:
                        continue  # Skip malformed lines

                    # Find first space to separate name from description
                    if " " in cmd_line:
                        first_space = cmd_line.find(" ")
                        name = cmd_line[:first_space].strip()
                        description = cmd_line[first_space:].strip()
                    else:
                        name = cmd_line
                        description = "Command" if not description else description

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
                        duplicate_count += 1

            print(
                f"Added {added} commands, {duplicate_count} duplicates from {file_path}"
            )
            total_added += added

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

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

    print(f"\\n=== FINAL COMPREHENSIVE VERIFICATION ===")
    print(f"Total entries: {final_total}")
    print(
        f"Total commands: {final_commands} (was {current_commands}, +{final_commands - current_commands})"
    )

    # Check for specific commands you wanted
    target_commands = [
        "sim/comm/AP/CMD_C",
        "sim/comm/AP/CMD_L",
        "sim/comm/AP/CMD_R",
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

    print("\\n=== CHECKING ALL TARGET COMMANDS ===")
    found_count = 0
    missing_count = 0

    for cmd in target_commands:
        if cmd in updated_data:
            found_count += 1
            entry = updated_data[cmd]
            print(f"✅ FOUND: {cmd} -> {entry.get('description', 'N/A')}")
        else:
            missing_count += 1
            print(f"❌ MISSING: {cmd}")

    print(
        f"\\nTARGET STATUS: {found_count}/{len(target_commands)} found, {missing_count} missing"
    )

    if missing_count > 0:
        print("\\n⚠️  SOME TARGET COMMANDS STILL MISSING!")
        print("The final merge should have included all commands.")
        print("Let me check the command file format...")

        # Check specific file for the missing ones
        missing_file = "XP12 dataref list and commands/commands (2).txt"
        if os.path.exists(missing_file):
            print(f"\\nChecking {missing_file} for missing commands...")
            with open(missing_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if missing_count <= 0:
                        break
                    line = line.strip()
                    if not line or not line.startswith("1-sim/"):
                        continue

                    cmd_line = line[2:].strip()
                    first_space = cmd_line.find(" ")
                    name = cmd_line[:first_space].strip()

                    if name in target_commands and name not in updated_data:
                        print(f"Line {line_num}: {name} (MISSING from database)")

    print(f"\\n=== FINAL RESULT ===")
    print(f"Database now contains {final_commands} commands ready for use!")
    return final_commands >= current_commands


if __name__ == "__main__":
    final_command_merge()
