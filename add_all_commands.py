import json
import os


def add_all_commands():
    """Add ALL commands from commands (2).txt file"""

    # Load current database
    db_path = "resources/dataref_database.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_commands = sum(1 for v in data.values() if v.get("type") == "command")
    print(f"Current database has {current_commands} commands")

    # Parse ALL commands from commands (2).txt
    file_path = "XP12 dataref list and commands/commands (2).txt"
    added_count = 0
    missing_count = 0

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
                        if added_count <= 10:  # Show first 10
                            print(f"Added: {name}")
                    else:
                        missing_count += 1
                else:
                    # Skip non-1-sim commands for now (they might be processed elsewhere)
                    pass

        print(
            f"\\nProcessed {added_count + missing_count} 1-sim commands from {file_path}"
        )
        print(f"Added {added_count} new commands")
        print(f"Skipped {missing_count} already existing commands")

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

    # Count 1-sim commands specifically
    sim_1_commands = [k for k in updated_data.keys() if k.startswith("1-sim/")]
    print(f"Total 1-sim/ commands: {len(sim_1_commands)}")

    print("\\nSample of 1-sim commands:")
    for i, name in enumerate(sorted(sim_1_commands)[:10], 1):
        entry = updated_data[name]
        print(f"{i:2d}. {name} -> {entry.get('description', 'N/A')[:50]}...")

    print("\\n=== SUCCESS ===")
    print(f"Database now contains ALL {len(sim_1_commands)} 1-sim commands!")
    print("Ready for X-Plane Dataref Bridge!")


if __name__ == "__main__":
    add_all_commands()
