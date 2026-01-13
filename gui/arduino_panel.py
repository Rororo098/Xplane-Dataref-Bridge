from __future__ import annotations
import logging
from typing import Dict, Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QGroupBox, QFormLayout, QComboBox, QTextEdit,
    QSplitter, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QCompleter, QTabWidget, QFrame,
    QScrollArea, QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

from core.arduino.arduino_device import ArduinoDevice, DeviceState
from core.arduino.arduino_manager import ArduinoManager

log = logging.getLogger(__name__)


class DeviceWidget(QFrame):
    """Widget representing a single connected device."""
    
    def __init__(self, port: str, arduino_manager: ArduinoManager, dataref_list: List[str], parent=None):
        super().__init__(parent)
        self.port = port
        self.arduino_manager = arduino_manager
        self.dataref_list = dataref_list
        
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.port_label = QLabel(f"<b>{self.port}</b>")
        self.port_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(self.port_label)
        
        self.status_label = QLabel("Connecting...")
        self.status_label.setStyleSheet("color: orange;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setMaximumWidth(100)
        header_layout.addWidget(self.disconnect_btn)
        
        layout.addLayout(header_layout)
        
        # Device info
        self.info_label = QLabel("Waiting for handshake...")
        self.info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setMaximumHeight(280)
        
        # === Mappings Tab ===
        mappings_widget = QWidget()
        mappings_layout = QVBoxLayout(mappings_widget)
        mappings_layout.setContentsMargins(4, 4, 4, 4)
        
        # Add mapping
        add_layout = QHBoxLayout()
        
        self.dataref_input = QLineEdit()
        self.dataref_input.setPlaceholderText("Dataref name...")
        
        if self.dataref_list:
            completer = QCompleter(self.dataref_list)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(10)
            self.dataref_input.setCompleter(completer)
        
        add_layout.addWidget(self.dataref_input)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Device Output ID")
        self.key_input.setMaximumWidth(100)
        self.key_input.setToolTip(
            "The ID defined in your Arduino firmware.\n"
            "Examples: LED, GEAR, AP, WARN, PIN_13\n"
            "Use the 'LIST' command in the Monitor to see available IDs."
        )
        add_layout.addWidget(self.key_input)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.setMaximumWidth(50)
        add_layout.addWidget(self.add_btn)
        
        mappings_layout.addLayout(add_layout)
        
        # Quick mappings
        quick_layout = QHBoxLayout()
        
        quick_mappings = [
            ("Gear", "sim/cockpit2/switches/gear_handle_status", "GEAR"),
            ("AP", "sim/cockpit/autopilot/autopilot_state", "AP"),
            ("Warn", "sim/cockpit/warnings/master_warning", "WARN"),
            ("Caut", "sim/cockpit/warnings/master_caution", "CAUT"),
            ("Beacon", "sim/cockpit2/switches/beacon_on", "BEACON"),
        ]
        
        for name, dataref, key in quick_mappings:
            btn = QPushButton(name)
            btn.setMaximumWidth(55)
            btn.setToolTip(f"{dataref} → {key}")
            btn.clicked.connect(lambda checked, d=dataref, k=key: self._add_mapping(d, k))
            quick_layout.addWidget(btn)
        
        quick_layout.addStretch()
        mappings_layout.addLayout(quick_layout)

        # Add help label
        help_label = QLabel(
            "<span style='color: gray; font-size: 10px;'>"
            "Map an X-Plane dataref to a named output on this device.<br>"
            "Example: <i>sim/cockpit/gear_handle_status</i> → <b>GEAR</b>"
            "</span>"
        )
        mappings_layout.addWidget(help_label)

        # Mapping table
        self.mapping_table = QTableWidget(0, 3)
        self.mapping_table.setHorizontalHeaderLabels(["X-Plane Dataref", "Device Output ID", ""])
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.mapping_table.setMaximumHeight(120)
        mappings_layout.addWidget(self.mapping_table)
        
        self.tabs.addTab(mappings_widget, "Mappings")
        
        # === Monitor Tab ===
        monitor_widget = QWidget()
        monitor_layout = QVBoxLayout(monitor_widget)
        monitor_layout.setContentsMargins(4, 4, 4, 4)
        
        self.monitor_text = QTextEdit()
        self.monitor_text.setReadOnly(True)
        self.monitor_text.setStyleSheet("font-family: monospace; font-size: 9pt;")
        self.monitor_text.setMaximumHeight(100)
        monitor_layout.addWidget(self.monitor_text)
        
        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Command...")
        cmd_layout.addWidget(self.cmd_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setMaximumWidth(50)
        cmd_layout.addWidget(self.send_btn)
        
        for cmd in ["LIST", "STATUS", "TEST"]:
            btn = QPushButton(cmd)
            btn.setMaximumWidth(50)
            btn.clicked.connect(lambda checked, c=cmd: self._send_command(c))
            cmd_layout.addWidget(btn)
        
        monitor_layout.addLayout(cmd_layout)
        
        self.tabs.addTab(monitor_widget, "Monitor")
        
        layout.addWidget(self.tabs)
    
    def _connect_signals(self):
        self.disconnect_btn.clicked.connect(self._disconnect)
        self.add_btn.clicked.connect(self._add_mapping_from_inputs)
        self.send_btn.clicked.connect(self._send_command_from_input)
        self.cmd_input.returnPressed.connect(self._send_command_from_input)
        self.dataref_input.returnPressed.connect(self._add_mapping_from_inputs)
    
    def _disconnect(self):
        self.arduino_manager.disconnect(self.port)
    
    def _add_mapping_from_inputs(self):
        dataref = self.dataref_input.text().strip()
        key = self.key_input.text().strip().upper()
        
        if dataref and key:
            self._add_mapping(dataref, key)
            self.dataref_input.clear()
            self.key_input.clear()
    
    def _add_mapping(self, dataref: str, key: str):
        # Use the traditional subscription method (still supported)
        self.arduino_manager.subscribe_dataref(self.port, dataref, key)

        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)

        self.mapping_table.setItem(row, 0, QTableWidgetItem(dataref))
        self.mapping_table.setItem(row, 1, QTableWidgetItem(key))

        remove_btn = QPushButton("✕")
        remove_btn.setMaximumWidth(25)
        remove_btn.clicked.connect(lambda: self._remove_mapping(dataref))
        self.mapping_table.setCellWidget(row, 2, remove_btn)

        self._add_monitor_message(f"Mapped: {dataref} → {key}")
    
    def _remove_mapping(self, dataref: str):
        self.arduino_manager.unsubscribe_dataref(self.port, dataref)
        
        for row in range(self.mapping_table.rowCount()):
            item = self.mapping_table.item(row, 0)
            if item and item.text() == dataref:
                self.mapping_table.removeRow(row)
                break
        
        self._add_monitor_message(f"Removed: {dataref}")
    
    def _send_command_from_input(self):
        cmd = self.cmd_input.text().strip()
        if cmd:
            self._send_command(cmd)
            self.cmd_input.clear()
    
    def _send_command(self, command: str):
        self.arduino_manager.send_command(self.port, command)
        self._add_monitor_message(f"> {command}", is_sent=True)
    
    def _add_monitor_message(self, message: str, is_sent: bool = False):
        if is_sent:
            self.monitor_text.append(f'<span style="color: blue;">{message}</span>')
        else:
            self.monitor_text.append(message)
        
        scrollbar = self.monitor_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_device(self, device: ArduinoDevice):
        """Update display with device info."""
        state_styles = {
            DeviceState.DISCONNECTED: ("Disconnected", "color: gray;"),
            DeviceState.CONNECTING: ("Connecting...", "color: orange;"),
            DeviceState.HANDSHAKE: ("Handshake...", "color: orange;"),
            DeviceState.READY: ("Ready", "color: green; font-weight: bold;"),
            DeviceState.ACTIVE: ("Active", "color: green; font-weight: bold;"),
            DeviceState.ERROR: ("Error", "color: red; font-weight: bold;"),
        }
        
        text, style = state_styles.get(device.state, ("Unknown", ""))
        self.status_label.setText(text)
        self.status_label.setStyleSheet(style)
        
        if device.firmware_version or device.board_type or device.device_name:
            info = f"{device.device_name} | {device.board_type} v{device.firmware_version}"
            self.info_label.setText(info)
            self.info_label.setStyleSheet("color: #666; font-size: 11px;")
    
    def on_message(self, message: str):
        """Handle incoming message from device."""
        self._add_monitor_message(f"[rx] {message}")


class ArduinoPanel(QWidget):
    """Panel for managing multiple Arduino devices."""
    
    # Signals for thread-safe updates
    device_update_signal = pyqtSignal(dict)
    message_received_signal = pyqtSignal(str, str)
    
    def __init__(self, arduino_manager: ArduinoManager, dataref_manager) -> None:
        super().__init__()
        
        self.arduino_manager = arduino_manager
        self.dataref_manager = dataref_manager
        
        self.dataref_list = dataref_manager.get_all_dataref_names()
        self._device_widgets: Dict[str, DeviceWidget] = {}
        
        self._setup_ui()
        self._connect_signals()
        
        # Connect signals for thread-safe updates
        self.device_update_signal.connect(self._handle_device_update)
        self.message_received_signal.connect(self._handle_message)
        
        # Set manager callbacks to emit signals
        self.arduino_manager.on_device_update = lambda devices: self.device_update_signal.emit(devices)
        self.arduino_manager.on_message_received = lambda port, msg: self.message_received_signal.emit(port, msg)
        
        # Refresh timer
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_ports)
        self._refresh_timer.start(5000)
        
        self._refresh_ports()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Connection panel
        conn_group = QGroupBox("Connect New Device")
        conn_layout = QHBoxLayout(conn_group)
        
        conn_layout.addWidget(QLabel("Port:"))
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(250)
        conn_layout.addWidget(self.port_combo)
        
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setMaximumWidth(30)
        self.refresh_btn.setToolTip("Refresh port list")
        conn_layout.addWidget(self.refresh_btn)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumWidth(100)
        conn_layout.addWidget(self.connect_btn)
        
        conn_layout.addStretch()
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        conn_layout.addWidget(self.status_label)
        
        layout.addWidget(conn_group)
        
        # Scroll area for devices
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.devices_container = QWidget()
        self.devices_layout = QVBoxLayout(self.devices_container)
        self.devices_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.devices_layout.setSpacing(10)
        
        self.no_devices_label = QLabel(
            "No devices connected.\n\n"
            "Select a port above and click 'Connect' to add a device."
        )
        self.no_devices_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_devices_label.setStyleSheet("color: gray; padding: 40px;")
        self.devices_layout.addWidget(self.no_devices_label)
        
        scroll.setWidget(self.devices_container)
        layout.addWidget(scroll)
    
    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self._refresh_ports)
        self.connect_btn.clicked.connect(self._connect_device)
    
    def _refresh_ports(self):
        """Refresh available serial ports with detailed info."""
        current_port = self.port_combo.currentData()
        self.port_combo.clear()

        ports = self.arduino_manager.list_ports()
        connected_ports = set(self._device_widgets.keys())

        available_count = 0
        for info in ports:
            port = info['port']
            # Skip already connected
            if port in connected_ports:
                continue

            # Format: COM3 - Arduino Leonardo (2341:8036)
            desc = info.get('description', 'Serial Device')
            vid = info.get('vid')
            pid = info.get('pid')

            label = f"{port} - {desc}"
            if vid and pid:
                # Convert VID/PID to hex if they are integers, handle strings safely
                try:
                    if isinstance(vid, int): vid_str = f"{vid:04X}"
                    else: vid_str = str(vid)

                    if isinstance(pid, int): pid_str = f"{pid:04X}"
                    else: pid_str = str(pid)

                    label += f" ({vid_str}:{pid_str})"
                except:
                    pass

            if info.get('is_esp32'):
                label = f"🔥 {label}"  # Highlight ESP32s

            self.port_combo.addItem(label, port)
            available_count += 1

        # Restore selection
        if current_port:
            idx = self.port_combo.findData(current_port)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)

        # Update status
        device_count = len(self._device_widgets)
        if device_count > 0:
            self.status_label.setText(f"{device_count} device(s) connected")
        else:
            self.status_label.setText("")
    
    def _connect_device(self):
        port = self.port_combo.currentData()
        if not port:
            return

        if port in self._device_widgets:
            QMessageBox.warning(self, "Already Connected", f"Already connected to {port}")
            return

        self.arduino_manager.connect(port)
        self._add_device_widget(port)
        self._refresh_ports()

    def auto_connect(self, ports: List[str]):
        """Attempt to auto-connect to a list of ports."""
        available = [p['port'] for p in self.arduino_manager.list_ports()]

        for port in ports:
            if port in available and port not in self._device_widgets:
                if self.arduino_manager.connect(port):
                    self._add_device_widget(port)
                    log.info("Auto-connected to %s", port)

        self._refresh_ports()
    
    def _add_device_widget(self, port: str):
        if port in self._device_widgets:
            return
        
        self.no_devices_label.hide()
        
        widget = DeviceWidget(port, self.arduino_manager, self.dataref_list)
        self._device_widgets[port] = widget
        self.devices_layout.addWidget(widget)
    
    def _remove_device_widget(self, port: str):
        if port in self._device_widgets:
            widget = self._device_widgets.pop(port)
            self.devices_layout.removeWidget(widget)
            widget.deleteLater()
        
        if not self._device_widgets:
            self.no_devices_label.show()
        
        self._refresh_ports()
    
    def _handle_device_update(self, devices: Dict[str, ArduinoDevice]):
        """Handle device updates (called via signal, thread-safe)."""
        current_ports = set(devices.keys())
        widget_ports = set(self._device_widgets.keys())
        
        # Add new
        for port in current_ports - widget_ports:
            self._add_device_widget(port)
        
        # Remove disconnected
        for port in widget_ports - current_ports:
            self._remove_device_widget(port)
        
        # Update existing
        for port, device in devices.items():
            if port in self._device_widgets:
                self._device_widgets[port].update_device(device)
                
                if device.state == DeviceState.DISCONNECTED:
                    self._remove_device_widget(port)
    
    def _handle_message(self, port: str, message: str):
        """Handle incoming message (called via signal, thread-safe)."""
        if port in self._device_widgets:
            self._device_widgets[port].on_message(message)

    def refresh_from_manager(self):
        """Refresh the dataref list and autocomplete."""
        self.dataref_list = self.dataref_manager.get_all_dataref_names()
        # Update all device widgets
        for widget in self._device_widgets.values():
            if hasattr(widget, 'dataref_input'):
                completer = QCompleter(self.dataref_list)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
                completer.setMaxVisibleItems(10)
                widget.dataref_input.setCompleter(completer)