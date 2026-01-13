from __future__ import annotations
import logging
from typing import Dict, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSlot

from core.hid.hid_device import HIDDevice
from core.hid.hid_manager import HIDManager

log = logging.getLogger(__name__)


class HIDPanel(QWidget):
    """Panel for HID device management and mapping."""
    
    def __init__(self, hid_manager: HIDManager, dataref_manager) -> None:
        super().__init__()
        
        self.hid_manager = hid_manager
        self.dataref_manager = dataref_manager
        
        self._selected_device: Optional[str] = None
        
        self._setup_ui()
        self._connect_signals()
        
        # Subscribe to HID updates
        self.hid_manager.on_device_update = self._on_devices_updated
    
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        
        # Left: Device list
        left_group = QGroupBox("HID Devices")
        left_layout = QVBoxLayout(left_group)
        
        self.device_list = QListWidget()
        self.device_list.setMinimumWidth(200)
        left_layout.addWidget(self.device_list)
        
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        btn_layout.addWidget(self.refresh_btn)
        left_layout.addLayout(btn_layout)
        
        # Right: Device info and mappings
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Device info
        info_group = QGroupBox("Device Information")
        info_layout = QFormLayout(info_group)
        
        self.name_label = QLabel("-")
        self.vid_label = QLabel("-")
        self.pid_label = QLabel("-")
        self.status_label = QLabel("-")
        
        info_layout.addRow("Name:", self.name_label)
        info_layout.addRow("Vendor ID:", self.vid_label)
        info_layout.addRow("Product ID:", self.pid_label)
        info_layout.addRow("Status:", self.status_label)
        
        right_layout.addWidget(info_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)
        
        self.num_axes = QSpinBox()
        self.num_axes.setRange(0, 16)
        self.num_axes.setValue(8)
        
        self.num_buttons = QSpinBox()
        self.num_buttons.setRange(0, 128)
        self.num_buttons.setValue(32)
        
        config_layout.addRow("Axes:", self.num_axes)
        config_layout.addRow("Buttons:", self.num_buttons)
        
        right_layout.addWidget(config_group)
        
        # Axis values (live display)
        axis_group = QGroupBox("Axis Values")
        axis_layout = QVBoxLayout(axis_group)
        
        self.axis_table = QTableWidget(8, 2)
        self.axis_table.setHorizontalHeaderLabels(["Axis", "Value"])
        self.axis_table.horizontalHeader().setStretchLastSection(True)
        self.axis_table.setMaximumHeight(200)
        
        for i in range(8):
            self.axis_table.setItem(i, 0, QTableWidgetItem(f"Axis {i}"))
            self.axis_table.setItem(i, 1, QTableWidgetItem("0.000"))
        
        axis_layout.addWidget(self.axis_table)
        right_layout.addWidget(axis_group)
        
        right_layout.addStretch()
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_group)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 450])
        
        layout.addWidget(splitter)
    
    def _connect_signals(self) -> None:
        self.device_list.currentItemChanged.connect(self._on_device_selected)
        self.refresh_btn.clicked.connect(self._refresh_devices)
    
    def _refresh_devices(self) -> None:
        """Manually refresh device list."""
        devices = self.hid_manager.devices_snapshot()
        self._update_device_list(devices)
    
    def _on_devices_updated(self, devices: Dict[str, HIDDevice]) -> None:
        """Called when HID manager reports device changes."""
        # Must use Qt signal/slot for thread safety
        # For now, direct call (assumes same thread or use QMetaObject.invokeMethod)
        self._update_device_list(devices)
    
    def _update_device_list(self, devices: Dict[str, HIDDevice]) -> None:
        """Update the device list widget."""
        current_ids = set(devices.keys())
        existing_ids = set()
        
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            if item:
                existing_ids.add(item.data(Qt.ItemDataRole.UserRole))
        
        # Add new devices
        for dev_id in current_ids - existing_ids:
            device = devices[dev_id]
            item = QListWidgetItem(device.name)
            item.setData(Qt.ItemDataRole.UserRole, dev_id)
            self.device_list.addItem(item)
        
        # Remove disconnected devices
        for i in range(self.device_list.count() - 1, -1, -1):
            item = self.device_list.item(i)
            if item:
                dev_id = item.data(Qt.ItemDataRole.UserRole)
                if dev_id not in current_ids:
                    self.device_list.takeItem(i)
    
    def _on_device_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle device selection."""
        if not current:
            self._clear_device_info()
            return
        
        device_id = current.data(Qt.ItemDataRole.UserRole)
        device = self.hid_manager.get_device(device_id)
        
        if not device:
            self._clear_device_info()
            return
        
        self._selected_device = device_id
        self._display_device(device)
    
    def _display_device(self, device: HIDDevice) -> None:
        """Display device information."""
        self.name_label.setText(device.name)
        self.vid_label.setText(f"0x{device.vendor_id:04X}")
        self.pid_label.setText(f"0x{device.product_id:04X}")
        self.status_label.setText("Connected" if device.connected else "Disconnected")
        
        self.num_axes.setValue(device.num_axes)
        self.num_buttons.setValue(device.num_buttons)
        
        # Update axis table
        for i, value in enumerate(device.axes[:8]):
            item = self.axis_table.item(i, 1)
            if item:
                item.setText(f"{value:.3f}")
    
    def _clear_device_info(self) -> None:
        """Clear device info display."""
        self._selected_device = None
        self.name_label.setText("-")
        self.vid_label.setText("-")
        self.pid_label.setText("-")
        self.status_label.setText("-")