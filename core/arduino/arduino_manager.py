from __future__ import annotations
import asyncio
import logging
import re
import threading
import time
from typing import Dict, Callable, Optional, List, Any
from dataclasses import dataclass, field
from enum import Enum, auto

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# Import shared definitions
from .arduino_device import ArduinoDevice, DeviceState, DeviceType

log = logging.getLogger(__name__)


class ArduinoManager:
    """
    Manages Arduino/ESP32 device connections and communication.
    Supports Universal Mapping (Dataref -> Key Broadcast).
    """

    # Known ESP32 USB VID/PIDs
    ESP32_VIDS = {0x303A, 0x1A86, 0x10C4}

    def __init__(self, variable_store=None, dataref_manager=None, xplane_conn=None) -> None:
        self._devices: Dict[str, ArduinoDevice] = {}
        self._serials: Dict[str, serial.Serial] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

        # Cache for last sent values to avoid spam
        self._last_sent: Dict[str, Dict[str, float]] = {}

        # Universal Mappings: output_key -> {'source': source, 'is_variable': bool}
        self._universal_mappings: Dict[str, Dict[str, any]] = {}
        
        # Monitored Datarefs: Set of datarefs being watched (even if no key is mapped)
        self._monitored_datarefs: set[str] = set()

        # Variable store for unified variable system
        self.variable_store = variable_store
        
        # Dataref manager for type information
        self.dataref_manager = dataref_manager
        
        # X-Plane connection for writing datarefs
        self.xplane_conn = xplane_conn

        # Store tasks to prevent garbage collection
        self._tasks: List[asyncio.Task] = []

        # Callbacks
        self.on_device_update: Optional[Callable[[Dict[str, ArduinoDevice]], None]] = None
        self.on_input_received: Optional[Callable[[str, str, float], None]] = None
        self.on_message_received: Optional[Callable[[str, str], None]] = None
        self.on_dataref_write: Optional[Callable[[str, float], None]] = None
        self.on_command_send: Optional[Callable[[str], None]] = None

        log.info("ArduinoManager initialized (Serial available: %s)", SERIAL_AVAILABLE)

    # ============================================================
    # Universal Mapping API
    # ============================================================

    def set_universal_mapping(self, source: str, key: str, is_variable: bool = False) -> None:
        """
        Register a mapping from a source (dataref or variable) to a universal key.
        When this source changes, the key/value will be sent to ALL devices.
        """
        if not source or not source.strip():
            log.warning("Rejecting universal mapping for empty source name.")
            return

        if not key:
            if key in self._universal_mappings:
                del self._universal_mappings[key]
                log.info("Removed mapping for %s", key)
        else:
            # Normalize key to uppercase
            key = key.upper()

            # If this key was previously mapped to a different source, log a warning
            if key in self._universal_mappings and self._universal_mappings[key]['source'] != source:
                log.warning(f"Key '{key}' re-mapped from '{self._universal_mappings[key]['source']}' to '{source}'")

            # Store the mapping with the 'is_variable' flag
            self._universal_mappings[key] = {
                'source': source,
                'is_variable': is_variable
            }
            if not is_variable:
                self.add_monitor(source)  # Implicitly monitor datarefs, but not variables
            log.info(f"Mapped {source} -> {key} (Universal)" + (" (Variable)" if is_variable else ""))

    def get_universal_key(self, source: str) -> Optional[str]:
        """Get the key mapped to a source (dataref or variable)."""
        for key, info in self._universal_mappings.items():
            if info['source'] == source:
                return key
        return None

    def get_all_universal_mappings(self) -> Dict[str, Dict[str, any]]:
        """Get copy of all universal mappings."""
        return dict(self._universal_mappings)

    def get_all_output_keys(self) -> List[str]:
        """Get list of all unique output keys (IDs) used in mappings."""
        keys = set(self._universal_mappings.keys())
        return sorted(keys)

    def clear_universal_mappings(self) -> None:
        """Clear all universal mappings."""
        self._universal_mappings.clear()
        self._monitored_datarefs.clear() # Clear monitors too as they are usually tied to UI rows

    # ============================================================
    # Monitoring API (For Persistence)
    # ============================================================

    def add_monitor(self, dataref: str) -> None:
        """Track a dataref as being monitored (for UI persistence)."""
        if dataref and dataref.strip():
            self._monitored_datarefs.add(dataref)
        log.debug("Added monitor for %s", dataref)

    def remove_monitor(self, dataref: str) -> None:
        """Stop tracking a dataref."""
        if dataref in self._monitored_datarefs:
            self._monitored_datarefs.remove(dataref)

    def get_monitored_datarefs(self) -> List[str]:
        """Get list of all monitored datarefs."""
        return list(self._monitored_datarefs)

    def _send_if_changed(self, port: str, key: str, value: float) -> None:
        """Send value only if it changed significantly."""
        # Initialize cache
        if port not in self._last_sent:
            self._last_sent[port] = {}

        cache_key = f"{key}"
        last_value = self._last_sent[port].get(cache_key)

        # Threshold for float comparison
        if last_value is None or abs(value - last_value) > 0.001:
            self.send_value(port, key, value)
            self._last_sent[port][cache_key] = value

    @staticmethod
    def list_ports() -> List[Dict]:
        """Return list of available serial ports with device info."""
        if not SERIAL_AVAILABLE:
            return []
        
        try:
            ports = serial.tools.list_ports.comports()
            result = []
            
            for p in ports:
                info = {
                    "port": p.device,
                    "description": p.description,
                    "hwid": p.hwid,
                    "vid": p.vid,
                    "pid": p.pid,
                    "serial_number": p.serial_number,
                    "manufacturer": p.manufacturer,
                    "product": p.product,
                    "is_esp32": p.vid in ArduinoManager.ESP32_VIDS if p.vid else False,
                }
                result.append(info)
            
            return result
            
        except Exception as e:
            log.error("Failed to list ports: %s", e)
            return []
    
    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """Connect to a device on the specified port."""
        if not SERIAL_AVAILABLE:
            log.error("pyserial not available")
            return False
        
        with self._lock:
            if port in self._devices and self._devices[port].is_connected:
                log.warning("Already connected to %s", port)
                return False
            
            device = ArduinoDevice(port=port, baudrate=baudrate)
            self._devices[port] = device
        
        # Start device thread
        thread = threading.Thread(target=self._device_loop, args=(device,), daemon=True)
        self._threads[port] = thread
        thread.start()
        
        return True
    
    def disconnect(self, port: str) -> None:
        """Disconnect from a device."""
        with self._lock:
            device = self._devices.get(port)
            if device:
                device.transition(DeviceState.DISCONNECTED)
            
            ser = self._serials.pop(port, None)
            if ser:
                try:
                    ser.close()
                except Exception:
                    pass
        
        log.info("Disconnected from %s", port)
        self._notify_update()
    
    def disconnect_all(self) -> None:
        """Disconnect from all devices."""
        ports = list(self._devices.keys())
        for port in ports:
            self.disconnect(port)
    
    def devices_snapshot(self) -> Dict[str, ArduinoDevice]:
        """Get a snapshot of all devices."""
        with self._lock:
            return dict(self._devices)
    
    def get_device(self, port: str) -> Optional[ArduinoDevice]:
        """Get a specific device."""
        with self._lock:
            return self._devices.get(port)
    
    def send_value(self, port: str, key: str, value: float) -> bool:
        """Send a value to a device."""
        with self._lock:
            ser = self._serials.get(port)
            device = self._devices.get(port)
        
        if not ser or not device or not device.is_ready:
            return False
        
        try:
            line = f"SET {key} {value:.4f}\n"
            ser.write(line.encode())
            log.debug("Sent to %s: %s", port, line.strip())
            return True
        except Exception as e:
            log.error("Failed to send to %s: %s", port, e)
            return False
    
    def send_command(self, port: str, command: str) -> bool:
        """Send a raw command to a device."""
        with self._lock:
            ser = self._serials.get(port)
            device = self._devices.get(port)

        if not ser or not device or not device.is_ready:
            return False

        try:
            ser.write(f"{command}\n".encode())
            log.debug("Sent command to %s: %s", port, command)
            return True
        except Exception as e:
            log.error("Failed to send command to %s: %s", port, e)
            return False

    def send_dref_command(self, port: str, dataref: str, value: float) -> bool:
        """Send a DREF command to a device."""
        command = f"DREF {dataref} {value}"
        return self.send_command(port, command)

    def send_cmd_command(self, port: str, command: str) -> bool:
        """Send a CMD command to a device."""
        full_command = f"CMD {command}"
        return self.send_command(port, full_command)
    
    def subscribe_dataref(self, port: str, dataref: str, key: str) -> bool:
        """
        Subscribe a device to a dataref.
        When the dataref changes, send "SET <key> <value>" to the device.
        """
        with self._lock:
            device = self._devices.get(port)
            if device:
                device.subscriptions[dataref] = key
                log.info("Device %s subscribed: %s -> %s", port, dataref, key)
                return True
        return False
    
    def unsubscribe_dataref(self, port: str, dataref: str) -> None:
        """Unsubscribe a device from a dataref."""
        with self._lock:
            device = self._devices.get(port)
            if device and dataref in device.subscriptions:
                del device.subscriptions[dataref]
    
    def on_dataref_update(self, dataref: str, value: float) -> None:
        """
        Called when a dataref value changes.
        Broadcasts to all devices if a universal mapping exists.
        """
        # 1. Check for Universal Mapping
        universal_key = self._universal_mappings.get(dataref)

        if universal_key:
            # Broadcast to ALL connected devices
            with self._lock:
                ports = [p for p, d in self._devices.items() if d.is_ready]

            for port in ports:
                self._send_if_changed(port, universal_key, value)

        # 2. Check for Specific Subscriptions (Legacy/Direct mode)
        # This preserves existing functionality for specific device subscriptions
        with self._lock:
            devices_to_update = []
            for port, device in self._devices.items():
                if dataref in device.subscriptions and device.is_ready:
                    key = device.subscriptions[dataref]
                    # Avoid double sending if we just broadcasted the same key
                    if key != universal_key:
                        devices_to_update.append((port, key))

        for port, key in devices_to_update:
            self._send_if_changed(port, key, value)

    def broadcast_by_key(self, key: str, value: Any) -> bool:
        """
        Broadcast a value to all Arduino devices using the specified key.
        Handles different dataref types appropriately.
        
        Args:
            key: The OUTPUT ID key
            value: The value to send (type depends on dataref)
        
        Returns:
            True if successful, False otherwise
        """
        # Find the dataref associated with this key
        dataref = self._get_dataref_by_key(key)
        if not dataref:
            log.warning("No dataref found for key: %s", key)
            # Fall back to simple broadcast for unmapped keys
            self._simple_broadcast(key, value)
            return False
        
        # Get dataref info
        info = self.dataref_manager.get_dataref_info(dataref) if self.dataref_manager else None
        if not info:
            log.warning("No info found for dataref: %s", dataref)
            # Fall back to simple broadcast
            self._simple_broadcast(key, value)
            return False
        
        dataref_type = info.get("type", "")
        
        # Handle based on dataref type
        if dataref_type == "command":
            # Commands don't have values, just execute
            return self._execute_command(dataref)
        elif "[" in dataref_type:
            # Array type
            return self._handle_array_dataref(dataref, dataref_type, value)
        elif "string" in dataref_type or "byte" in dataref_type:
            # String/byte type
            return self._handle_string_dataref(dataref, dataref_type, value)
        else:
            # Scalar type (int, float, double, bool)
            return self._handle_scalar_dataref(dataref, dataref_type, value)

    def _simple_broadcast(self, key: str, value: Any) -> None:
        """Simple broadcast for unmapped keys - converts value to float."""
        if not key:
            return

        # Convert value to float for backward compatibility
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            log.warning("Cannot convert value %s to float for key %s", value, key)
            return

        with self._lock:
            ports = [p for p, d in self._devices.items() if d.is_ready]

        for port in ports:
            self._send_if_changed(port, key, float_value)

    def _get_dataref_by_key(self, key: str) -> Optional[str]:
        """Find the dataref associated with an OUTPUT ID key."""
        mapping = self._universal_mappings.get(key.upper())
        if mapping:
            return mapping.get('source')
        return None

    def _execute_command(self, command: str) -> bool:
        """Execute a command dataref."""
        if not self.xplane_conn:
            log.warning("No X-Plane connection available for command: %s", command)
            return False
        
        try:
            task = asyncio.create_task(self.xplane_conn.send_command(command))
            self._tasks.append(task)  # Store task to prevent garbage collection
            log.info("Executed command: %s", command)
            return True
        except Exception as e:
            log.error("Failed to execute command %s: %s", command, e)
            return False

    def _handle_array_dataref(self, dataref: str, dataref_type: str, value: Any) -> bool:
        """Handle array datarefs (int[n], float[n], byte[n])."""
        if not self.xplane_conn:
            log.warning("No X-Plane connection available for array dataref: %s", dataref)
            return False
        
        # Parse array size
        match = re.search(r'\[(\d+)\]', dataref_type)
        if not match:
            log.warning("Invalid array type: %s", dataref_type)
            return False
        
        array_size = int(match.group(1))
        
        try:
            # Handle different array types
            if isinstance(value, (list, tuple)):
                # If value is a list, write each element
                if len(value) > array_size:
                    log.warning("Value list too long for array of size %d", array_size)
                    value = value[:array_size]
                
                # Write each element
                tasks = []
                for i, val in enumerate(value):
                    indexed_dataref = f"{dataref}[{i}]"
                    float_val = float(val)
                    task = asyncio.create_task(self.xplane_conn.write_dataref(indexed_dataref, float_val))
                    tasks.append(task)

                log.info("Wrote array %s with %d elements", dataref, len(value))
                return True
            else:
                # If value is a scalar, write to first element
                indexed_dataref = f"{dataref}[0]"
                float_val = float(value)
                task = asyncio.create_task(self.xplane_conn.write_dataref(indexed_dataref, float_val))
                log.info("Wrote scalar value to first element of array %s", dataref)
                return True
        except (ValueError, TypeError) as e:
            log.error("Failed to write array dataref %s: %s", dataref, e)
            return False

    def _handle_string_dataref(self, dataref: str, dataref_type: str, value: Any) -> bool:
        """Handle string/byte datarefs."""
        if not self.xplane_conn:
            log.warning("No X-Plane connection available for string dataref: %s", dataref)
            return False
        
        # Parse array size
        match = re.search(r'\[(\d+)\]', dataref_type)
        if not match:
            log.warning("Invalid byte array type: %s", dataref_type)
            return False
        
        max_len = int(match.group(1))
        
        try:
            # Convert value to string if needed
            if not isinstance(value, str):
                value = str(value)
            
            # Truncate if too long
            if len(value) > max_len:
                log.warning("String too long for dataref of size %d", max_len)
                value = value[:max_len]
            
            # Write string to dataref
            task = asyncio.create_task(self.xplane_conn.write_dataref_string(dataref, value, max_len))
            self._tasks.append(task)  # Store task to prevent garbage collection
            log.info("Wrote string to dataref %s: %s", dataref, value)
            return True
        except Exception as e:
            log.error("Failed to write string dataref %s: %s", dataref, e)
            return False

    def _handle_scalar_dataref(self, dataref: str, dataref_type: str, value: Any) -> bool:
        """Handle scalar datarefs (int, float, double, bool)."""
        if not self.xplane_conn:
            log.warning("No X-Plane connection available for scalar dataref: %s", dataref)
            return False
        
        try:
            # Convert to appropriate type
            if dataref_type == "int":
                float_val = float(int(value))
            elif dataref_type == "bool":
                float_val = 1.0 if bool(value) else 0.0
            else:  # float, double
                float_val = float(value)
            
            # Write to dataref
            task = asyncio.create_task(self.xplane_conn.write_dataref(dataref, float_val))
            self._tasks.append(task)  # Store task to prevent garbage collection
            log.info("Wrote scalar value to dataref %s: %s (%s)", dataref, value, dataref_type)
            return True
        except (ValueError, TypeError) as e:
            log.error("Failed to write scalar dataref %s: %s", dataref, e)
            return False
    
    # ============================================================
    # Device Communication Loop
    # ============================================================
    
    def _device_loop(self, device: ArduinoDevice) -> None:
        """Main communication loop for a device."""
        port = device.port
        ser = None
        
        try:
            device.transition(DeviceState.CONNECTING)
            self._notify_update()
            
            # Open serial port
            try:
                ser = serial.Serial(
                    device.port,
                    device.baudrate,
                    timeout=1.0,
                    write_timeout=1.0
                )
            except serial.SerialException as e:
                device.transition(DeviceState.ERROR, f"Cannot open port: {e}")
                self._notify_update()
                return
            
            with self._lock:
                self._serials[port] = ser
            
            # Wait for device reset
            log.info("Waiting for device reset on %s...", port)
            time.sleep(2.5)
            
            # Clear buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # Perform handshake
            device.transition(DeviceState.HANDSHAKE)
            self._notify_update()
            
            if not self._perform_handshake(device, ser):
                device.transition(DeviceState.ERROR, "Handshake failed")
                self._notify_update()
                return
            
            # Ready
            device.transition(DeviceState.READY)
            self._notify_update()
            log.info("Device ready on %s: %s %s (%s)", 
                     port, device.board_type, device.firmware_version, device.device_name)
            
            # Main communication loop
            while device.state in (DeviceState.READY, DeviceState.ACTIVE):
                try:
                    self._process_incoming(device, ser)
                except serial.SerialException:
                    break
                
                time.sleep(0.010)
        
        except Exception as e:
            log.error("Device loop error on %s: %s", port, e)
            device.transition(DeviceState.ERROR, str(e))
        
        finally:
            with self._lock:
                self._serials.pop(port, None)
            
            if ser:
                try:
                    ser.close()
                except Exception:
                    pass
            
            if device.state not in (DeviceState.DISCONNECTED, DeviceState.ERROR):
                device.transition(DeviceState.DISCONNECTED)
            
            self._notify_update()
            log.info("Device loop ended for %s", port)
    
    def _perform_handshake(self, device: ArduinoDevice, ser: serial.Serial) -> bool:
        """Perform handshake with device."""
        try:
            # Send hello
            ser.write(b"HELLO\n")
            
            # Wait for response
            start = time.time()
            while time.time() - start < 5.0:
                if ser.in_waiting:
                    line = ser.readline().decode(errors="ignore").strip()
                    
                    if line.startswith("XPDR"):
                        # Handshake format: XPDR;fw=1.0;board=ESP32S2;name=FGCP
                        self._parse_handshake(device, line)
                        return True
                
                time.sleep(0.1)
            
            log.warning("Handshake timeout on %s", device.port)
            return False
        
        except Exception as e:
            log.error("Handshake error on %s: %s", device.port, e)
            return False
    
    def _parse_handshake(self, device: ArduinoDevice, line: str) -> None:
        """Parse handshake response."""
        parts = line.split(";")
        
        for part in parts[1:]:
            if "=" in part:
                key, val = part.split("=", 1)
                if key == "fw":
                    device.firmware_version = val
                elif key == "board":
                    device.board_type = val
                    device.device_type = self._detect_device_type(val)
                elif key == "name":
                    device.device_name = val
    
    def _detect_device_type(self, board: str) -> DeviceType:
        """Detect device type from board string."""
        board_lower = board.lower()
        
        if "esp32s2" in board_lower:
            return DeviceType.ESP32S2
        elif "esp32s3" in board_lower:
            return DeviceType.ESP32S3
        elif "esp32" in board_lower:
            return DeviceType.ESP32
        elif "leonardo" in board_lower:
            return DeviceType.ARDUINO_LEONARDO
        elif "micro" in board_lower:
            return DeviceType.ARDUINO_PRO_MICRO
        elif "nano" in board_lower:
            return DeviceType.ARDUINO_NANO
        else:
            return DeviceType.UNKNOWN
    
    def _process_incoming(self, device: ArduinoDevice, ser: serial.Serial) -> None:
        """Process incoming messages from device."""
        while ser.in_waiting:
            try:
                line = ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                
                device.last_seen = time.time()
                
                if device.state == DeviceState.READY:
                    device.transition(DeviceState.ACTIVE)
                    self._notify_update()
                
                # Notify raw message listeners
                if self.on_message_received:
                    self.on_message_received(device.port, line)
                
                # Parse specific message types
                if line.startswith("INPUT "):
                    self._handle_input(device, line)
                elif line.startswith("DREF "):
                    self._handle_dref(device, line)
                elif line.startswith("CMD "):
                    self._handle_cmd(device, line)
                elif line.startswith("ACK "):
                    log.debug("ACK from %s: %s", device.port, line)
                elif line.startswith("STATUS"):
                    log.debug("Status from %s: %s", device.port, line)
                    
            except Exception as e:
                log.error("Error processing message from %s: %s", device.port, e)
    
    def _handle_input(self, device: ArduinoDevice, line: str) -> None:
        """Handle INPUT message from device."""
        # Format: INPUT <key> <value>
        parts = line.split()
        if len(parts) >= 3:
            key = parts[1]
            try:
                value = float(parts[2])
                device.set_input(key, value)

                # Update variable store if available
                if self.variable_store:
                    from core.variable_store import VariableType
                    self.variable_store.update_value(
                        key,
                        value,
                        VariableType.VARIABLE_ARDUINO,
                        f"Input from Arduino device on {device.port}"
                    )

                # Notify listeners
                if self.on_input_received:
                    self.on_input_received(device.port, key, value)

                log.debug("Input from %s: %s = %.4f", device.port, key, value)

            except ValueError:
                pass

    def _handle_dref(self, device: ArduinoDevice, line: str) -> None:
        """Handle DREF message from device to set dataref value."""
        # Format: DREF sim/dataref 1.0
        # Split by FIRST space (DREF), then LAST space (Value) is safer
        try:
            # Extract the part after "DREF "
            data_part = line[5:].strip()
            # Split from the right side to separate dataref from value
            parts = data_part.rsplit(' ', 1)
            if len(parts) == 2:
                dataref = parts[0].strip()
                val_str = parts[1].strip()

                try:
                    value = float(val_str)

                    # Notify listeners that a dataref should be written
                    if self.on_dataref_write:
                        self.on_dataref_write(dataref, value)

                    log.info("DREF command from %s: %s = %.4f", device.port, dataref, value)
                except ValueError:
                    log.error("Invalid float value from Arduino: '%s'", val_str)
            else:
                log.error("Invalid DREF format: %s", line)
        except Exception as e:
            log.error("Error parsing DREF command: %s", e)

    def _handle_cmd(self, device: ArduinoDevice, line: str) -> None:
        """Handle CMD message from device to send X-Plane command."""
        # Format: CMD sim/cockpit/electrical/beacon_lights_toggle
        try:
            # Extract the command after "CMD "
            command = line[4:].strip()

            # Notify listeners that a command should be sent
            if self.on_command_send:
                self.on_command_send(command)

            log.info("CMD command from %s: %s", device.port, command)
        except Exception as e:
            log.error("Error parsing CMD command: %s", e)
    
    def _notify_update(self) -> None:
        """Notify listeners of device state change."""
        if self.on_device_update:
            self.on_device_update(self.devices_snapshot())
