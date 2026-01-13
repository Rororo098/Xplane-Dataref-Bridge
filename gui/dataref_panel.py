from __future__ import annotations
import logging
import asyncio
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QHeaderView, QCompleter, QDoubleSpinBox,
    QMessageBox, QListWidget, QListWidgetItem, QSplitter,
    QComboBox, QFrame, QDialog,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

log = logging.getLogger(__name__)


class DatarefPanel(QWidget):
    """Panel for browsing, searching, and subscribing to X-Plane datarefs."""
    
    def __init__(self, dataref_manager, xplane_connection) -> None:
        super().__init__()
        
        self.dataref_manager = dataref_manager
        self.xplane_connection = xplane_connection
        
        self._subscribed_datarefs: Dict[str, int] = {}
        self._all_datarefs = dataref_manager.get_all_dataref_names()
        
        self._setup_ui()
        self._connect_signals()
        self._populate_list()
        
        # Debounce timer for search
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
    
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        
        # === LEFT: Browse/Search Panel ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with add button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Dataref Browser</b>"))

        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.count_label)

        header_layout.addStretch()

        # Add custom dataref button
        self.add_custom_btn = QPushButton("➕ Add Custom")
        self.add_custom_btn.setMaximumWidth(100)
        self.add_custom_btn.setToolTip("Add a custom dataref (for payware aircraft)")
        self.add_custom_btn.clicked.connect(self._add_custom_dataref)
        header_layout.addWidget(self.add_custom_btn)

        left_layout.addLayout(header_layout)
        
        # Search box
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search datarefs (e.g., 'gear', 'autopilot', 'throttle')...")
        self.search_input.setClearButtonEnabled(True)
        search_layout.addWidget(self.search_input)
        
        left_layout.addLayout(search_layout)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", "all")
        self.category_combo.addItem("🎛️ Controls", "controls")
        self.category_combo.addItem("🛫 Autopilot", "autopilot")
        self.category_combo.addItem("⚙️ Engine", "engine")
        self.category_combo.addItem("🛞 Gear", "gear")
        self.category_combo.addItem("💡 Lights", "lights")
        self.category_combo.addItem("⚠️ Warnings", "warnings")
        self.category_combo.addItem("📊 Instruments", "instruments")
        self.category_combo.addItem("📻 Radios", "radios")
        self.category_combo.addItem("📍 Position", "position")
        self.category_combo.addItem("📦 Other", "other")
        filter_layout.addWidget(self.category_combo)
        
        filter_layout.addStretch()
        left_layout.addLayout(filter_layout)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setAlternatingRowColors(True)
        self.results_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        left_layout.addWidget(self.results_list)
        
        # Selected dataref info
        self.info_frame = QFrame()
        self.info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.info_frame.setMaximumHeight(80)
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(8, 8, 8, 8)
        
        self.info_name = QLabel("<i>Select a dataref</i>")
        self.info_name.setWordWrap(True)
        info_layout.addWidget(self.info_name)
        
        self.info_details = QLabel("")
        self.info_details.setStyleSheet("color: gray; font-size: 11px;")
        info_layout.addWidget(self.info_details)
        
        left_layout.addWidget(self.info_frame)
        
        # Subscribe and edit buttons
        btn_layout = QHBoxLayout()
        self.subscribe_btn = QPushButton("Subscribe Selected →")
        self.subscribe_btn.setEnabled(False)
        btn_layout.addWidget(self.subscribe_btn)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setMaximumWidth(60)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setVisible(False)  # Initially hidden
        self.edit_btn.clicked.connect(self._edit_selected_dataref)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setMaximumWidth(60)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setVisible(False)  # Initially hidden
        self.delete_btn.clicked.connect(self._delete_selected_dataref)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        
        # === RIGHT: Subscribed Datarefs ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Connection status
        self.connection_label = QLabel("⚪ Not connected to X-Plane")
        self.connection_label.setStyleSheet("color: gray; font-weight: bold;")
        right_layout.addWidget(self.connection_label)
        
        right_layout.addWidget(QLabel("<b>Subscribed Datarefs</b>"))
        
        # Quick subscribe buttons
        quick_group = QGroupBox("Quick Subscribe")
        quick_layout = QHBoxLayout(quick_group)
        
        quick_datarefs = [
            ("Flaps", "sim/cockpit2/controls/flap_ratio"),
            ("Throttle", "sim/cockpit2/engine/actuators/throttle_ratio_all"),
            ("Gear", "sim/cockpit2/switches/gear_handle_status"),
            ("AP State", "sim/cockpit/autopilot/autopilot_state"),
            ("IAS", "sim/cockpit2/gauges/indicators/airspeed_kts_pilot"),
            ("Alt", "sim/cockpit2/gauges/indicators/altitude_ft_pilot"),
        ]
        
        for name, dataref in quick_datarefs:
            btn = QPushButton(name)
            btn.setMaximumWidth(70)
            btn.setToolTip(dataref)
            btn.clicked.connect(lambda checked, dr=dataref: self._subscribe_dataref(dr))
            quick_layout.addWidget(btn)
        
        quick_layout.addStretch()
        right_layout.addWidget(quick_group)
        
        # Subscribed table
        self.values_table = QTableWidget(0, 4)
        self.values_table.setHorizontalHeaderLabels(["Dataref", "Value", "Write", ""])
        self.values_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.values_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.values_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.values_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.values_table.setAlternatingRowColors(True)
        right_layout.addWidget(self.values_table)
        
        # Manual subscribe
        manual_group = QGroupBox("Manual Subscribe")
        manual_layout = QHBoxLayout(manual_group)
        
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Type any dataref name...")
        
        # Autocomplete
        if self._all_datarefs:
            completer = QCompleter(self._all_datarefs)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(15)
            self.manual_input.setCompleter(completer)
        
        manual_layout.addWidget(self.manual_input)
        
        self.manual_btn = QPushButton("Subscribe")
        manual_layout.addWidget(self.manual_btn)
        
        right_layout.addWidget(manual_group)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter)
    
    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self._on_search_changed)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        self.results_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.subscribe_btn.clicked.connect(self._subscribe_selected)
        self.manual_btn.clicked.connect(self._subscribe_manual)
        self.manual_input.returnPressed.connect(self._subscribe_manual)
    
    def _populate_list(self) -> None:
        """Populate the list with all datarefs."""
        self.results_list.clear()

        datarefs = sorted(self._all_datarefs)

        for dr in datarefs:
            info = self.dataref_manager.get_dataref_info(dr)

            # Create item
            display_name = dr
            if info and info.get("custom"):
                display_name = f"✨ {dr}"

            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, dr)  # Store actual name

            # Style custom datarefs
            if info and info.get("custom"):
                item.setForeground(QColor("#8B008B"))  # Purple for custom

            # Add tooltip
            if info:
                desc = info.get("description", "")
                dtype = info.get("type", "")
                writable = "writable" if info.get("writable") else "read-only"

                tooltip = f"{dr}\n\nType: {dtype}\nAccess: {writable}"
                if desc:
                    tooltip += f"\n\n{desc}"
                if info.get("aircraft"):
                    tooltip += f"\n\nAircraft: {info['aircraft']}"
                item.setToolTip(tooltip)

            self.results_list.addItem(item)

        self._update_count()
    
    def _on_search_changed(self, text: str) -> None:
        """Handle search input change with debounce."""
        self._search_timer.stop()
        self._search_timer.start(200)  # Wait 200ms before searching
    
    def _on_category_changed(self) -> None:
        """Handle category filter change."""
        self._do_search()
    
    def _do_search(self) -> None:
        """Perform the actual search/filter."""
        query = self.search_input.text().lower()
        category = self.category_combo.currentData()

        visible_count = 0

        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            # Get the actual dataref name from UserRole
            dataref = item.data(Qt.ItemDataRole.UserRole)
            if not dataref:
                dataref = item.text().replace("✨ ", "")  # Fallback

            # Category filter
            if category and category != "all":
                info = self.dataref_manager.get_dataref_info(dataref)
                dr_category = ""
                if info:
                    dr_category = info.get("category", "")
                if not dr_category:
                    dr_category = self.dataref_manager._guess_category(dataref)

                if dr_category != category:
                    item.setHidden(True)
                    continue

            # Text search
            if query:
                # Search in name
                name_match = query in dataref.lower()

                # Search in description
                desc_match = False
                info = self.dataref_manager.get_dataref_info(dataref)
                if info:
                    desc = info.get("description", "").lower()
                    desc_match = query in desc

                if not name_match and not desc_match:
                    item.setHidden(True)
                    continue

            item.setHidden(False)
            visible_count += 1

        self._update_count(visible_count)
    
    def _update_count(self, visible: int = None) -> None:
        """Update the count label."""
        total = self.results_list.count()
        
        if visible is None:
            visible = sum(1 for i in range(total) if not self.results_list.item(i).isHidden())
        
        if visible == total:
            self.count_label.setText(f"({total} datarefs)")
        else:
            self.count_label.setText(f"(showing {visible} of {total})")
    
    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        item = self.results_list.currentItem()

        if item:
            # Get the actual dataref name from UserRole
            dataref = item.data(Qt.ItemDataRole.UserRole)
            if not dataref:
                dataref = item.text().replace("✨ ", "")  # Fallback

            info = self.dataref_manager.get_dataref_info(dataref)

            # Check if custom
            is_custom = info.get("custom", False) if info else False

            # Show/hide and enable/disable edit/delete buttons
            self.edit_btn.setVisible(is_custom)
            self.delete_btn.setVisible(is_custom)
            self.edit_btn.setEnabled(is_custom)
            self.delete_btn.setEnabled(is_custom)

            # Update info display
            self.info_name.setText(f"<b>{dataref}</b>")

            if is_custom:
                self.info_name.setText(f"<b>{dataref}</b> <span style='color: purple;'>(Custom)</span>")

            if info:
                details = []
                if info.get("type"):
                    details.append(f"Type: {info['type']}")
                if info.get("writable") is not None:
                    details.append("✏️ Writable" if info["writable"] else "🔒 Read-only")
                if info.get("units"):
                    details.append(f"Units: {info['units']}")
                if info.get("aircraft"):
                    details.append(f"Aircraft: {info['aircraft']}")

                self.info_details.setText(" | ".join(details))

                if info.get("description"):
                    self.info_details.setText(
                        self.info_details.text() + f"\n{info['description']}"
                    )
            else:
                self.info_details.setText("No additional info available")

            self.subscribe_btn.setEnabled(True)
        else:
            self.info_name.setText("<i>Select a dataref</i>")
            self.info_details.setText("")
            self.subscribe_btn.setEnabled(False)
            self.edit_btn.setVisible(False)
            self.delete_btn.setVisible(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def _on_item_double_clicked(self, item) -> None:
        """Handle item double click."""
        # Get the actual dataref name from UserRole
        dataref = item.data(Qt.ItemDataRole.UserRole)
        if not dataref:
            dataref = item.text().replace("✨ ", "")  # Fallback
        self._subscribe_dataref(dataref)

    def _subscribe_selected(self) -> None:
        """Subscribe to selected dataref."""
        item = self.results_list.currentItem()
        if item:
            # Get the actual dataref name from UserRole
            dataref = item.data(Qt.ItemDataRole.UserRole)
            if not dataref:
                dataref = item.text().replace("✨ ", "")  # Fallback
            self._subscribe_dataref(dataref)
    
    def _subscribe_manual(self) -> None:
        """Subscribe to manually entered dataref."""
        dataref = self.manual_input.text().strip()
        if dataref:
            self._subscribe_dataref(dataref)
            self.manual_input.clear()
    
    def _subscribe_dataref(self, dataref: str) -> None:
        """Subscribe to a dataref."""
        if not dataref:
            return
        
        if dataref in self._subscribed_datarefs:
            return
        
        row = self.values_table.rowCount()
        self.values_table.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(dataref)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.values_table.setItem(row, 0, name_item)
        
        # Value
        value_item = QTableWidgetItem("-")
        value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.values_table.setItem(row, 1, value_item)
        
        # Write control
        write_widget = QWidget()
        write_layout = QHBoxLayout(write_widget)
        write_layout.setContentsMargins(2, 2, 2, 2)
        
        write_spin = QDoubleSpinBox()
        write_spin.setRange(-999999, 999999)
        write_spin.setDecimals(4)
        write_spin.setMaximumWidth(100)
        write_layout.addWidget(write_spin)
        
        write_btn = QPushButton("Set")
        write_btn.setMaximumWidth(35)
        write_btn.clicked.connect(lambda: self._write_dataref(dataref, write_spin.value()))
        write_layout.addWidget(write_btn)
        
        self.values_table.setCellWidget(row, 2, write_widget)
        
        # Unsubscribe
        unsub_btn = QPushButton("✕")
        unsub_btn.setMaximumWidth(25)
        unsub_btn.clicked.connect(lambda: self._unsubscribe_dataref(dataref))
        self.values_table.setCellWidget(row, 3, unsub_btn)
        
        self._subscribed_datarefs[dataref] = row
        
        if self.xplane_connection.connected:
            asyncio.create_task(self.xplane_connection.subscribe_dataref(dataref))
        
        log.info("Subscribed to dataref: %s", dataref)
    
    def _unsubscribe_dataref(self, dataref: str) -> None:
        """Unsubscribe from a dataref."""
        if dataref not in self._subscribed_datarefs:
            return
        
        row = self._subscribed_datarefs[dataref]
        self.values_table.removeRow(row)
        del self._subscribed_datarefs[dataref]
        
        # Reindex
        new_subs = {}
        for dr, r in self._subscribed_datarefs.items():
            new_subs[dr] = r - 1 if r > row else r
        self._subscribed_datarefs = new_subs
        
        if self.xplane_connection.connected:
            asyncio.create_task(self.xplane_connection.unsubscribe_dataref(dataref))
        
        log.info("Unsubscribed from dataref: %s", dataref)
    
    def _write_dataref(self, dataref: str, value: float) -> None:
        """Write a value to a dataref."""
        if not self.xplane_connection.connected:
            QMessageBox.warning(self, "Not Connected", "Not connected to X-Plane")
            return
        
        asyncio.create_task(self.xplane_connection.write_dataref(dataref, value))
        log.info("Wrote %s = %.4f", dataref, value)
    
    def update_value(self, dataref: str, value: float) -> None:
        """Update displayed value for a dataref."""
        if dataref not in self._subscribed_datarefs:
            return
        
        row = self._subscribed_datarefs[dataref]
        item = self.values_table.item(row, 1)
        if item:
            if abs(value) >= 1000:
                item.setText(f"{value:.1f}")
            elif abs(value) >= 1:
                item.setText(f"{value:.2f}")
            else:
                item.setText(f"{value:.4f}")
    
    def on_connection_changed(self, connected: bool) -> None:
        """Handle X-Plane connection state change."""
        if connected:
            self.connection_label.setText("🟢 Connected to X-Plane")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")

            for dataref in self._subscribed_datarefs.keys():
                asyncio.create_task(self.xplane_connection.subscribe_dataref(dataref))
        else:
            self.connection_label.setText("⚪ Not connected to X-Plane")
            self.connection_label.setStyleSheet("color: gray; font-weight: bold;")

    def _add_custom_dataref(self):
        """Open dialog to add a custom dataref."""
        from gui.custom_dataref_dialog import CustomDatarefDialog

        dialog = CustomDatarefDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, info = dialog.get_dataref_data()

            # Add to manager
            self.dataref_manager.add_custom_dataref(name, info)

            # Save database
            self.dataref_manager.save_database()

            # Refresh list
            self._refresh_list()

            # Show confirmation
            QMessageBox.information(
                self, "Dataref Added",
                f"Custom dataref added:\n\n{name}\n\n"
                "It has been saved to the database."
            )

    def _edit_selected_dataref(self):
        """Edit the selected custom dataref."""
        item = self.results_list.currentItem()
        if not item:
            return

        # Get the actual dataref name from UserRole
        dataref = item.data(Qt.ItemDataRole.UserRole)
        if not dataref:
            dataref = item.text().replace("✨ ", "")  # Fallback

        info = self.dataref_manager.get_dataref_info(dataref)

        if not info or not info.get("custom", False):
            QMessageBox.warning(
                self, "Cannot Edit",
                "Only custom datarefs can be edited."
            )
            return

        from gui.custom_dataref_dialog import CustomDatarefDialog

        dialog = CustomDatarefDialog(self, existing_dataref=dataref, existing_info=info)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, new_info = dialog.get_dataref_data()

            # Update in manager
            self.dataref_manager.add_custom_dataref(name, new_info)

            # Save database
            self.dataref_manager.save_database()

            # Refresh
            self._refresh_list()
            self._on_selection_changed()

    def _delete_selected_dataref(self):
        """Delete the selected custom dataref."""
        item = self.results_list.currentItem()
        if not item:
            return

        # Get the actual dataref name from UserRole
        dataref = item.data(Qt.ItemDataRole.UserRole)
        if not dataref:
            dataref = item.text().replace("✨ ", "")  # Fallback

        if not self.dataref_manager.is_custom_dataref(dataref):
            QMessageBox.warning(
                self, "Cannot Delete",
                "Only custom datarefs can be deleted.\n\n"
                "Built-in datarefs cannot be removed."
            )
            return

        result = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete this custom dataref?\n\n{dataref}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            self.dataref_manager.remove_custom_dataref(dataref)
            self.dataref_manager.save_database()
            self._refresh_list()

    def _refresh_list(self):
        """Refresh the dataref list."""
        self._all_datarefs = self.dataref_manager.get_all_dataref_names()
        self._populate_list()

        # Update autocomplete
        if self._all_datarefs:
            completer = QCompleter(self._all_datarefs)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(15)
            self.manual_input.setCompleter(completer)