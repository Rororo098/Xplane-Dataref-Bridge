from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import time


@dataclass(slots=True)
class HIDDevice:
    """Represents a single HID device with its current state."""

    device_id: str
    name: str
    vendor_id: int
    product_id: int
    path: bytes

    # Capabilities
    num_axes: int = 0
    num_buttons: int = 0
    num_hats: int = 0

    # State
    axes: List[float] = field(default_factory=list)
    raw_axes: List[int] = field(default_factory=list)  # Added raw values for calibration
    buttons: List[bool] = field(default_factory=list)
    buttons: List[bool] = field(default_factory=list)
    hats: List[tuple] = field(default_factory=list) # (x, y) tuples for hat switches

    last_update: float = field(default_factory=time.time)
    connected: bool = True

    # HID usage info (for report parsing)
    usage: int = 0
    usage_page: int = 0

    def __post_init__(self) -> None:
        # Initialize state arrays based on capabilities
        # Note: These might be resized once we receive actual reports
        if not self.axes:
            self.axes = [0.0] * max(8, self.num_axes)
        if not self.raw_axes:
            self.raw_axes = [32768] * max(8, self.num_axes)
        if not self.buttons:
            self.buttons = [False] * max(32, self.num_buttons)
        if not self.hats:
            self.hats = [(0, 0)] * max(1, self.num_hats)

    def update_state(self, axes: List[float], buttons: List[bool], hats: List[tuple] = None):
        """Update the device state."""
        # Check for changes before updating
        axes_changed = self.axes != axes
        buttons_changed = self.buttons != buttons
        hats_changed = hats and self.hats != hats

        self.axes = axes
        self.buttons = buttons
        if hats:
            self.hats = hats
        self.last_update = time.time()

        return axes_changed or buttons_changed or hats_changed

    def update(self, axes: List[float], buttons: List[bool], hats: List[tuple], raw_axes: List[int] = None):
        """Update live state (used by Windows backend)."""
        self.axes = axes
        if raw_axes:
            self.raw_axes = raw_axes
        self.buttons = buttons
        self.hats = hats
        self.last_update = time.time()

    def update_axis(self, index: int, value: float) -> None:
        if 0 <= index < self.num_axes:
            self.axes[index] = value
            self.last_update = time.time()

    def update_button(self, index: int, pressed: bool) -> None:
        if 0 <= index < self.num_buttons:
            self.buttons[index] = pressed
            self.last_update = time.time()

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "vendor_id": self.vendor_id,
            "product_id": self.product_id,
            "num_axes": self.num_axes,
            "num_buttons": self.num_buttons,
            "num_hats": self.num_hats,
            "connected": self.connected,
        }