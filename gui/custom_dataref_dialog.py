from __future__ import annotations
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QDialogButtonBox,
    QFormLayout, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt

from core.dataref_manager import DatarefManager

log = logging.getLogger(__name__)


class CustomDatarefDialog(QDialog):
    """Dialog to create custom datarefs."""
    
    def __init__(self, dataref_manager: DatarefManager, parent=None):
        super().__init__(parent)
        self.dataref_manager = dataref_manager
        self.setWindowTitle("Create Custom Dataref")
        self.setMinimumWidth(400)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel(
            "Create a custom dataref placeholder. This allows you to use a dataref "
            "that might not exist in X-Plane's database (e.g., for mod aircraft)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; background: #fff3cd; padding: 8px; border-radius: 4px;")
        layout.addWidget(info)

        # Form
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., my_mod/led_status or sim/custom/my_dataref")
        form.addRow("Full Dataref Path:", self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["float", "int", "byte", "string", "command"])
        form.addRow("Data Type:", self.type_combo)
        
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description of this dataref")
        form.addRow("Description:", self.desc_input)
        
        self.writable_check = QCheckBox("Writable")
        self.writable_check.setChecked(True)
        form.addRow("Is Writable?", self.writable_check)
        
        layout.addLayout(form)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _save(self):
        """Save the custom dataref."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name is required.")
            return

        # Validate name format
        if not name.startswith("sim/"):
            reply = QMessageBox.question(
                self,
                "Confirm Dataref Path",
                f"The dataref '{name}' doesn't start with 'sim/'. Would you like to prefix it with 'sim/custom/'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                name = f"sim/custom/{name}"
            else:
                if not name.startswith("sim/"):
                    QMessageBox.warning(self, "Error", "Dataref name must start with 'sim/'.")
                    return

        dtype = self.type_combo.currentText()
        desc = self.desc_input.text().strip()
        writable = self.writable_check.isChecked()

        # Add to dataref manager
        success = self.dataref_manager.add_custom_dataref(name, dtype, desc, writable)
        
        if success:
            QMessageBox.information(self, "Success", f"Custom dataref '{name}' added to database.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Dataref '{name}' already exists or is invalid.")