import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


class DatarefEntry:
    def __init__(
        self,
        name: str,
        data_type: str,
        units: str = "",
        writable: bool = False,
        description: str = "",
        version: Optional[str] = None,
        array_size: Optional[int] = None,
    ):
        self.name = name
        self.data_type = data_type
        self.units = units
        self.writable = writable
        self.description = description
        self.version = version
        self.array_size = array_size


class DatabaseMerger:
    def __init__(self):
        self.datarefs = {}
        self.commands = {}
        self.stats = {
            "new_datarefs": 0,
            "new_commands": 0,
            "errors": 0,
            "version_matches": 0,
        }

    def load_version_info(self, file_path: str) -> Dict[str, str]:
        """Load version information from XPLANE_DB_DW.json"""
        version_info = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if "path" in item:
                        version = item.get("version", "unknown")
                        # Clean up version string (remove double v, etc.)
                        if version.startswith("vv"):
                            version = version[1:]  # Remove one v
                        elif not version.startswith("v"):
                            version = "v" + version
                        version_info[item["path"]] = version
        except Exception as e:
            print(f"Error loading version info: {e}")
        return version_info

    def parse_command_file(self, file_path: str) -> List[DatarefEntry]:
        """Parse command file - commands are in format: name followed by description"""
        commands = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip header lines and empty lines
                    if (
                        not line
                        or line.startswith("#")
                        or "|" in line
                        or line.isdigit()
                    ):
                        continue

                    # Find first space to separate name from description
                    if " " in line:
                        first_space = line.find(" ")
                        name = line[:first_space].strip()
                        description = line[first_space:].strip()

                        cmd = DatarefEntry(name, "command", "", False, description)
                        commands.append(cmd)
                    else:
                        # Just name, no description
                        cmd = DatarefEntry(line, "command", "", False, "Command")
                        commands.append(cmd)
        except Exception as e:
            print(f"Error parsing command file {file_path}: {e}")
            self.stats["errors"] += 1
        return commands

    def parse_dataref_file(self, file_path: str) -> List[DatarefEntry]:
        """Parse dataref file - tabular format: name\ttype\twritable\tunits\tdescription"""
        datarefs = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip header lines and empty lines
                    if (
                        not line
                        or line.startswith("#")
                        or "|" in line
                        or line.isdigit()
                        or not "\t" in line
                    ):
                        continue

                    # Split into columns
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        type_info = parts[1].strip() if len(parts) > 1 else ""
                        writable_info = parts[2].strip() if len(parts) > 2 else ""
                        units = parts[3].strip() if len(parts) > 3 else ""
                        description = parts[4].strip() if len(parts) > 4 else ""

                        # Detect data type
                        data_type, writable = self.detect_type_and_writable(
                            type_info, name, description
                        )

                        # Override writability from explicit flag
                        if writable_info == "y":
                            writable = True
                        elif writable_info == "n":
                            writable = False

                        # Check for arrays
                        array_size = None
                        if "[" in name and "]" in name:
                            array_match = re.search(r"\[([0-9]+)\]", name)
                            if array_match:
                                array_size = int(array_match.group(1))

                        entry = DatarefEntry(
                            name, data_type, units, writable, description
                        )
                        entry.array_size = array_size
                        datarefs.append(entry)
        except Exception as e:
            print(f"Error parsing dataref file {file_path}: {e}")
            self.stats["errors"] += 1
        return datarefs

    def detect_type_and_writable(
        self, type_info: str, name: str, description: str
    ) -> tuple:
        """Detect data type and writability from context"""
        # Default values
        data_type = "float"
        writable = False

        # Check explicit type
        type_lower = type_info.lower()
        if "float" in type_lower or type_info == "y":
            data_type = "float"
        elif "int" in type_lower or "integer" in type_lower:
            data_type = "int"
        elif "bool" in type_lower or "boolean" in type_lower:
            data_type = "boolean"
        elif "byte" in type_lower:
            data_type = "byte"

        # Check writability
        if type_info == "y" or "writable" in type_lower:
            writable = True
        elif type_info == "n" or "read only" in type_lower or "readonly" in type_lower:
            writable = False

        # Infer from description
        if not type_info:
            desc_lower = description.lower()
            if any(kw in desc_lower for kw in ["seconds", "time", "hz"]):
                data_type = "float"
            elif any(kw in desc_lower for kw in ["count", "number", "index"]):
                data_type = "int"
            elif any(kw in desc_lower for kw in ["boolean", "bool", "on", "off"]):
                data_type = "boolean"

        return data_type, writable

    def process_files(
        self,
        dataref_files: List[str],
        version_db: Optional[str],
        command_files: List[str],
        output_path: str,
    ):
        """Process all files and merge them"""
        # Load version info
        version_info = {}
        if version_db:
            version_info = self.load_version_info(version_db)
            print(f"Loaded {len(version_info)} version entries")

        # Process dataref files
        for file_path in dataref_files:
            print(f"Processing dataref file: {file_path}")
            datarefs = self.parse_dataref_file(file_path)
            for entry in datarefs:
                if entry.name not in self.datarefs:
                    # Add version info to description if available
                    version_found = None
                    if (
                        entry.name in version_info
                        and version_info[entry.name] != "unknown"
                    ):
                        version_found = version_info[entry.name]
                        self.stats["version_matches"] += 1

                    if version_found:
                        # Clean up version format
                        clean_version = str(version_found)
                        if clean_version.startswith("vv"):
                            clean_version = clean_version[1:]
                        elif not clean_version.startswith("v"):
                            clean_version = "v" + clean_version
                        version_prefix = clean_version + " - "
                        entry.description = version_prefix + entry.description

                    self.datarefs[entry.name] = entry
                    self.stats["new_datarefs"] += 1

        # Process command files
        for file_path in command_files:
            print(f"Processing command file: {file_path}")
            commands = self.parse_command_file(file_path)
            for cmd in commands:
                if cmd.name not in self.commands:
                    # Add version info to description if available
                    version_found = None
                    if cmd.name in version_info and version_info[cmd.name] != "unknown":
                        version_found = version_info[cmd.name]
                        self.stats["version_matches"] += 1

                    if version_found:
                        # Clean up version format
                        clean_version = str(version_found)
                        if clean_version.startswith("vv"):
                            clean_version = clean_version[1:]
                        elif not clean_version.startswith("v"):
                            clean_version = "v" + clean_version
                        version_prefix = clean_version + " - "
                        cmd.description = version_prefix + cmd.description

                    self.commands[cmd.name] = cmd
                    self.stats["new_commands"] += 1

        # Merge and save
        return self.merge_data(output_path)

    def merge_data(self, output_path: str):
        """Merge all parsed data into unified database"""
        # Load existing database
        existing_data = {}
        if Path(output_path).exists():
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"Error loading existing database: {e}")

        # Convert entries to dict format
        for name, entry in self.datarefs.items():
            entry_dict = {
                "name": entry.name,
                "type": entry.data_type,
                "description": entry.description,
                "units": entry.units,
                "writable": entry.writable,
            }
            if entry.array_size:
                entry_dict["array_size"] = entry.array_size
            if entry.version:
                entry_dict["version"] = entry.version

            existing_data[name] = entry_dict

        # Convert commands to dict format
        for name, entry in self.commands.items():
            entry_dict = {
                "name": entry.name,
                "type": entry.data_type,  # 'command'
                "description": entry.description,
                "units": entry.units,
                "writable": entry.writable,
            }
            if entry.version:
                entry_dict["version"] = entry.version

            existing_data[name] = entry_dict

        # Write merged database
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=2, sort_keys=True)
            print(f"Successfully wrote database to {output_path}")
            return True
        except Exception as e:
            print(f"Error writing database: {e}")
            return False


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python merge_xplane_data_fixed.py <output_db.json> <xplane_db.json> [dataref_file.txt] [command_file.txt]"
        )
        return

    output_db = sys.argv[1]
    version_db = None

    # Collect files by type
    dataref_files = []
    command_files = []

    for i in range(2, len(sys.argv)):
        arg = sys.argv[i]
        if arg.endswith(".json"):
            version_db = arg
        elif arg.endswith(".txt") and ("dataref" in arg.lower() or "DataRefs" in arg):
            dataref_files.append(arg)
        elif arg.endswith(".txt") and "command" in arg.lower():
            command_files.append(arg)

    print(f"Output database: {output_db}")
    if version_db:
        print(f"Version database: {version_db}")
    print(f"Dataref files: {dataref_files}")
    print(f"Command files: {command_files}")

    merger = DatabaseMerger()
    success = merger.process_files(dataref_files, version_db, command_files, output_db)

    if success:
        print("\nProcessing complete. Statistics:")
        print(f"  New datarefs: {merger.stats['new_datarefs']}")
        print(f"  New commands: {merger.stats['new_commands']}")
        print(f"  Version matches: {merger.stats['version_matches']}")
        print(
            f"  Total entries: {merger.stats['new_datarefs'] + merger.stats['new_commands']}"
        )
        if merger.stats["errors"] > 0:
            print(f"  Errors encountered: {merger.stats['errors']}")


if __name__ == "__main__":
    main()
