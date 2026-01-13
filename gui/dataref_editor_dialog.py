from __future__ import annotations
import logging
import asyncio
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QWidget, QLineEdit, QDialogButtonBox, QMessageBox, QTabWidget,
    QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

log = logging.getLogger(__name__)

class DatarefEditorDialog(QDialog):
    """
    Editor for Scalar, Array, and String datarefs.
    Detects type and switches UI accordingly.
    """
    
    # Signal to request read
    request_read = pyqtSignal(str) 

    def __init__(self, dataref_name: str, dataref_info: dict, xplane_conn, dataref_manager, variable_store=None, parent=None):
        super().__init__(parent)
        self.dataref_name = dataref_name
        self.info = dataref_info
        self.conn = xplane_conn
        self.manager = dataref_manager
        self.variable_store = variable_store
        
        self.setWindowTitle(f"Edit Dataref: {dataref_name}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Type Detection
        dtype = self.info.get("type", "float")
        
        # Parse size if it's an array type (e.g., float[8], byte[260])
        m = re.search(r'\[(\d+)\]', dtype)
        self.array_size = int(m.group(1)) if m else 0
        
        if "[" in self.dataref_name:
            # It's an array type (already indexed, e.g., acf_ICAO[0])
            base_name = self.dataref_name.split("[")[0]
            # If we don't have size but it's indexed, assume at least 10 or whatever is known
            size = self.array_size if self.array_size > 0 else 10
            self._setup_array_editor(base_name, size)
        elif "string" in dtype or "byte" in dtype:
            # It's a string type (likely byte[n])
            self._setup_string_editor(dtype)
        elif self.array_size > 0:
            # It's an array type detected via metadata, but name is scalar
            self._setup_array_editor(self.dataref_name, self.array_size)
        else:
            # Scalar
            self._setup_scalar_editor()
            
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._save_changes)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _setup_scalar_editor(self):
        self.stacked = QTabWidget()
        
        # Tab 1: Value Editor
        page1 = QWidget()
        l1 = QVBoxLayout(page1)
        l1.addWidget(QLabel(f"<b>Dataref:</b> {self.dataref_name}"))
        l1.addWidget(QLabel("<b>Type:</b> Float / Int"))
        
        self.scalar_input = QDoubleSpinBox()
        self.scalar_input.setRange(-999999, 999999)
        self.scalar_input.setDecimals(4)
        l1.addWidget(self.scalar_input)
        
        btn_read = QPushButton("🔄 Refresh from X-Plane")
        btn_read.clicked.connect(self._trigger_read)
        l1.addWidget(btn_read)
        
        self.stacked.addTab(page1, "Value")
        self.layout().addWidget(self.stacked)
        
        # Pre-fill value if known
        if self.conn:
            val = self.conn.get_value(self.dataref_name)
            if val is not None:
                self.scalar_input.setValue(val)

    def _setup_array_editor(self, base_name: str, size: int):
        """Editor for arrays (e.g., acf_ICAO[0..9])."""
        self.stacked = QTabWidget()
        
        # Tab 1: Indexed List
        page1 = QWidget()
        l1 = QVBoxLayout(page1)
        l1.addWidget(QLabel(f"<b>Base Name:</b> {base_name}"))
        
        self.array_table = QTableWidget()
        self.array_table.setColumnCount(2)
        self.array_table.setHorizontalHeaderLabels(["Index", "Value (Float/Int)"])
        self.array_table.horizontalHeader().setStretchLastSection(True)
        
        # Fill with indices 
        for i in range(size):
            self._add_array_row(i)
            
        l1.addWidget(self.array_table)
        
        # Add row button (if user needs more than metadata says)
        btn_add = QPushButton("+ Add More Indices")
        btn_add.clicked.connect(lambda: self._add_array_row(self.array_table.rowCount()))
        l1.addWidget(btn_add)

        self.stacked.addTab(page1, "Indices")
        
        # Tab 2: Hex/Ascii Viewer (for byte[n])
        page2 = QWidget()
        l2 = QVBoxLayout(page2)
        self.hex_table = QTableWidget()
        self.hex_table.setColumnCount(3)
        self.hex_table.setHorizontalHeaderLabels(["Index", "Hex", "ASCII"])
        
        l2.addWidget(QLabel("<b>Raw Data View (Hex/ASCII)</b>"))
        l2.addWidget(self.hex_table)
        self.stacked.addTab(page2, "Raw Hex")
        
        self.layout().addWidget(self.stacked)
        
        # Load existing values if known
        QTimer.singleShot(100, self._load_array_data)

    def _setup_string_editor(self, dtype: str):
        """Editor for string/byte datarefs."""
        self.stacked = QTabWidget()
        
        page1 = QWidget()
        l1 = QVBoxLayout(page1)
        l1.addWidget(QLabel(f"<b>Dataref:</b> {self.dataref_name}"))
        l1.addWidget(QLabel(f"<b>Type:</b> {dtype}"))
        
        self.string_input = QLineEdit()
        self.string_input.setPlaceholderText("Enter text here...")
        l1.addWidget(self.string_input)
        
        l1.addWidget(QLabel("Note: This will update the byte array."))
        
        self.stacked.addTab(page1, "String Editor")
        self.layout().addWidget(self.stacked)

    def _trigger_read(self):
        if self.conn:
            self.request_read.emit(self.dataref_name)
        else:
            QMessageBox.warning(self, "Error", "Not connected to X-Plane")

    def _load_array_data(self):
        """Poll X-Plane connection for array values."""
        if hasattr(self, 'array_table'):
            base_name = self.dataref_name.split("[")[0]
            # Try to populate from connection cache first
            if self.conn:
                for i in range(self.array_table.rowCount()):
                    name = f"{base_name}[{i}]"
                    val = self.conn.get_value(name)
                    if val is not None:
                        self.set_array_value(i, val)
                    else:
                        # Request read
                        self.request_read.emit(name)

    def set_scalar_value(self, val: float):
        if hasattr(self, 'scalar_input'):
            self.scalar_input.setValue(val)

    def set_array_value(self, index: int, val: float):
        if hasattr(self, 'array_table') and index < self.array_table.rowCount():
             self.array_table.setItem(index, 1, QTableWidgetItem(f"{val:.4f}"))
             
             # Also update Hex/Ascii if visible
             if hasattr(self, 'hex_table') and self.hex_table.rowCount() <= index:
                 self.hex_table.setRowCount(index + 1)
             
             if hasattr(self, 'hex_table'):
                 # Hex
                 hex_val = f"0x{int(val):02X}"
                 self.hex_table.setItem(index, 0, QTableWidgetItem(f"[{index}]"))
                 self.hex_table.setItem(index, 1, QTableWidgetItem(hex_val))
                 
                 # ASCII
                 try:
                     char = chr(int(val))
                     if not char.isprintable(): char = "."
                 except: char = "."
                 self.hex_table.setItem(index, 2, QTableWidgetItem(char))

    def _add_array_row(self, i: int):
        self.array_table.insertRow(i)
        idx_item = QTableWidgetItem(f"[{i}]")
        idx_item.setFlags(idx_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        val_item = QTableWidgetItem("...")
        self.array_table.setItem(i, 0, idx_item)
        self.array_table.setItem(i, 1, val_item)

    def _save_changes(self):
        """Write changes to X-Plane or VariableStore."""
        # 0. Check for variable routing
        is_var = self.dataref_name.startswith("VAR:")
        target_name = self.dataref_name[4:] if is_var else self.dataref_name

        if hasattr(self, 'string_input'):
            txt = self.string_input.text()
            if is_var and self.variable_store:
                # String variables are rare but maybe someone wants it
                from core.variable_store import VariableType
                self.variable_store.update_value(target_name, 0.0, VariableType.VARIABLE_VIRTUAL, description=txt)
            elif self.conn:
                 # Pass array_size as max_len to ensure proper clearing
                 asyncio.create_task(self.conn.write_dataref_string(self.dataref_name, txt, max_len=self.array_size))
                 log.info("Writing string '%s' to %s (max_len=%d)", txt, self.dataref_name, self.array_size)
                 
        elif hasattr(self, 'scalar_input'):
            val = self.scalar_input.value()
            if is_var and self.variable_store:
                from core.variable_store import VariableType
                self.variable_store.update_value(target_name, val, VariableType.VARIABLE_VIRTUAL)
                log.info("Saving virtual variable %.4f to %s", val, target_name)
            elif self.conn:
                log.info("Saving scalar %.4f to %s", val, self.dataref_name)
                asyncio.create_task(self.conn.write_dataref(self.dataref_name, val))
                
        elif hasattr(self, 'array_table'):
            base_name = self.dataref_name.split("[")[0]
            log.info("Saving array data for %s", base_name)
            for row in range(self.array_table.rowCount()):
                 val_item = self.array_table.item(row, 1)
                 if val_item and "..." not in val_item.text():
                     try:
                         val = float(val_item.text())
                         name = f"{base_name}[{row}]"
                         if is_var and self.variable_store:
                             v_name = f"{target_name}[{row}]"
                             from core.variable_store import VariableType
                             self.variable_store.update_value(v_name, val, VariableType.VARIABLE_VIRTUAL)
                         elif self.conn:
                             asyncio.create_task(self.conn.write_dataref(name, val))
                     except ValueError: 
                         log.warning("Invalid value at row %d: %s", row, val_item.text())
            log.info("Wrote array values for %s", base_name)
        
        self.accept()
