from __future__ import annotations
import logging
import asyncio
import re
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QFrame,
    QCompleter,
    QDialog,
    QTextEdit,
    QMessageBox,
    QGroupBox,
    QComboBox,
    QDoubleSpinBox,
    QMenu,
    QApplication,
    QTabWidget,
    QInputDialog,
    QFormLayout,
    QDialogButtonBox,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon

from .variable_dialog import VariableDialog
from core.logic_engine import LogicBlock
from core.variable_store import VariableType
from .custom_dataref_dialog import CustomDatarefDialog
from .dataref_editor_dialog import DatarefEditorDialog
from .output_panel_array_edit import ArrayEditDialog
from core.dataref_writer import DatarefWriter

log = logging.getLogger(__name__)






# Constants for duplicated literals
CODE_HANDLED_FALSE = "    bool handled = false;\n\n"
CODE_HANDLED_TRUE = "        handled = true;\n"
CODE_CLOSE_BRACE = "    }\n"
CODE_CLOSE_BRACE_ELSE = "    } else {\n"
CODE_CLOSE_BRACE_NEWLINE = "    }\n\n"
CODE_IF_HANDLED = "\n    if (handled) {\n"
PLACEHOLDER_OUTPUT_KEY = "e.g., GEAR_LED"
WARNING_DUPLICATE_KEY = "Duplicate Output Key"


