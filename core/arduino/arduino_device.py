from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Set
import time


import threading


class DeviceType(Enum):
    UNKNOWN = auto()
    ARDUINO_NANO = auto()
    ARDUINO_PRO_MICRO = auto()
    ARDUINO_LEONARDO = auto()
    ESP32 = auto()
    ESP32S2 = auto()
    ESP32S3 = auto()


class DeviceState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    HANDSHAKE = auto()
    READY = auto()
    ACTIVE = auto()
    ERROR = auto()


@dataclass
class ArduinoDevice:
    """Represents a connected Arduino/ESP32 device."""

    port: str
    baudrate: int = 115200

    state: DeviceState = DeviceState.DISCONNECTED
    device_type: DeviceType = DeviceType.UNKNOWN

    firmware_version: str = ""
    board_type: str = ""
    device_name: str = ""

    last_seen: float = field(default_factory=time.time)
    error_message: str = ""

    # Subscriptions: dataref -> local key mapping
    subscriptions: Dict[str, str] = field(default_factory=dict)

    # Last received input values
    _inputs: Dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set_input(self, key: str, value: float) -> None:
        """Thread-safe method to set an input value."""
        with self._lock:
            self._inputs[key] = value

    def get_input(self, key: str) -> float | None:
        """Thread-safe method to get a single input value."""
        with self._lock:
            return self._inputs.get(key)

    def get_all_inputs(self) -> Dict[str, float]:
        """Thread-safe method to get a copy of all input values."""
        with self._lock:
            return self._inputs.copy()

    def transition(self, new_state: DeviceState, error: str = "") -> None:
        self.state = new_state
        self.last_seen = time.time()
        self.error_message = error

    @property
    def is_ready(self) -> bool:
        return self.state in (DeviceState.READY, DeviceState.ACTIVE)

    @property
    def is_connected(self) -> bool:
        return self.state not in (DeviceState.DISCONNECTED, DeviceState.ERROR)

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "state": self.state.name,
            "device_type": self.device_type.name,
            "firmware_version": self.firmware_version,
            "board_type": self.board_type,
            "device_name": self.device_name,
            "subscriptions": dict(self.subscriptions),
            "inputs": self.get_all_inputs(),
        }
