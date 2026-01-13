from __future__ import annotations
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)

class VariableType(Enum):
    DATAREF_XPLANE = "XP"    # Real X-Plane dataref
    DATAREF_CUSTOM = "CUSTOM"  # User defined custom dataref
    VARIABLE_VIRTUAL = "VAR"     # Logic Engine computed variable
    VARIABLE_ARDUINO = "ARD"  # Input from Arduino/ESP32


@dataclass
class VariableEntry:
    name: str
    value: float
    type: VariableType
    last_updated: float
    description: str = ""
    unit: str = ""
    initial_value: Optional[float] = None


class VariableStore:
    """
    Global store for all variables.
    Bridges X-Plane, Logic Engine, and Hardware.
    """
    def __init__(self):
        self._variables: Dict[str, VariableEntry] = {}
        self._listeners = [] # Callbacks for value changes

    def register_listener(self, callback):
        self._listeners.append(callback)

    def _notify_listeners(self, entry: VariableEntry):
        for cb in self._listeners:
            try:
                cb(entry.name, entry.value)
            except Exception as e:
                log.error(f"Variable listener error: {e}")

    def update_value(self, name: str, value: float, var_type: VariableType, description: str = ""):
        """Update or create a variable entry."""
        existing = self._variables.get(name)

        if existing:
            # Update if type matches or overwrite if new type
            existing.value = value
            existing.last_updated = time.time()
            if not existing.description and description:
                existing.description = description
        else:
            # Create new
            self._variables[name] = VariableEntry(
                name=name,
                value=value,
                type=var_type,
                last_updated=time.time(),
                description=description
            )

        self._notify_listeners(self._variables[name])

    def get_value(self, name: str) -> Optional[float]:
        if name in self._variables:
            return self._variables[name].value
        return None

    def get_all(self) -> Dict[str, VariableEntry]:
        return self._variables
    
    def get_names(self) -> List[str]:
        return list(self._variables.keys())

    def get_by_type(self, var_type: VariableType) -> List[VariableEntry]:
        return [v for v in self._variables.values() if v.type == var_type]