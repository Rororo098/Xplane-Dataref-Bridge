import json
import re

def parse_commands_to_json(input_file, output_file, append_to_existing=False, existing_db="dataref_database.json"):
    """
    Parse the commands.txt file and convert it to JSON format for dataref database.
    
    Args:
        input_file (str): Path to the input commands.txt file
        output_file (str): Path to the output JSON file
        append_to_existing (bool): Whether to append to an existing database
        existing_db (str): Path to existing database file if appending
    """
    commands_list = []
    
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
            
            # Create a dictionary entry for the command
            command_entry = {
                "name": command,
                "description": description,
                "type": "command",  # Specify that this is a command, not a dataref
                "category": command.split('/')[1] if len(command.split('/')) > 1 else "unknown"
            }
            
            commands_list.append(command_entry)
        else:
            # If the split didn't work as expected, try another approach
            # Look for the first sequence of spaces and split there
            match = re.match(r'^(\S+)\s+(.+)$', line)
            if match:
                command = match.group(1)
                description = match.group(2)
                
                command_entry = {
                    "name": command,
                    "description": description,
                    "type": "command",
                    "category": command.split('/')[1] if len(command.split('/')) > 1 else "unknown"
                }
                
                commands_list.append(command_entry)
    
    # If appending to existing database, load it first
    if append_to_existing:
        try:
            with open(existing_db, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            print(f"Existing database {existing_db} not found. Creating new one.")
            existing_data = []
        
        # Add new commands to existing data, avoiding duplicates
        existing_names = {item['name'] for item in existing_data}
        new_items = [cmd for cmd in commands_list if cmd['name'] not in existing_names]
        combined_data = existing_data + new_items
        
        # Save to the existing database file
        with open(existing_db, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"Merged {len(new_items)} new commands with existing database.")
        print(f"Total entries in database: {len(combined_data)}")
        print(f"Saved to {existing_db}")
    else:
        # Write the parsed commands to a new JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(commands_list, f, indent=2, ensure_ascii=False)
        
        print(f"Parsed {len(commands_list)} commands from {input_file}")
        print(f"Saved to {output_file}")

def main():
    # Define input and output file paths
    input_file = "Commands.txt"
    output_file = "dataref_database.json"  # Changed to match your target database name
    
    # Ask user if they want to append to existing database
    append_choice = input("Do you want to append to an existing database? (y/n): ").lower().strip()
    if append_choice == 'y':
        existing_db = input("Enter the path to existing database (default: dataref_database.json): ").strip()
        if not existing_db:
            existing_db = "dataref_database.json"
        parse_commands_to_json(input_file, output_file, append_to_existing=True, existing_db=existing_db)
    else:
        # Just create a new file with the parsed commands
        parse_commands_to_json(input_file, output_file)

if __name__ == "__main__":
    main()