import json
import re

def parse_commands_to_new_format(input_file, output_file):
    """
    Parse the commands.txt file and convert it to the new object format for dataref database.

    Args:
        input_file (str): Path to the input commands.txt file
        output_file (str): Path to the output JSON file
    """
    commands_dict = {}

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Split the line into command and description
        # The format appears to be: command followed by multiple spaces and then description
        parts = re.split(r'\s{2,}', line)  # Split on 2 or more spaces

        if len(parts) >= 2:
            command = parts[0].strip()
            description = ' '.join(parts[1:]).strip()  # Join all remaining parts as description

            # Create an entry in the dictionary format you specified
            commands_dict[command] = {
                "description": description,
                "type": "command",  # Commands are a specific type
                "writable": False  # Commands are typically not writable in the same way as datarefs
            }
        else:
            # If the split didn't work as expected, try another approach
            # Look for the first sequence of spaces and split there
            match = re.match(r'^(\S+)\s+(.+)$', line)
            if match:
                command = match.group(1)
                description = match.group(2)

                commands_dict[command] = {
                    "description": description,
                    "type": "command",
                    "writable": False
                }

    # Write the parsed commands to a JSON file in the new format
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(commands_dict, f, indent=2, ensure_ascii=False)

    print(f"Parsed {len(commands_dict)} commands from {input_file}")
    print(f"Saved to {output_file}")
    return commands_dict

if __name__ == "__main__":
    # Define input and output file paths
    input_file = "Commands.txt"  # Adjust path as needed
    output_file = "datarefcommands_database.json"  # Changed to your target database name

    # Parse the commands in the new format
    commands = parse_commands_to_new_format(input_file, output_file)