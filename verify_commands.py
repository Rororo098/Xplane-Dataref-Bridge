import json


def verify_commands():
    """Simple verification script to show specific commands"""

    # Load database
    try:
        with open("resources/dataref_database.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading database: {e}")
        return

    # Commands to verify
    target_commands = [
        "sim/MH/DoubleClickFromXP",
        "sim/MH/LeftClickFromXP",
        "sim/MH/RightClickFromXP",
        "sim/MH/WheelIncDown",
        "sim/MH/WheelIncMinus",
        "sim/MH/WheelIncPlus",
        "sim/MH/WheelIncUp",
        "sim/MH/glewMode",
        "sim/MH/mainTrigger",
        "sim/MH/trimmer",
    ]

    print("=== COMMAND VERIFICATION ===")
    print(f"Database path: resources/dataref_database.json")
    print(f"Total entries in database: {len(data)}")

    print("\nChecking for specific commands:")
    found = 0
    missing = 0

    for cmd in target_commands:
        if cmd in data:
            found += 1
            entry = data[cmd]
            print(f"✅ FOUND: {cmd}")
            print(f"   Type: {entry.get('type', 'unknown')}")
            print(f"   Description: {entry.get('description', 'N/A')}")
            print(f"   Full entry: {entry}")
        else:
            missing += 1
            print(f"❌ MISSING: {cmd}")

    print(f"\n=== SUMMARY ===")
    print(f"Commands found: {found}")
    print(f"Commands missing: {missing}")

    # Show all sim/MH commands
    print(f"\n=== ALL sim/MH COMMANDS ===")
    mh_commands = [(k, v) for k, v in data.items() if "sim/MH/" in k]
    print(f"Total sim/MH commands: {len(mh_commands)}")

    for i, (name, entry) in enumerate(mh_commands, 1):
        print(f"{i:2d}. {name}")
        print(f"    Type: {entry.get('type', 'unknown')}")
        print(f"    Description: {entry.get('description', 'N/A')}")
        if i >= 5:  # Show only first 5
            print(f"    ... and {len(mh_commands) - 5} more")
            break


if __name__ == "__main__":
    verify_commands()
