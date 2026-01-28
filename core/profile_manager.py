from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import types for reconstruction
from core.input_mapper import InputMapping, InputAction

log = logging.getLogger(__name__)


class ProfileManager:
    """
    Manages loading and saving of application profiles.
    Persists:
    1. Output Mappings (Dataref -> Universal Key)
    2. Input Mappings (Device Input -> X-Plane Command)
    3. Logic Blocks (Virtual Variables)
    """

    PROFILE_DIR = Path("config/profiles")
    DEFAULT_PROFILE = "default"

    # Store device names even if disconnected for offline viewing
    # DeviceID -> Last Known Name
    _known_devices: Dict[str, str] = {}

    def __init__(
        self,
        arduino_manager,
        input_mapper,
        xplane_conn,
        logic_engine=None,
        hid_manager=None,
        dataref_manager=None,
    ):
        self.arduino_manager = arduino_manager
        self.input_mapper = input_mapper
        self.xplane_conn = xplane_conn
        self.logic_engine = logic_engine
        self.hid_manager = hid_manager
        self.dataref_manager = dataref_manager

        # Device aliases dictionary
        self._device_aliases: Dict[str, str] = {}

        self.PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    def save_profile(self, name: str = "default") -> bool:
        """Save current state to a profile file."""
        data = {
            "version": "1.0",
            "outputs": self._get_output_config(),
            "monitored_datarefs": self._get_monitored_datarefs_config(),  # Save monitored list
            "inputs": self._get_input_config(),
            "logic": self._get_logic_config(),
            "calibration": self._get_calibration_config(),
            "auto_connect": self._get_auto_connect_config(),
            "device_aliases": self._get_device_aliases_config(),
            "known_devices": self._known_devices,  # Save metadata for offline display
        }

        path = self.PROFILE_DIR / f"{name}.json"
        # Clear custom datarefs before saving to ensure empty profile resets placeholders
        if self.dataref_manager:
            try:
                self.dataref_manager.clear_custom_datarefs()
            except Exception as e:
                log.warning("Failed to clear custom datarefs before save: %s", e)
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            log.info("Saved profile to %s", path)
            return True
        except Exception as e:
            log.error("Failed to save profile: %s", e)
            return False

    def load_profile(self, name: str = "default") -> bool:
        """Load state from a profile file."""
        path = self.PROFILE_DIR / f"{name}.json"
        if not path.exists():
            log.info("Profile %s not found (fresh start)", path)
            return False

        try:
            with open(path, "r") as f:
                data = json.load(f)

            # 1. Load Outputs
            self._load_output_config(data.get("outputs", {}))

            # 1b. Load Monitored Datarefs (Persistence Fix)
            self._load_monitored_datarefs_config(data.get("monitored_datarefs", []))

            # 2. Load Inputs
            self._load_input_config(data.get("inputs", []))

            # 3. Load Logic
            if self.logic_engine:
                self._load_logic_config(data.get("logic", []))

            # 4. Load Device Aliases
            self._load_device_aliases_config(data.get("device_aliases", {}))

            # 5. Load Calibration (NEW)
            self._load_calibration_config(data.get("calibration", {}))

            # 6. Load Known Devices (Offline metadata)
            self._known_devices.update(data.get("known_devices", {}))

            # 6. Auto-connect devices
            ports = data.get("auto_connect", [])
            self._load_auto_connect_config(ports)

            log.info("Loaded profile %s", path)
            return True
        except Exception as e:
            log.error("Failed to load profile: %s", e)
            return False

    # --- Internal Helpers ---

    def _get_output_config(self) -> Dict[str, str]:
        """Extract output mappings."""
        # Get from ArduinoManager (Source of Truth)
        if hasattr(self.arduino_manager, "get_all_universal_mappings"):
            return self.arduino_manager.get_all_universal_mappings()
        return self.arduino_manager._universal_mappings  # Fallback

    def _load_output_config(self, data: Dict[str, Dict[str, any]]):
        """Restore output mappings."""
        # Clear existing
        if hasattr(self.arduino_manager, "clear_universal_mappings"):
            self.arduino_manager.clear_universal_mappings()
        else:
            self.arduino_manager._universal_mappings.clear()

        # Add new (JUST update the manager state)
        for key, info in data.items():
            self.arduino_manager.set_universal_mapping(
                info["source"], key, info.get("is_variable", False)
            )

    def _get_monitored_datarefs_config(self) -> List[str]:
        """Get list of monitored datarefs."""
        if hasattr(self.arduino_manager, "get_monitored_datarefs"):
            return self.arduino_manager.get_monitored_datarefs()
        return []

    def _load_monitored_datarefs_config(self, data: List[str]):
        """Load monitored datarefs."""
        if not hasattr(self.arduino_manager, "add_monitor"):
            return

        for dataref in data:
            self.arduino_manager.add_monitor(dataref)

    def _get_input_config(self) -> list:
        """Extract input mappings."""
        return [m.to_dict() for m in self.input_mapper.get_mappings()]

    def _load_input_config(self, data: list):
        """Restore input mappings."""
        try:
            mappings = []
            for item in data:
                # Handle enum conversion if needed (from_dict usually handles strings)
                mapping = InputMapping.from_dict(item)
                if mapping:
                    mappings.append(mapping)

            # Replace mappings list
            self.input_mapper._mappings = mappings
        except Exception as e:
            log.error("Error parsing input config: %s", e)

    def _get_device_aliases_config(self) -> Dict[str, str]:
        """Get device aliases for renaming."""
        return dict(self._device_aliases)

    def _load_device_aliases_config(self, data: Dict[str, str]):
        """Load device aliases."""
        self._device_aliases = dict(data)

    def _get_calibration_config(self) -> Dict:
        """Get calibration data."""
        if hasattr(self.hid_manager, "get_all_calibration"):
            return self.hid_manager.get_all_calibration()
        return {}

    def _load_calibration_config(self, data: Dict):
        """Load calibration data."""
        if hasattr(self.hid_manager, "load_calibration"):
            self.hid_manager.load_calibration(data)

    def set_device_alias(self, device_id: str, alias: str):
        """Set an alias for a device."""
        if alias.strip():
            self._device_aliases[device_id] = alias.strip()
        elif device_id in self._device_aliases:
            del self._device_aliases[device_id]

    def get_device_alias(self, device_id: str) -> Optional[str]:
        """Get the alias for a device, or None if not set."""
        return self._device_aliases.get(device_id)

    def _get_auto_connect_config(self) -> list:
        """Get list of ports to auto-connect to."""
        # Get currently connected ports from ArduinoManager
        devices = self.arduino_manager.devices_snapshot()
        # Only return ports that are actually connected
        connected_ports = [p for p, d in devices.items() if d.is_connected]
        return connected_ports

    def _load_auto_connect_config(self, data: list):
        """Auto-connect to specified ports."""
        for port in data:
            log.info("Auto-connecting to %s...", port)
            try:
                # We need to access the arduino_manager to connect
                # This might be called during initialization, so we'll try to connect
                self.arduino_manager.connect(port)
            except Exception as e:
                log.error("Failed to auto-connect to %s: %s", port, e)

    def _get_logic_config(self) -> list:
        """Extract logic blocks."""
        if not self.logic_engine:
            return []
        return [b.to_dict() for b in self.logic_engine.get_blocks()]

    def _load_logic_config(self, data: list):
        """Restore logic blocks."""
        if not self.logic_engine:
            return

        # Clear existing
        self.logic_engine.clear_blocks()

        from core.logic_engine import LogicBlock

        for item in data:
            try:
                block = LogicBlock.from_dict(item)
                self.logic_engine.add_block(block)
            except Exception as e:
                log.error("Error loading logic block: %s", e)

    def export_profile(self, name: str, target_path: Path) -> bool:
        """Copy a profile to an external location."""
        # Ensure latest state is saved to the internal profile first
        self.save_profile(name)
        source_path = self.PROFILE_DIR / f"{name}.json"
        if not source_path.exists():
            log.error("Profile %s not found for export", name)
            return False

        try:
            import shutil

            # Ensure target directory exists
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the profile file
            shutil.copy2(source_path, target_path)
            log.info("Exported profile %s to %s", name, target_path)
            return True
        except Exception as e:
            log.error("Failed to export profile: %s", e)
            import traceback
            log.error("Export traceback: %s", traceback.format_exc())
            return False

    def import_profile(self, source_path: Path) -> Optional[str]:
        """Copy an external profile into the internal directory and load it."""
        try:
            source_path = Path(source_path)

            # Validate source file exists
            if not source_path.exists():
                log.error("Source profile file not found: %s", source_path)
                return None

            # Validate it's a JSON file
            if source_path.suffix.lower() != '.json':
                log.error("Source file is not a JSON file: %s", source_path)
                return None

            # Read and validate the profile data before importing
            try:
                with open(source_path, 'r') as f:
                    profile_data = json.load(f)

                # Validate profile structure
                if not isinstance(profile_data, dict):
                    log.error("Invalid profile structure: not a dictionary")
                    return None

                # Check for required fields
                if 'version' not in profile_data:
                    log.warning("Profile missing version field, but will attempt to import")

            except json.JSONDecodeError as e:
                log.error("Invalid JSON in profile file: %s", e)
                return None
            except Exception as e:
                log.error("Error reading profile file: %s", e)
                return None

            # Generate a unique name if profile already exists
            new_name = source_path.stem
            target_path = self.PROFILE_DIR / f"{new_name}.json"

            # If profile already exists, append a number
            counter = 1
            while target_path.exists():
                new_name = f"{source_path.stem}_{counter}"
                target_path = self.PROFILE_DIR / f"{new_name}.json"
                counter += 1

            import shutil

            # Copy the profile file
            shutil.copy2(source_path, target_path)
            log.info("Imported profile from %s to %s", source_path, target_path)

            # Load it
            if self.load_profile(new_name):
                return new_name
            else:
                log.error("Failed to load imported profile: %s", new_name)
                return None
        except Exception as e:
            log.error("Failed to import profile: %s", e)
            import traceback
            log.error("Import traceback: %s", traceback.format_exc())
            return None

    def record_device_name(self, device_id: str, name: str):
        """Update last known name for a device."""
        if device_id and name:
            self._known_devices[device_id] = name

    def get_known_device_name(self, device_id: str) -> str:
        """Get the last known name for a device."""
        return self._known_devices.get(device_id, device_id)
