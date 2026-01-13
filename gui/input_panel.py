from __future__ import annotations
import logging
import asyncio
import json
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QScrollArea,
    QGridLayout, QPushButton, QFrame, QProgressBar,
    QGroupBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QDialog, QLineEdit, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QBrush, QPen

from core.hid.hid_device import HIDDevice
from core.hid.hid_manager import HIDManager
from core.input_mapper import InputMapper, InputMapping, InputAction
from .input_mapping_dialog import InputMappingDialog
from .input_mapping_dialog import InputMappingDialog
from .hat_switch_widget import HatSwitchWidget


log = logging.getLogger(__name__)




class InputVisualizer(QWidget):
    """
    Visualizes the EXACT state of a controller.
    """

    # Signal: DeviceID, KeyName, Value
    input_detected = pyqtSignal(str, str, float)

    def __init__(self, device: HIDDevice, input_mapper: InputMapper, dataref_manager=None, variable_store=None, parent=None):
        super().__init__(parent)
        self.device = device
        self.input_mapper = input_mapper
        self.dataref_manager = dataref_manager
        self.variable_store = variable_store  # NEW: Variable store for all variable types

        self._axis_bars: List[QProgressBar] = []
        self._btn_widgets: List[QPushButton] = []
        self._hat_widgets: List[HatSwitchWidget] = []
        self._last_axis_values: List[float] = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Header Info ---
        info_group = QGroupBox(f"Device: {self.device.name}")
        info_layout = QVBoxLayout(info_group)

        id_label = QLabel(f"VID: {self.device.vendor_id:04X}  PID: {self.device.product_id:04X}  |  ID: {self.device.device_id}")
        id_label.setStyleSheet("color: gray;")
        info_layout.addWidget(id_label)
        layout.addWidget(info_group)

        # --- Axes Section ---
        if self.device.num_axes > 0:
            axes_group = QGroupBox(f"Axes ({self.device.num_axes} detected)")
            axes_grid = QGridLayout(axes_group)

            for i in range(self.device.num_axes):
                # Label
                axes_grid.addWidget(QLabel(f"Axis {i}"), i, 0)

                # Bar
                bar = QProgressBar()
                bar.setRange(0, 255)
                bar.setValue(128)  # Center
                bar.setTextVisible(False)
                bar.setFixedHeight(15)
                axes_grid.addWidget(bar, i, 1)
                self._axis_bars.append(bar)

                # Value label
                val_label = QLabel("0.00")
                val_label.setMinimumWidth(50)
                val_label.setStyleSheet("font-family: monospace;")
                axes_grid.addWidget(val_label, i, 2)

                # Config Button
                cfg_btn = QPushButton("⚙️")
                cfg_btn.setFixedSize(30, 20)
                cfg_btn.setToolTip(f"Configure Axis {i}")
                cfg_btn.clicked.connect(lambda c, idx=i: self._configure_input(f"AXIS_{idx}"))
                axes_grid.addWidget(cfg_btn, i, 3)

            layout.addWidget(axes_group)

        # --- Hats Section ---
        if self.device.num_hats > 0:
            hats_group = QGroupBox(f"Hat Switches ({self.device.num_hats} detected)")
            hats_layout = QHBoxLayout(hats_group)

            for i in range(self.device.num_hats):
                v_box = QVBoxLayout()

                # Visual Widget - Use the new 8-way HatSwitchWidget
                hat_viz = HatSwitchWidget()
                v_box.addWidget(hat_viz, alignment=Qt.AlignmentFlag.AlignCenter)
                self._hat_widgets.append(hat_viz)

                # Config Buttons (8 directions)
                grid = QGridLayout()
                grid.setSpacing(2)

                # Diagonal buttons layout:
                #     U
                #   L + R
                #     D
                # With diagonals in corners:
                # LU U RU
                # L  +  R
                # LD D RD

                # Up
                btn_u = QPushButton("▲")
                btn_u.setFixedSize(24, 24)
                btn_u.clicked.connect(lambda c, h=i: self._configure_input(f"HAT_{h}_UP"))
                grid.addWidget(btn_u, 0, 1)

                # Up-Left
                btn_lu = QPushButton("◤")
                btn_lu.setFixedSize(24, 24)
                btn_lu.clicked.connect(lambda c, h=i: self._configure_input(f"HAT_{h}_UP_LEFT"))
                grid.addWidget(btn_lu, 0, 0)

                # Up-Right
                btn_ru = QPushButton("◥")
                btn_ru.setFixedSize(24, 24)
                btn_ru.clicked.connect(lambda c, h=i: self._configure_input(f"HAT_{h}_UP_RIGHT"))
                grid.addWidget(btn_ru, 0, 2)

                # Left
                btn_l = QPushButton("◀")
                btn_l.setFixedSize(24, 24)
                btn_l.clicked.connect(lambda c, h=i: self._configure_input(f"HAT_{h}_LEFT"))
                grid.addWidget(btn_l, 1, 0)

                # Center (placeholder)
                center_label = QLabel("+")
                center_label.setFixedSize(24, 24)
                center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                grid.addWidget(center_label, 1, 1)

                # Right
                btn_r = QPushButton("▶")
                btn_r.setFixedSize(24, 24)
                btn_r.clicked.connect(lambda c, h=i: self._configure_input(f"HAT_{h}_RIGHT"))
                grid.addWidget(btn_r, 1, 2)

                # Down-Left
                btn_ld = QPushButton("◣")
                btn_ld.setFixedSize(24, 24)
                btn_ld.clicked.connect(lambda c, h=i: self._configure_input(f"HAT_{h}_DOWN_LEFT"))
                grid.addWidget(btn_ld, 2, 0)

                # Down
                btn_d = QPushButton("▼")
                btn_d.setFixedSize(24, 24)
                btn_d.clicked.connect(lambda c, h=i: self._configure_input(f"HAT_{h}_DOWN"))
                grid.addWidget(btn_d, 2, 1)

                # Down-Right
                btn_rd = QPushButton("◢")
                btn_rd.setFixedSize(24, 24)
                btn_rd.clicked.connect(lambda c, h=i: self._configure_input(f"HAT_{h}_DOWN_RIGHT"))
                grid.addWidget(btn_rd, 2, 2)

                v_box.addLayout(grid)
                hats_layout.addLayout(v_box)

            layout.addWidget(hats_group)

        # --- Buttons Section ---
        if self.device.num_buttons > 0:
            btn_group = QGroupBox(f"Buttons ({self.device.num_buttons} detected)")
            btn_layout = QVBoxLayout(btn_group)

            # Scroll area for buttons
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setMaximumHeight(250)

            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(5)

            cols = 8
            for i in range(self.device.num_buttons):
                btn = QPushButton(f"{i}")
                btn.setCheckable(True)
                btn.setFixedSize(35, 35)
                btn.clicked.connect(lambda c, idx=i: self._configure_input(f"BTN_{idx}"))

                grid.addWidget(btn, i // cols, i % cols)
                self._btn_widgets.append(btn)

            scroll.setWidget(grid_widget)
            btn_layout.addWidget(scroll)
            layout.addWidget(btn_group)

        layout.addStretch()

    def set_offline_mode(self, offline: bool, device_name: str = ""):
        """Set visualizer to offline mode."""
        # Clear existing content
        # (This is handled by the parent when swapping modes)
        pass

    def update_state(self, fresh_device: HIDDevice):
        """Called periodically to update UI from device state."""

        # Initialize last values if needed
        if len(self._last_axis_values) != len(fresh_device.axes):
            self._last_axis_values = [0.0] * len(fresh_device.axes)

        # Update Axes
        for i, val in enumerate(fresh_device.axes):
            if i < len(self._axis_bars):
                # Map -1.0..1.0 to 0..255
                int_val = int((val + 1.0) * 127.5)
                self._axis_bars[i].setValue(int_val)

                # Update value label if it exists
                parent_layout = self._axis_bars[i].parent()
                if parent_layout:
                    grid = parent_layout.layout()
                    if grid and i < grid.rowCount():
                        val_item = grid.itemAtPosition(i, 2)
                        if val_item and val_item.widget():
                            val_item.widget().setText(f"{val:.2f}")

                # Emit signal for significant axis changes
                if i < len(self._last_axis_values):
                    old_val = self._last_axis_values[i]
                    if abs(val - old_val) > 0.05:
                        key = f"AXIS_{i}"
                        self.input_detected.emit(self.device.device_id, key, val)
                        self._last_axis_values[i] = val

        # Update Hats
        for i, hat_val in enumerate(fresh_device.hats):
            if i < len(self._hat_widgets):
                # hat_val is typically a tuple like (x, y) where x,y are -1, 0, or 1
                # Convert to normalized x, y values for the 8-way widget
                if isinstance(hat_val, tuple) and len(hat_val) == 2:
                    x, y = hat_val
                    self._hat_widgets[i].set_direction(float(x), float(y))
                else:
                    # If hat_val is an integer state (like POV hat), convert to x,y
                    # Standard hat values: -1=center, 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
                    if isinstance(hat_val, int):
                        if hat_val == -1:  # Center
                            self._hat_widgets[i].set_direction(0.0, 0.0)
                        elif hat_val == 0:  # North
                            self._hat_widgets[i].set_direction(0.0, 1.0)
                        elif hat_val == 1:  # NE
                            self._hat_widgets[i].set_direction(0.707, 0.707)
                        elif hat_val == 2:  # East
                            self._hat_widgets[i].set_direction(1.0, 0.0)
                        elif hat_val == 3:  # SE
                            self._hat_widgets[i].set_direction(0.707, -0.707)
                        elif hat_val == 4:  # South
                            self._hat_widgets[i].set_direction(0.0, -1.0)
                        elif hat_val == 5:  # SW
                            self._hat_widgets[i].set_direction(-0.707, -0.707)
                        elif hat_val == 6:  # West
                            self._hat_widgets[i].set_direction(-1.0, 0.0)
                        elif hat_val == 7:  # NW
                            self._hat_widgets[i].set_direction(-0.707, 0.707)
                        else:  # Unknown state
                            self._hat_widgets[i].set_direction(0.0, 0.0)
                    else:
                        self._hat_widgets[i].set_direction(0.0, 0.0)

        # Update Buttons
        for i, pressed in enumerate(fresh_device.buttons):
            if i < len(self._btn_widgets):
                was_checked = self._btn_widgets[i].isChecked()
                if was_checked != pressed:
                    self._btn_widgets[i].setChecked(pressed)

                    if pressed:
                        self._btn_widgets[i].setStyleSheet(
                            "background-color: #00FF00; font-weight: bold; color: black;"
                        )
                    else:
                        self._btn_widgets[i].setStyleSheet("")

                    # Emit signal for button changes
                    key = f"BTN_{i}"
                    val = 1.0 if pressed else 0.0
                    self.input_detected.emit(self.device.device_id, key, val)

    def _configure_input(self, input_key: str):
        """Open the mapping dialog for a specific input."""
        # Determine default action based on key type
        default_action = InputAction.COMMAND
        if input_key.startswith("AXIS"):
            default_action = InputAction.AXIS
        elif input_key.startswith("ENC"):
            default_action = InputAction.DATAREF_INC

        # Create a default mapping template
        mapping = InputMapping(
            input_key=input_key,
            device_port=self.device.device_id,
            action=default_action,
            target="",
            description=f"{self.device.name} - {input_key}"
        )

        # Check if mapping already exists
        existing = self.input_mapper.get_mappings_for_input(input_key, self.device.device_id)
        if existing:
            mapping = existing[0]

        # Open dialog with fixed_input=True (input already selected)
        dialog = InputMappingDialog(
            parent=self,
            mapping=mapping,
            dataref_manager=self.dataref_manager,
            variable_store=self.variable_store,
            fixed_input=True
        )

        # --- NEW: Pass HID Manager for Calibration Wizard ---
        # Access HID manager from the parent context (InputPanel)
        parent_widget = self.parent()
        if hasattr(parent_widget, 'hid_manager'):
            dialog._hid_manager = parent_widget.hid_manager
        elif hasattr(parent_widget, 'input_panel') and hasattr(parent_widget.input_panel, 'hid_manager'):
            dialog._hid_manager = parent_widget.input_panel.hid_manager
        elif hasattr(parent_widget, 'main_window') and hasattr(parent_widget.main_window, 'hid_manager'):
            dialog._hid_manager = parent_widget.main_window.hid_manager
        else:
            # Try to find HID manager in the widget hierarchy
            current_parent = parent_widget
            while current_parent:
                if hasattr(current_parent, 'hid_manager'):
                    dialog._hid_manager = current_parent.hid_manager
                    break
                elif hasattr(current_parent, 'input_panel') and hasattr(current_parent.input_panel, 'hid_manager'):
                    dialog._hid_manager = current_parent.input_panel.hid_manager
                    break
                elif hasattr(current_parent, 'main_window') and hasattr(current_parent.main_window, 'hid_manager'):
                    dialog._hid_manager = current_parent.main_window.hid_manager
                    break
                current_parent = current_parent.parent()
        # ---------------------------------------------------

        if dialog.exec():
            new_mapping = dialog.get_mapping()

            # Remove old mapping for this input on this device
            self.input_mapper.remove_mappings_for_input(input_key, self.device.device_id)

            # Add new mapping
            self.input_mapper.add_mapping(new_mapping)
            self.input_mapper.save_mappings()

            log.info("Saved mapping: %s -> %s (%s)",
                     input_key, new_mapping.target, new_mapping.action.name)


class InputPanel(QWidget):
    """
    Main Input Configuration Tab.
    Left: List of devices.
    Right: Visualizer for selected device + Mappings list.
    """

    def __init__(self, hid_manager: HIDManager, input_mapper: InputMapper, profile_manager=None, variable_store=None):
        super().__init__()
        self.hid_manager = hid_manager
        self.input_mapper = input_mapper
        self.profile_manager = profile_manager
        self.variable_store = variable_store  # NEW: Variable store for all variable types

        # Get dataref_manager from input_mapper
        self.dataref_manager = input_mapper.dataref_manager

        # --- NEW: Highlight Logic ---
        self._highlight_timer = QTimer()
        self._highlight_timer.setSingleShot(True)
        self._highlight_timer.timeout.connect(self._clear_highlights)
        # ------------------------------

        self._current_visualizer: Optional[InputVisualizer] = None
        self._selected_device_id: Optional[str] = None
        self._learning_dialog: Optional[InputMappingDialog] = None

        self._setup_ui()
        self._setup_connections()  # NEW: Setup connections for highlighting

        # Timer for Device List Refresh (1Hz)
        self._list_timer = QTimer()
        self._list_timer.timeout.connect(self._refresh_device_list)
        self._list_timer.start(1000)

        # Timer for Visualizer Update (30Hz)
        self._viz_timer = QTimer()
        self._viz_timer.timeout.connect(self._update_visualizer)
        self._viz_timer.start(33)

        # Timer for Mappings Table Refresh (2Hz)
        self._mappings_timer = QTimer()
        self._mappings_timer.timeout.connect(self._refresh_mappings_table)
        self._mappings_timer.start(500)

        # Initial populate
        self._refresh_device_list()
        self._refresh_mappings_table()

    def _setup_connections(self):
        """Setup additional connections for highlighting functionality."""
        # --- NEW: Listen for mapping triggers ---
        # We want to know exactly which mapping fired to highlight the table row
        if hasattr(self.input_mapper, 'on_mapping_triggered'):
            # Connect to our highlight method
            self.input_mapper.on_mapping_triggered = self._on_mapping_triggered
        # --------------------------------

    def _on_mapping_triggered(self, mapping, value):
        """
        Called when a mapping executes.
        Finds the corresponding row in the table and flashes it.
        """
        # 1. Identify the row.
        # Since we allow sorting, row index != list index.
        # We scan the table items to find the match.

        found_row = -1
        for row in range(self.mappings_table.rowCount()):
            item = self.mappings_table.item(row, 0)  # Input column
            if item and mapping.input_key in item.text() and mapping.device_port in item.text():
                found_row = row
                break

        if found_row != -1:
            self._flash_row(found_row)

    def _flash_row(self, row_index: int):
        """Flashes a row Green for 250ms."""

        # Define highlight color (Soft Green)
        highlight_color = QColor("#d4edda")

        # Apply color to all columns in row
        for col in range(self.mappings_table.columnCount()):
            item = self.mappings_table.item(row_index, col)
            if item:
                item.setBackground(highlight_color)

        # Start timer to clear it
        self._highlight_timer.start(250)  # 250ms flash

    def _clear_highlights(self):
        """Restores all rows to default background."""
        for row in range(self.mappings_table.rowCount()):
            for col in range(self.mappings_table.columnCount()):
                item = self.mappings_table.item(row, col)
                if item:
                    # Restore default white (or transparent)
                    item.setBackground(QColor(255, 255, 255, 0))  # Transparent

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === Left Panel: Device List ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("<b>🎮 Detected Controllers</b>"))

        self.device_list = QListWidget()
        self.device_list.setAlternatingRowColors(True)
        self.device_list.itemClicked.connect(self._on_device_clicked)
        self.device_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.device_list.customContextMenuRequested.connect(self._show_device_context_menu)
        left_layout.addWidget(self.device_list)

        info_lbl = QLabel("Select a device to view inputs & configure mappings.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: gray; font-size: 11px;")
        left_layout.addWidget(info_lbl)

        splitter.addWidget(left_widget)

        # === Middle Panel: Visualizer Area ===
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)

        middle_layout.addWidget(QLabel("<b>🕹️ Input Test & Config</b>"))

        self.viz_container = QFrame()
        self.viz_container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.viz_layout = QVBoxLayout(self.viz_container)
        self.viz_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.placeholder = QLabel("No Device Selected\n\nSelect a controller from the list to view and configure its inputs.")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 14px;")
        self.viz_layout.addWidget(self.placeholder)

        middle_layout.addWidget(self.viz_container)

        splitter.addWidget(middle_widget)

        # === Right Panel: Mappings List ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>📋 Active Mappings</b>"))
        header_layout.addStretch()

        self.add_mapping_btn = QPushButton("➕ Add Mapping")
        self.add_mapping_btn.clicked.connect(self._add_new_mapping)
        header_layout.addWidget(self.add_mapping_btn)

        right_layout.addLayout(header_layout)

        # Mappings table
        self.mappings_table = QTableWidget(0, 4)
        self.mappings_table.setHorizontalHeaderLabels(["Input", "Action", "Target", ""])

        header = self.mappings_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.mappings_table.setAlternatingRowColors(True)
        self.mappings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.mappings_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.mappings_table.customContextMenuRequested.connect(self._show_mapping_context_menu)
        self.mappings_table.doubleClicked.connect(self._edit_selected_mapping)

        right_layout.addWidget(self.mappings_table)

        # Stats
        self.stats_label = QLabel("0 mappings configured")
        self.stats_label.setStyleSheet("color: gray; font-size: 11px;")
        right_layout.addWidget(self.stats_label)

        splitter.addWidget(right_widget)

        # Set splitter ratio
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)

        main_layout.addWidget(splitter)

    def _refresh_device_list(self):
        """Update the list of connected devices."""
        devices = self.hid_manager.devices_snapshot()

        existing_ids = set()
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            did = item.data(Qt.ItemDataRole.UserRole)
            existing_ids.add(did)

            dev = devices.get(did)
            if dev:
                status = "🟢" if dev.connected else "🔴"
                alias = None
                if self.profile_manager:
                    alias = self.profile_manager.get_device_alias(did)
                display_name = alias if alias else dev.name
                item.setText(f"{status} {display_name}")

        # Add new devices
        for did, dev in devices.items():
            if did not in existing_ids and dev.connected:
                alias = None
                if self.profile_manager:
                    alias = self.profile_manager.get_device_alias(did)
                display_name = alias if alias else dev.name
                item = QListWidgetItem(f"🟢 {display_name}")
                item.setData(Qt.ItemDataRole.UserRole, did)
                item.setToolTip(f"ID: {did}\nAxes: {dev.num_axes}\nButtons: {dev.num_buttons}\nHats: {dev.num_hats}")
                self.device_list.addItem(item)
                if self.profile_manager:
                    self.profile_manager.record_device_name(did, dev.name)

        # Add "Offline" devices (Devices that have mappings or are known but not connected)
        if self.profile_manager:
            known_ids = set(self.profile_manager._known_devices.keys())
            # Also check existing mappings
            for m in self.input_mapper.get_mappings():
                if m.device_port and m.device_port != "*":
                    known_ids.add(m.device_port)
            
            for did in known_ids:
                if did not in [item.data(Qt.ItemDataRole.UserRole) for item in self.device_list.findItems("*", Qt.MatchFlag.MatchWildcard)]:
                    # Known but not connected
                    name = self.profile_manager.get_known_device_name(did)
                    alias = self.profile_manager.get_device_alias(did)
                    display_name = alias if alias else name
                    item = QListWidgetItem(f"🔴 (Disconnected) {display_name}")
                    item.setData(Qt.ItemDataRole.UserRole, did)
                    item.setForeground(QColor("gray"))
                    self.device_list.addItem(item)

    def _on_device_clicked(self, item: QListWidgetItem):
        """User clicked a device in the list."""
        device_id = item.data(Qt.ItemDataRole.UserRole)

        if device_id == self._selected_device_id:
            return

        self._selected_device_id = device_id
        device = self.hid_manager.get_device(device_id)

        if not device or not device.connected:
            # Show Offline Placeholder
            self._load_offline_placeholder(device_id)
            return

        self._load_visualizer(device)

    def _load_visualizer(self, device: HIDDevice):
        """Clear old visualizer and load new one."""
        if self._current_visualizer:
            self.viz_layout.removeWidget(self._current_visualizer)
            self._current_visualizer.deleteLater()
            self._current_visualizer = None

        self.placeholder.hide()

        self._current_visualizer = InputVisualizer(
            device,
            self.input_mapper,
            self.dataref_manager,
            self.variable_store  # Pass variable store
        )
        self._current_visualizer.input_detected.connect(self._on_input_detected)

        self.viz_layout.addWidget(self._current_visualizer)

        log.info("Loaded visualizer for %s", device.name)

    def _load_offline_placeholder(self, device_id: str):
        """Show placeholder for disconnected device."""
        if self._current_visualizer:
            self.viz_layout.removeWidget(self._current_visualizer)
            self._current_visualizer.deleteLater()
            self._current_visualizer = None

        self.placeholder.show()
        name = self.profile_manager.get_known_device_name(device_id) if self.profile_manager else device_id
        self.placeholder.setText(
            f"Device Offline: {name}\n\n"
            f"Hardware is not connected, but you can still view and edit\n"
            f"its mappings in the 'Active Mappings' table on the right."
        )

    def _on_input_detected(self, device_id: str, key: str, value: float):
        """Handle input detection from HID devices."""
        # Forward to input mapper for processing
        try:
            asyncio.create_task(self.input_mapper.process_input(device_id, key, value))
        except Exception as e:
            log.error("Error processing HID input: %s", e)

        # Pass to learning dialog if active
        if value != 0 and self._learning_dialog:
            self._learning_dialog.on_input_detected(key, device_id)

    def _update_visualizer(self):
        """Fast timer loop to update visualizer."""
        if not self._current_visualizer or not self._selected_device_id:
            return

        device = self.hid_manager.get_device(self._selected_device_id)
        if device and device.connected:
            self._current_visualizer.update_state(device)

    def _refresh_mappings_table(self):
        """Refresh the mappings table."""
        mappings = self.input_mapper.get_mappings()

        # 2. Sort Mappings
        # Priority: Device ID -> Input Type (BTN, AXIS, HAT) -> Index
        def sort_key(m):
            dev_id = m.device_port or "ZZZ"

            # Extract Type and Index from Input Key
            # e.g., "BTN_0" -> ("BTN", 0)
            # "AXIS_2" -> ("AXIS", 2)
            # "HAT_0" -> ("HAT", 0)

            parts = m.input_key.split('_')
            type_str = parts[0]
            idx_str = parts[1] if len(parts) > 1 else "0"

            try:
                idx = int(idx_str)
            except ValueError:
                idx = 999

            # Type Priority: BTN (0) < AXIS (1) < HAT (2)
            type_val = 0
            if type_str == "AXIS": type_val = 1
            elif type_str == "HAT": type_val = 2

            return (dev_id, type_val, idx)

        sorted_mappings = sorted(mappings, key=sort_key)

        # Only update if count changed (avoid flicker)
        if self.mappings_table.rowCount() != len(sorted_mappings):
            self.mappings_table.setRowCount(len(sorted_mappings))

        for row, mapping in enumerate(sorted_mappings):
            # Input
            input_item = QTableWidgetItem(f"{mapping.device_port}/{mapping.input_key}")
            input_item.setToolTip(mapping.description or "No description")
            input_item.setFlags(input_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mappings_table.setItem(row, 0, input_item)

            # Action
            action_names = {
                InputAction.COMMAND: "🖱️ Command",
                InputAction.DATAREF_SET: "🔘 Set",
                InputAction.DATAREF_TOGGLE: "🔄 Toggle",
                InputAction.DATAREF_INC: "⬆️ Inc",
                InputAction.DATAREF_DEC: "⬇️ Dec",
                InputAction.AXIS: "📊 Axis",
                InputAction.SEQUENCE: "📜 Sequence",
            }
            action_item = QTableWidgetItem(action_names.get(mapping.action, "?"))
            action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Color code based on condition
            if mapping.conditions:
                action_item.setBackground(QColor("#fff8e6"))
                action_item.setToolTip("Has condition: Check before executing")

            self.mappings_table.setItem(row, 1, action_item)

            # Target
            target_text = mapping.target
            if mapping.action == InputAction.SEQUENCE:
                target_text = f"{len(mapping.sequence_actions)} actions"
            elif mapping.targets:
                target_text = f"{len(mapping.targets)} targets"
            target_item = QTableWidgetItem(target_text)
            target_item.setFlags(target_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mappings_table.setItem(row, 2, target_item)

            # Delete button
            if not self.mappings_table.cellWidget(row, 3):
                del_btn = QPushButton("🗑️")
                del_btn.setFixedSize(30, 24)
                del_btn.setToolTip("Delete this mapping")
                del_btn.clicked.connect(lambda c, r=row: self._delete_mapping(r))
                self.mappings_table.setCellWidget(row, 3, del_btn)

        # Update stats
        condition_count = sum(1 for m in sorted_mappings if m.conditions)
        sequence_count = sum(1 for m in sorted_mappings if m.action == InputAction.SEQUENCE)

        stats_parts = [f"{len(sorted_mappings)} mapping(s)"]
        if condition_count > 0:
            stats_parts.append(f"{condition_count} with conditions")
        if sequence_count > 0:
            stats_parts.append(f"{sequence_count} sequences")

        self.stats_label.setText(" | ".join(stats_parts))

    def _add_new_mapping(self):
        """Add a new mapping with learn mode."""
        dialog = InputMappingDialog(
            self,
            None,
            self.dataref_manager,
            self.variable_store,  # NEW: Pass variable store
            fixed_input=False
        )

        # --- NEW: Pass HID Manager for Calibration Wizard ---
        dialog._hid_manager = self.hid_manager
        # ---------------------------------------------------

        # Store reference for learning
        self._learning_dialog = dialog

        if dialog.exec():
            new_mapping = dialog.get_mapping()

            # Remove any existing mapping for this input
            self.input_mapper.remove_mappings_for_input(
                new_mapping.input_key,
                new_mapping.device_port
            )

            self.input_mapper.add_mapping(new_mapping)
            self._refresh_mappings_table()

            log.info("Added new mapping: %s -> %s",
                     new_mapping.input_key, new_mapping.target)

        self._learning_dialog = None

    def _edit_selected_mapping(self):
        """Edit the selected mapping."""
        row = self.mappings_table.currentRow()
        if row < 0:
            return

        mappings = self.input_mapper.get_mappings()
        if row >= len(mappings):
            return

        mapping = mappings[row]

        dialog = InputMappingDialog(
            self,
            mapping,
            self.dataref_manager,
            self.variable_store,
            fixed_input=True
        )

        # --- NEW: Pass HID Manager for Calibration Wizard ---
        dialog._hid_manager = self.hid_manager
        # ---------------------------------------------------

        if dialog.exec():
            new_mapping = dialog.get_mapping()

            # Remove old and add new
            self.input_mapper.remove_mapping(row)
            self.input_mapper.add_mapping(new_mapping)
            self._refresh_mappings_table()

            log.info("Updated mapping: %s -> %s",
                     new_mapping.input_key, new_mapping.target)

    def _delete_mapping(self, row: int):
        """Delete a mapping."""
        mappings = self.input_mapper.get_mappings()
        if row >= len(mappings):
            return

        mapping = mappings[row]

        reply = QMessageBox.question(
            self,
            "Delete Mapping",
            f"Delete mapping for {mapping.input_key}?\n\n{mapping.description or mapping.target}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.input_mapper.remove_mapping(row)
            self._refresh_mappings_table()
            log.info("Deleted mapping: %s", mapping.input_key)

    def _show_mapping_context_menu(self, position):
        """Show context menu for mappings table."""
        row = self.mappings_table.rowAt(position.y())
        if row < 0:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("✏️ Edit Mapping")
        delete_action = menu.addAction("🗑️ Delete Mapping")
        menu.addSeparator()
        duplicate_action = menu.addAction("📋 Duplicate")

        # Copy/Paste actions
        menu.addSeparator()
        copy_action = menu.addAction("📋 Copy Settings")
        paste_action = menu.addAction("📋 Paste Settings")

        # Check if clipboard has valid JSON for pasting
        clipboard = QApplication.clipboard()
        try:
            text = clipboard.text()
            json.loads(text)  # Check if valid JSON
            paste_action.setEnabled(True)
        except:
            paste_action.setEnabled(False)

        action = menu.exec(self.mappings_table.viewport().mapToGlobal(position))

        if action == edit_action:
            self.mappings_table.setCurrentCell(row, 0)
            self._edit_selected_mapping()
        elif action == delete_action:
            self._delete_mapping(row)
        elif action == duplicate_action:
            self._duplicate_mapping(row)
        elif action == copy_action:
            self._copy_mapping_settings(row)
        elif action == paste_action:
            self._paste_mapping_settings()

    def _duplicate_mapping(self, row: int):
        """Duplicate a mapping."""
        mappings = self.input_mapper.get_mappings()
        if row >= len(mappings):
            return

        mapping = mappings[row]

        # Create a copy with modified description
        new_mapping = InputMapping.from_dict(mapping.to_dict())
        new_mapping.description = f"{mapping.description} (Copy)"

        self.input_mapper.add_mapping(new_mapping)
        self._refresh_mappings_table()

        log.info("Duplicated mapping: %s", mapping.input_key)

    def _copy_mapping_settings(self, row):
        """Serialize mapping to JSON and copy to clipboard."""
        # 1. Retrieve mapping
        mappings = self.input_mapper.get_mappings()
        if row >= len(mappings):
            return

        mapping = mappings[row]
        if mapping:
            data = mapping.to_dict()
            # Remove unique identifiers like input_key, device_port so user can paste to other buttons
            # Or keep them if they want to overwrite same button.
            # User request: "paste... to another variable or HID input".
            # So we should CLEAR input_key and device_port so they can assign new ones.
            data['input_key'] = ''
            data['device_port'] = '*'

            json_str = json.dumps(data, indent=2)
            QApplication.clipboard().setText(json_str)
            self.statusBar().showMessage(f"Copied settings for '{mapping.description or mapping.input_key}'", 3000)

    def _paste_mapping_settings(self):
        """Load settings from clipboard and open Edit Dialog."""
        text = QApplication.clipboard().text()
        try:
            data = json.loads(text)

            # Create a temporary mapping from the data
            mapping = InputMapping.from_dict(data)

            # Open Dialog for user to assign to new input
            dialog = InputMappingDialog(self, mapping=mapping, dataref_manager=self.dataref_manager, variable_store=self.variable_store)

            # --- NEW: Pass HID Manager for Calibration Wizard ---
            dialog._hid_manager = self.hid_manager
            # ---------------------------------------------------

            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Save the new mapping
                new_mapping = dialog.get_mapping()
                self.input_mapper.add_mapping(new_mapping)
                self._refresh_mappings_table()
                self.statusBar().showMessage("Pasted and Created New Mapping", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to paste settings:\n{e}")

    def _show_device_context_menu(self, position):
        """Show context menu for device renaming."""
        if not self.profile_manager:
            return

        item = self.device_list.itemAt(position)
        if not item:
            return

        device_id = item.data(Qt.ItemDataRole.UserRole)
        if not device_id:
            return

        device = self.hid_manager.get_device(device_id)
        if not device:
            return

        menu = QMenu(self)

        current_alias = self.profile_manager.get_device_alias(device_id)
        current_display = current_alias if current_alias else device.name

        rename_action = menu.addAction(f"✏️ Rename '{current_display}'...")
        action = menu.exec(self.device_list.mapToGlobal(position))

        if action == rename_action:
            self._rename_device(device_id, device)

    def _rename_device(self, device_id: str, device: HIDDevice):
        """Open rename dialog for device."""
        current_alias = self.profile_manager.get_device_alias(device_id) if self.profile_manager else ""

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Rename Device")
        dialog_layout = QVBoxLayout(dialog)

        dialog_layout.addWidget(QLabel(f"Original name: {device.name}"))

        alias_input = QLineEdit()
        alias_input.setText(current_alias or "")
        alias_input.setPlaceholderText("Enter new name...")
        dialog_layout.addWidget(alias_input)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        dialog_layout.addLayout(btn_layout)

        if dialog.exec():
            new_alias = alias_input.text().strip()
            if self.profile_manager:
                self.profile_manager.set_device_alias(device_id, new_alias)
            self._refresh_device_list()

    def handle_input_signal(self, key: str, port: str):
        """
        Pass input signal to active dialog for 'Learning'.
        Called by main window when Arduino input is received.
        """
        if self._learning_dialog:
            self._learning_dialog.on_input_detected(key, port)
