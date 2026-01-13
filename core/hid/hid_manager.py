from __future__ import annotations
import logging
import threading
import time
from typing import Dict, Optional, List

# Use our new Windows backend
try:
    from . import winmm_backend as winmm
    WINMM_AVAILABLE = True
except ImportError:
    WINMM_AVAILABLE = False

from .hid_device import HIDDevice

log = logging.getLogger(__name__)

class HIDManager:
    """
    Manages Joystick/Controller inputs using Windows Native API (winmm).
    Solves input scrambling by using OS-level driver parsing.
    """
    
    def __init__(self) -> None:
        self._devices: Dict[str, HIDDevice] = {}
        self._lock = threading.Lock()
        self._running = False
        
        # Callbacks
        self.on_device_update = None
        
        # Calibration Data: device_id -> axis_index -> {min, max, center, deadzone}
        self._calibration_data: Dict[str, Dict[int, Dict[str, float]]] = {}
        
        if not WINMM_AVAILABLE:
            log.error("Windows Multimedia API not available. Input will not work.")
        else:
            log.info("HIDManager initialized (Windows Native Backend)")

    def start(self) -> None:
        if self._running or not WINMM_AVAILABLE: return
        self._running = True
        threading.Thread(target=self._poll_loop, daemon=True).start()
        log.info("HID polling loop started")

    def stop(self) -> None:
        self._running = False
        log.info("HIDManager stopped")

    def devices_snapshot(self) -> Dict[str, HIDDevice]:
        with self._lock: return dict(self._devices)

    def get_device(self, device_id: str) -> Optional[HIDDevice]:
        with self._lock: return self._devices.get(device_id)

    def _poll_loop(self) -> None:
        """Main loop: Detects devices and reads inputs."""
        while self._running:
            try:
                self._scan_and_read()
                if self.on_device_update:
                    self.on_device_update(self.devices_snapshot())
            except Exception as e:
                log.error("HID Loop Error: %s", e)
            
            time.sleep(0.02) # 50Hz

    def _scan_and_read(self) -> None:
        """
        Scans all 16 possible joystick IDs (Windows limit).
        Reads their state if connected. This method is designed to be thread-safe.
        """
        max_sticks = winmm.get_num_devices()
        active_ids = set()
        found_devices: Dict[str, HIDDevice] = {}

        for i in range(max_sticks):
            caps = winmm.get_device_caps(i)
            if not caps:
                continue

            dev_id = f"WINMM_{i}"
            active_ids.add(dev_id)

            with self._lock:
                device = self._devices.get(dev_id)

            # Register if new
            if not device:
                name = caps.szPname.decode('utf-8', errors='ignore')
                log.info("Found Joystick: %s (ID: %d)", name, i)
                
                info = winmm.get_device_state(i)
                has_pov = (caps.wCaps & 0x0004) != 0
                if info and not has_pov and info.dwPOV != 0:
                    has_pov = True
                
                device = HIDDevice(
                    device_id=dev_id,
                    name=name,
                    vendor_id=caps.wMid,
                    product_id=caps.wPid,
                    path=str(i).encode(),
                    num_axes=caps.wNumAxes,
                    num_buttons=caps.wNumButtons,
                    num_hats=1 if has_pov else 0
                )
            
            found_devices[dev_id] = device

            # Read State and update
            info = winmm.get_device_state(i)
            if info:
                self._update_device_state(device, info, caps)

        # Update master device list and connection states
        with self._lock:
            # Add newly found devices
            for dev_id, device in found_devices.items():
                if dev_id not in self._devices:
                    self._devices[dev_id] = device
            
            # Update connection status for all devices
            all_known_ids = set(self._devices.keys())
            disconnected_ids = all_known_ids - active_ids
            
            for dev_id in active_ids:
                if dev_id in self._devices and not self._devices[dev_id].connected:
                    log.info("Joystick Reconnected: %s", self._devices[dev_id].name)
                    self._devices[dev_id].connected = True
            
            for dev_id in disconnected_ids:
                if dev_id in self._devices and self._devices[dev_id].connected:
                    log.info("Joystick Disconnected: %s", self._devices[dev_id].name)
                    self._devices[dev_id].connected = False

    def _update_device_state(self, device: HIDDevice, info, caps) -> None:
        """Parses the JOYINFOEX structure into normalized values."""

        # --- Axes ---
        # Windows returns 0..65535. We map to -1.0..1.0
        # The axes order in info structure: X, Y, Z, R, U, V
        raw_axes = [
            info.dwXpos, info.dwYpos, info.dwZpos,
            info.dwRpos, info.dwUpos, info.dwVpos
        ]
        
        # Capture raw range for storage
        raw_axes_list = [val for val in raw_axes[:device.num_axes]]

        normalized_axes = []
        normalized_axes = []
        for i, val in enumerate(raw_axes[:device.num_axes]):
            # Check calibration
            cal = self._get_axis_cal(device.device_id, i)
            
            if cal:
                # Calibrated Normalization
                # 1. Clamp to Min/Max
                # 2. Rescale center-to-min and center-to-max independently to ensure true 0.0 center
                
                # Apply Deadzone at center
                if cal["center"] - cal["deadzone"] <= val <= cal["center"] + cal["deadzone"]:
                    norm = 0.0
                elif val < cal["center"]:
                    # Lower half
                    if val <= cal["min"]:
                         norm = -1.0
                    else:
                         range_low = cal["center"] - cal["deadzone"] - cal["min"]
                         if range_low == 0: range_low = 1 # Avoid div/0
                         norm = -1.0 + ((val - cal["min"]) / range_low)
                else:
                    # Upper half
                    if val >= cal["max"]:
                        norm = 1.0
                    else:
                        range_high = cal["max"] - (cal["center"] + cal["deadzone"])
                        if range_high == 0: range_high = 1
                        norm = (val - (cal["center"] + cal["deadzone"])) / range_high
                        
            else:
                # Default Normalization (val - 32768) / 32768.0
                norm = (val - 32768) / 32768.0
            
            # Final clamp safety
            norm = max(-1.0, min(1.0, norm))
            normalized_axes.append(norm)

        # --- Buttons ---
        # dwButtons is a bitmask
        buttons = []
        for b in range(device.num_buttons):
            is_pressed = (info.dwButtons & (1 << b)) != 0
            buttons.append(is_pressed)

        # --- Hats (POV) ---
        hats = []
        if device.num_hats > 0:
            pov = info.dwPOV

            # Windows API: 65535 = Centered
            if pov == 65535:
                hats.append((0, 0))
            else:
                # 0..35900 (Hundredths of degrees)
                # North is 0. If device returns 0 for "Not Supported",
                # we might glitch to North.
                # But since we checked for 65535 in scan, this should be safe.

                angle = pov
                if 33750 < angle or angle <= 2250: # Up
                    hats.append((0, 1))
                elif 2250 < angle <= 6750: # Up-Right
                    hats.append((1, 1))
                elif 6750 < angle <= 11250: # Right
                    hats.append((1, 0))
                elif 11250 < angle <= 15750: # Down-Right
                    hats.append((1, -1))
                elif 15750 < angle <= 20250: # Down
                    hats.append((0, -1))
                elif 20250 < angle <= 24750: # Down-Left
                    hats.append((-1, -1))
                elif 24750 < angle <= 29250: # Left
                    hats.append((-1, 0))
                elif 29250 < angle <= 33750: # Up-Left
                    hats.append((-1, 1))
                else:
                    hats.append((0,0)) # Fallback

        # Commit update
        device.update(normalized_axes, buttons, hats, raw_axes=raw_axes_list)

    # ============================================================
    # Calibration API
    # ============================================================

    def set_calibration(self, device_id: str, axis_index: int, min_val: float, max_val: float, center_val: float, deadzone: float = 0.0):
        """Set calibration for a specific axis."""
        with self._lock:
            if device_id not in self._calibration_data:
                self._calibration_data[device_id] = {}
            
            self._calibration_data[device_id][axis_index] = {
                "min": min_val,
                "max": max_val,
                "center": center_val,
                "deadzone": deadzone
            }
            log.info("Calibrated %s Axis %d: %s", device_id, axis_index, self._calibration_data[device_id][axis_index])

    def get_calibration(self, device_id: str, axis_index: int) -> Optional[Dict[str, float]]:
        """Get calibration for an axis."""
        with self._lock:
            return self._calibration_data.get(device_id, {}).get(axis_index)

    def get_all_calibration(self) -> Dict:
        """Get full calibration data for persistence."""
        with self._lock:
            return dict(self._calibration_data)

    def load_calibration(self, data: Dict):
        """Load full calibration data."""
        with self._lock:
             # Convert keys back to int if JSON stringified them
             clean_data = {}
             for dev, axes in data.items():
                 clean_axes = {}
                 for ax_idx, cal in axes.items():
                     clean_axes[int(ax_idx)] = cal
                 clean_data[dev] = clean_axes
             self._calibration_data = clean_data

    def _get_axis_cal(self, device_id: str, axis_index: int):
        """Internal helper without lock (called from locked context or loop)."""
        return self._calibration_data.get(device_id, {}).get(axis_index)