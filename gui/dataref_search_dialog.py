from __future__ import annotations
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QDialogButtonBox,
    QLabel, QAbstractItemView, QSplitter
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor

from core.variable_store import VariableStore, VariableType

log = logging.getLogger(__name__)

class DatarefSearchDialog(QDialog):
    """
    A searchable dialog to select X-Plane datarefs from the database.
    """
    def __init__(self, dataref_manager, variable_store=None, parent=None):
        super().__init__(parent)
        self.dataref_manager = dataref_manager
        self.variable_store = variable_store
        self.selected_dataref: Optional[str] = None

        self.setWindowTitle("Select Dataref")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self._setup_ui()
        self._load_datarefs()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search (e.g., 'gear', 'lights', 'aircraft')...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(QLabel("🔍"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        # Description Box (Context)
        self.desc_label = QLabel("Select a dataref to see details.")
        self.desc_label.setStyleSheet("color: #555; font-style: italic; padding: 5px; background: #f0f0f0; border-radius: 4px;")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        # Debounce timer for search to prevent UI freezing on large lists
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._all_datarefs = []

    def _load_datarefs(self):
        """Load all datarefs from manager into memory for searching."""
        items = []

        # 1. X-Plane Datarefs (Official + Custom)
        if self.dataref_manager:
            items.extend(self.dataref_manager.get_all_dataref_names())

        # 2. Variables from Store (Arduino Inputs + Virtual Vars)
        if self.variable_store:
            for name, entry in self.variable_store.get_all().items():
                # Create a display name that distinguishes it
                # Example: "[ARD] LIGHT_SWITCH_1" -> "LIGHT_SWITCH_1"
                display_name = f"[{entry.type.name}] {name}"
                items.append(display_name)

        # 3. Logic Variables (Virtual Variables from Logic Engine)
        # If we have access to the logic engine, include its variables too
        # For now, we'll include all variables from the variable store
        # which should include logic variables

        self._all_datarefs = items
        self._populate_list(items)

    def _on_search_changed(self, text: str):
        """Trigger search after short delay."""
        self._search_timer.start(150) # 150ms debounce

    def _perform_search(self):
        """Filter the list based on search text."""
        query = self.search_input.text().lower().strip()
        
        if not query:
            filtered = self._all_datarefs
        else:
            filtered = [d for d in self._all_datarefs if query in d.lower()]
        
        self._populate_list(filtered)

    def _populate_list(self, items):
        """Fill the list widget."""
        self.list_widget.clear()
        for item_name in items:
            list_item = QListWidgetItem(item_name)
            # If it's a variable (wrapped in brackets), style it differently
            # Assuming format: [TYPE] NAME
            if item_name.startswith("["):
                list_item.setForeground(QColor("#0078d4")) # Blue for variables
                list_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            # Simplistic highlighting (Qt doesn't support rich text in QListWidget natively easily)
            # We stick to plain text for performance with 5000+ items
            self.list_widget.addItem(list_item)

        self.desc_label.setText(f"Found {len(items)} items.")

    def _on_item_clicked(self, item: QListWidgetItem):
        """Update description label when an item is clicked."""
        name = item.text()
        # In a full implementation, fetch description/unit from manager if available
        self.desc_label.setText(f"<b>{name}</b>")

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Select and close on double click."""
        self.selected_dataref = item.text()
        self.accept()

    def get_selected_dataref(self) -> Optional[str]:
        """Return the selected dataref."""
        if self.selected_dataref:
            # If it's a variable with format "[TYPE] name", extract just the name
            if self.selected_dataref.startswith("[") and "] " in self.selected_dataref:
                parts = self.selected_dataref.split("] ", 1)
                if len(parts) == 2:
                    return parts[1]
            return self.selected_dataref
        return None

    def accept(self):
        """Override accept to grab selection."""
        item = self.list_widget.currentItem()
        if item:
            txt = item.text()
            # If it's a variable (wrapped in brackets), extract the actual name
            # Example: "[ARD] LIGHT_SWITCH_1" -> "LIGHT_SWITCH_1"
            # Assuming format: [TYPE] NAME
            if txt.startswith("["):
                parts = txt.split("] ", 1)
                if len(parts) == 2:
                    self.selected_dataref = parts[1]
                else:
                    self.selected_dataref = txt
            else:
                self.selected_dataref = txt
        else:
            self.selected_dataref = None
        super().accept()