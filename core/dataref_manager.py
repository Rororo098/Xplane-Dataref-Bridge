from __future__ import annotations
import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from core.input_mapper import ConditionRule, LogicGate
from core.variable_store import VariableType

log = logging.getLogger(__name__)

DATAREF_DATABASE_FILE = "dataref_database.json"

# Try multiple possible paths for the database
POSSIBLE_PATHS = [
    Path(__file__).parent.parent / "resources" / DATAREF_DATABASE_FILE,
    Path.cwd() / "resources" / DATAREF_DATABASE_FILE,
    Path(__file__).parent / "resources" / DATAREF_DATABASE_FILE,
]

# Path to custom definitions
CUSTOM_DATAREFS_FILE = Path(__file__).parent.parent / "config" / "custom_datarefs.json"


class DatarefManager:
    """Manages X-Plane dataref definitions and provides search functionality."""
    
    def __init__(self, variable_store=None, arduino_manager=None, logic_engine=None) -> None:
        self.variable_store = variable_store
        self.arduino_manager = arduino_manager
        self.logic_engine = logic_engine
        
        self._database: Dict[str, Any] = {}
        self._subscriptions: Dict[str, float] = {}
        self._categories: Dict[str, List[str]] = {}
        self._custom_datarefs: Dict[str, dict] = {}

        self._load_database()
        self.load_custom_datarefs()
        self._build_categories()

    def parse_array_type(self, type_str: str) -> tuple[int, list[int]]:
        """
        Parse array type string and return (flattened_size, dimensions_list).

        Examples:
        - 'float[8]' -> (8, [8])
        - 'float[8][4]' -> (32, [8, 4])
        - 'int[5][3][2]' -> (30, [5, 3, 2])
        - 'float' -> (0, [])
        """
        if not type_str:
            return 0, []

        # Find all bracketed numbers
        dimension_matches = re.findall(r'\[(\d+)\]', type_str)

        if not dimension_matches:
            return 0, []  # Not an array

        # Convert to integers
        dimensions = [int(dim) for dim in dimension_matches]

        # Calculate flattened size by multiplying all dimensions
        flattened_size = 1
        for dim in dimensions:
            flattened_size *= dim

        return flattened_size, dimensions

    def get_array_size_from_type(self, type_str: str) -> int:
        """Extract array size from type string (e.g., 'float[8]' -> 8)."""
        flattened_size, _ = self.parse_array_type(type_str)
        return flattened_size

    def get_expanded_datarefs(self):
        """Return datarefs with arrays expanded into per-element entries."""
        out = []
        for name, info in self._database.items():
            type_str = info.get("type", "")
            flattened_size = info.get("array_size", 0)

            if flattened_size > 0:
                base = name.split("[")[0]  # Extract base name from array notation
                dimensions = info.get("dimensions", [])

                # If we have a value that's a list/array, use it; otherwise create placeholder values
                original_value = info.get("value", [0] * flattened_size if isinstance(info.get("value"), list) else 0)

                # Handle case where original_value is a list/array
                if isinstance(original_value, (list, tuple)):
                    # Generate all possible indices for multidimensional arrays
                    element_indices = self._generate_element_indices(dimensions)

                    for idx, flat_idx in enumerate(element_indices):
                        if idx < len(original_value):
                            out.append({
                                "name": f"{base}{flat_idx}",
                                "type": type_str,
                                "description": f"{info.get('description', '')} {flat_idx}",
                                "writable": info.get("writable", False),
                                "value": original_value[idx],
                                "custom": info.get("custom", False),
                                "base_name": base,
                                "element_index": flat_idx,
                                "flat_index": idx
                            })
                        else:
                            # If we don't have enough values, use placeholder
                            out.append({
                                "name": f"{base}{flat_idx}",
                                "type": type_str,
                                "description": f"{info.get('description', '')} {flat_idx}",
                                "writable": info.get("writable", False),
                                "value": 0.0,  # Placeholder value
                                "custom": info.get("custom", False),
                                "base_name": base,
                                "element_index": flat_idx,
                                "flat_index": idx
                            })
                else:
                    # If not a list, create individual entries with placeholder values
                    element_indices = self._generate_element_indices(dimensions)

                    for idx, flat_idx in enumerate(element_indices):
                        out.append({
                            "name": f"{base}{flat_idx}",
                            "type": type_str,
                            "description": f"{info.get('description', '')} {flat_idx}",
                            "writable": info.get("writable", False),
                            "value": 0.0,  # Placeholder value
                            "custom": info.get("custom", False),
                            "base_name": base,
                            "element_index": flat_idx,
                            "flat_index": idx
                        })
            else:
                # Non-array dataref, add as-is
                info_copy = info.copy()
                info_copy["name"] = name
                info_copy["base_name"] = name
                info_copy["element_index"] = ""
                info_copy["flat_index"] = -1
                out.append(info_copy)

        return out

    def _generate_element_indices(self, dimensions: list[int]) -> list[str]:
        """
        Generate all possible index combinations for multidimensional arrays.

        Examples:
        - [8] -> ["[0]", "[1]", ..., "[7]"]
        - [2, 3] -> ["[0][0]", "[0][1]", "[0][2]", "[1][0]", "[1][1]", "[1][2]"]
        - [2, 3, 4] -> ["[0][0][0]", "[0][0][1]", ..., "[1][2][3]"]
        """
        if not dimensions:
            return []

        # Generate all combinations of indices
        combinations = [[]]

        for dim_size in dimensions:
            new_combinations = []
            for combo in combinations:
                for i in range(dim_size):
                    new_combinations.append(combo + [i])
            combinations = new_combinations

        # Convert to string format like "[0][1][2]"
        result = []
        for combo in combinations:
            index_str = "".join([f"[{idx}]" for idx in combo])
            result.append(index_str)

        return result

    def get_base_dataref_from_element(self, element_name: str) -> tuple[str, int, list[int]]:
        """
        Map a per-element name back to its base dataref and determine the flat index.

        Args:
            element_name: Name of the element (e.g., "sim/flightmodel/controls/yawb_def[2]")

        Returns:
            Tuple of (base_name, flat_index, dimensions) or (None, -1, []) if not found
        """
        # Extract base name by removing the index part
        base_match = re.match(r'^(.+?)(\[\d+\].*)$', element_name)
        if not base_match:
            return "", -1, []

        base_name = base_match.group(1)
        index_part = base_match.group(2)  # e.g., "[2][1]"

        # Look up the base dataref in our database
        if base_name not in self._database:
            return "", -1, []

        base_info = self._database[base_name]
        dimensions = base_info.get("dimensions", [])

        if not dimensions:
            # Not an array, return as-is
            return base_name, -1, []

        # Parse the indices from the element name
        indices = []
        for match in re.finditer(r'\[(\d+)\]', index_part):
            indices.append(int(match.group(1)))

        # Validate indices against dimensions
        if len(indices) != len(dimensions):
            return "", -1, []

        for i, (idx, dim_size) in enumerate(zip(indices, dimensions)):
            if idx >= dim_size:
                return "", -1, []

        # Calculate the flat index based on multidimensional indices
        flat_index = 0
        multiplier = 1

        # Calculate flat index using row-major order (last dimension changes fastest)
        for i in range(len(dimensions) - 1, -1, -1):
            if i == len(dimensions) - 1:
                flat_index = indices[i]
            else:
                flat_index += indices[i] * multiplier
            multiplier *= dimensions[i]

        return base_name, flat_index, dimensions

    def update_array_element_value(self, element_name: str, value: float) -> bool:
        """
        Update a specific element in an array dataref.

        Args:
            element_name: Name of the element to update (e.g., "sim/flightmodel/controls/yawb_def[2]")
            value: New value for the element

        Returns:
            True if update was successful, False otherwise
        """
        base_name, flat_index, dimensions = self.get_base_dataref_from_element(element_name)

        if not base_name or flat_index < 0 or not dimensions:
            return False

        # Get the base dataref info
        base_info = self._database[base_name]
        array_size = base_info.get("array_size", 0)

        if array_size <= 0:
            return False

        # Initialize the value array if it doesn't exist
        if "value" not in base_info or not isinstance(base_info["value"], list):
            base_info["value"] = [0.0] * array_size

        # Update the specific element
        if 0 <= flat_index < len(base_info["value"]):
            base_info["value"][flat_index] = value

            # Also update the corresponding expanded element in the subscription cache if it exists
            if element_name in self._subscriptions:
                self._subscriptions[element_name] = value

            return True

        return False

    def _load_database(self) -> None:
        """Load dataref database from JSON file."""

        # Try each possible path
        for db_path in POSSIBLE_PATHS:
            log.info("Trying dataref database path: %s", db_path)

            if db_path.exists():
                try:
                    with open(db_path, 'r', encoding='utf-8') as f:
                        self._database = json.load(f)

                    # Enhance all entries with array metadata and ensure description field
                    for name, info in self._database.items():
                        if "description" not in info:
                            info["description"] = ""

                        # Add array metadata
                        type_str = info.get("type", "")
                        flattened_size, dimensions = self.parse_array_type(type_str)
                        if flattened_size > 0:
                            info["array_size"] = flattened_size
                            info["dimensions"] = dimensions
                            info["is_array"] = True
                        else:
                            info["array_size"] = 0
                            info["dimensions"] = []
                            info["is_array"] = False

                    log.info("Loaded %d datarefs from: %s", len(self._database), db_path)
                    return
                except Exception as e:
                    log.error("Failed to load dataref database from %s: %s", db_path, e)

        log.warning("No dataref database found. Searched paths:")
        for p in POSSIBLE_PATHS:
            log.warning("  - %s (exists: %s)", p, p.exists())

        # Create a minimal default database
        self._create_default_database()

    def load_custom_datarefs(self):
        """Load user-defined custom datarefs."""
        if not CUSTOM_DATAREFS_FILE.exists():
            # Create directory if it doesn't exist
            CUSTOM_DATAREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
            return

        try:
            with open(CUSTOM_DATAREFS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Format: {"name": {"type": "float", "description": "...", "writable": true}}
                self._custom_datarefs = data
                # Add custom datarefs to main database and mark as custom
                for name, info in self._custom_datarefs.items():
                    info["custom"] = True
                    self._database[name] = info
                log.info(f"Loaded {len(self._custom_datarefs)} custom datarefs.")
        except Exception as e:
            log.error(f"Failed to load custom datarefs: {e}")

    def save_custom_datarefs(self):
        """Persist custom datarefs to disk."""
        try:
            with open(CUSTOM_DATAREFS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._custom_datarefs, f, indent=4)
            log.info("Saved custom datarefs.")
        except Exception as e:
            log.error(f"Failed to save custom datarefs: {e}")
    
    def _create_default_database(self) -> None:
        """Create a minimal default database with common datarefs."""
        log.info("Creating default dataref database...")

        self._database = {
            # Gear
            "sim/cockpit2/switches/gear_handle_status": {
                "type": "int", "writable": True,
                "description": "Gear handle: 0=up, 1=down",
                "category": "gear"
            },
            # Controls
            "sim/cockpit2/controls/flap_ratio": {
                "type": "float", "writable": True,
                "description": "Flap deployment 0-1",
                "category": "controls"
            },
            "sim/cockpit2/controls/yoke_pitch_ratio": {
                "type": "float", "writable": True,
                "description": "Yoke pitch -1 to 1",
                "category": "controls"
            },
            "sim/cockpit2/controls/yoke_roll_ratio": {
                "type": "float", "writable": True,
                "description": "Yoke roll -1 to 1",
                "category": "controls"
            },
            "sim/cockpit2/controls/parking_brake_ratio": {
                "type": "float", "writable": True,
                "description": "Parking brake 0-1",
                "category": "controls"
            },
            # Engine
            "sim/cockpit2/engine/actuators/throttle_ratio_all": {
                "type": "float", "writable": True,
                "description": "All throttles 0-1",
                "category": "engine"
            },
            # Autopilot
            "sim/cockpit/autopilot/autopilot_state": {
                "type": "int", "writable": False,
                "description": "Autopilot state bitfield",
                "category": "autopilot"
            },
            "sim/cockpit/autopilot/heading_mag": {
                "type": "float", "writable": True,
                "description": "AP heading bug",
                "category": "autopilot"
            },
            "sim/cockpit/autopilot/altitude": {
                "type": "float", "writable": True,
                "description": "AP target altitude",
                "category": "autopilot"
            },
            # Warnings
            "sim/cockpit/warnings/master_warning": {
                "type": "int", "writable": False,
                "description": "Master warning light",
                "category": "warnings"
            },
            "sim/cockpit/warnings/master_caution": {
                "type": "int", "writable": False,
                "description": "Master caution light",
                "category": "warnings"
            },
            # Lights
            "sim/cockpit2/switches/beacon_on": {
                "type": "int", "writable": True,
                "description": "Beacon light switch",
                "category": "lights"
            },
            "sim/cockpit2/switches/landing_lights_on": {
                "type": "int", "writable": True,
                "description": "Landing lights switch",
                "category": "lights"
            },
            "sim/cockpit2/switches/navigation_lights_on": {
                "type": "int", "writable": True,
                "description": "Nav lights switch",
                "category": "lights"
            },
            "sim/cockpit2/switches/strobe_lights_on": {
                "type": "int", "writable": True,
                "description": "Strobe lights switch",
                "category": "lights"
            },
            # Instruments
            "sim/cockpit2/gauges/indicators/airspeed_kts_pilot": {
                "type": "float", "writable": False,
                "description": "Indicated airspeed knots",
                "category": "instruments"
            },
            "sim/cockpit2/gauges/indicators/altitude_ft_pilot": {
                "type": "float", "writable": False,
                "description": "Indicated altitude feet",
                "category": "instruments"
            },
            "sim/cockpit2/gauges/indicators/heading_electric_deg_mag_pilot": {
                "type": "float", "writable": False,
                "description": "Magnetic heading",
                "category": "instruments"
            },
            "sim/cockpit2/gauges/indicators/vvi_fpm_pilot": {
                "type": "float", "writable": False,
                "description": "Vertical speed FPM",
                "category": "instruments"
            },
        }

        # Enhance all entries with array metadata
        for name, info in self._database.items():
            type_str = info.get("type", "")
            flattened_size, dimensions = self.parse_array_type(type_str)
            if flattened_size > 0:
                info["array_size"] = flattened_size
                info["dimensions"] = dimensions
                info["is_array"] = True
            else:
                info["array_size"] = 0
                info["dimensions"] = []
                info["is_array"] = False

        log.info("Created default database with %d datarefs", len(self._database))
    
    def _build_categories(self) -> None:
        """Build category index from database."""
        self._categories = {}
        
        for dataref, info in self._database.items():
            # Try to get category from info, or guess from path
            category = info.get("category", "")
            
            if not category:
                # Guess category from dataref path
                category = self._guess_category(dataref)
            
            if category not in self._categories:
                self._categories[category] = []
            
            self._categories[category].append(dataref)
    
    def _guess_category(self, dataref: str) -> str:
        """Guess category from dataref path."""
        parts = dataref.lower()
        return self._categorize_by_parts(parts)

    def _categorize_by_parts(self, parts: str) -> str:
        """Helper function to categorize dataref based on its parts."""
        category_map = [
            (lambda p: "autopilot" in p or "/ap/" in p, "autopilot"),
            (lambda p: "gear" in p, "gear"),
            (lambda p: any(keyword in p for keyword in ["flap", "yoke", "control", "brake"]), "controls"),
            (lambda p: any(keyword in p for keyword in ["engine", "throttle", "prop", "mixture"]), "engine"),
            (lambda p: any(keyword in p for keyword in ["light", "beacon", "strobe", "nav_"]), "lights"),
            (lambda p: any(keyword in p for keyword in ["warning", "caution", "annun"]), "warnings"),
            (lambda p: any(keyword in p for keyword in ["gauge", "indicator", "airspeed", "altitude"]), "instruments"),
            (lambda p: any(keyword in p for keyword in ["radio", "com1", "nav1", "transponder"]), "radios"),
            (lambda p: any(keyword in p for keyword in ["weather", "wind", "cloud"]), "weather"),
            (lambda p: any(keyword in p for keyword in ["position", "latitude", "longitude"]), "position"),
        ]

        for condition, category in category_map:
            if condition(parts):
                return category

        return "other"
    
    def add_custom_dataref(self, name: str, dtype: str, description: str, writable: bool) -> bool:
        """
        Add a new custom dataref.
        Returns True if added, False if exists or invalid.
        """
        if not name.startswith("sim/"):
            name = "sim/custom/" + name

        # Check collision
        if name in self._database or name in self._custom_datarefs:
            log.warning(f"Dataref {name} already exists.")
            return False

        self._custom_datarefs[name] = {
            "name": name,
            "type": dtype,
            "description": description,
            "writable": writable,
            "custom": True
        }

        # Also add to main database
        self._database[name] = self._custom_datarefs[name]

        self.save_custom_datarefs()
        return True

    def get_all_dataref_names(self) -> List[str]:
        """Return list of all known dataref names, variables, and Arduino IDs with prefixes."""
        suggestions = []

        # 1. X-Plane Datarefs
        for name in self._database.keys():
            suggestions.append(name)

        # 2. Virtual Variables (VAR:)
        if self.variable_store:
            for name in self.variable_store.get_names():
                suggestions.append(f"VAR:{name}")

        # 3. Logic Engine Output IDs (raw keys)
        if self.logic_engine:
            for key in self.logic_engine.get_all_output_keys():
                suggestions.append(key)

        # 4. Arduino Output IDs (ID:)
        if self.arduino_manager:
            output_keys = self.arduino_manager.get_all_output_keys()
            for key in output_keys:
                suggestions.append(f"ID:{key}")

        return sorted(set(suggestions))

    
    def __init__(self, variable_store=None, arduino_manager=None, logic_engine=None) -> None:
        self.variable_store = variable_store
        self.arduino_manager = arduino_manager
        self.logic_engine = logic_engine

        self._database: Dict[str, Any] = {}
        self._subscriptions: Dict[str, float] = {}
        self._categories: Dict[str, List[str]] = {}
        self._custom_datarefs: Dict[str, dict] = {}

        # Add cache for frequently accessed descriptions
        self._description_cache: Dict[str, str] = {}

        self._load_database()
        self.load_custom_datarefs()
        self._build_categories()

    def _get_description(self, name: str) -> str:
        """
        Retrieve a user-friendly description for a dataref with caching.
        - Supports prefixed names (XP:, VAR:, ID:)
        - Handles array elements by consulting element-specific description first, then base
        - Normalizes placeholder descriptions (e.g., "Custom Dataref", "unknown", "N/A")
        - Falls back to formatted name if neither element nor base provides a real description
        """
        # Check cache first
        cached = self._description_cache.get(name)
        if cached is not None:
            return cached

        # Strip prefixes for lookup
        lookup_name = name
        if lookup_name.startswith("XP:"):
            lookup_name = lookup_name[3:]
        elif lookup_name.startswith("VAR:"):
            lookup_name = lookup_name[4:]
        elif lookup_name.startswith("ID:"):
            lookup_name = lookup_name[3:]

        # Determine base name if this is an array element (supports multi-dim)
        base_name = lookup_name.split("[")[0] if "[" in lookup_name else lookup_name

        def is_placeholder(desc: str) -> bool:
            return (desc or "").strip().lower() in {"custom dataref", "custom datarefs", "unknown", "n/a", ""}

        # 1) Try exact element description
        info = self._database.get(lookup_name)
        if info:
            element_desc = (info.get("description") or "").strip()
            if not is_placeholder(element_desc):
                self._description_cache[name] = element_desc
                return element_desc

        # 2) If element is placeholder or not found and it's an array element, try base dataref
        if lookup_name != base_name:
            base_info = self._database.get(base_name)
            if base_info:
                base_desc = (base_info.get("description") or "").strip()
                if not is_placeholder(base_desc):
                    self._description_cache[name] = base_desc
                    return base_desc

        # 3) If still not found, but base exists, try any non-empty description on the base
        if not info and base_name in self._database:
            base_info = self._database[base_name]
            base_desc = (base_info.get("description") or "").strip()
            if base_desc:
                self._description_cache[name] = base_desc
                return base_desc

        # 4) Fallback: format from the cleaned lookup/base name
        fallback_source = base_name if base_name else lookup_name
        fallback_desc = self._format_description_from_name(fallback_source)
        self._description_cache[name] = fallback_desc
        return fallback_desc

    def _format_description_from_name(self, name: str) -> str:
        """
        Format a description from a dataref name when no description is available.
        """
        # Replace slashes and underscores with spaces, capitalize words
        formatted = name.replace("/", " ").replace("_", " ").strip()
        words = [word.capitalize() for word in formatted.split() if word]
        return " ".join(words)

    def get_dataref_info(self, name: str) -> Optional[Dict]:
        """Get information about a specific dataref. Handles prefixed names."""
        if not name:
            return None

        # Strip prefixes for lookup
        lookup_name = name
        if lookup_name.startswith("XP:"):
            lookup_name = lookup_name[3:]
        elif lookup_name.startswith("VAR:"):
            lookup_name = lookup_name[4:]
        elif lookup_name.startswith("ID:"):
            # ID mappings are in ArduinoManager, but we might want info from the source dataref if possible
            # For now, just strip it.
            lookup_name = lookup_name[3:]

        return self._database.get(lookup_name)

    def get_array_metadata(self, name: str) -> Optional[Dict]:
        """
        Get array-specific metadata for a dataref.

        Args:
            name: Name of the dataref

        Returns:
            Dictionary with array metadata or None if not an array
        """
        info = self.get_dataref_info(name)
        if not info or not info.get("is_array", False):
            return None

        return {
            "is_array": True,
            "array_size": info.get("array_size", 0),
            "dimensions": info.get("dimensions", []),
            "element_type": info.get("type", "").split('[')[0] if '[' in info.get("type", "") else info.get("type", "")
        }

    def is_array_dataref(self, name: str) -> bool:
        """
        Check if a dataref is an array.

        Args:
            name: Name of the dataref

        Returns:
            True if the dataref is an array, False otherwise
        """
        info = self.get_dataref_info(name)
        return info.get("is_array", False) if info else False

    def get_array_elements(self, base_name: str) -> List[Dict]:
        """
        Get all elements of an array dataref.

        Args:
            base_name: Base name of the array (e.g., "sim/flightmodel/controls/yawb_def")

        Returns:
            List of dictionaries representing each array element
        """
        info = self.get_dataref_info(base_name)
        if not info or not info.get("is_array", False):
            return []

        array_size = info.get("array_size", 0)
        dimensions = info.get("dimensions", [])

        elements = []
        base = base_name.split("[")[0]  # Extract base name

        # Generate all possible indices for multidimensional arrays
        element_indices = self._generate_element_indices(dimensions)

        for idx, element_index in enumerate(element_indices):
            element_name = f"{base}{element_index}"
            element_info = {
                "name": element_name,
                "base_name": base,
                "element_index": element_index,
                "flat_index": idx,
                "type": info.get("type", ""),
                "description": f"{info.get('description', '')} {element_index}",
                "writable": info.get("writable", False),
                "custom": info.get("custom", False)
            }

            # Add current value if available
            if "value" in info and isinstance(info["value"], list) and idx < len(info["value"]):
                element_info["value"] = info["value"][idx]
            else:
                element_info["value"] = 0.0

            elements.append(element_info)

        return elements

    def get_array_base_from_element(self, element_name: str) -> str:
        """
        Get the base name of an array from an element name.

        Args:
            element_name: Name of the array element (e.g., "sim/flightmodel/controls/yawb_def[2]")

        Returns:
            Base name of the array or empty string if not an array element
        """
        # Extract base name by removing the index part
        match = re.match(r'^(.+?)(?:\[\d+\].*)?$', element_name)
        if match:
            base_name = match.group(1)
            # Check if the base is actually an array in our database
            if self.is_array_dataref(base_name):
                return base_name
        return ""
    
    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        return sorted(self._categories.keys())
    
    def get_datarefs_in_category(self, category: str) -> List[str]:
        """Get all datarefs in a category."""
        return self._categories.get(category, [])
    
    def search(self, query: str, category: str = None, limit: int = 100) -> List[str]:
        """
        Search for datarefs matching query.
        
        Args:
            query: Search string (matches anywhere in dataref name or description)
            category: Optional category filter
            limit: Maximum results to return
        
        Returns:
            List of matching dataref names
        """
        query = query.lower()
        results = []
        
        for dataref, info in self._database.items():
            # Category filter
            if category and category != "all":
                dr_category = info.get("category", self._guess_category(dataref))
                if dr_category != category:
                    continue
            
            # Search in name
            if query in dataref.lower():
                results.append(dataref)
                # Skip to next iteration after adding to results

            # Search in description
            desc = info.get("description", "").lower()
            if query in desc:
                results.append(dataref)
                # Skip to next iteration after adding to results
        
        # Sort by relevance (exact matches first, then alphabetically)
        results.sort(key=lambda x: (not x.lower().startswith(query), x))
        
        return results[:limit]
    
    def subscribe(self, dataref: str) -> None:
        """Subscribe to a dataref."""
        self._subscriptions[dataref] = 0.0
        log.info("Subscribed to: %s", dataref)
    
    def unsubscribe(self, dataref: str) -> None:
        """Unsubscribe from a dataref."""
        self._subscriptions.pop(dataref, None)
        log.info("Unsubscribed from: %s", dataref)
    
    def update_value(self, dataref: str, value: float) -> None:
        """Update the value of a subscribed dataref."""
        if dataref in self._subscriptions:
            self._subscriptions[dataref] = value
    
    def get_value(self, dataref: str) -> Optional[float]:
        """Get the current value of a subscribed dataref."""
        return self._subscriptions.get(dataref)
    
    def get_dataref_count(self) -> int:
        """Get total number of datarefs in database."""
        return len(self._database)

    def add_custom_dataref_dict(self, name: str, info: Dict[str, Any]) -> bool:
        """
        Add a custom dataref to the database from a dictionary.

        Args:
            name: Dataref name
            info: Dataref info dict

        Returns:
            True if added successfully
        """
        if name in self._database:
            # Update existing
            self._database[name].update(info)
            if name in self._custom_datarefs:
                self._custom_datarefs[name].update(info)
            log.info("Updated dataref: %s", name)
        else:
            # Add new
            info["custom"] = True
            self._database[name] = info
            self._custom_datarefs[name] = info
            log.info("Added custom dataref: %s", name)

        # Rebuild categories
        self._build_categories()
        
        # Save to disk immediately for persistence
        self.save_custom_datarefs()

        return True

    def add_custom_dataref(self, name: str, dtype: str = "float", description: str = "Custom Dataref", writable: bool = True) -> bool:
        """Helper to add a custom dataref from the UI."""
        info = {
            "type": dtype,
            "description": description,
            "writable": writable,
            "custom": True
        }
        return self.add_custom_dataref_dict(name, info)
    
    def reload_database(self) -> bool:
        """Reload the dataref database from file."""
        try:
            # Clear current database
            self._database.clear()

            # Load fresh database
            self._load_database()

            # Reload custom datarefs
            self.load_custom_datarefs()

            # Rebuild categories
            self._build_categories()

            log.info("Database reloaded successfully")
            return True
        except Exception as e:
            log.error("Failed to reload database: %s", e)
            return False

    def save_database(self) -> bool:
        """Save the database to file (preserves custom datarefs)."""
        # Find the database path
        db_path = None
        for path in POSSIBLE_PATHS:
            if path.exists():
                db_path = path
                break

        if not db_path:
            # Create in default location
            db_path = POSSIBLE_PATHS[0]
            db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(self._database, f, indent=4, sort_keys=True)
            log.info("Saved dataref database to: %s", db_path)
            return True
        except Exception as e:
            log.error("Failed to save database: %s", e)
            return False
    
    def get_custom_datarefs(self) -> Dict[str, Any]:
        """Get all custom datarefs."""
        return {
            name: info for name, info in self._database.items()
            if info.get("custom", False)
        }
    
    def is_custom_dataref(self, name: str) -> bool:
        """Check if a dataref is custom."""
        info = self._database.get(name)
        return info.get("custom", False) if info else False

    def remove_custom_dataref(self, name: str) -> bool:
        """
        Remove a custom dataref from the database.
        Only allows removing datarefs marked as custom.
        """
        if name not in self._database:
            return False

        info = self._database[name]
        if not info.get("custom", False):
            log.warning(f"Cannot remove non-custom dataref: {name}")
            return False

        # Remove from main database
        del self._database[name]

        # Remove from custom datarefs if it exists there
        if name in self._custom_datarefs:
            del self._custom_datarefs[name]

        # Rebuild categories
        self._build_categories()

        # Save to file
        self.save_custom_datarefs()

        log.info(f"Removed custom dataref: {name}")
        return True

    def export_custom_datarefs(self, filepath: str) -> bool:
        """Export only custom datarefs to a separate file."""
        custom = self.get_custom_datarefs()
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(custom, f, indent=4, sort_keys=True)
            log.info("Exported %d custom datarefs to: %s", len(custom), filepath)
            return True
        except Exception as e:
            log.error("Failed to export custom datarefs: %s", e)
            return False
    
    def import_custom_datarefs(self, filepath: str) -> int:
        """Import custom datarefs from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                custom = json.load(f)
            
            count = 0
            for name, info in custom.items():
                info["custom"] = True
                self.add_custom_dataref_dict(name, info)
                count += 1
            
            log.info("Imported %d custom datarefs from: %s", count, filepath)
            return count
        except Exception as e:
            log.error("Failed to import custom datarefs: %s", e)
            return 0
