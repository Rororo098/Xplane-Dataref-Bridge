from __future__ import annotations
import logging
import asyncio
import socket
import struct
import time
import errno
from typing import Optional, Callable, Dict, List, Union
from dataclasses import dataclass, field
import threading

log = logging.getLogger(__name__)


@dataclass
class DatarefSubscription:
    name: str
    index: int
    frequency: int
    value: float = 0.0
    # NEW: Metadata for array handling
    is_array: bool = False
    array_index: int = -1
    base_name: str = ""


class XPlaneConnection:
    def __init__(self, ip: str = "127.0.0.1", send_port: int = 49000, recv_port: int = 49001) -> None:
        self.ip = ip
        self.port = send_port
        self.recv_port = recv_port
        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._running = False
        self._recv_thread: Optional[threading.Thread] = None
        self._subscriptions: Dict[int, DatarefSubscription] = {}
        self._dataref_to_index: Dict[str, int] = {}
        self._next_index = 1
        
        # Discovery status
        self._discovered_info: Dict[str, Any] = {}
        self._beacon_stop_event = threading.Event()
        self._beacon_thread: Optional[threading.Thread] = None
        
        self.on_dataref_update: Optional[Callable[[str, float], None]] = None
        self.on_connection_changed: Optional[Callable[[bool], None]] = None

        # Separate storage for live values (from X-Plane) and virtual values (written by user/system)
        self._live_values: Dict[str, float] = {}  # Values received from X-Plane
        self._virtual_values: Dict[str, float] = {}  # Values written by user/system
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    async def connect(self) -> bool:
        if self._connected: return True
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                self._socket.bind(("0.0.0.0", self.recv_port))
                log.info("Bound to receive port %d", self.recv_port)
            except OSError as e:
                log.error("Cannot bind to port %d: %s", self.recv_port, e)
                log.error("Make sure no other application is using this port")
                self._cleanup()
                return False
            
            self._socket.setblocking(False)
            
            self._connected = True
            self._running = True
            
            self._recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._recv_thread.start()
            
            # Start Beacon Listener for auto-discovery
            self.start_beacon_listener()
            
            time.sleep(0.1)
            
            # Re-send all stored subscriptions upon connection
            log.info("Synchronizing %d subscriptions...", len(self._subscriptions))
            for sub in self._subscriptions.values():
                self._send_rref_sync(sub.name, sub.index, sub.frequency)

            log.info("Connected to X-Plane: %s:%d", self.ip, self.port)
            if self.on_connection_changed:
                self.on_connection_changed(True)
            
            return True
            
        except Exception as e:
            log.error("Failed to connect to X-Plane: %s", e)
            self._cleanup()
            return False
    
    async def disconnect(self) -> None:
        if not self._connected: return
        
        log.info("Disconnecting from X-Plane...")
        self._running = False
        self.stop_beacon_listener()
        
        # Unsubscribe all
        for sub in list(self._subscriptions.values()):
            try:
                self._send_rref_sync(sub.name, sub.index, 0)
            except Exception:
                pass
        
        if self._recv_thread and self._recv_thread.is_alive():
            self._recv_thread.join(timeout=2.0)
        
        self._subscriptions.clear()
        self._dataref_to_index.clear()
        self._next_index = 1
        self._cleanup()
        
        if self.on_connection_changed:
            self.on_connection_changed(False)
    
    def _cleanup(self) -> None:
        self._connected = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    async def subscribe_dataref(self, dataref: str, frequency: int = 5, count: int = 1) -> int:
        # Strip prefixes
        if dataref.startswith("XP:"):
            dataref = dataref[3:]
            
        # Determine if we should subscribe to a range (array)
        if count > 1:
            base_name = dataref.split("[")[0]
            first_idx = -1
            
            for i in range(count):
                name = f"{base_name}[{i}]"
                if name in self._dataref_to_index:
                    idx = self._dataref_to_index[name]
                else:
                    idx = self._next_index
                    self._next_index += 1
                    
                    sub = DatarefSubscription(
                        name=name, 
                        index=idx, 
                        frequency=frequency, 
                        is_array=True, 
                        array_index=i, 
                        base_name=base_name
                    )
                    self._subscriptions[idx] = sub
                    self._dataref_to_index[name] = idx
                
                if first_idx == -1: first_idx = idx
                self._send_rref_sync(name, idx, frequency)
            
            return first_idx
        
        # Handle explicit indexed subscription (e.g. sim/foo[0]) if passed via name
        if "[" in dataref and "]" in dataref and count == 1:
            # We treat this as a single scalar subscription to an indexed element
            if dataref in self._dataref_to_index:
                return self._dataref_to_index[dataref]
            
            idx = self._next_index
            self._next_index += 1
            
            sub = DatarefSubscription(name=dataref, index=idx, frequency=frequency, is_array=False)
            self._subscriptions[idx] = sub
            self._dataref_to_index[dataref] = idx
            self._send_rref_sync(dataref, idx, frequency)
            return idx
            
        # Standard Scalar Subscription
        if dataref in self._dataref_to_index:
            return self._dataref_to_index[dataref]
        
        idx = self._next_index
        self._next_index += 1
        
        sub = DatarefSubscription(name=dataref, index=idx, frequency=frequency, is_array=False)
        self._subscriptions[idx] = sub
        self._dataref_to_index[dataref] = idx
        
        self._send_rref_sync(dataref, idx, frequency)
        return idx

    async def unsubscribe_dataref(self, dataref: str) -> None:
        if dataref.startswith("XP:"):
            dataref = dataref[3:]
            
        # Check if we have multiple subscriptions starting with this base
        base = dataref.split("[")[0]
        keys_to_remove = [k for k in self._dataref_to_index if k == dataref or k.startswith(f"{base}[")]
        
        for k in keys_to_remove:
            idx = self._dataref_to_index[k]
            self._send_rref_sync(k, idx, 0)
            if idx in self._subscriptions:
                del self._subscriptions[idx]
            if k in self._dataref_to_index:
                del self._dataref_to_index[k]

    async def write_dataref(self, dataref: str, value: float) -> bool:
        # Store original dataref for callback to maintain prefix information
        original_dataref = dataref

        if dataref.startswith("XP:"):
            dataref = dataref[3:]

        # Update internal cache REGARDLESS of connection
        # This allows "ghost" or "custom" datarefs to have local state
        if dataref in self._dataref_to_index:
            idx = self._dataref_to_index[dataref]
            if idx in self._subscriptions:
                self._subscriptions[idx].value = value

        # Store as virtual value (written by user/system)
        self._virtual_values[dataref] = value

        if not self._socket or not self._connected:
            # Still notify locally even if not connected for UI consistency
            if self.on_dataref_update:
                self.on_dataref_update(original_dataref, value)
            return True

        try:
            # Construction of a 509-byte DREF packet
            # Format: 'DREF' (4) + Null (1) + Float (4) + Name (500)
            msg = bytearray(509)
            msg[0:4] = b"DREF"
            # msg[4] is 0x00

            # Pack float value at offset 5
            struct.pack_into("<f", msg, 5, float(value))

            # Fill the name buffer (index 9 to 508) with SPACES first (0x20)
            # This is suggested by some X-Plane docs for better reliability.
            msg[9:509] = b' ' * 500

            # Pack name at offset 9
            name_bytes = dataref.encode("utf-8")
            if len(name_bytes) > 499:
                log.error("Dataref name too long: %s", dataref)
                return False

            msg[9 : 9 + len(name_bytes)] = name_bytes
            # Null terminate the name specifically
            msg[9 + len(name_bytes)] = 0x00

            self._socket.sendto(msg, (self.ip, self.port))
            log.info("UDP DREF Pack: %s = %.4f to %s:%d", dataref, value, self.ip, self.port)

            # Notify locally immediately so UI/Logic sees it (crucial for custom/ghost datarefs)
            # Use original dataref to preserve prefix information
            if self.on_dataref_update:
                self.on_dataref_update(original_dataref, value)
            return True

        except Exception as e:
            log.error("Failed to write dataref %s: %s", dataref, e)
            return False
    
    async def write_dataref_string(self, dataref: str, string_value: str, max_len: int = 0) -> bool:
        """
        Writes a string to a byte[n] dataref (e.g., acf_ICAO).
        Iterates through indices and sends each char as float.
        If max_len is provided, clears the rest of the buffer with nulls.
        """
        # Store original dataref for consistency
        original_dataref = dataref

        if dataref.startswith("XP:"):
            dataref = dataref[3:]

        if not self._connected and self._socket is None:
            log.warning("Attempted to write string to %s but not connected", dataref)
            # Still allow local updates for UI consistency
            return True

        base_name = dataref.split("[")[0]
        log.info("Sending string '%s' to %s", string_value, base_name)

        # 1. Write characters from string
        for i, char_code in enumerate(string_value):
            if i >= 499: break # UDP packet limit for one DREF
            await self.write_dataref(f"{base_name}[{i}]", float(ord(char_code)))

        # 2. Add Null Terminator
        last_idx = len(string_value)
        await self.write_dataref(f"{base_name}[{last_idx}]", 0.0)

        # 3. Clear trailing bytes if max_len is known
        if max_len > last_idx + 1:
            # We don't want to spam 500 packets. Maybe clear just a few more?
            # Or trust the first null is enough for most UI.
            # Let's clear up to 4 more bytes just in case.
            for i in range(last_idx + 1, min(last_idx + 5, max_len)):
                await self.write_dataref(f"{base_name}[{i}]", 0.0)

        return True

    async def select_data_output(self, indices: List[int]) -> bool:
        """Sends DSEL packet to enable specific Data Output rows."""
        if not self._socket or not self._connected: return False
        try:
            # DSEL\0 (5 bytes) + array of 4-byte ints
            msg = bytearray(5 + len(indices) * 4)
            msg[0:4] = b"DSEL"
            for i, idx in enumerate(indices):
                struct.pack_into("<i", msg, 5 + i * 4, int(idx))
            self._socket.sendto(msg, (self.ip, self.port))
            log.info("UDP DSEL: Enabled %d rows", len(indices))
            return True
        except Exception as e:
            log.error("Failed to send DSEL: %s", e)
            return False

    async def set_data_output_target(self, target_ip: str, target_port: int) -> bool:
        """Sends ISE4 packet to tell X-Plane to send DATA outputs to this target."""
        if not self._socket or not self._connected: return False
        try:
            # ISE4\0 (5 bytes) + index (4) + ip(16) + pt(8) + use(4) = 37 bytes
            msg = bytearray(37)
            msg[0:4] = b"ISE4"
            struct.pack_into("<i", msg, 5, 64) # 64 is index for Data Output
            ip_b = target_ip.encode("utf-8")
            msg[9:9+len(ip_b)] = ip_b
            pt_b = str(target_port).encode("utf-8")
            msg[25:25+len(pt_b)] = pt_b
            struct.pack_into("<i", msg, 33, 1) # 1 = Enable
            self._socket.sendto(msg, (self.ip, self.port))
            log.info("UDP ISE4: Set target to %s:%d", target_ip, target_port)
            return True
        except Exception as e:
            log.error("Failed to send ISE4: %s", e)
            return False

    def start_beacon_listener(self):
        """Starts a thread to listen for X-Plane discovery beacons."""
        if self._beacon_thread and self._beacon_thread.is_alive(): return
        self._beacon_stop_event.clear()
        self._beacon_thread = threading.Thread(target=self._beacon_loop, daemon=True)
        self._beacon_thread.start()
        log.info("Discovery Beacon listener started")

    def stop_beacon_listener(self):
        self._beacon_stop_event.set()

    def _beacon_loop(self):
        """Background loop to catch BECN packets on port 49707."""
        b_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        b_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            b_sock.bind(("", 49707))
            b_sock.settimeout(1.0)
        except Exception as e:
            log.error("Failed to bind discovery socket: %s", e)
            return

        while not self._beacon_stop_event.is_set():
            try:
                data, addr = b_sock.recvfrom(1024)
                if data.startswith(b"BECN"):
                    # BECN format: 'BECN' (4) + null (1) + ver_major(1) + ver_minor(1) + hostid(4) + ver(4) + role(4) + port(2)
                    xp_port = struct.unpack("<H", data[19:21])[0]
                    xp_ip = addr[0]
                    
                    if xp_ip != self.ip or xp_port != self.port:
                        log.info("Discovered X-Plane at %s:%d", xp_ip, xp_port)
                        self.ip = xp_ip
                        self.port = xp_port
                        # Trigger any callbacks if needed?
                    
                    self._discovered_info = {
                        "ip": xp_ip,
                        "port": xp_port,
                        "last_seen": time.time()
                    }
            except socket.timeout:
                continue
            except Exception as e:
                log.error("Beacon error: %s", e)
                break
        b_sock.close()

    async def send_command(self, command: str) -> bool:
        if not self._socket or not self._connected: return False
        try:
            packet = b"CMND\x00"
            packet += command.encode("utf-8").ljust(500, b"\x00")
            self._socket.sendto(packet, (self.ip, self.port))
            return True
        except Exception as e:
            log.error("Failed to send command %s: %s", command, e)
            return False
    
    def _send_rref_sync(self, dataref: str, index: int, frequency: int) -> None:
        if not self._socket: return
        try:
            packet = b"RREF\x00"
            packet += struct.pack("<ii", frequency, index)
            packet += dataref.encode("utf-8").ljust(400, b"\x00")
            self._socket.sendto(packet, (self.ip, self.port))
        except Exception as e:
            log.error("Failed to send RREF: %s", e)
    
    def _receive_loop(self) -> None:
        log.info("Receive loop started on port %d", self.recv_port)
        while self._running and self._socket:
            try:
                try:
                    data, addr = self._socket.recvfrom(4096)
                except BlockingIOError:
                    time.sleep(0.001)
                    continue
                except OSError as e:
                    if hasattr(e, 'winerror') and e.winerror == 10054:
                        continue
                    elif e.errno == errno.ECONNRESET:
                        continue
                    elif self._running:
                        log.error("Socket error in receive loop: %s", e)
                        break
                
                if len(data) < 5: continue
                
                header = data[:4].decode("utf-8", errors="ignore")

                if header == "RREF":
                    self._parse_rref(data)
                elif header == "DATA":
                    self._parse_data(data)
                elif header == "DREF":
                    self._parse_dref(data)
                else:
                    if len(data) > 0:
                        log.debug("Unknown packet: %s (%d bytes)", header, len(data))
                    
            except Exception as e:
                if self._running:
                    log.error("Receive loop error: %s", e)
        
        log.info("Receive loop ended")
    
    def _parse_rref(self, data: bytes) -> None:
        offset = 5
        while offset + 8 <= len(data):
            index, value = struct.unpack_from("<if", data, offset)
            offset += 8

            sub = self._subscriptions.get(index)
            if sub:
                sub.value = value
                # Store as live value (received from X-Plane)
                self._live_values[sub.name] = value

                if self.on_dataref_update:
                    try:
                        # Add array index to name if needed
                        name_to_report = sub.name
                        if sub.is_array:
                            name_to_report = f"{sub.base_name}[{sub.array_index}]"

                        self.on_dataref_update(name_to_report, value)
                    except Exception as e:
                        log.error("Callback error for %s: %s", sub.name, e)

    def _parse_data(self, data: bytes) -> None:
        """Parses standard X-Plane DATA packets (36-byte blocks)."""
        offset = 5
        while offset + 36 <= len(data):
            row_idx = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            # 8 float values follow
            values = struct.unpack_from("<8f", data, offset)
            offset += 32
            
            # log.debug("Received DATA Row %d: %s", row_idx, values)
            # We don't have a direct map to dataref names here, 
            # so this is mostly for debugging or future mapping.
            pass

    def _parse_dref(self, data: bytes) -> None:
        if len(data) < 9: return
        try:
            value = struct.unpack_from("<f", data, 5)[0]
            name_start = 9
            name_end = data.find(b'\x00', name_start)
            if name_end == -1: name_end = len(data)
            dataref_name = data[name_start:name_end].decode("utf-8", errors="ignore").strip()

            if dataref_name and self.on_dataref_update:
                # Check if this is an array index we are tracking
                if dataref_name in self._dataref_to_index:
                    idx = self._dataref_to_index[dataref_name]
                    if idx in self._subscriptions:
                        self._subscriptions[idx].value = value

                # Store as live value (received from X-Plane)
                self._live_values[dataref_name] = value

                self.on_dataref_update(dataref_name, value)

        except Exception as e:
            log.debug("DREF parse error: %s", e)
    
    def get_value(self, dataref: str, source: str = "any") -> Optional[float]:
        """
        Get value for a dataref.

        Args:
            dataref: The dataref name
            source: "live" for X-Plane values, "virtual" for written values, "any" for first available
        """
        # Strip prefixes
        if dataref.startswith("XP:"):
            dataref = dataref[3:]
        elif dataref.startswith("VAR:"):
            # VAR: is handled by VariableStore, but if it leaks here...
            dataref = dataref[4:]

        if source == "live":
            return self._live_values.get(dataref)
        elif source == "virtual":
            return self._virtual_values.get(dataref)
        else:  # "any"
            # Prioritize live values over virtual values
            if dataref in self._live_values:
                return self._live_values[dataref]
            elif dataref in self._virtual_values:
                return self._virtual_values[dataref]
            elif dataref in self._dataref_to_index:
                idx = self._dataref_to_index[dataref]
                sub = self._subscriptions.get(idx)
                return sub.value if sub else None
        return None

    def get_live_value(self, dataref: str) -> Optional[float]:
        """Get the live value received from X-Plane."""
        if dataref.startswith("XP:"):
            dataref = dataref[3:]
        elif dataref.startswith("VAR:"):
            dataref = dataref[4:]
        return self._live_values.get(dataref)

    def get_virtual_value(self, dataref: str) -> Optional[float]:
        """Get the virtual value written by user/system."""
        if dataref.startswith("XP:"):
            dataref = dataref[3:]
        elif dataref.startswith("VAR:"):
            dataref = dataref[4:]
        return self._virtual_values.get(dataref)

    def get_all_live_values(self) -> Dict[str, float]:
        """Get all live values received from X-Plane."""
        return self._live_values.copy()

    def get_all_virtual_values(self) -> Dict[str, float]:
        """Get all virtual values written by user/system."""
        return self._virtual_values.copy()
    
    def get_all_values(self) -> Dict[str, float]:
        return {sub.name: sub.value for sub in self._subscriptions.values()}