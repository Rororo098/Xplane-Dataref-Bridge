import json

# Simple script to show you what's in the database
with open("resources/dataref_database.json", "r") as f:
    data = json.load(f)

print("=== ALL COMMANDS IN DATABASE ===")
print(f"Total commands: {sum(1 for v in data.values() if v.get('type') == 'command')}")

# Show all commands that contain 'MH'
mh_commands = []
for name, entry in data.items():
    if entry.get("type") == "command" and "MH" in name:
        mh_commands.append((name, entry.get("description", "N/A")))

print(f"Commands with 'MH': {len(mh_commands)}")
print("First 15 MH commands:")
for i, (name, desc) in enumerate(mh_commands[:15], 1):
    print(f"{i:2d}. {name}")
    print(f"    Description: {desc}")

# Also check for 1-sim prefix commands
print(
    f"\nCommands with '1-sim': {len([k for k in data.keys() if k.startswith('1-sim') and data[k].get('type') == 'command'])}"
)

print(
    "\nIf you're looking for commands with '1-sim' prefix, there should be some here!"
)
print("\nTry searching for these exact strings:")
print('"1-sim/MH/DoubleClickFromXP"')
print('"1-sim/MH/LeftClickFromXP"')
print('"1-sim/MH/RightClickFromXP"')
print("\nUse your text editor's search (Ctrl+F) to find them in the database file.")