class CodeGeneratorDialog(QDialog):
    """Dialog to show generated Arduino code."""

    def __init__(
        self,
        mappings: Dict[str, str],
        dataref_types: Dict[str, str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Arduino Code Generator")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Copy this code into your Arduino IDE as a new sketch.\n"
            "It includes setup, loop, and handshake for full compatibility."
        )
        layout.addWidget(info)

        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setReadOnly(True)

        code = self._generate_code(mappings, dataref_types or {})
        self.text_edit.setPlainText(code)

        layout.addWidget(self.text_edit)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        layout.addWidget(copy_btn)

    def _copy_to_clipboard(self):
        # FIX: Use QApplication to access the clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

    def _generate_code(
        self, mappings: Dict[str, str], dataref_types: Dict[str, str]
    ) -> str:
        code = self._generate_header()
        code += self._generate_configuration()
        code += self._generate_pin_declarations(mappings)
        code += self._generate_helper_functions(mappings)
        code += self._generate_handle_set_function(mappings, dataref_types)
        code += self._generate_handle_command_function(mappings, dataref_types)
        code += self._generate_handle_array_element_function(mappings, dataref_types)
        code += self._generate_process_line_function(mappings, dataref_types)
        code += self._generate_setup_function(mappings)
        code += self._generate_main_loop_function()

        return code

    def _generate_header(self) -> str:
        code = "// --- Auto-Generated Arduino Code ---\n"
        code += "#include <Arduino.h>\n\n"
        return code

    def _generate_configuration(self) -> str:
        code = "// --- Configuration ---\n"
        code += "const int BAUD_RATE = 115200;\n"
        code += 'const char* DEVICE_NAME = "MyXPDevice";\n'
        code += 'const char* FW_VERSION = "1.0";\n'
        code += 'const char* BOARD_TYPE = "UNO";\n\n'
        return code

    def _generate_pin_declarations(self, mappings: Dict[str, str]) -> str:
        code = "// --- Pin Definitions & State ---\n"
        for key in mappings.values():
            code += f"const int {key}_PIN = XX;  // TODO: Define your pin for {key}\n"
            code += f"float {key}_VAL = 0.0;    // Internal state for {key}\n"
        code += "\n"
        return code

    def _generate_helper_functions(self, mappings: Dict[str, str]) -> str:
        code = "// --- Helper Functions ---\n"
        code += "void runSelfTest() {\n"
        code += '    Serial.println("STATUS Running Test Sequence...");\n'
        for key in mappings.values():
            code += f"    // Test {key}\n"
            code += f'    Serial.print("STATUS Testing "); Serial.println("{key}");\n'
            code += f"    // TODO: Add your hardware test for {key} here\n"
            code += f"    // Example: digitalWrite({key}_PIN, HIGH); delay(200); digitalWrite({key}_PIN, LOW);\n"
        code += '    Serial.println("STATUS Test Complete.");\n'
        code += "}\n\n"
        return code

    def _generate_handle_set_function(
        self, mappings: Dict[str, str], dataref_types: Dict[str, str]
    ) -> str:
        code = "void handleSet(String key, String valueStr) {\n"
        code += CODE_HANDLED_FALSE
        for dataref, key_name in mappings.items():
            dataref_type = dataref_types.get(dataref, "")
            code += f"    // Dataref: {dataref} (Type: {dataref_type})\n"
            code += f'    if (key == "{key_name}") {{\n'
            if dataref_type == "command":
                code += (
                    "        // Command dataref - execute instead of setting value\n"
                )
                code += f"        // TODO: Add command execution logic for {key_name}\n"
                code += '        Serial.print("STATUS Executed command: "); Serial.println(key);\n'
            elif "[" in dataref_type:
                code += "        // Array dataref - handle as comma-separated values or single value\n"
                code += "        if (valueStr.indexOf(',') != -1) {\n"
                code += "            // Multiple values: val1,val2,val3\n"
                code += f"            // TODO: Parse and handle array values for {key_name}\n"
                code += f'            Serial.print("STATUS Updated array {key_name} with multiple values: "); Serial.println(valueStr);\n'
                code += "        }} else {{\n"
                code += "            // Single value to first element\n"
                code += "            float value = valueStr.toFloat();\n"
                code += f"            {key_name}_VAL = value;\n"
                code += f"            // TODO: Add your array logic for {key_name}[0] here\n"
                code += f'            Serial.print("STATUS Updated {key_name}[0] = "); Serial.println(value);\n'
                code += "        }}\n"
            elif dataref_type in ["string", "byte"]:
                code += "        // String/byte dataref\n"
                code += f"        // TODO: Handle string value for {key_name}\n"
                code += f'        Serial.print("STATUS Updated string {key_name} = "); Serial.println(valueStr);\n'
            else:
                code += "        // Scalar dataref (int, float, double, bool)\n"
                code += "        float value = valueStr.toFloat();\n"
                code += f"        {key_name}_VAL = value; // Update internal state\n"
                code += f"        // TODO: Add your logic for {key_name} here\n"
                code += f"        // Example: digitalWrite({key_name}_PIN, value > 0.5 ? HIGH : LOW);\n"
                code += f'        Serial.print("STATUS Updated {key_name} = "); Serial.println(value);\n'
            code += CODE_HANDLED_TRUE
            code += CODE_CLOSE_BRACE
        code += CODE_IF_HANDLED
        code += '        Serial.print("ACK "); Serial.print(key); Serial.print(" "); Serial.println(valueStr);\n'
        code += CODE_CLOSE_BRACE
        code += "}\n\n"
        return code

    def _generate_handle_command_function(
        self, mappings: Dict[str, str], dataref_types: Dict[str, str]
    ) -> str:
        code = "void handleCommand(String key) {\n"
        code += CODE_HANDLED_FALSE
        for dataref, key_name in mappings.items():
            dataref_type = dataref_types.get(dataref, "")
            if dataref_type == "command":
                code += f"    // Command: {dataref}\n"
                code += f'    if (key == "{key_name}") {{\n'
                code += f"        // TODO: Execute command for {key_name}\n"
                code += f'        // Example: if (key == "{key_name}") {{ toggleLandingGear(); }}\n'
                code += '        Serial.print("STATUS Executed command: "); Serial.println(key);\n'
                code += CODE_HANDLED_TRUE
                code += CODE_CLOSE_BRACE
        code += CODE_IF_HANDLED
        code += '        Serial.print("ACK CMD "); Serial.println(key);\n'
        code += CODE_CLOSE_BRACE_ELSE
        code += (
            '        Serial.print("ERROR Unknown command: "); Serial.println(key);\n'
        )
        code += CODE_CLOSE_BRACE
        code += "}\n\n"
        return code

    def _generate_handle_array_element_function(
        self, mappings: Dict[str, str], dataref_types: Dict[str, str]
    ) -> str:
        code = "void handleArrayElement(String baseKey, int index, String valueStr) {\n"
        code += CODE_HANDLED_FALSE
        for dataref, key_name in mappings.items():
            dataref_type = dataref_types.get(dataref, "")
            if "[" in dataref_type:
                code += f"    // Array element: {dataref}[index]\n"
                code += f'    if (baseKey == "{key_name}") {{\n'
                code += "        float value = valueStr.toFloat();\n"
                code += (
                    f"        // TODO: Handle array element {key_name}[index] = value\n"
                )
                code += f'        Serial.print("STATUS Updated {key_name}["); Serial.print(index); Serial.print("] = "); Serial.println(value);\n'
                code += CODE_HANDLED_TRUE
                code += CODE_CLOSE_BRACE
        code += CODE_IF_HANDLED
        code += '        Serial.print("ACK "); Serial.print(baseKey); Serial.print("["); Serial.print(index); Serial.print("] "); Serial.println(valueStr);\n'
        code += CODE_CLOSE_BRACE_ELSE
        code += '        Serial.print("ERROR Unknown array key: "); Serial.println(baseKey);\n'
        code += CODE_CLOSE_BRACE
        code += "}\n\n"
        return code

    def _generate_process_line_function(
        self, mappings: Dict[str, str], dataref_types: Dict[str, str]
    ) -> str:
        code = "void processLine(String line) {\n"
        code += "    line.trim();\n\n"
        code += "    // --- HANDSHAKE ---\n"
        code += '    if (line == "HELLO") {\n'
        code += '        Serial.print("XPDR;fw="); Serial.print(FW_VERSION);\n'
        code += '        Serial.print(";board="); Serial.print(BOARD_TYPE);\n'
        code += '        Serial.print(";name="); Serial.println(DEVICE_NAME);\n'
        code += CODE_CLOSE_BRACE_NEWLINE
        code += "    // --- MONITOR COMMANDS ---\n"
        code += '    else if (line.equalsIgnoreCase("LIST")) {\n'
        code += '        Serial.println("STATUS Available Keys:");\n'
        for dataref, key in mappings.items():
            dataref_type = dataref_types.get(dataref, "")
            type_info = f" [{dataref_type}]" if dataref_type else ""
            code += f'        Serial.println("STATUS - {key} (Dataref: {dataref}{type_info})");\n'
        code += CODE_CLOSE_BRACE_NEWLINE
        code += '    else if (line.equalsIgnoreCase("STATUS")) {\n'
        code += '        Serial.println("STATUS Current Values:");\n'
        for key in mappings.values():
            code += f'        Serial.print("STATUS [{key}]: "); Serial.println({key}_VAL);\n'
        code += CODE_CLOSE_BRACE_NEWLINE
        code += '    else if (line.equalsIgnoreCase("TEST")) {\n'
        code += "        runSelfTest();\n"
        code += CODE_CLOSE_BRACE_NEWLINE
        code += "    // --- DATA UPDATES (SET) ---\n"
        code += '    else if (line.startsWith("SET ")) {\n'
        code += "        int firstSpace = line.indexOf(' ');\n"
        code += "        int secondSpace = line.lastIndexOf(' ');\n"
        code += "        if (firstSpace > 0 && secondSpace > firstSpace) {\n"
        code += (
            "            String key = line.substring(firstSpace + 1, secondSpace);\n"
        )
        code += "            String valueStr = line.substring(secondSpace + 1);\n"
        code += "            handleSet(key, valueStr);\n"
        code += "        }\n"
        code += CODE_CLOSE_BRACE_NEWLINE
        code += "    // --- COMMAND EXECUTION ---\n"
        code += '    else if (line.startsWith("CMD ")) {\n'
        code += "        String key = line.substring(4);\n"
        code += "        handleCommand(key);\n"
        code += CODE_CLOSE_BRACE_NEWLINE
        code += "    // --- ARRAY ELEMENT ACCESS ---\n"
        code += "    else if (line.indexOf('[') != -1 && line.indexOf(']') != -1 && line.indexOf(\"SET \") != -1) {\n"
        code += "        // Handle array element: SET KEY[index] value\n"
        code += '        int setPos = line.indexOf("SET ");\n'
        code += "        int bracketPos = line.indexOf('[', setPos);\n"
        code += "        int endBracketPos = line.indexOf(']', bracketPos);\n"
        code += "        if (bracketPos != -1 && endBracketPos != -1) {\n"
        code += "            String baseKey = line.substring(setPos + 4, bracketPos);\n"
        code += "            String indexStr = line.substring(bracketPos + 1, endBracketPos);\n"
        code += "            String valueStr = line.substring(endBracketPos + 2);\n"
        code += "            int index = indexStr.toInt();\n"
        code += "            handleArrayElement(baseKey, index, valueStr);\n"
        code += "        }\n"
        code += CODE_CLOSE_BRACE_NEWLINE
        code += "    // --- CUSTOM COMMANDS ---\n"
        code += "    else {\n"
        code += "        // Echo back or handle custom commands here\n"
        code += '        Serial.print("STATUS Echo: "); Serial.println(line);\n'
        code += '        // Example: if (line == "MY_CMD") { doSomething(); }\n'
        code += CODE_CLOSE_BRACE
        code += "}\n\n"
        return code

    def _generate_setup_function(self, mappings: Dict[str, str]) -> str:
        code = "void setup() {\n"
        code += "    Serial.begin(BAUD_RATE);\n"
        code += "    // Initialize pins\n"
        for key in mappings.values():
            code += f"    pinMode({key}_PIN, OUTPUT);\n"
        code += "}\n\n"
        return code

    def _generate_main_loop_function(self) -> str:
        code = "void loop() {\n"
        code += "    if (Serial.available()) {\n"
        code += "        String line = Serial.readStringUntil('\\n');\n"
        code += "        processLine(line);\n"
        code += CODE_CLOSE_BRACE
        code += "}\n"
        return code


class OutputPanel(QWidget):
    """
    Unified Output Configuration Panel.
    - Search & Subscribe to Datarefs
    - Assign Universal Keys (e.g. GEAR_LED)
    - Monitor Live Values
    - Generate Firmware Code
    """

    def __init__(
        self,
        dataref_manager,
        xplane_conn,
        arduino_manager,
        variable_store=None,
        logic_engine=None,
    ):
        super().__init__()
        self.dataref_manager = dataref_manager
        self.xplane_conn = xplane_conn
        self.arduino_manager = arduino_manager
        self.variable_store = variable_store
        self.logic_engine = logic_engine  # NEW: Logic Engine for variables persistence
        self._subscribed_datarefs = {}  # dataref -> row_index

        # Initialize DatarefWriter for handling different dataref types
        self.dataref_writer = DatarefWriter(xplane_conn, dataref_manager)
        self._dataref_list = dataref_manager.get_all_dataref_names()

        # Initialize tasks list to prevent premature garbage collection
        self._tasks = []

        self._setup_ui()
        self._connect_signals()

        # Timer to update live values (debounce UI updates)
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_live_values)
        self._update_timer.start(100)  # 10Hz UI update

        # Temp storage for live values
        self._live_values = {}

        # Connect variable store to receive updates for virtual variables
        if self.variable_store:
            self.variable_store.register_listener(self._on_variable_update)

        # Connect to X-Plane connection for live value updates
        if hasattr(self.xplane_conn, 'register_dataref_listener'):
            self.xplane_conn.register_dataref_listener(self._on_xplane_dataref_update)

    def _format_dataref_description_from_name(self, name: str) -> str:
        """Format dataref description from its name."""
        s = name.replace("/", " ").replace("_", " ")
        s = re.sub(r"\\s+", " ", s).strip()
        parts = s.split(" ")
        parts = [p.capitalize() for p in parts if p]
        return " ".join(parts)

    def _compose_description_cell(self, display_name: str, info: dict | None, data_type: str, full_text: bool = False) -> tuple[str, str]:
        """Compose the description cell text and tooltip from DB info with fallbacks.
        Returns (cell_text, tooltip_text). Tooltip receives the full text prior to truncation.
        """
        base_name = display_name.split("[")[0] if "[" in display_name else display_name
        info = info or {}
        db_description = (info.get("description") or "").strip() if isinstance(info, dict) else ""
        # Normalize placeholders to trigger fallback
        if db_description.lower() in {"custom dataref", "custom datarefs", "unknown", "n/a"}:
            db_description = ""
        units = (info.get("units") or "").strip() if isinstance(info, dict) else ""
        desc_core = db_description if db_description else format_dataref_description_from_name(base_name)
        if units:
            desc_core = f"{desc_core} ({units})"

        # Truncate for cell view if needed
        max_desc_length = 80
        if full_text or len(desc_core) <= max_desc_length:
            truncated = desc_core
        else:
            truncated = desc_core[:max_desc_length] + "..."

        writable = bool(isinstance(info, dict) and info.get("writable", False))
        parts = []
        if data_type:
            parts.append(f"[{data_type}]")
        parts.append(truncated)
        if writable:
            parts.append("[WRITABLE]")
        cell_text = " ".join(parts)
        return cell_text, desc_core

    def _on_xplane_dataref_update(self, dataref_name: str, value):
        """Handle live dataref updates from X-Plane connection."""
        if dataref_name in self._subscribed_datarefs:
            row = self._subscribed_datarefs[dataref_name]
            if row < self.table.rowCount():
                # Update the value in the table
                value_item = self.table.item(row, 2)
                if value_item:
                    formatted_value = self._format_value(dataref_name, value, "")
                    value_item.setText(formatted_value)

                    # Update color based on value
                    if isinstance(value, (int, float)) and value >= 0.5:
                        value_item.setForeground(QColor("#28a745"))  # Green
                    else:
                        value_item.setForeground(QColor("#6c757d"))  # Gray

    def _update_live_values(self):
        """Update live values in the table from stored values."""
        for dataref_name, row in self._subscribed_datarefs.items():
            if row < self.table.rowCount():
                # Get the current value from stored live values
                current_value = self._live_values.get(dataref_name)
                if current_value is not None:
                    # Update the value in the table
                    value_item = self.table.item(row, 2)
                    if value_item:
                        formatted_value = self._format_value(dataref_name, current_value, "")
                        value_item.setText(formatted_value)

                        # Update color based on value
                        if isinstance(current_value, (int, float)) and current_value >= 0.5:
                            value_item.setForeground(QColor("#28a745"))  # Green
                        else:
                            value_item.setForeground(QColor("#6c757d"))  # Gray

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the table."""
        # Ctrl+A to select all rows
        select_all_shortcut = QAction("Select All", self)
        select_all_shortcut.setShortcut("Ctrl+A")
        select_all_shortcut.triggered.connect(self._select_all_rows)
        self.addAction(select_all_shortcut)

        # Delete key to remove selected rows
        delete_shortcut = QAction("Delete Selected", self)
        delete_shortcut.setShortcut("Delete")
        delete_shortcut.triggered.connect(self._delete_selected_rows)
        self.addAction(delete_shortcut)

        # Add to table as well for better UX
        self.table.addAction(select_all_shortcut)
        self.table.addAction(delete_shortcut)

        # Add more keyboard shortcuts
        # Ctrl+Shift+A to select all in datarefs table
        select_all_datarefs_shortcut = QAction("Select All Datarefs", self)
        select_all_datarefs_shortcut.setShortcut("Ctrl+Shift+A")
        select_all_datarefs_shortcut.triggered.connect(lambda: self.table.selectAll())
        self.table.addAction(select_all_datarefs_shortcut)

    def _select_all_rows(self):
        """Select all rows in the table."""
        self.table.selectAll()

    def _delete_selected_rows(self):
        """Delete all selected rows in the table."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        # Get all selected rows
        selected_rows = set()
        for range_obj in selected_ranges:
            for row in range(range_obj.topRow(), range_obj.bottomRow() + 1):
                selected_rows.add(row)

        # Convert to sorted list in reverse order to avoid index shifting issues
        rows_to_delete = sorted(list(selected_rows), reverse=True)

        # Delete rows in reverse order
        for row in rows_to_delete:
            if row < self.table.rowCount():
                # Get the dataref name for removal from the subscription map
                name_item = self.table.item(row, 0)
                if name_item:
                    dataref_name = name_item.text()
                    if dataref_name in self._subscribed_datarefs:
                        del self._subscribed_datarefs[dataref_name]

                # Remove the row from the table
                self.table.removeRow(row)

        log.info(f"Deleted {len(rows_to_delete)} selected rows")

    def _show_context_menu(self, position):
        """Show context menu for bulk operations."""
        # Determine which table was clicked
        sender = self.sender()
        if sender == self.table:
            target_table = self.table
        elif sender == self.vars_table:
            target_table = self.vars_table
        else:
            return

        menu = QMenu(self)

        # Add actions based on selection
        selected_ranges = target_table.selectedRanges()
        has_selection = len(selected_ranges) > 0

        if has_selection:
            # Count selected rows
            selected_count = 0
            for range_obj in selected_ranges:
                selected_count += (range_obj.bottomRow() - range_obj.topRow() + 1)

            # Select All action
            select_all_action = QAction(f"Select All ({target_table.rowCount()} rows)", self)
            select_all_action.triggered.connect(lambda: target_table.selectAll())
            menu.addAction(select_all_action)

            menu.addSeparator()

            # Delete action
            delete_action = QAction(f"Delete Selected ({selected_count} rows)", self)
            delete_action.triggered.connect(lambda: self._delete_selected_rows_from_table(target_table))
            menu.addAction(delete_action)

            # Add other bulk operations if needed
            if sender == self.table:  # Only for datarefs table
                # Add more actions for dataref operations
                pass
        else:
            # No selection - just show select all
            select_all_action = QAction(f"Select All ({target_table.rowCount()} rows)", self)
            select_all_action.triggered.connect(lambda: target_table.selectAll())
            menu.addAction(select_all_action)

        menu.exec(target_table.viewport().mapToGlobal(position))

    def _delete_selected_rows_from_table(self, table_widget):
        """Delete selected rows from a specific table."""
        selected_ranges = table_widget.selectedRanges()
        if not selected_ranges:
            return

        # Get all selected rows
        selected_rows = set()
        for range_obj in selected_ranges:
            for row in range(range_obj.topRow(), range_obj.bottomRow() + 1):
                selected_rows.add(row)

        # Convert to sorted list in reverse order to avoid index shifting issues
        rows_to_delete = sorted(list(selected_rows), reverse=True)

        # Choose the appropriate deletion method based on which table
        if table_widget == self.table:  # Datarefs table
            # Show confirmation dialog for bulk operations
            reply = QMessageBox.question(
                self,
                "Confirm Bulk Delete",
                f"Are you sure you want to delete {len(rows_to_delete)} selected dataref(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                for row in rows_to_delete:
                    if row < table_widget.rowCount():
                        # Get the dataref name for removal from the subscription map
                        name_item = table_widget.item(row, 0)
                        if name_item:
                            dataref_name = name_item.text()

                            # Clean up subscriptions and mappings
                            if dataref_name in self._subscribed_datarefs:
                                del self._subscribed_datarefs[dataref_name]

                            # Check if this is an array element and handle base array cleanup
                            array_match = re.match(r"^(.+)\[(\d+)\]$", dataref_name)
                            if array_match:
                                base_name = array_match.group(1)
                                # Check if there are any other elements of this array still subscribed
                                other_elements_exist = any(
                                    re.match(rf"^{re.escape(base_name)}\[\d+\]$", key) and key != dataref_name
                                    for key in self._subscribed_datarefs.keys()
                                )

                                # Only unsubscribe from the base array if no other elements of it are still subscribed
                                if not other_elements_exist:
                                    task = asyncio.create_task(
                                        self.xplane_conn.unsubscribe_dataref(base_name)
                                    )
                                    self._tasks.append(task)  # Prevent garbage collection
                                    log.info("Unsubscribed from array dataref: %s", base_name)
                            else:
                                # Regular dataref (non-array)
                                task = asyncio.create_task(self.xplane_conn.unsubscribe_dataref(dataref_name))
                                self._tasks.append(task)  # Prevent garbage collection

                            # Remove from Arduino manager mappings
                            self.arduino_manager.set_universal_mapping(dataref_name, "")

                            if hasattr(self.arduino_manager, "remove_monitor"):
                                self.arduino_manager.remove_monitor(dataref_name)

                        # Remove the row from the table
                        table_widget.removeRow(row)

                # Re-index the subscription map after deletions
                self._reindex_subscribed_datarefs()
        elif table_widget == self.vars_table:  # Variables table
            # For variables table, we might want to handle differently
            for row in rows_to_delete:
                if row < table_widget.rowCount():
                    # Get the variable name
                    name_item = table_widget.item(row, 0)
                    if name_item:
                        var_name = name_item.text()
                        # Call the appropriate deletion method for variables
                        self._delete_variable_by_name(var_name)

        log.info(f"Deleted {len(rows_to_delete)} rows from table")

    def _parse_array_size(self, type_str: str) -> int:
        """Parse total array size from type string (supports multi-dim like 'float[8][4]')."""
        if not type_str:
            return 0
        import re

        dims = [int(n) for n in re.findall(r"\[(\d+)\]", type_str)]
        if not dims:
            return 0
        total = 1
        for d in dims:
            total *= d
        return total

    def _test_led_state_array(self):
        """Test method for LED_STATE_ARRAY functionality."""
        # This method can be called to test LED_STATE_ARRAY expansion
        test_arrays = [
            "LED_STATE_ARRAY",
            "sim/cockpit/electrical/led_states",  # hypothetical example
        ]

        for array_name in test_arrays:
            info = self.dataref_manager.get_dataref_info(array_name)
            if info:
                dtype = info.get("type", "")
                size = self._parse_array_size(dtype)
                if size > 0:
                    log.info(f"Found array {array_name} with size {size}")
                    # Expand the array elements
                    base = array_name.split("[")[0]
                    for idx in range(size):
                        elem_name = f"{base}[{idx}]"
                        log.info(f"  Element: {elem_name}")
                    return True

        # If no predefined LED array found, try common patterns
        all_datarefs = self.dataref_manager.get_all_dataref_names()
        led_arrays = [name for name in all_datarefs if "led" in name.lower() and "[" in name]

        if led_arrays:
            log.info(f"Found potential LED arrays: {led_arrays[:5]}")  # Show first 5
            return True

        log.info("No LED arrays found in database")
        return False

    def _populate_live_monitor(self, datarefs):
        """Populate live monitor with array expansion."""
        # datarefs: list of dicts with at least {name, type, value}
        self.table.setRowCount(0)  # Clear existing rows
        self._subscribed_datarefs.clear()  # Clear mapping

        for dr in datarefs:
            name = dr.get("name", "")
            type_str = dr.get("type", "")
            size = self._parse_array_size(type_str)

            if size >= 1:
                base = name.split("[")[0]  # Extract base name from array notation
                log.debug(
                    f"Expanding array {name} (type: {type_str}, size: {size}) -> base: {base}"
                )
                for idx in range(size):
                    elem_name = f"{base}[{idx}]"
                    value = self._get_value_for_dataref_element(dr, idx)
                    log.debug(f"  Creating row for element: {elem_name} = {value}")
                    # Pass the original dataref info to preserve type and other metadata
                    self._add_live_row(elem_name, type_str, value, original_info=dr)
            else:
                value = dr.get("value", 0.0)
                log.debug(f"  Creating row for scalar: {name} = {value}")
                self._add_live_row(name, type_str, value, original_info=dr)

    def _add_visual_indicator_for_array(self, name_item: QTableWidgetItem):
        """Add visual indicator for array elements in the table."""
        # Check if this is an array element
        if "[" in name_item.text() and "]" in name_item.text():
            # Add a visual indicator to the name item
            name_item.setText(f"📋 {name_item.text()}")
            # Set a different background color for array elements
            name_item.setBackground(QColor(248, 248, 255))  # Light blue tint for arrays

    def _add_live_row(self, display_name, data_type, value, original_info=None):
        """Add a single row to the live monitor."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Add dataref name
        name_item = QTableWidgetItem(display_name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Add visual indicator for array elements
        self._add_visual_indicator_for_array(name_item)
        self.table.setItem(row, 0, name_item)

        # Add description (real data from DB if available, else derived from name)
        # Use original_info if provided, otherwise get from dataref manager
        # Always prefer canonical DB lookup; use base name for arrays
        base_name = display_name.split("[")[0] if "[" in display_name else display_name
        info = self.dataref_manager.get_dataref_info(base_name) or self.dataref_manager.get_dataref_info(display_name) or {}
        # If original_info exists, merge missing fields from it (non-destructive)
        if original_info and isinstance(original_info, dict):
            for k, v in original_info.items():
                if k not in info:
                    info[k] = v

        # Compose description using unified builder and mark finalized
        cell_text, tooltip_text = self._compose_description_cell(display_name, info, data_type)
        desc_item = QTableWidgetItem(cell_text)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        try:
            desc_item.setData(Qt.ItemDataRole.UserRole, {"finalized_desc": True})
        except Exception:
            pass
        self.table.setItem(row, 1, desc_item)
        desc_item.setToolTip(tooltip_text)

        # Add live value
        value_item = QTableWidgetItem(f"{value:.4f}")
        value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 2, value_item)

        # Add modify button
        is_command = data_type == "command"
        is_complex = "[" in data_type or "string" in data_type or "byte" in data_type
        is_array = self._is_array_dataref(display_name, data_type)
        btn_text = (
            "EXECUTE" if is_command
            else ("Inspect/Edit Array" if is_array else "Inspect/Edit" if is_complex else "Write")
        )
        modify_btn = QPushButton(btn_text)
        modify_btn.clicked.connect(lambda _, r=row: self._modify_value(r))
        self.table.setCellWidget(row, 3, modify_btn)

        # Add output key input
        key_input = QLineEdit()
        key_input.setPlaceholderText(PLACEHOLDER_OUTPUT_KEY)
        self.table.setCellWidget(row, 4, key_input)

        # Add delete button
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda _, n=display_name: self._remove_row(n))
        self.table.setCellWidget(row, 5, del_btn)

        # Store mapping from name to row
        self._subscribed_datarefs[display_name] = row

    def _get_value_for_dataref_element(self, dataref_dict, index):
        """Get the value for a specific array element."""
        value = dataref_dict.get("value", 0.0)
        if isinstance(value, (list, tuple)) and index < len(value):
            return value[index]
        elif isinstance(value, str) and "," in value:
            # Handle comma-separated values as array
            try:
                values = [float(x.strip()) for x in value.split(",")]
                return values[index] if index < len(values) else 0.0
            except (ValueError, IndexError):
                return 0.0
        else:
            # For scalar values or if index is out of bounds, return default
            return 0.0

    def _setup_ui(self):
        # Create a tab widget to separate Datarefs and Variables
        tab_widget = QTabWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(tab_widget)

        # Datarefs tab (original functionality)
        datarefs_widget = QWidget()
        datarefs_layout = QVBoxLayout(datarefs_widget)

        # --- Top Bar: Search & Add ---
        top_group = QGroupBox("Add Output")
        top_layout = QHBoxLayout(top_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "🔍 Search Datarefs (e.g. 'gear', 'flap', 'autopilot')..."
        )
        self.search_input.setClearButtonEnabled(True)

        # Autocomplete
        completer = QCompleter(self._dataref_list)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setMaxVisibleItems(20)
        self.search_input.setCompleter(completer)

        top_layout.addWidget(self.search_input, 3)

        self.add_btn = QPushButton("Subscribe")
        self.add_btn.clicked.connect(self._subscribe_manual)
        top_layout.addWidget(self.add_btn)

        self.add_cust_btn = QPushButton("➕ Add Custom Dataref")
        self.add_cust_btn.clicked.connect(self._add_custom_dataref)
        top_layout.addWidget(self.add_cust_btn)

        datarefs_layout.addWidget(top_group)

        # --- Main Table ---
        self.table = QTableWidget(0, 6)
        headers = [
            "X-Plane Dataref",
            "Description",
            "Live Value",
            "Action / Edit",
            "Output Key (Device ID)",
            "Delete",
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Detailed tooltips for beginners
        tooltips = [
            "The internal name of the X-Plane data (e.g. sim/gear/deploy_ratio)",
            "Detailed information about what this dataref represents",
            "Real-time value received from X-Plane",
            "Actions: Trigger X-Plane command or edit complex values (Arrays/Strings)",
            "The short KEY you'll use in your Arduino code (e.g. GEAR_LED). Any device listening for this key will receive the data.",
            "Remove this dataref from your output list",
        ]
        for i, tooltip in enumerate(tooltips):
            item = self.table.horizontalHeaderItem(i)
            if item:
                item.setToolTip(tooltip)

        # Styling
        header = self.table.horizontalHeader()
        header.setSectionsMovable(True)  # Allow reordering
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )  # Allow manual resize

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Dataref name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Interactive
        )  # Value (can be long for arrays)
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )  # Action / Edit
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Key input
        self.table.setColumnWidth(4, 150)
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )  # Delete

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._on_row_double_clicked)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # NEW: Show description popup on cell click
        self.table.cellClicked.connect(self._on_cell_clicked)

        # Enable multi-selection
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

        # Context menu for bulk operations
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        datarefs_layout.addWidget(self.table)

        # --- Footer ---
        footer_layout = QHBoxLayout()

        info_label = QLabel(
            "💡 <b>Tip:</b> Assign an 'Output Key' (e.g. GEAR_LED). "
            "Any connected microcontroller listening for that key will react."
        )
        info_label.setStyleSheet("color: #666;")
        footer_layout.addWidget(info_label)

        self.gen_code_btn = QPushButton("📝 Generate Arduino Code")
        self.gen_code_btn.clicked.connect(self._generate_code)
        footer_layout.addWidget(self.gen_code_btn)

        datarefs_layout.addLayout(footer_layout)

        # Add datarefs tab to the tab widget
        tab_widget.addTab(datarefs_widget, "Datarefs")

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Variables tab (Logic Variables / Virtual Datarefs)
        vars_widget = QWidget()
        vars_layout = QVBoxLayout(vars_widget)

        # Variables section header
        vars_header = QLabel("Logic Variables / Virtual Datarefs")
        vars_header.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; background: #f0f0f0; border-radius: 4px;"
        )
        vars_layout.addWidget(vars_header)

        # Variables description
        vars_desc = QLabel(
            "Create virtual variables that compute values based on logic conditions. "
            "Variables can read from datarefs and write to other datarefs based on rules."
        )
        vars_desc.setWordWrap(True)
        vars_desc.setStyleSheet("color: #555; padding: 5px;")
        vars_layout.addWidget(vars_desc)

        # Variables table
        self.vars_table = QTableWidget(0, 8)
        var_headers = [
            "Variable Name",
            "Description",
            "Value",
            "Status",
            "Action / Edit",
            "Prop / Size",
            "Output Key",
            "Delete",
        ]
        self.vars_table.setColumnCount(len(var_headers))
        self.vars_table.setHorizontalHeaderLabels(var_headers)
        # Detailed tooltips for beginners
        var_tooltips = [
            "User-defined name for this virtual logic variable",
            "Description of what this logic handles",
            "Current live state (0 or 1)",
            "Shows if the logic is currently active",
            "Modify the logic rules or delete this variable",
            "Properties/Size: Displays data format and size if applicable",
            "Output ID Key: Mapping for hardware communication (Arduino/ESP32)",
            "Permanently remove this variable",
        ]
        for i, tooltip in enumerate(var_tooltips):
            item = self.vars_table.horizontalHeaderItem(i)
            if item:
                item.setToolTip(tooltip)

        # Styling for variables table
        vars_header_view = self.vars_table.horizontalHeader()
        vars_header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        vars_header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        vars_header_view.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        vars_header_view.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        vars_header_view.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        vars_header_view.setSectionResizeMode(
            5, QHeaderView.ResizeMode.Interactive
        )  # Output Key
        vars_header_view.setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents
        )

        self.vars_table.setAlternatingRowColors(True)
        self.vars_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.vars_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vars_table.customContextMenuRequested.connect(self._on_context_menu)
        vars_layout.addWidget(self.vars_table)

        # Variables controls
        vars_controls_layout = QHBoxLayout()

        add_var_btn = QPushButton("Add Variable Logic and Conditions")
        add_var_btn.clicked.connect(self._add_variable)
        vars_controls_layout.addWidget(add_var_btn)

        edit_var_btn = QPushButton("Edit Selected")
        edit_var_btn.clicked.connect(self._edit_selected_variable)
        vars_controls_layout.addWidget(edit_var_btn)

        delete_var_btn = QPushButton("Delete Selected")
        delete_var_btn.clicked.connect(self._delete_selected_variable)
        vars_controls_layout.addWidget(delete_var_btn)

        vars_controls_layout.addStretch()
        vars_layout.addLayout(vars_controls_layout)

        # Add variables tab to the tab widget
        tab_widget.addTab(vars_widget, "Variables")

    def _add_custom_dataref(self):
        """Open dialog to add a custom dataref."""
        if not self.dataref_manager:
            QMessageBox.warning(self, "Error", "Dataref manager not available.")
            return

        dialog = CustomDatarefDialog(self.dataref_manager, self)
        if dialog.exec():
            QMessageBox.information(
                self,
                "Success",
                "Custom dataref added. It will now appear in all search helpers.",
            )
            # TRIGGER REFRESH of all search completers across the app!
            main_win = self.window()
            if hasattr(main_win, "refresh_search_helpers"):
                main_win.refresh_search_helpers()
            else:
                self._update_autocomplete()

    def _add_sequence_events(self):
        """Open dialog to add a sequence event."""
        # Create a dialog for sequence events
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Sequence Event")
        dialog.setMinimumWidth(600)

        layout = QVBoxLayout(dialog)

        # Form for sequence event details
        form_layout = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter sequence name")
        form_layout.addRow("Name:", name_input)

        desc_input = QLineEdit()
        desc_input.setPlaceholderText("Enter sequence description")
        form_layout.addRow("Description:", desc_input)

        key_input = QLineEdit()
        key_input.setPlaceholderText("Enter Output ID KEY (for hardware)")
        form_layout.addRow("Output ID KEY:", key_input)

        layout.addLayout(form_layout)

        # Add sequence actions section
        seq_header = QLabel("Sequence Actions:")
        seq_header.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(seq_header)

        # Table for sequence actions
        seq_table = QTableWidget(0, 3)
        seq_table.setHorizontalHeaderLabels(["Dataref/Variable", "Value", "Actions"])
        seq_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        seq_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        seq_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(seq_table)

        # Buttons for sequence actions
        seq_btn_layout = QHBoxLayout()

        add_action_btn = QPushButton("Add Action")
        add_action_btn.clicked.connect(lambda: self._add_sequence_action_row(seq_table))
        seq_btn_layout.addWidget(add_action_btn)

        seq_btn_layout.addStretch()
        layout.addLayout(seq_btn_layout)

        # Dialog buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Create sequence event object
            sequence_event = {
                "name": name_input.text().strip(),
                "description": desc_input.text().strip(),
                "key": key_input.text().strip(),
                "actions": [],
                "active": True,  # Default to active
            }

            # Collect actions from the table
            for row in range(seq_table.rowCount()):
                dataref_item = seq_table.item(row, 0)
                value_item = seq_table.item(row, 1)

                if dataref_item and value_item:
                    try:
                        value = float(value_item.text())
                        sequence_event["actions"].append(
                            {"dataref": dataref_item.text(), "value": value}
                        )
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Error",
                            f"Invalid value in row {row}. Please enter a number.",
                        )
                        return

            # Store the sequence event (for now, we'll use a simple list)
            if not hasattr(self, "_sequence_events"):
                self._sequence_events = []
            self._sequence_events.append(sequence_event)

            # Refresh the table
            self._refresh_vars_list()

            QMessageBox.information(
                self, "Success", "Sequence event added successfully."
            )

    def _add_sequence_action_row(self, table):
        """Add a new row to the sequence actions table."""
        row = table.rowCount()
        table.insertRow(row)

        # Dataref/Variable combo box
        dataref_combo = QComboBox()
        # Populate with datarefs and variables
        all_items = self.dataref_manager.get_all_dataref_names()

        # Add variables from variable store if available
        if self.variable_store:
            for name, entry in self.variable_store.get_all().items():
                if name not in all_items:
                    all_items.append(name)

        # Add variables from the Variables tab if available
        if hasattr(self, "_variables"):
            for block in self._variables:
                if block.name not in all_items:
                    all_items.append(block.name)

        dataref_combo.addItems(sorted(all_items))

        # Add search helper functionality
        completer = QCompleter(sorted(all_items))
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        dataref_combo.setEditable(True)
        dataref_combo.setCompleter(completer)

        table.setCellWidget(row, 0, dataref_combo)

        # Value input
        value_input = QDoubleSpinBox()
        value_input.setRange(-999999, 999999)
        value_input.setDecimals(4)
        value_input.setValue(0.0)
        table.setCellWidget(row, 1, value_input)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: table.removeRow(row))
        table.setCellWidget(row, 2, delete_btn)

    def _refresh_vars_list(self):
        """Refresh the Variables & Inputs table."""
        self.vars_table.setRowCount(0)

        # 1. Custom & Tracked Datarefs
        # Iterate all tracked datarefs
        all_drefs = self.dataref_manager.get_all_dataref_names()
        for name in all_drefs:
            info = self.dataref_manager.get_dataref_info(name)
            # Default to float if unknown
            dtype = info.get("type", "float") if info else "float"
            writable = info.get("writable", False) if info else False
            val = self._live_values.get(name, 0.0)

            self._add_var_row(name, "Dataref", val, writable, dtype)

        # 2. Variables from Store
        if self.variable_store:
            for var in self.variable_store.get_all().values():
                # var has .type (VariableType enum), .value, .name
                dtype = "float"  # Virtual vars are usually floats
                self._add_var_row(var.name, "Virtual", var.value, True, dtype)

        # 3. Sequence Events
        if hasattr(self, "_sequence_events"):
            for seq_event in self._sequence_events:
                self._add_sequence_row(seq_event)

    def _add_var_row(self, name, type_str, val, is_writable, dtype):
        row = self.vars_table.rowCount()
        self.vars_table.insertRow(row)

        self.vars_table.setItem(row, 0, QTableWidgetItem(str(name)))

        type_item = QTableWidgetItem(str(type_str))
        type_item.setForeground(QColor("#0078d4"))
        self.vars_table.setItem(row, 1, type_item)

        # Value Display Logic
        val_str = self._format_value(name, val, dtype)
        self.vars_table.setItem(row, 2, QTableWidgetItem(val_str))
        self.vars_table.setItem(row, 3, QTableWidgetItem(str(dtype)))
        self.vars_table.setItem(row, 4, QTableWidgetItem("W" if is_writable else "R"))

        # Action: Edit Button
        actions_widget = QWidget()
        l = QHBoxLayout(actions_widget)
        l.setContentsMargins(2, 2, 2, 2)
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(60, 24)
        edit_btn.clicked.connect(lambda _, n=name: self._open_dataref_editor(n))
        l.addWidget(edit_btn)
        self.vars_table.setCellWidget(row, 5, actions_widget)

    def _add_sequence_row(self, seq_event):
        row = self.vars_table.rowCount()
        self.vars_table.insertRow(row)

        self.vars_table.setItem(row, 0, QTableWidgetItem(seq_event.get("name", "")))
        self.vars_table.setItem(row, 1, QTableWidgetItem("SEQUENCE"))
        self.vars_table.setItem(row, 2, QTableWidgetItem("-"))
        self.vars_table.setItem(row, 3, QTableWidgetItem("Sequence"))
        self.vars_table.setItem(row, 4, QTableWidgetItem("-"))

        # Action: Edit Button
        actions_widget = QWidget()
        l = QHBoxLayout(actions_widget)
        l.setContentsMargins(2, 2, 2, 2)
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(60, 24)
        edit_btn.clicked.connect(lambda _, s=seq_event: self._edit_sequence_event(s))
        l.addWidget(edit_btn)
        self.vars_table.setCellWidget(row, 5, actions_widget)

    def _on_context_menu(self, pos):
        """Show Edit or Reload options."""
        item = self.vars_table.itemAt(pos)
        if not item:
            return

        row = item.row()
        name_item = self.vars_table.item(row, 0)
        if not name_item:
            return
        name = name_item.text()

        menu = QMenu(self)

        edit_act = QAction("Edit / Inspect Value", self)
        edit_act.triggered.connect(lambda: self._open_dataref_editor(name))
        menu.addAction(edit_act)

        reload_act = QAction("Force Refresh from X-Plane", self)
        reload_act.triggered.connect(lambda: self._force_reload_dataref(name))
        menu.addAction(reload_act)

        menu.exec(self.vars_table.viewport().mapToGlobal(pos))

    def _open_dataref_editor(self, dataref_name: str):
        """Open the new specialized editor for Arrays/Strings."""
        if not self.dataref_manager:
            return

        info = self.dataref_manager.get_dataref_info(dataref_name)
        # Fallback info
        if not info:
            info = {"type": "float", "writable": True}

        # Keep reference to prevent GC
        self._current_editor = DatarefEditorDialog(
            dataref_name=dataref_name,
            dataref_info=info,
            xplane_conn=self.xplane_conn,
            dataref_manager=self.dataref_manager,
            variable_store=self.variable_store,
            parent=self,
        )
        self._current_editor.show()

    def _force_reload_dataref(self, name: str):
        # Trigger unsubscribe/subscribe
        if self.xplane_conn:
            task1 = asyncio.create_task(self.xplane_conn.unsubscribe_dataref(name))
            self._tasks.append(task1)  # Prevent garbage collection

            # Delayed re-subscribe?
            def delayed_subscribe():
                task = asyncio.create_task(self.xplane_conn.subscribe_dataref(name))
                self._tasks.append(task)  # Prevent garbage collection

            QTimer.singleShot(200, delayed_subscribe)

    def _on_variable_update(self, name: str, value: float):
        """Handle incoming variable update."""
        # Update temp cache
        self._live_values[name] = value

        # Find row in table and update the value directly
        for row in range(self.vars_table.rowCount()):
            item = self.vars_table.item(row, 0)
            if item and item.text() == name:
                # Update value text with consistent formatting to prevent flickering
                val_item = self.vars_table.item(row, 2)
                if val_item:
                    val_item.setText(f"{value:.4f}")
                    # Update color based on value
                    if value >= 0.5:
                        val_item.setForeground(QColor("#28a745"))  # Green
                    else:
                        val_item.setForeground(QColor("#6c757d"))  # Gray
                return

    def _view_variable(self, name: str):
        """View variable details."""
        # Placeholder for viewing variable details
        QMessageBox.information(
            self, "View Variable", f"Viewing details for variable: {name}"
        )

    def _edit_variable(self, name: str):
        """Edit variable."""
        # Placeholder for editing variable
        QMessageBox.information(self, "Edit Variable", f"Editing variable: {name}")

    def _toggle_sequence_active(self, seq_event: dict, state: int):
        """Toggle the active state of a sequence event."""
        seq_event["active"] = state == Qt.CheckState.Checked.value
        # Refresh the table to update the status display
        self._refresh_vars_list()

    def execute_sequence_by_key(self, key: str):
        """Execute a sequence event by its Output ID KEY if it's active."""
        if hasattr(self, "_sequence_events"):
            for seq_event in self._sequence_events:
                if seq_event.get("key", "").upper() == key.upper() and seq_event.get(
                    "active", False
                ):
                    # Execute the sequence actions
                    self._execute_sequence_actions(seq_event)
                    return True
        return False

    def _execute_sequence_actions(self, seq_event: dict):
        """Execute the actions in a sequence event."""
        for action in seq_event.get("actions", []):
            dataref = action.get("dataref", "")
            value = action.get("value", 0.0)
            if dataref:
                # Send the action to X-Plane
                task = asyncio.create_task(
                    self.xplane_conn.write_dataref(dataref, value)
                )
                self._tasks.append(task)  # Prevent garbage collection

    def _edit_sequence_event(self, seq_event: dict):
        """Edit an existing sequence event."""
        # Find the index of this sequence event
        if hasattr(self, "_sequence_events"):
            idx = -1
            for i, seq in enumerate(self._sequence_events):
                if seq is seq_event:  # Compare by identity
                    idx = i
                    break

            if idx >= 0:
                # Create edit dialog similar to add dialog
                dialog = self._create_edit_sequence_dialog(seq_event)

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self._update_sequence_event_from_dialog(seq_event, dialog)
                    # Refresh the table
                    self._refresh_vars_list()

    def _create_edit_sequence_dialog(self, seq_event: dict):
        """Create the edit sequence dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Sequence Event")
        dialog.setMinimumWidth(600)

        layout = QVBoxLayout(dialog)

        # Create form for sequence event details
        name_input, desc_input, key_input = self._create_sequence_form(
            dialog, seq_event, layout
        )

        # Add sequence actions section
        seq_table = self._create_sequence_table(seq_event)
        layout.addWidget(seq_table)

        # Add buttons for sequence actions
        self._add_sequence_buttons(seq_table, layout)

        # Add dialog buttons
        self._add_dialog_buttons(dialog, layout)

        # Store references to inputs for later use
        dialog.name_input = name_input
        dialog.desc_input = desc_input
        dialog.key_input = key_input
        dialog.seq_table = seq_table

        return dialog

    def _create_sequence_form(self, parent, seq_event: dict, layout):
        """Create the form for sequence event details."""
        form_layout = QFormLayout()

        name_input = QLineEdit(seq_event.get("name", ""))
        form_layout.addRow("Name:", name_input)

        desc_input = QLineEdit(seq_event.get("description", ""))
        form_layout.addRow("Description:", desc_input)

        key_input = QLineEdit(seq_event.get("key", ""))
        form_layout.addRow("Output ID KEY:", key_input)

        layout.addLayout(form_layout)

        return name_input, desc_input, key_input

    def _create_sequence_table(self, seq_event: dict):
        """Create the table for sequence actions."""
        # Add sequence actions section
        seq_header = QLabel("Sequence Actions:")
        seq_header.setStyleSheet("font-weight: bold; margin-top: 10px;")

        # Table for sequence actions
        seq_table = QTableWidget(0, 3)
        seq_table.setHorizontalHeaderLabels(["Dataref/Variable", "Value", "Actions"])
        seq_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        seq_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        seq_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )

        # Populate with existing actions
        for action in seq_event.get("actions", []):
            self._add_action_row_to_table(seq_table, action)

        return seq_table

    def _add_action_row_to_table(self, seq_table: QTableWidget, action: dict):
        """Add a single action row to the sequence table."""
        row = seq_table.rowCount()
        seq_table.insertRow(row)

        # Dataref/Variable combo box
        dataref_combo = QComboBox()
        all_items = self._get_all_available_items()
        dataref_combo.addItems(sorted(all_items))
        dataref_combo.setEditable(True)
        dataref_combo.setEditText(action.get("dataref", ""))
        seq_table.setCellWidget(row, 0, dataref_combo)

        # Value input
        value_input = QDoubleSpinBox()
        value_input.setRange(-999999, 999999)
        value_input.setDecimals(4)
        value_input.setValue(action.get("value", 0.0))
        seq_table.setCellWidget(row, 1, value_input)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda _, r=row: seq_table.removeRow(r))
        seq_table.setCellWidget(row, 2, delete_btn)

    def _get_all_available_items(self):
        """Get all available items for the combo box."""
        all_items = self.dataref_manager.get_all_dataref_names()
        # Add variables from variable store if available
        if self.variable_store:
            for name, entry in self.variable_store.get_all().items():
                if name not in all_items:
                    all_items.append(name)

        # Add variables from the Variables tab if available
        if hasattr(self, "_variables"):
            for block in self._variables:
                if block.name not in all_items:
                    all_items.append(block.name)

        return all_items

    def _add_sequence_buttons(self, seq_table: QTableWidget, layout):
        """Add buttons for sequence actions."""
        # Buttons for sequence actions
        seq_btn_layout = QHBoxLayout()

        add_action_btn = QPushButton("Add Action")
        add_action_btn.clicked.connect(lambda: self._add_sequence_action_row(seq_table))
        seq_btn_layout.addWidget(add_action_btn)

        seq_btn_layout.addStretch()
        layout.addLayout(seq_btn_layout)

    def _add_dialog_buttons(self, dialog: QDialog, layout):
        """Add OK/Cancel buttons to the dialog."""
        # Dialog buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

    def _update_sequence_event_from_dialog(self, seq_event: dict, dialog):
        """Update sequence event from dialog inputs."""
        # Update sequence event
        seq_event["name"] = dialog.name_input.text().strip()
        seq_event["description"] = dialog.desc_input.text().strip()
        seq_event["key"] = dialog.key_input.text().strip()

        # Collect actions from the table
        seq_event["actions"] = []
        for row in range(dialog.seq_table.rowCount()):
            dataref_widget = dialog.seq_table.cellWidget(row, 0)
            value_widget = dialog.seq_table.cellWidget(row, 1)

            if isinstance(dataref_widget, QComboBox) and isinstance(
                value_widget, QDoubleSpinBox
            ):
                dataref = dataref_widget.currentText()
                value = value_widget.value()
                seq_event["actions"].append({"dataref": dataref, "value": value})

    def _delete_sequence_event(self, seq_event: dict):
        """Delete a sequence event."""
        reply = QMessageBox.question(
            self,
            "Delete Sequence Event",
            f"Are you sure you want to delete the sequence event '{seq_event.get('name', '')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, "_sequence_events"):
                # Remove the sequence event
                self._sequence_events = [
                    seq for seq in self._sequence_events if seq is not seq_event
                ]
                # Refresh the table
                self._refresh_vars_list()

    def _add_variable(self):
        """Open dialog to add a new variable."""
        if not self.logic_engine:
            QMessageBox.warning(self, "Error", "Logic Engine not available.")
            return

        dialog = VariableDialog(
            self.dataref_manager, variable_store=self.variable_store, parent=self
        )
        if dialog.exec():
            block = dialog.get_block()
            # Add to Logic Engine (Central Persistence)
            self.logic_engine.add_block(block)
            self._refresh_variables_table()

            # TRIGGER REFRESH of all search completers across the app!
            main_win = self.window()
            if hasattr(main_win, "refresh_search_helpers"):
                main_win.refresh_search_helpers()

    def _edit_selected_variable(self):
        """Edit the selected variable."""
        row = self.vars_table.currentRow()
        if not self._is_valid_row(row):
            return

        block = self._variables[row]
        dialog = VariableDialog(
            self.dataref_manager,
            block=block,
            variable_store=self.variable_store,
            parent=self,
        )
        if dialog.exec():
            self._process_updated_block(block, dialog.get_block())

    def _is_valid_row(self, row: int) -> bool:
        """Check if the row is valid for variable editing."""
        return row >= 0 and hasattr(self, "_variables") and row < len(self._variables)

    def _process_updated_block(self, old_block, updated_block):
        """Process the updated block after dialog."""
        old_key = old_block.output_key
        new_key = updated_block.output_key

        # Update the block in the LogicEngine
        self.logic_engine.add_block(updated_block)

        # Handle key change synchronization
        self._handle_key_change(old_key, new_key)

        # Refresh UI and helpers
        self._refresh_after_edit(new_key, old_key)

    def _handle_key_change(self, old_key: str, new_key: str):
        """Handle changes in output key."""
        if old_key != new_key:
            log.info(
                f"Variable Output Key changed: '{old_key}' -> '{new_key}'. Updating mappings."
            )

        # Check if the old key was subscribed in the Datarefs table
        if old_key in self._subscribed_datarefs:
            self._handle_old_key_subscription(old_key, new_key)

    def _handle_old_key_subscription(self, old_key: str, new_key: str):
        """Handle old key subscription when key changes."""
        # Remove the old row
        self._remove_row(old_key, force=True)
        log.info(f"Removed stale subscription for old key: {old_key}")

        # If the new key is not empty, add a new row for it
        if new_key:
            self._add_output_row(new_key)
            log.info(f"Added new subscription for updated key: {new_key}")

    def _refresh_after_edit(self, new_key: str, old_key: str):
        """Refresh UI and search helpers after editing."""
        self._refresh_variables_table()

        # Trigger global search helper refresh
        main_win = self.window()
        if hasattr(main_win, "refresh_search_helpers"):
            main_win.refresh_search_helpers()

    def _delete_selected_variable(self):
        """Delete the selected variable."""
        row = self.vars_table.currentRow()
        if row >= 0 and hasattr(self, "_variables") and row < len(self._variables):
            block = self._variables[row]
            old_key = block.output_key

            # Remove from LogicEngine
            self.logic_engine.remove_block(block.name)

            # Clean up DatarefManager (if the key was subscribed as a dataref)
            if old_key in self._subscribed_datarefs:
                self._remove_row(old_key, force=True)
                log.info(f"Removed subscription for deleted variable key: {old_key}")

            # Refresh UI
            self._refresh_variables_table()

            # TRIGGER REFRESH of all search completers across the app!
            main_win = self.window()
            if hasattr(main_win, "refresh_search_helpers"):
                main_win.refresh_search_helpers()

    @property
    def _variables(self):
        """Bridge to LogicEngine blocks."""
        if self.logic_engine:
            return self.logic_engine.get_blocks()
        return []

    def _refresh_variables_table(self):
        """Refresh the variables table - only update values if possible, rebuild if necessary."""
        # If we have a logic engine, use it.
        if not self.logic_engine:
            self.vars_table.setRowCount(0)
            return

        # Check if we can do an incremental update instead of full rebuild
        current_row_count = self.vars_table.rowCount()
        needed_row_count = len(self._variables)

        if current_row_count == needed_row_count:
            # Same number of blocks, try to update in place to preserve UI state
            self._update_existing_rows()
        else:
            # Different number of blocks, need to rebuild
            self._rebuild_table()

    def _update_existing_rows(self):
        """Update existing rows without rebuilding the table."""
        for row, block in enumerate(self._variables):
            self._update_name_column(row, block)
            self._update_description_column(row, block)
            self._update_value_column(row, block)
            self._update_status_column(row, block)
            self._update_prop_column(row, block)
            self._update_output_key_column(row, block)

    def _update_name_column(self, row: int, block):
        """Update the name column for a block."""
        name_item = self.vars_table.item(row, 0)
        if name_item:
            name_item.setText(block.name)
        else:
            name_item = QTableWidgetItem(block.name)
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.vars_table.setItem(row, 0, name_item)

    def _update_description_column(self, row: int, block):
        """Update the description column for a block."""
        desc_item = self.vars_table.item(row, 1)
        if desc_item:
            desc_item.setText(block.description)
        else:
            desc_item = QTableWidgetItem(block.description)
            desc_item.setFlags(desc_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.vars_table.setItem(row, 1, desc_item)

    def _update_value_column(self, row: int, block):
        """Update the value column for a block."""
        # Update Live Value Column (Read-Only) - Format consistently to prevent flickering
        val = 0.0
        if self.variable_store and block.name:
            val = self.variable_store.get_value(block.name) or 0.0
        val_item = self.vars_table.item(row, 2)
        if val_item:
            val_item.setText(f"{val:.4f}")
            self._set_value_color(val_item, val)
        else:
            val_item = QTableWidgetItem(f"{val:.4f}")
            val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._set_value_color(val_item, val)
            val_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.vars_table.setItem(row, 2, val_item)

    def _set_value_color(self, val_item: QTableWidgetItem, val: float):
        """Set the color for the value item based on its value."""
        if val >= 0.5:
            val_item.setForeground(QColor("#28a745"))  # Green
        else:
            val_item.setForeground(QColor("#6c757d"))  # Gray

    def _update_status_column(self, row: int, block):
        """Update the status column for a block."""
        status = "ACTIVE" if block.enabled else "INACTIVE"
        status_item = self.vars_table.item(row, 3)
        if status_item:
            status_item.setText(status)
            self._set_status_color(status_item, block.enabled)
        else:
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._set_status_color(status_item, block.enabled)
            self.vars_table.setItem(row, 3, status_item)

    def _set_status_color(self, status_item: QTableWidgetItem, is_enabled: bool):
        """Set the color for the status item based on its state."""
        if is_enabled:
            status_item.setForeground(QColor("#28a745"))  # Green
        else:
            status_item.setForeground(QColor("#dc3545"))  # Red

    def _update_prop_column(self, row: int, block):
        """Update the prop column for a block."""
        prop_str = "Logic"
        if block.outputs:
            prop_str = f"Logic ({len(block.conditions)} in / {len(block.outputs)} out)"
        prop_item = self.vars_table.item(row, 5)
        if prop_item:
            prop_item.setText(prop_str)
        else:
            prop_item = QTableWidgetItem(prop_str)
            prop_item.setFlags(prop_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.vars_table.setItem(row, 5, prop_item)

    def _update_output_key_column(self, row: int, block):
        """Update the output key column for a block."""
        key_widget = self.vars_table.cellWidget(row, 6)
        if not key_widget or not isinstance(key_widget, QLineEdit):
            self._create_key_widget(row, block)
        else:
            # Update existing widget
            key_widget.blockSignals(
                True
            )  # Prevent triggering the handler during update
            key_widget.setText(block.output_key)
            key_widget.blockSignals(False)

    def _create_key_widget(self, row: int, block):
        """Create the key widget for a block."""
        key_input = QLineEdit()
        key_input.setText(block.output_key)
        key_input.setPlaceholderText(PLACEHOLDER_OUTPUT_KEY)

        # Only register mapping if it's not already registered
        if block.output_key and self.arduino_manager:
            # Check if this mapping already exists to avoid repeated registrations
            current_mappings = self.arduino_manager.get_all_universal_mappings()
            if (
                block.output_key not in current_mappings
                or current_mappings[block.output_key]["source"] != block.name
            ):
                log.info(
                    "Registering Variable '%s' with output key '%s'",
                    block.name,
                    block.output_key,
                )
                self.arduino_manager.set_universal_mapping(
                    block.name, block.output_key, is_variable=True
                )

        # Create a localized handler to catch the block correctly
        def make_handler(b, idx, widget):
            def handler():
                new_key = widget.text().strip().upper()
                # Only check if changed
                if new_key == b.output_key:
                    return

                if new_key and self._check_duplicate_key(
                    new_key, exclude_var_index=idx
                ):
                    QMessageBox.warning(
                        self,
                        WARNING_DUPLICATE_KEY,
                        f"The key '{new_key}' is already assigned.\n"
                        "Each output must have a unique key.",
                    )
                    widget.setText(b.output_key or "")  # Revert
                    return

                b.output_key = new_key

                # Register mapping with ArduinoManager so it's searchable
                if self.arduino_manager:
                    self.arduino_manager.set_universal_mapping(
                        b.name, new_key, is_variable=True
                    )

                # TRIGGER REFRESH of all search completers across the app!
                main_win = self.window()
                if hasattr(main_win, "refresh_search_helpers"):
                    main_win.refresh_search_helpers()

            return handler

        key_input.editingFinished.connect(make_handler(block, row, key_input))
        self.vars_table.setCellWidget(row, 6, key_input)

    def _rebuild_table(self):
        """Completely rebuild the table - use when number of blocks changes."""
        self.vars_table.setRowCount(0)
        self.vars_table.setRowCount(len(self._variables))

        for row, block in enumerate(self._variables):
            self._add_row_for_block(row, block)

    def _add_row_for_block(self, row: int, block):
        """Add a single row for a block."""
        self._add_name_column(row, block)
        self._add_description_column(row, block)
        self._add_value_column(row, block)
        self._add_status_column(row, block)
        self._add_action_column(row, block)
        self._add_prop_column(row, block)
        self._add_key_column(row, block)
        self._add_delete_column(row, block)

    def _add_name_column(self, row: int, block):
        """Add the name column for a block."""
        name_item = QTableWidgetItem(block.name)
        name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.vars_table.setItem(row, 0, name_item)

    def _add_description_column(self, row: int, block):
        """Add the description column for a block."""
        desc_item = QTableWidgetItem(block.description)
        desc_item.setFlags(desc_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.vars_table.setItem(row, 1, desc_item)

    def _add_value_column(self, row: int, block):
        """Add the value column for a block."""
        # Live Value Column (Read-Only) - Format consistently to prevent flickering
        val = 0.0
        if self.variable_store and block.name:
            val = self.variable_store.get_value(block.name) or 0.0
        val_item = QTableWidgetItem(f"{val:.4f}")
        val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if val >= 0.5:
            val_item.setForeground(QColor("#28a745"))  # Green
        else:
            val_item.setForeground(QColor("#6c757d"))  # Gray
        val_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vars_table.setItem(row, 2, val_item)

    def _add_status_column(self, row: int, block):
        """Add the status column for a block."""
        status = "ACTIVE" if block.enabled else "INACTIVE"
        status_item = QTableWidgetItem(status)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if block.enabled:
            status_item.setForeground(QColor("#28a745"))  # Green
        else:
            status_item.setForeground(QColor("#dc3545"))  # Red
        self.vars_table.setItem(row, 3, status_item)

    def _add_action_column(self, row: int, block):
        """Add the action column for a block."""
        edit_btn = QPushButton("Configure Logic")
        edit_btn.clicked.connect(lambda _, r=row: self._edit_variable_by_index(r))
        self.vars_table.setCellWidget(row, 4, edit_btn)

    def _add_prop_column(self, row: int, block):
        """Add the prop column for a block."""
        prop_str = "Logic"
        if block.outputs:
            prop_str = f"Logic ({len(block.conditions)} in / {len(block.outputs)} out)"
        prop_item = QTableWidgetItem(prop_str)
        prop_item.setFlags(prop_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.vars_table.setItem(row, 5, prop_item)

    def _add_key_column(self, row: int, block):
        """Add the key column for a block."""
        key_input = QLineEdit()
        key_input.setText(block.output_key)
        key_input.setPlaceholderText(PLACEHOLDER_OUTPUT_KEY)

        # Only register mapping if it's not already registered
        if block.output_key and self.arduino_manager:
            # Check if this mapping already exists to avoid repeated registrations
            current_mappings = self.arduino_manager.get_all_universal_mappings()
            if (
                block.output_key not in current_mappings
                or current_mappings[block.output_key]["source"] != block.name
            ):
                log.info(
                    "Registering Variable '%s' with output key '%s'",
                    block.name,
                    block.output_key,
                )
                self.arduino_manager.set_universal_mapping(
                    block.name, block.output_key, is_variable=True
                )

        # Create a localized handler to catch the block correctly
        def make_handler(b, idx, widget):
            def handler():
                new_key = widget.text().strip().upper()
                # Only check if changed
                if new_key == b.output_key:
                    return

                if new_key and self._check_duplicate_key(
                    new_key, exclude_var_index=idx
                ):
                    QMessageBox.warning(
                        self,
                        WARNING_DUPLICATE_KEY,
                        f"The key '{new_key}' is already assigned.\n"
                        "Each output must have a unique key.",
                    )
                    widget.setText(b.output_key or "")  # Revert
                    return

                b.output_key = new_key

                # Register mapping with ArduinoManager so it's searchable
                if self.arduino_manager:
                    self.arduino_manager.set_universal_mapping(
                        b.name, new_key, is_variable=True
                    )

                # TRIGGER REFRESH of all search completers across the app!
                main_win = self.window()
                if hasattr(main_win, "refresh_search_helpers"):
                    main_win.refresh_search_helpers()

            return handler

        key_input.editingFinished.connect(make_handler(block, row, key_input))
        self.vars_table.setCellWidget(row, 6, key_input)

    def _add_delete_column(self, row: int, block):
        """Add the delete column for a block."""
        del_btn = QPushButton("Delete")
        del_btn.setStyleSheet("background-color: #dc3545; color: white;")
        # Use name-based deletion to be robust against row shifts
        v_name = block.name
        del_btn.clicked.connect(lambda _, n=v_name: self._delete_variable_by_name(n))
        self.vars_table.setCellWidget(row, 7, del_btn)

    # --- Variable Handlers ---

    def _on_variable_item_changed(self, item):
        """Handle changes to variable name or description."""
        row = item.row()
        col = item.column()

        if row < 0 or row >= len(self._variables):
            return

        block = self._variables[row]

        if col == 0:  # Name column
            block.name = item.text()
        elif col == 1:  # Description column
            block.description = item.text()

    def _edit_variable_by_index(self, index):
        """Edit variable by index."""
        if self.logic_engine and index < len(self._variables):
            block = self._variables[index]
            dialog = VariableDialog(
                self.dataref_manager,
                block=block,
                variable_store=self.variable_store,
                parent=self,
            )
            if dialog.exec():
                updated_block = dialog.get_block()
                self._variables[index] = updated_block
                # Since block is a reference, it should be updated. LogicEngine holds the reference.
                self._refresh_variables_table()

    def _delete_variable_by_name(self, name: str):
        """Delete variable by name."""
        if not self.logic_engine:
            return

        reply = QMessageBox.question(
            self,
            "Delete Variable",
            f"Are you sure you want to delete the variable '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.logic_engine.remove_block(name)
            self._refresh_variables_table()

            # TRIGGER REFRESH of all search completers across the app!
            main_win = self.window()
            if hasattr(main_win, "refresh_search_helpers"):
                main_win.refresh_search_helpers()

    def _connect_signals(self):
        self.search_input.returnPressed.connect(self._subscribe_manual)

    def _subscribe_manual(self):
        dataref = self.search_input.text().strip()
        if dataref:
            self._add_output_row(dataref)

    def _add_output_row(self, dataref: str):
        """Add a row to the table for a dataref."""
        # FIX: Handle ID: prefix for Variables
        clean_name = self._get_clean_name(dataref)

        if not self._validate_dataref(clean_name):
            return

        # Check if this is an array dataref
        info = self.dataref_manager.get_dataref_info(clean_name)
        if info:
            data_type = info.get("type", "")
            size = self._parse_array_size(data_type)

            if size > 1:
                # This is an array dataref - expand into individual elements
                base = clean_name.split("[")[0]  # Extract base name
                for idx in range(size):
                    elem_name = f"{base}[{idx}]"
                    self._add_single_output_row(elem_name, dataref)
            else:
                # Regular dataref - add single row
                self._add_single_output_row(clean_name, dataref)
        else:
            # If no info available, treat as regular dataref
            self._add_single_output_row(clean_name, dataref)

    def _add_single_output_row(self, display_name: str, original_dataref: str):
        """Add a single output row to the table."""
        row = self._add_table_row(display_name)

        # Store mapping
        self._subscribed_datarefs[display_name] = row

        # Subscribe to X-Plane if appropriate
        self._subscribe_if_appropriate(display_name, original_dataref)

        # Persistence: Mark as monitored
        if hasattr(self.arduino_manager, "add_monitor"):
            self.arduino_manager.add_monitor(original_dataref)

    def _get_clean_name(self, dataref: str) -> str:
        """Get the clean name from the dataref string."""
        clean_name = dataref
        if dataref.startswith("ID:"):
            clean_name = dataref.split(":", 1)[1]
            # Check if this is actually a variable
            if self.variable_store and clean_name in self.variable_store.get_names():
                log.warning(
                    f"Attempted to subscribe to variable '{clean_name}' via Datarefs table. Redirecting to Variables tab logic."
                )
        return clean_name

    def _validate_dataref(self, clean_name: str) -> bool:
        """Validate the dataref before adding."""
        if clean_name in self._subscribed_datarefs:
            log.warning("Dataref already subscribed: %s", clean_name)
            return False

        # Prevent subscribing to variables in the datarefs tab
        if clean_name.startswith("VAR:"):
            QMessageBox.warning(
                self,
                "Invalid Dataref",
                "Variables cannot be subscribed as datarefs. Use the Variables tab instead.",
            )
            return False

        return True

    def _add_table_row(self, clean_name: str) -> int:
        """Add a table row with all necessary elements."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Add dataref name
        self._add_dataref_name(row, clean_name)

        # Add description
        info = self._get_or_add_dataref_info(clean_name)
        self._add_description(row, clean_name, info)

        # Add live value
        self._add_live_value(row)

        # Add modify/execute button
        self._add_modify_button(row, info)

        # Add output key input
        self._add_output_key_input(row, clean_name)

        # Add delete button
        self._add_delete_button(row, clean_name)

        return row

    def _add_dataref_name(self, row: int, clean_name: str):
        """Add the dataref name to the row."""
        dataref_item = QTableWidgetItem(clean_name)
        dataref_item.setFlags(dataref_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, dataref_item)

    def _get_or_add_dataref_info(self, clean_name: str):
        """Get dataref info or add as custom if not found."""
        info = self.dataref_manager.get_dataref_info(clean_name)
        if not info:
            # Unrecognized? Add as custom dataref so it persists and is searchable!
            self.dataref_manager.add_custom_dataref(clean_name)
            info = self.dataref_manager.get_dataref_info(clean_name)

            # TRIGGER REFRESH of all search completers across the app!
            main_win = self.window()
            if hasattr(main_win, "refresh_search_helpers"):
                main_win.refresh_search_helpers()

        return info

    def _add_description(self, row: int, clean_name: str, info):
        """Add the description to the row."""
        desc = info.get("description", "") if info else ""
        writable = info.get("writable", False) if info else False
        writable_str = "[WRITABLE]" if writable else "[READ-ONLY]"
        dataref_type = info.get("type", "") if info else ""
        type_str = f"[{dataref_type}]" if dataref_type else ""

        # Truncate description if too long and add tooltip for full text
        max_desc_length = 80
        if len(desc) > max_desc_length:
            truncated_desc = desc[:max_desc_length] + "..."
        else:
            truncated_desc = desc

        desc_item = QTableWidgetItem(f"{type_str} {writable_str} {truncated_desc}")
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if not writable:
            desc_item.setForeground(QColor("#666"))

        # Set tooltip to show full description
        desc_item.setToolTip(desc)
        self.table.setItem(row, 1, desc_item)

    def _add_live_value(self, row: int) -> QTableWidgetItem:
        """Add the live value to the row."""
        value_item = QTableWidgetItem("")
        value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        # Add tooltip to indicate it's a live value
        value_item.setToolTip("Live value from X-Plane")
        self.table.setItem(row, 2, value_item)
        return value_item

    def _add_modify_button(self, row: int, info):
        """Add the modify/execute button to the row."""
        is_complex = False
        is_command = False
        if info:
            t = info.get("type", "")
            if t == "command":
                is_command = True
            elif "[" in t or "string" in t or "byte" in t:
                is_complex = True

        if is_command:
            btn_text = "EXECUTE"
        else:
            btn_text = "Inspect/Edit" if is_complex else "Write"

        modify_btn = QPushButton(btn_text)
        modify_btn.clicked.connect(lambda: self._modify_value(row))

        if is_command:
            modify_btn.setStyleSheet(
                "background-color: #0078d4; color: white; font-weight: bold;"
            )
        elif is_complex:
            modify_btn.setStyleSheet("color: #0078d4; font-weight: bold;")

        self.table.setCellWidget(row, 3, modify_btn)

    def _add_output_key_input(self, row: int, clean_name: str):
        """Add the output key input to the row."""
        key_input = QLineEdit()
        key_input.setPlaceholderText(PLACEHOLDER_OUTPUT_KEY)
        # Connect text change to update mapping
        # Use editingFinished to avoid validation on every keystroke
        # Robust against row shifts: capture dataref name, not row index
        key_input.editingFinished.connect(
            lambda dr=clean_name, widget=key_input: self._on_key_input_edited(
                dr, widget
            )
        )
        self.table.setCellWidget(row, 4, key_input)

    def _add_delete_button(self, row: int, clean_name: str):
        """Add the delete button to the row."""
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda: self._remove_row(clean_name))
        self.table.setCellWidget(row, 5, del_btn)

        # Enable deletion for all datarefs (both custom and official)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)

    def _subscribe_if_appropriate(self, clean_name: str, dataref: str):
        """Subscribe to X-Plane if appropriate."""
        # Check if this is an array element (e.g., LED_STATE[3])
        array_match = re.match(r"^(.+)\[(\d+)\]$", clean_name)
        if array_match:
            # This is an array element, subscribe to the base array
            base_name = array_match.group(1)
            info = self.dataref_manager.get_dataref_info(base_name)
        else:
            info = self.dataref_manager.get_dataref_info(clean_name)

        # Determine frequency and count (for arrays)
        freq = 5
        count = 1
        if info:
            dtype = info.get("type", "")
            # check for array patterns: float[8], int[4], byte[260]
            m = re.search(r"\[(\d+)\]", dtype)
            if m:
                count = int(m.group(1))
                log.info("Detected array size %d for %s", count, dataref)

        # Check if it's a command
        is_command = info and info.get("type", "") == "command"

        # Subscribe if it's a dataref, not a command, and not a variable
        if not is_command and not (
            self.variable_store and clean_name in self.variable_store.get_names()
        ):
            # For array elements, we need to make sure the base array is subscribed
            # But we only want to subscribe once to the base array even if multiple elements are displayed
            if array_match:
                base_name = array_match.group(1)
                # Check if we've already subscribed to this base array for this session
                # We'll use a temporary set to track which arrays we've subscribed to
                if not hasattr(self, "_subscribed_arrays"):
                    self._subscribed_arrays = set()

                if base_name not in self._subscribed_arrays:
                    task = asyncio.create_task(
                        self.xplane_conn.subscribe_dataref(base_name, freq, count=count)
                    )
                    self._tasks.append(task)  # Prevent garbage collection
                    self._subscribed_arrays.add(base_name)
                    log.info(
                        "Subscribed to array dataref: %s (freq=%d, count=%d)",
                        base_name,
                        freq,
                        count,
                    )
            else:
                task = asyncio.create_task(
                    self.xplane_conn.subscribe_dataref(clean_name, freq, count=count)
                )
                self._tasks.append(task)  # Prevent garbage collection
                log.info(
                    "Subscribed to dataref: %s (freq=%d, count=%d)",
                    dataref,
                    freq,
                    count,
                )
        else:
            value_item = self.table.item(
                self.table.rowCount() - 1, 2
            )  # Get the value item for this row
            if value_item:
                value_item.setText("COMMAND")
                value_item.setForeground(QColor("#0078d4"))
            log.info("Added command wrapper: %s", dataref)

    def _check_duplicate_key(
        self, key: str, exclude_dataref: str = None, exclude_var_index: int = None
    ) -> bool:
        """Check if key is already assigned. Returns True if duplicate found."""
        if not key:
            return False

        key = key.upper()

        # Check Datarefs Table
        if self._has_duplicate_in_datarefs_table(key, exclude_dataref):
            return True

        # Check Variables
        if self._has_duplicate_in_variables(key, exclude_var_index):
            return True

        return False

    def _has_duplicate_in_datarefs_table(
        self, key: str, exclude_dataref: str = None
    ) -> bool:
        """Check if the key already exists in the datarefs table."""
        for row in range(self.table.rowCount()):
            # Get dataref for this row to check exclusion
            d_item = self.table.item(row, 0)
            if not d_item:
                continue
            row_dataref = d_item.text()

            if exclude_dataref and row_dataref == exclude_dataref:
                continue

            key_widget = self.table.cellWidget(row, 4)
            if isinstance(key_widget, QLineEdit):
                other_key = key_widget.text().strip().upper()
                if other_key and other_key == key:
                    return True
        return False

    def _has_duplicate_in_variables(
        self, key: str, exclude_var_index: int = None
    ) -> bool:
        """Check if the key already exists in the variables."""
        if not hasattr(self, "_variables"):
            return False

        for i, block in enumerate(self._variables):
            if exclude_var_index is not None and i == exclude_var_index:
                continue

            if block.output_key and block.output_key.upper() == key:
                return True
        return False

    def _on_key_input_edited(self, dataref: str, widget: QLineEdit):
        """Handle key input field changes."""
        key = widget.text().strip().upper()

        # 0. Find current row to handle revert/clear logic
        row = self._subscribed_datarefs.get(dataref)
        if row is None:
            log.warning("Received key edit for non-existent row/dataref: %s", dataref)
            return

        # 1. Duplicate Check
        if key and self._check_duplicate_key(key, exclude_dataref=dataref):
            QMessageBox.warning(
                self,
                WARNING_DUPLICATE_KEY,
                f"The key '{key}' is already assigned to another output.\n"
                "Each output must have a unique key.",
            )

            # Revert/Clear
            widget.setText("")  # Clear it to force user to choose another
            return  # Do not save

        # 2. Update Arduino manager mapping
        self.arduino_manager.set_universal_mapping(
            dataref, key
        )  # Empty key removes mapping
        if key:
            log.info("Mapped %s -> %s", dataref, key)
            # Register with DatarefWriter
            self.dataref_writer.register_output_id(key, dataref)
        else:
            log.info("Removed mapping for %s", dataref)
            # Unregister from DatarefWriter
            self.dataref_writer.unregister_output_id(key)

        # 3. TRIGGER REFRESH of all search completers across the app!
        main_win = self.window()
        if hasattr(main_win, "refresh_search_helpers"):
            main_win.refresh_search_helpers()

    def _remove_row(self, dataref: str, force: bool = False):
        """Remove a row for a dataref."""
        if dataref not in self._subscribed_datarefs:
            return

        row = self._subscribed_datarefs[dataref]

        # 1. Ask for confirmation unless forced
        if not self._confirm_removal(dataref, force):
            return

        # 2. Remove from table
        self.table.removeRow(row)

        # 3. Cleanup state
        self._cleanup_dataref_state(dataref, row)

        # 4. Handle array elements - if this was an array element, check if we need to unsubscribe from the base array
        array_match = re.match(r"^(.+)\[(\d+)\]$", dataref)
        if array_match:
            base_name = array_match.group(1)
            # Check if there are any other elements of this array still subscribed
            other_elements_exist = any(
                re.match(rf"^{re.escape(base_name)}\[\d+\]$", key) and key != dataref
                for key in self._subscribed_datarefs.keys()
            )

            # If no other elements of this array are subscribed, we might want to unsubscribe from the base array
            # For now, we'll just leave the subscription as is since it might be used by other parts of the app

    def _confirm_removal(self, dataref: str, force: bool) -> bool:
        """Confirm removal with user if not forced."""
        if force:
            return True

        if self.dataref_manager.is_custom_dataref(dataref):
            return self._confirm_custom_dataref_removal(dataref)
        else:
            return self._confirm_subscription_removal(dataref)

    def _confirm_custom_dataref_removal(self, dataref: str) -> bool:
        """Confirm removal of custom dataref."""
        reply = QMessageBox.question(
            self,
            "Delete Custom Dataref",
            f"Do you want to delete the custom dataref '{dataref}'?\n\n"
            "This will remove it from the database and all mappings using it.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.dataref_manager.remove_custom_dataref(dataref)
            return True
        return False

    def _confirm_subscription_removal(self, dataref: str) -> bool:
        """Confirm removal of subscription."""
        reply = QMessageBox.question(
            self,
            "Remove Subscription",
            f"Do you want to remove the subscription to '{dataref}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _cleanup_dataref_state(self, dataref: str, row: int):
        """Clean up the dataref state after removal."""
        # Remove from live values
        if dataref in self._live_values:
            del self._live_values[dataref]

        # Remove from subscribed datarefs mapping
        if dataref in self._subscribed_datarefs:
            del self._subscribed_datarefs[dataref]

        # Re-index all remaining rows to prevent desync
        self._reindex_subscribed_datarefs()

        # Notify bridge/manager
        self._notify_managers_of_removal(dataref)

        log.info("Unsubscribed and removed row for: %s", dataref)
        log.info("Unsubscribed from dataref: %s", dataref)

    def _reindex_subscribed_datarefs(self):
        """Re-index all remaining rows to prevent desync after row removal."""
        new_map = {}
        for r in range(self.table.rowCount()):
            d_item = self.table.item(r, 0)
            if d_item:
                new_map[d_item.text()] = r
        self._subscribed_datarefs = new_map

    def _notify_managers_of_removal(self, dataref: str):
        """Notify managers of dataref removal."""
        # Check if this is an array element
        array_match = re.match(r"^(.+)\[(\d+)\]$", dataref)
        if array_match:
            # This is an array element, unsubscribe from the base array only if no other elements are subscribed
            base_name = array_match.group(1)
            # Check if there are any other elements of this array still subscribed
            other_elements_exist = any(
                re.match(rf"^{re.escape(base_name)}\[\d+\]$", key) and key != dataref
                for key in self._subscribed_datarefs.keys()
            )

            # Only unsubscribe from the base array if no other elements of it are still subscribed
            if not other_elements_exist:
                task = asyncio.create_task(
                    self.xplane_conn.unsubscribe_dataref(base_name)
                )
                self._tasks.append(task)  # Prevent garbage collection
                log.info("Unsubscribed from array dataref: %s", base_name)
        else:
            # Regular dataref (non-array)
            task = asyncio.create_task(self.xplane_conn.unsubscribe_dataref(dataref))
            self._tasks.append(task)  # Prevent garbage collection

        self.arduino_manager.set_universal_mapping(dataref, "")

        if hasattr(self.arduino_manager, "remove_monitor"):
            self.arduino_manager.remove_monitor(dataref)

    def _update_mapping(self, dataref: str, key: str):
        """Update the mapping for a dataref."""
        if dataref not in self._subscribed_datarefs:
            return

        row = self._subscribed_datarefs[dataref]

        # Update the UI key input field
        key_widget = self.table.cellWidget(row, 4)  # Column 4 is now Output Key
        if key_widget and isinstance(key_widget, QLineEdit):
            key_widget.setText(key)

        # Update Arduino manager mapping
        self.arduino_manager.set_universal_mapping(
            dataref, key
        )  # Empty key removes mapping
        if key:
            log.info("Mapped %s -> %s", dataref, key)
        else:
            log.info("Removed mapping for %s", dataref)

    def _write_dataref(self, dataref: str, value: float):
        """Write a value to a dataref."""
        task = asyncio.create_task(self.xplane_conn.write_dataref(dataref, value))
        self._tasks.append(task)  # Prevent garbage collection
        log.info("Wrote %s = %.2f", dataref, value)

    def _open_custom_dialog(self):
        """Open dialog to add a custom dataref."""
        text, ok = QInputDialog.getText(self, "Custom Dataref", "Enter dataref name:")
        if ok and text.strip():
            self._add_output_row(text.strip())

    def _update_autocomplete(self):
        """Update autocomplete with current dataref list."""
        if hasattr(self, "search_input"):
            completer = QCompleter(self._dataref_list)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(20)
            self.search_input.setCompleter(completer)

    def restore_state(self):
        """Restore UI state from ArduinoManager (called after profile load)."""
        # 1. Clear current table
        self._clear_current_table()

        # 2. Get Monitored Datarefs and Mappings
        monitored = self._get_monitored_datarefs()
        inverted_mappings = self._get_inverted_mappings()

        # 3. Rebuild Table with array expansion
        all_datarefs = set(monitored) | set(inverted_mappings.keys())
        self._process_datarefs_for_restoration(all_datarefs, inverted_mappings)

        # 4. Refresh Variables Table (Logic Engine state is already loaded)
        self._refresh_variables_table()

        log.info("Restored Output Panel state: %d rows", len(all_datarefs))

    def _clear_current_table(self):
        """Clear the current table and reset state."""
        while self.table.rowCount() > 0:
            self.table.removeRow(0)
        self._subscribed_datarefs.clear()

    def _get_monitored_datarefs(self) -> list:
        """Get monitored datarefs from the Arduino manager."""
        monitored = []
        if hasattr(self.arduino_manager, "get_monitored_datarefs"):
            monitored = self.arduino_manager.get_monitored_datarefs()
        return monitored

    def _get_inverted_mappings(self) -> dict:
        """Get inverted mappings from key to dataref."""
        raw_mappings = self.arduino_manager.get_all_universal_mappings()
        # Invert the mapping: from {key: {'source': dataref, ...}} to {dataref: key}
        inverted_mappings = {}
        for key, info in raw_mappings.items():
            if isinstance(info, dict) and "source" in info:
                dataref_source = info["source"]
                inverted_mappings[dataref_source] = key
        return inverted_mappings

    def _set_key_input_for_dataref(self, dataref: str, key: str):
        """Set the key input for a specific dataref."""
        if dataref in self._subscribed_datarefs:
            row = self._subscribed_datarefs[dataref]
            key_widget = self.table.cellWidget(row, 4)  # Output Key column
            if isinstance(key_widget, QLineEdit):
                key_widget.setText(key)

                # Update Arduino manager mapping
                self.arduino_manager.set_universal_mapping(
                    dataref, key
                )  # Empty key removes mapping
                if key:
                    log.info("Mapped %s -> %s", dataref, key)
                else:
                    log.info("Removed mapping for %s", dataref)

    def _process_datarefs_for_restoration(
        self, all_datarefs: set, inverted_mappings: dict
    ):
        """Process datarefs for restoration."""
        for dataref in all_datarefs:
            if self._is_logic_variable(dataref):
                log.debug("Skipping variable %s in Datarefs table", dataref)
                continue

            # Check if this is an array dataref for expansion
            info = self.dataref_manager.get_dataref_info(dataref)
            if info:
                data_type = info.get("type", "")
                size = self._parse_array_size(data_type)

                if size > 1:
                    # This is an array dataref - expand into individual elements
                    base = dataref.split("[")[0]  # Extract base name
                    for idx in range(size):
                        elem_name = f"{base}[{idx}]"
                        self._add_single_output_row(elem_name, dataref)

                        # If the base dataref has a mapping, apply it to the first element
                        # or create individual mappings if needed
                        if dataref in inverted_mappings:
                            # Apply the mapping to this element (we could create element-specific mappings if needed)
                            # For now, we'll just apply the base mapping to the first element
                            if idx == 0:
                                self._set_key_input_if_mapped(
                                    elem_name, inverted_mappings
                                )
                            # Or if we want to create element-specific mappings, we could do:
                            # self._set_key_input_if_mapped(elem_name, inverted_mappings)  # This would apply to each element
                else:
                    # Regular dataref - add single row
                    self._add_output_row(dataref)
                    self._set_key_input_if_mapped(dataref, inverted_mappings)
            else:
                # If no info available, treat as regular dataref
                self._add_output_row(dataref)
                self._set_key_input_if_mapped(dataref, inverted_mappings)

    def _is_logic_variable(self, dataref: str) -> bool:
        """Check if the dataref is a logic variable."""
        if not self.logic_engine:
            return False

        for block in self.logic_engine.get_blocks():
            if block.name == dataref:
                return True
        return False

    def _set_key_input_if_mapped(self, dataref: str, inverted_mappings: dict):
        """Set the key input if the dataref has a mapping."""
        if dataref not in inverted_mappings:
            return

        key = inverted_mappings[dataref]
        row = self._subscribed_datarefs.get(dataref)
        if row is not None:
            key_widget = self.table.cellWidget(row, 4)
            if isinstance(key_widget, QLineEdit):
                key_widget.setText(key)

                # Update Arduino manager mapping
                self.arduino_manager.set_universal_mapping(
                    dataref, key
                )  # Empty key removes mapping
                if key:
                    log.info("Mapped %s -> %s", dataref, key)
                else:
                    log.info("Removed mapping for %s", dataref)

    def _generate_code(self):
        """Generate Arduino code for all mappings."""
        mappings = self._collect_mappings_from_table()
        self._add_universal_mappings(mappings)

        if not mappings:
            QMessageBox.information(
                self, "No Mappings", "No output mappings configured."
            )
            return

        dataref_types = self._collect_dataref_types(mappings)
        dialog = CodeGeneratorDialog(mappings, dataref_types)
        dialog.exec()

    def _collect_mappings_from_table(self) -> dict:
        """Collect mappings from the table."""
        mappings = {}
        for dataref, row in self._subscribed_datarefs.items():
            key_widget = self.table.cellWidget(
                row, 4
            )  # Output Key column (column 4: "Output Key (Device ID)")
            if key_widget and isinstance(key_widget, QLineEdit):
                key = key_widget.text().strip()
                if key:
                    mappings[dataref] = key
        return mappings

    def _add_universal_mappings(self, mappings: dict):
        """Add universal mappings from the Arduino manager."""
        universal_mappings = self.arduino_manager.get_all_universal_mappings()
        for key, info in universal_mappings.items():
            if isinstance(info, dict) and "source" in info:
                dataref_source = info["source"]
                if (
                    dataref_source not in mappings and key
                ):  # Only add if not already in table mappings
                    mappings[dataref_source] = key

    def _collect_dataref_types(self, mappings: dict) -> dict:
        """Collect dataref types for each mapping."""
        dataref_types = {}
        for dataref in mappings.keys():
            info = self.dataref_manager.get_dataref_info(dataref)
            if info:
                dataref_types[dataref] = info.get("type", "")
        return dataref_types

    def on_dataref_update(self, dataref: str, value: float):
        """Handle dataref update from X-Plane."""
        # Store in the general live values cache for backward compatibility
        self._live_values[dataref] = value

        # Check if this is an array element update (e.g., LED_STATE[3])
        array_match = re.match(r"^(.+)\[(\d+)\]$", dataref)
        if array_match:
            base_name = array_match.group(1)
            index = int(array_match.group(2))

            # Update the specific array element in the UI
            element_name = f"{base_name}[{index}]"
            if element_name in self._subscribed_datarefs:
                row = self._subscribed_datarefs[element_name]
                self._update_table_item(row, element_name, value, "LIVE")
        else:
            # Regular dataref update - update the corresponding row in the UI
            if dataref in self._subscribed_datarefs:
                row = self._subscribed_datarefs[dataref]
                self._update_table_item(row, dataref, value, "LIVE")

    def _format_value(self, name: str, value: float, dtype: str) -> str:
        """Helper to format a value based on type (supports arrays/strings)."""
        try:
            if dtype == "command":
                return "COMMAND"

            if self._is_complex_dtype(dtype):
                return self._format_complex_value(name, dtype)

            return f"{float(value):.4f}"
        except Exception:
            return str(value)

    def _is_complex_dtype(self, dtype: str) -> bool:
        """Check if the data type is complex (array, string, or byte)."""
        return "[" in dtype or "string" in dtype or "byte" in dtype

    def _format_complex_value(self, name: str, dtype: str) -> str:
        """Format complex values (arrays, strings, bytes)."""
        base = name.split("[")[0]
        size = self._get_array_size(dtype)

        indices = self._get_array_indices(base, size)

        if not indices:
            return "..."

        return self._format_indices(indices, dtype)

    def _get_array_size(self, dtype: str) -> int:
        """Get the size of the array from the dtype."""
        m = re.search(r"\[(\d+)\]", dtype)
        return int(m.group(1)) if m else 1

    def _get_array_indices(self, base: str, size: int) -> list:
        """Get the array indices values."""
        indices = []
        for i in range(size):
            idx_name = f"{base}[{i}]"
            val = self._live_values.get(idx_name)
            if val is not None:
                indices.append(val)
            else:
                break
        return indices

    def _format_indices(self, indices: list, dtype: str) -> str:
        """Format the indices based on the data type."""
        if "string" in dtype or "byte" in dtype:
            return self._format_string_byte(indices)
        else:
            return self._format_numeric_array(indices)

    def _format_string_byte(self, indices: list) -> str:
        """Format string or byte array."""
        chars = [chr(int(v)) for v in indices if v > 0]
        reassembled = "".join(chars)
        return f'"{reassembled}"'

    def _format_numeric_array(self, indices: list) -> str:
        """Format numeric array."""
        display_vals = [f"{v:.2f}" for v in indices[:4]]
        text = "[" + ", ".join(display_vals)
        if len(indices) > 4:
            text += ", ..."
        return text + "]"

    def _update_live_values(self):
        """Update live values in both tables."""
        # 1. Update Datarefs Table
        self._update_datarefs_table_values()

        # 2. Update Variables Table (Logic Status)
        self._update_variables_table_values()

    def _update_datarefs_table_values(self):
        """Update values in the datarefs table."""
        for dataref, row in self._subscribed_datarefs.items():
            # Check if this is an array element (e.g., LED_STATE[3])
            array_match = re.match(r"^(.+)\[(\d+)\]$", dataref)
            if array_match:
                # This is an array element, get the base dataref name
                base_name = array_match.group(1)
                index = int(array_match.group(2))

                # Get the base dataref's live value (which should be an array/list)
                live_value = (
                    self.xplane_conn.get_live_value(base_name)
                    if self.xplane_conn
                    else None
                )

                if (
                    live_value is not None
                    and isinstance(live_value, (list, tuple))
                    and index < len(live_value)
                ):
                    value = live_value[index]
                    value_source = "LIVE"
                else:
                    # Fallback to stored value
                    value = self._live_values.get(dataref, 0.0)
                    value_source = None
            else:
                # Regular dataref (non-array)
                live_value = (
                    self.xplane_conn.get_live_value(dataref)
                    if self.xplane_conn
                    else None
                )
                virtual_value = (
                    self.xplane_conn.get_virtual_value(dataref)
                    if self.xplane_conn
                    else None
                )

                # Determine value and source
                value, value_source = self._get_value_and_source(
                    dataref, live_value, virtual_value
                )

            # Update the table item
            self._update_table_item(row, dataref, value, value_source)

    def _get_value_and_source(self, dataref: str, live_value, virtual_value):
        """Get the value and its source for a dataref."""
        # FIX: Check if this dataref is actually a Variable
        # If it is, get the value from the VariableStore instead
        if self.variable_store and dataref in self.variable_store.get_names():
            return self.variable_store.get_value(dataref) or 0.0, "VAR"
        elif live_value is not None:
            return live_value, "LIVE"
        elif virtual_value is not None:
            return virtual_value, "VIRTUAL"
        else:
            return self._live_values.get(dataref, 0.0), None

    def _update_table_item(
        self, row: int, dataref: str, value: float, value_source: str
    ):
        """Update the table item with formatted value."""
        item = self.table.item(row, 2)  # Value column
        if not item:
            return

        info = self.dataref_manager.get_dataref_info(dataref)
        dtype = info.get("type", "float") if info else "float"

        # Format the value appropriately
        formatted_value = self._format_value(dataref, value, dtype)

        # Append the source indicator
        if value_source:
            formatted_value = f"{formatted_value} ({value_source})"

        item.setText(formatted_value)

        # Update Arduino if mapped
        self._update_arduino_if_mapped(row, dataref, value)

    def _update_arduino_if_mapped(self, row: int, dataref: str, value: float):
        """Update Arduino if the dataref is mapped."""
        key_widget = self.table.cellWidget(row, 4)
        if key_widget and isinstance(key_widget, QLineEdit):
            key = key_widget.text().strip()
            if key:
                self.arduino_manager.on_dataref_update(dataref, value)

    def _update_variables_table_values(self):
        """Update values in the variables table."""
        if not (hasattr(self, "vars_table") and self.logic_engine):
            return

        for row in range(self.vars_table.rowCount()):
            name_item = self.vars_table.item(row, 0)
            if not name_item:
                continue
            name = name_item.text()

            # Get live value from VariableStore
            val = 0.0
            if self.variable_store:
                val = self.variable_store.get_value(name) or 0.0

            # Update Value column with consistent formatting
            val_item = self.vars_table.item(row, 2)
            if val_item:
                # Format consistently as float to prevent 0 vs 0.0000 flickering
                val_item.setText(f"{val:.4f}")
                # Color feedback: Green for 1, Gray for 0
                if val >= 0.5:
                    val_item.setForeground(QColor("#28a745"))  # Green
                else:
                    val_item.setForeground(QColor("#6c757d"))  # Gray

    def on_connection_changed(self, connected: bool):
        """Handle X-Plane connection state change."""
        if not connected:
            # Clear live values when disconnected
            self._live_values.clear()
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 1)
                if item:
                    item.setText("")

    def refresh_from_manager(self):
        """Refresh from the dataref manager."""
        log.info("OutputPanel: Refreshing dataref list and search completer.")
        self._dataref_list = self.dataref_manager.get_all_dataref_names()
        self._update_autocomplete()

    def _update_autocomplete(self):
        """Update the search box completer with fresh dataref names."""
        if hasattr(self, "search_input"):
            completer = QCompleter(self._dataref_list)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(20)
            self.search_input.setCompleter(completer)
            log.info(
                "OutputPanel: Search completer updated with %d items.",
                len(self._dataref_list),
            )

    def _show_context_menu(self, position):
        """Show context menu for copying datarefs and bulk operations."""
        item = self.table.itemAt(position)
        if not item:
            return

        row = item.row()
        dataref_item = self.table.item(row, 0)  # Dataref column
        if not dataref_item:
            return

        dataref = dataref_item.text()

        menu = QMenu(self)

        # Add copy action
        copy_action = menu.addAction("Copy Dataref Name")

        # Add separator and bulk operations if there are selected items
        selected_ranges = self.table.selectedRanges()
        has_selection = len(selected_ranges) > 0

        if has_selection:
            menu.addSeparator()

            # Count selected rows
            selected_count = 0
            for range_obj in selected_ranges:
                selected_count += (range_obj.bottomRow() - range_obj.topRow() + 1)

            # Select All action
            select_all_action = menu.addAction(f"Select All ({self.table.rowCount()} rows)")
            select_all_action.triggered.connect(self._select_all_rows)

            # Delete action
            delete_action = menu.addAction(f"Delete Selected ({selected_count} rows)")
            delete_action.triggered.connect(self._delete_selected_rows)

            # Add more bulk operations
            menu.addSeparator()
            refresh_action = menu.addAction(f"Refresh Selected ({selected_count} rows)")
            refresh_action.triggered.connect(self._refresh_selected_rows)

        action = menu.exec(self.table.viewport().mapToGlobal(position))

        if action and action == copy_action:
            clipboard = QApplication.clipboard()
            clipboard.setText(dataref)
            log.info("Copied dataref to clipboard: %s", dataref)

    def _refresh_selected_rows(self):
        """Refresh selected rows by unsubscribing and resubscribing to datarefs."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        # Get all selected rows
        selected_rows = set()
        for range_obj in selected_ranges:
            for row in range(range_obj.topRow(), range_obj.bottomRow() + 1):
                selected_rows.add(row)

        # Refresh each selected dataref
        for row in selected_rows:
            if row < self.table.rowCount():
                name_item = self.table.item(row, 0)
                if name_item:
                    dataref_name = name_item.text()
                    # Trigger a refresh by unsubscribing and resubscribing
                    if self.xplane_conn:
                        task1 = asyncio.create_task(self.xplane_conn.unsubscribe_dataref(dataref_name))
                        self._tasks.append(task1)

                        # Resubscribe after a short delay
                        def delayed_resubscribe():
                            task = asyncio.create_task(self.xplane_conn.subscribe_dataref(dataref_name))
                            self._tasks.append(task)

                        QTimer.singleShot(200, delayed_resubscribe)

    def _modify_value(self, row: int):
        """Open editor for a dataref or execute if it's a command."""
        dataref_item = self.table.item(row, 0)
        if not dataref_item:
            return

        dataref = dataref_item.text()
        info = self.dataref_manager.get_dataref_info(dataref) or {}
        dtype = info.get("type", "")

        # Better array detection - check for array type or array notation in name
        is_array = self._is_array_dataref(dataref, dtype)

        if is_array:
            current_values = self._get_current_array_values(dataref)
            # Use the more advanced DatarefEditorDialog for arrays instead of basic ArrayEditDialog
            dialog = DatarefEditorDialog(
                dataref_name=dataref,
                dataref_info=info,
                xplane_conn=self.xplane_conn,
                dataref_manager=self.dataref_manager,
                variable_store=self.variable_store,
                parent=self
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get the updated values from the dialog
                updated_values = dialog.get_array_values()
                if updated_values is not None:
                    # Send the array update
                    success = self._send_array_update(dataref, updated_values)
                    if success:
                        # Refresh the array display to show updated values
                        self._refresh_array_display(dataref)
                        log.info(f"Successfully updated array {dataref} with {len(updated_values)} values")
                    else:
                        log.error(f"Failed to update array {dataref}")
            return

        # Non-array path (existing behavior)
        if info.get("type") == "command":
            if self.xplane_conn:
                task = asyncio.create_task(self.xplane_conn.send_command(dataref))
                self._tasks.append(task)  # Prevent garbage collection
                log.info("UDP Trigger Command: %s", dataref)
                # Visual feedback on live value col
                item = self.table.item(row, 2)
                if item:
                    orig_text = item.text()
                    item.setText("EXECUTING...")
                    QTimer.singleShot(500, lambda: item.setText(orig_text))
            return

        # Use the generic _open_dataref_editor method (Tab 1 uses it, we should reuse)
        self._open_dataref_editor(dataref)

    def _is_array_dataref(self, dataref_name: str, dataref_type: str) -> bool:
        """Detect if a dataref is an array based on name or type."""
        try:
            # Check if type indicates array (contains brackets)
            if "[" in dataref_type and "]" in dataref_type:
                log.debug(f"Detected array by type brackets: {dataref_name} -> {dataref_type}")
                return True

            # Check if name contains array notation (e.g., dataref[0])
            if "[" in dataref_name and "]" in dataref_name:
                log.debug(f"Detected array by name brackets: {dataref_name}")
                return True

            # Check if type is a known array type pattern
            array_patterns = ["array", "list", "vector"]
            if any(pattern in dataref_type.lower() for pattern in array_patterns):
                log.debug(f"Detected array by type pattern: {dataref_name} -> {dataref_type}")
                return True

            # Check if the dataref manager indicates this is an array
            info = self.dataref_manager.get_dataref_info(dataref_name)
            if info and "type" in info:
                type_info = info["type"]
                is_array = "[" in type_info and "]" in type_info
                if is_array:
                    log.debug(f"Detected array by manager info: {dataref_name} -> {type_info}")
                return is_array

            log.debug(f"Not detected as array: {dataref_name} -> {dataref_type}")
            return False

        except Exception as e:
            log.error(f"Error detecting array for {dataref_name}: {e}")
            return False

    def _get_current_array_values(self, dataref_name: str) -> list:
        """Get current live values for array dataref (fallback to zeros)."""
        try:
            # For arrays, we need to get values for each element individually
            info = self.dataref_manager.get_dataref_info(dataref_name) or {}
            dtype = info.get("type", "") if info else ""
            size = self._parse_array_size(dtype)

            if size <= 0:
                log.warning(f"No array size detected for {dataref_name}, returning empty list")
                return []

            # Get individual element values
            values = []
            base_name = dataref_name.split('[')[0]
            for i in range(size):
                element_name = f"{base_name}[{i}]"
                live_val = None
                virt_val = None

                if self.xplane_conn:
                    try:
                        live_val = self.xplane_conn.get_live_value(element_name)
                    except Exception as e:
                        log.debug(f"Could not get live value for {element_name}: {e}")

                    if live_val is None:
                        try:
                            virt_val = self.xplane_conn.get_virtual_value(element_name)
                        except Exception as e:
                            log.debug(f"Could not get virtual value for {element_name}: {e}")

                if live_val is not None:
                    values.append(live_val)
                elif virt_val is not None:
                    values.append(virt_val)
                else:
                    values.append(0.0)

            log.debug(f"Retrieved {len(values)} values for array {dataref_name}")
            return values

        except Exception as e:
            log.error(f"Error getting current array values for {dataref_name}: {e}")
            # Return default values in case of error
            info = self.dataref_manager.get_dataref_info(dataref_name) or {}
            dtype = info.get("type", "") if info else ""
            size = self._parse_array_size(dtype)
            return [0.0] * max(0, size)

    def _refresh_array_display(self, dataref_name: str = None):
        """Efficiently refresh array display in the table with proper signal handling."""
        try:
            # Block signals during update to prevent triggering other events
            self.table.blockSignals(True)

            if dataref_name:
                # Refresh only a specific array dataref
                if dataref_name in self._subscribed_datarefs:
                    row = self._subscribed_datarefs[dataref_name]
                    self._update_single_row_display(row, dataref_name)
            else:
                # Refresh all array datarefs in the table
                for dataref, row in self._subscribed_datarefs.items():
                    if row < self.table.rowCount():  # Safety check
                        info = self.dataref_manager.get_dataref_info(dataref) or {}
                        dtype = info.get("type", "")

                        # Check if this is an array dataref
                        if self._is_array_dataref(dataref, dtype):
                            self._update_single_row_display(row, dataref)

            # Unblock signals after update
            self.table.blockSignals(False)

            log.debug(f"Array display refreshed for dataref: {dataref_name if dataref_name else 'ALL ARRAYS'}")

        except Exception as e:
            log.error(f"Error refreshing array display: {e}")
            # Always unblock signals even if there's an error
            self.table.blockSignals(False)

    def _update_single_row_display(self, row: int, dataref_name: str):
        """Update the display of a single row for an array dataref."""
        try:
            # Update the live value column
            value_item = self.table.item(row, 2)  # Assuming column 2 is the value column
            if value_item and self.xplane_conn:
                # Get the current value from X-Plane connection
                current_value = self.xplane_conn.get_live_value(dataref_name)
                if current_value is not None:
                    formatted_value = self._format_value(dataref_name, current_value, "")
                    value_item.setText(formatted_value)

                    # Update color based on value
                    if isinstance(current_value, (int, float)) and current_value >= 0.5:
                        value_item.setForeground(QColor("#28a745"))  # Green
                    else:
                        value_item.setForeground(QColor("#6c757d"))  # Gray

            # Update the modify button text if needed
            modify_widget = self.table.cellWidget(row, 3)  # Assuming column 3 is the action column
            if modify_widget:
                # Find the actual button in the widget
                for child in modify_widget.findChildren(QPushButton):
                    if "inspect" in child.text().lower() or "edit" in child.text().lower():
                        info = self.dataref_manager.get_dataref_info(dataref_name) or {}
                        dtype = info.get("type", "")
                        is_array = self._is_array_dataref(dataref_name, dtype)
                        is_command = dtype == "command"

                        new_text = (
                            "EXECUTE" if is_command
                            else ("Inspect/Edit Array" if is_array else "Write")
                        )
                        child.setText(new_text)

        except Exception as e:
            log.error(f"Error updating single row display for {dataref_name}: {e}")

    def _format_value(self, dataref_name: str, value, dtype: str) -> str:
        """Format a value for display in the table."""
        if isinstance(value, list):
            # For array values, show a summary
            if len(value) <= 5:
                return f"[{', '.join([f'{v:.2f}' for v in value])}]"
            else:
                return f"[{len(value)} elements: {value[0]:.2f}, {value[1]:.2f}, ...]"
        elif isinstance(value, (int, float)):
            return f"{value:.4f}"
        else:
            return str(value)

    def _send_array_update(self, dataref_name: str, values: list):
        """Send array update to X-Plane via dataref writer with validation and batch processing."""
        # Validate inputs
        if not dataref_name or not values:
            log.warning(f"Invalid array update: dataref='{dataref_name}', values={values}")
            return False

        # Validate values are numeric
        validated_values = []
        for i, val in enumerate(values):
            try:
                validated_val = float(val)
                validated_values.append(validated_val)
            except (TypeError, ValueError):
                log.warning(f"Invalid value at index {i}: {val}. Setting to 0.0")
                validated_values.append(0.0)

        # Determine the dataref type to call the appropriate write method
        info = self.dataref_manager.get_dataref_info(dataref_name) or {}
        dtype = info.get("type", "")

        # Use the X-Plane connection to send each element individually
        if self.xplane_conn:
            # For array updates, we need to send each element to its indexed dataref
            base_name = dataref_name.split('[')[0]  # Extract base name

            # Calculate batch size for large arrays to prevent overwhelming the connection
            batch_size = min(10, len(validated_values))  # Process in batches of 10 or less
            total_batches = (len(validated_values) + batch_size - 1) // batch_size

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(validated_values))

                # Process this batch
                for i in range(start_idx, end_idx):
                    if i < len(validated_values):  # Safety check
                        indexed_dataref = f"{base_name}[{i}]"
                        task = asyncio.create_task(self.xplane_conn.write_dataref(indexed_dataref, float(validated_values[i])))
                        self._tasks.append(task)

                # Small delay between batches to prevent overwhelming the connection
                if batch_idx < total_batches - 1:  # Don't delay after the last batch
                    asyncio.create_task(asyncio.sleep(0.01))  # 10ms delay between batches

            log.info(f"Sent array update for {dataref_name} with {len(validated_values)} elements in {total_batches} batches")
            return True
        else:
            log.warning("X-Plane connection not available for array update")
            return False

    def verify_integration(self):
        """Verify complete integration and propagation of array operations."""
        try:
            # Check if all required components are available
            components_check = {
                'dataref_manager': self.dataref_manager is not None,
                'xplane_conn': self.xplane_conn is not None,
                'arduino_manager': self.arduino_manager is not None,
                'table_exists': hasattr(self, 'table'),
                'array_methods_exist': all([
                    hasattr(self, '_is_array_dataref'),
                    hasattr(self, '_parse_array_size'),
                    hasattr(self, '_get_current_array_values'),
                    hasattr(self, '_send_array_update'),
                    hasattr(self, '_refresh_array_display')
                ])
            }

            all_components_ok = all(components_check.values())

            # Test array detection
            sample_array_types = ["float[8]", "int[4]", "float[2][3]"]
            detection_results = {}
            for arr_type in sample_array_types:
                size = self._parse_array_size(arr_type)
                detection_results[arr_type] = size

            # Test with a known array dataref if available
            sample_arrays = []
            all_datarefs = self.dataref_manager.get_all_dataref_names() if self.dataref_manager else []

            # Look for potential array datarefs
            for dr in all_datarefs[:10]:  # Check first 10 datarefs
                info = self.dataref_manager.get_dataref_info(dr)
                if info and '[' in str(info.get('type', '')):
                    sample_arrays.append(dr)
                    break

            array_expansion_test = {}
            if sample_arrays:
                for arr_name in sample_arrays:
                    info = self.dataref_manager.get_dataref_info(arr_name)
                    dtype = info.get("type", "")
                    size = self._parse_array_size(dtype)
                    is_arr = self._is_array_dataref(arr_name, dtype)
                    array_expansion_test[arr_name] = {
                        'size': size,
                        'is_array': is_arr,
                        'type': dtype
                    }

            # Log results
            log.info("=== INTEGRATION VERIFICATION RESULTS ===")
            log.info(f"Component Availability: {components_check}")
            log.info(f"All Components OK: {all_components_ok}")
            log.info(f"Array Type Detection: {detection_results}")
            log.info(f"Sample Array Analysis: {array_expansion_test}")

            # Test subscription mapping integrity
            subscription_integrity = len(self._subscribed_datarefs) if hasattr(self, '_subscribed_datarefs') else 0
            table_row_count = self.table.rowCount() if hasattr(self, 'table') else 0
            log.info(f"Subscription Mapping Integrity: {subscription_integrity} mappings, {table_row_count} rows")

            # Overall status
            overall_status = all_components_ok and len(detection_results) > 0
            log.info(f"Overall Integration Status: {'SUCCESS' if overall_status else 'ISSUES DETECTED'}")
            log.info("========================================")

            return {
                'status': overall_status,
                'components': components_check,
                'detection': detection_results,
                'arrays': array_expansion_test,
                'subscription_count': subscription_integrity,
                'table_rows': table_row_count
            }

        except Exception as e:
            log.error(f"Error during integration verification: {e}")
            return {'status': False, 'error': str(e)}

    def _on_row_double_clicked(self, index):
        """Handle double-click on a row to assign it to an open dialog."""
        row = index.row()
        item = self.table.item(row, 0)
        if not item:
            return

        dataref = item.text()

        # Look for active InputMappingDialog in the application
        # It's usually a child of InputPanel
        from .input_mapping_dialog import InputMappingDialog
        from .input_panel import InputPanel

        # Traverse up to MainWindow then find InputPanel
        main_win = self.window()
        if main_win:
            # Look for InputPanel via the tabs
            for i in range(main_win.tabs.count()):
                widget = main_win.tabs.widget(i)
                if isinstance(widget, InputPanel) and widget._learning_dialog:
                    widget._learning_dialog.assign_dataref(dataref)
                    log.info("Assigned dataref via double-click: %s", dataref)
                    return

    def _on_cell_clicked(self, row, col):
        """Handle clicking on cells (e.g. for description popup)."""
        if col == 1:  # Description column
            item = self.table.item(row, col)
            if item:
                dataref_item = self.table.item(row, 0)
                dataref_name = dataref_item.text() if dataref_item else "Dataref"

                QMessageBox.information(
                    self, f"Description: {dataref_name}", item.text()
                )
