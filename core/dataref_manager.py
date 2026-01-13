from __future__ import annotations
import logging
import json
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
    
    def _load_database(self) -> None:
        """Load dataref database from JSON file."""

        # Try each possible path
        for db_path in POSSIBLE_PATHS:
            log.info("Trying dataref database path: %s", db_path)

            if db_path.exists():
                try:
                    with open(db_path, 'r', encoding='utf-8') as f:
                        self._database = json.load(f)
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
