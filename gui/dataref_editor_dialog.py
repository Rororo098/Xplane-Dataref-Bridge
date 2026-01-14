from __future__ import annotations
import logging
import asyncio
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QWidget, QLineEdit, QDialogButtonBox, QMessageBox, QTabWidget,
    QDoubleSpinBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication
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
            
        # Progress bar for large array operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

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

        # Add search/filter controls
        search_layout = QHBoxLayout()
        self.array_search_input = QLineEdit()
        self.array_search_input.setPlaceholderText("Filter by index or value...")
        self.array_search_input.textChanged.connect(self._filter_array_table)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.array_search_input)

        # Add quick jump to index
        jump_layout = QHBoxLayout()
        self.jump_to_index_input = QLineEdit()
        self.jump_to_index_input.setPlaceholderText("Jump to index...")
        self.jump_to_index_input.returnPressed.connect(self._jump_to_index)
        btn_jump = QPushButton("Go to Index")
        btn_jump.clicked.connect(self._jump_to_index)
        jump_layout.addWidget(QLabel("Jump to:"))
        jump_layout.addWidget(self.jump_to_index_input)
        jump_layout.addWidget(btn_jump)

        l1.addLayout(search_layout)
        l1.addLayout(jump_layout)

        self.array_table = QTableWidget()
        self.array_table.setColumnCount(3)  # Changed from 2 to 3 to add data type indicator
        self.array_table.setHorizontalHeaderLabels(["Index", "Value", "Type"])
        self.array_table.setAlternatingRowColors(True)
        self.array_table.setSortingEnabled(True)
        self.array_table.setEditTriggers(self.array_table.EditTrigger.DoubleClicked)
        self.array_table.setSelectionBehavior(self.array_table.SelectionBehavior.SelectRows)
        self.array_table.setSelectionMode(self.array_table.SelectionMode.SingleSelection)

        # Set up column sizing
        header = self.array_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)  # Index column
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)          # Value column
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents) # Type column

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

        # Add search for hex view too
        hex_search_layout = QHBoxLayout()
        self.hex_search_input = QLineEdit()
        self.hex_search_input.setPlaceholderText("Filter by index, hex, or ASCII...")
        self.hex_search_input.textChanged.connect(self._filter_hex_table)
        hex_search_layout.addWidget(QLabel("Search:"))
        hex_search_layout.addWidget(self.hex_search_input)

        # Add hex view jump
        hex_jump_layout = QHBoxLayout()
        self.hex_jump_to_index_input = QLineEdit()
        self.hex_jump_to_index_input.setPlaceholderText("Jump to index...")
        self.hex_jump_to_index_input.returnPressed.connect(self._jump_to_hex_index)
        btn_hex_jump = QPushButton("Go to Index")
        btn_hex_jump.clicked.connect(self._jump_to_hex_index)
        hex_jump_layout.addWidget(QLabel("Jump to:"))
        hex_jump_layout.addWidget(self.hex_jump_to_index_input)
        hex_jump_layout.addWidget(btn_hex_jump)

        l2.addLayout(hex_search_layout)
        l2.addLayout(hex_jump_layout)

        self.hex_table = QTableWidget()
        self.hex_table.setColumnCount(4)  # Added a color-coded column
        self.hex_table.setHorizontalHeaderLabels(["Index", "Hex", "ASCII", "Color"])
        self.hex_table.setAlternatingRowColors(True)
        self.hex_table.setSortingEnabled(True)

        # Set up hex table column sizing
        hex_header = self.hex_table.horizontalHeader()
        hex_header.setStretchLastSection(False)
        hex_header.setSectionResizeMode(0, hex_header.ResizeMode.ResizeToContents)  # Index
        hex_header.setSectionResizeMode(1, hex_header.ResizeMode.ResizeToContents)  # Hex
        hex_header.setSectionResizeMode(2, hex_header.ResizeMode.ResizeToContents)  # ASCII
        hex_header.setSectionResizeMode(3, hex_header.ResizeMode.ResizeToContents)  # Color

        l2.addWidget(QLabel("<b>Raw Data View (Hex/ASCII)</b>"))
        l2.addWidget(self.hex_table)
        self.stacked.addTab(page2, "Raw Hex")

        self.layout().addWidget(self.stacked)

        # Load existing values if known
        QTimer.singleShot(100, self._load_array_data)

        # Optimize layout for large arrays
        if size > 100:  # For large arrays, apply performance optimizations
            self._apply_large_array_optimizations()

    def _apply_large_array_optimizations(self):
        """Apply performance optimizations for large arrays."""
        # Reduce update frequency for large arrays
        self.array_table.setUpdatesEnabled(False)
        self.hex_table.setUpdatesEnabled(False)

        # Optimize table settings for large datasets
        self.array_table.setAlternatingRowColors(True)
        self.array_table.setWordWrap(False)
        self.array_table.setHorizontalScrollMode(self.array_table.ScrollMode.ScrollPerPixel)
        self.array_table.setVerticalScrollMode(self.array_table.ScrollMode.ScrollPerPixel)

        # Same for hex table
        self.hex_table.setAlternatingRowColors(True)
        self.hex_table.setWordWrap(False)
        self.hex_table.setHorizontalScrollMode(self.hex_table.ScrollMode.ScrollPerPixel)
        self.hex_table.setVerticalScrollMode(self.hex_table.ScrollMode.ScrollPerPixel)

        # Re-enable updates
        self.array_table.setUpdatesEnabled(True)
        self.hex_table.setUpdatesEnabled(True)

        # Force a repaint
        self.array_table.viewport().repaint()
        self.hex_table.viewport().repaint()

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

            # Apply layout optimizations after data is loaded
            self._optimize_table_layout(self.array_table)
            self._optimize_table_layout(self.hex_table)

    def set_scalar_value(self, val: float):
        if hasattr(self, 'scalar_input'):
            self.scalar_input.setValue(val)

    def set_array_value(self, index: int, val: float):
        if hasattr(self, 'array_table') and index < self.array_table.rowCount():
             self.array_table.setItem(index, 1, QTableWidgetItem(f"{val:.4f}"))

             # Determine data type and set color coding
             if val == int(val):
                 type_text = "int"
                 bg_color = QColor(240, 255, 240)  # Light green for integers
             else:
                 type_text = "float"
                 bg_color = QColor(240, 240, 255)  # Light blue for floats

             type_item = QTableWidgetItem(type_text)
             type_item.setBackground(bg_color)
             self.array_table.setItem(index, 2, type_item)

             # Also update Hex/Ascii if visible
             if hasattr(self, 'hex_table') and self.hex_table.rowCount() <= index:
                 self.hex_table.setRowCount(index + 1)

             if hasattr(self, 'hex_table'):
                 # Hex - improved formatting
                 hex_val = f"{int(val):02X}"
                 self.hex_table.setItem(index, 0, QTableWidgetItem(f"{index}"))
                 self.hex_table.setItem(index, 1, QTableWidgetItem(hex_val))

                 # ASCII - improved character display
                 try:
                     char_code = int(val) % 256  # Ensure it's in valid range
                     if 32 <= char_code <= 126:  # Printable ASCII range
                         char = chr(char_code)
                     elif char_code == 0:  # Null character
                         char = "·"  # Use middle dot to represent null
                     else:
                         char = "•"  # Use bullet for non-printable
                 except:
                     char = ""  # Use replacement character for errors

                 self.hex_table.setItem(index, 2, QTableWidgetItem(char))

                 # Add color coding based on value
                 color_item = QTableWidgetItem()
                 if char_code == 0:
                     color_item.setBackground(QColor(255, 200, 200))  # Light red for null
                     color_item.setText("NULL")
                 elif 32 <= char_code <= 126:
                     color_item.setBackground(QColor(200, 255, 200))  # Light green for printable
                     color_item.setText("PRINT")
                 else:
                     color_item.setBackground(QColor(255, 255, 200))  # Light yellow for non-printable
                     color_item.setText("NONP")

                 self.hex_table.setItem(index, 3, color_item)

                 # Apply alternating row colors to hex table if not already applied
                 if not self.hex_table.alternatingRowColors():
                     self._optimize_table_layout(self.hex_table)
                     self._optimize_table_layout(self.array_table)

    def _add_array_row(self, i: int):
        self.array_table.insertRow(i)
        idx_item = QTableWidgetItem(f"[{i}]")
        idx_item.setFlags(idx_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        val_item = QTableWidgetItem("...")
        type_item = QTableWidgetItem("float")  # Default type
        self.array_table.setItem(i, 0, idx_item)
        self.array_table.setItem(i, 1, val_item)
        self.array_table.setItem(i, 2, type_item)

    def _jump_to_index(self):
        """Jump to a specific index in the array table."""
        try:
            index = int(self.jump_to_index_input.text())
            if 0 <= index < self.array_table.rowCount():
                self.array_table.selectRow(index)
                self.array_table.scrollToItem(self.array_table.item(index, 0))
            else:
                QMessageBox.warning(self, "Invalid Index", f"Index must be between 0 and {self.array_table.rowCount()-1}")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid integer index")

    def _jump_to_hex_index(self):
        """Jump to a specific index in the hex table."""
        try:
            index = int(self.hex_jump_to_index_input.text())
            if 0 <= index < self.hex_table.rowCount():
                self.hex_table.selectRow(index)
                self.hex_table.scrollToItem(self.hex_table.item(index, 0))
            else:
                QMessageBox.warning(self, "Invalid Index", f"Index must be between 0 and {self.hex_table.rowCount()-1}")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid integer index")

    def _filter_array_table(self):
        """Filter the array table based on search input."""
        search_text = self.array_search_input.text().lower()

        for row in range(self.array_table.rowCount()):
            index_item = self.array_table.item(row, 0)
            value_item = self.array_table.item(row, 1)

            if not search_text:
                # Show all rows if no search text
                self.array_table.setRowHidden(row, False)
            else:
                # Hide row if neither index nor value contains search text
                index_match = search_text in index_item.text().lower() if index_item else False
                value_match = search_text in value_item.text().lower() if value_item else False
                self.array_table.setRowHidden(row, not (index_match or value_match))

    def _filter_hex_table(self):
        """Filter the hex table based on search input."""
        search_text = self.hex_search_input.text().lower()

        for row in range(self.hex_table.rowCount()):
            index_item = self.hex_table.item(row, 0)
            hex_item = self.hex_table.item(row, 1)
            ascii_item = self.hex_table.item(row, 2)

            if not search_text:
                # Show all rows if no search text
                self.hex_table.setRowHidden(row, False)
            else:
                # Hide row if none of the columns contain search text
                index_match = search_text in index_item.text().lower() if index_item else False
                hex_match = search_text in hex_item.text().lower() if hex_item else False
                ascii_match = search_text in ascii_item.text().lower() if ascii_item else False
                self.hex_table.setRowHidden(row, not (index_match or hex_match or ascii_match))

    def _optimize_table_layout(self, table_widget):
        """Apply responsive layout optimizations to a table widget."""
        # Enable alternating row colors for better readability
        table_widget.setAlternatingRowColors(True)

        # Set selection behavior
        table_widget.setSelectionBehavior(table_widget.SelectionBehavior.SelectRows)
        table_widget.setSelectionMode(table_widget.SelectionMode.SingleSelection)

        # Enable sorting
        table_widget.setSortingEnabled(True)

        # Set font for better readability
        font = QFont()
        font.setPointSize(9)
        table_widget.setFont(font)

        # Set row height for better spacing
        table_widget.verticalHeader().setDefaultSectionSize(24)

        # Apply custom styling
        table_widget.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                alternate-background-color: #f8f8f8;
            }
            QTableWidget::item:selected {
                background-color: #31a8ff;
                color: white;
            }
            QHeaderView::section {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f1f1f1, stop:1 #e6e6e6);
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)

        # Optimize for performance with large arrays
        table_widget.setWordWrap(False)
        table_widget.setTextElideMode(Qt.TextElideMode.ElideRight)

        # Set up scroll behavior for better performance
        table_widget.setVerticalScrollMode(table_widget.ScrollMode.ScrollPerPixel)
        table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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
            total_rows = self.array_table.rowCount()
            log.info("Saving array data for %s (%d elements)", base_name, total_rows)

            # Show progress bar for large arrays
            if total_rows > 50:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, total_rows)
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("Saving array data... %p%")

            for row in range(total_rows):
                # Update progress bar periodically
                if total_rows > 50 and row % 10 == 0:
                    self.progress_bar.setValue(row)
                    QApplication.processEvents()  # Allow UI to update

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

            # Complete progress bar
            if total_rows > 50:
                self.progress_bar.setValue(total_rows)
                QApplication.processEvents()
                # Brief pause to show completion
                QTimer.singleShot(200, lambda: self.progress_bar.setVisible(False))

            log.info("Wrote array values for %s", base_name)
        
        self.accept()
