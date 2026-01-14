from __future__ import annotations
import logging
import re
from typing import List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QDoubleSpinBox, QLineEdit,
    QDialogButtonBox, QScrollArea, QWidget, QGridLayout
)
from PyQt6.QtCore import Qt

log = logging.getLogger(__name__)

class ArrayEditDialog(QDialog):
    """Popup to edit all elements of an array dataref."""

    def __init__(self, dataref_name: str, current_values: List, dataref_type: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Array: {dataref_name}")
        self.setMinimumSize(700, 600)

        self.dataref_name = dataref_name
        self.dataref_type = dataref_type
        self.values = list(current_values)
        self.original_values = list(current_values)  # Keep original for reset functionality

        # Parse array dimensions from type string
        self.dimensions = self._parse_array_dimensions(dataref_type)

        # Performance optimization: threshold for large arrays
        self.large_array_threshold = 100
        self.is_large_array = len(current_values) > self.large_array_threshold

        layout = QVBoxLayout(self)

        # Add performance warning for large arrays
        header_text = f"<b>Dataref:</b> {dataref_name}<br><b>Type:</b> {dataref_type}<br><b>Total Elements:</b> {len(current_values)}"
        if self.is_large_array:
            header_text += f"<br><span style='color: orange;'>⚠️ Large array detected ({len(current_values)} elements). UI may be slower.</span>"

        header = QLabel(header_text)
        layout.addWidget(header)

        # Create scrollable area for the table
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Performance optimization: temporarily disable updates during population
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Element Index", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)

        # Disable sorting and updates during population for performance
        self.table.setSortingEnabled(False)
        self.table.setUpdatesEnabled(False)

        self._populate_elements()

        # Re-enable updates after population
        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(True)

        # Resize columns to fit content after population
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        scroll_layout.addWidget(self.table)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        layout.addWidget(scroll_area)

        # Add status label for user feedback
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        update_all_btn = QPushButton("Update All Elements")
        update_all_btn.clicked.connect(self._accept_and_send)
        btn_layout.addWidget(update_all_btn)

        # Add Reset button to revert changes
        reset_btn = QPushButton("Reset Changes")
        reset_btn.clicked.connect(self._reset_changes)
        btn_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _reset_changes(self):
        """Reset all values to their original state."""
        reply = QMessageBox.question(
            self,
            "Reset Changes",
            "Are you sure you want to reset all values to their original state?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Update the widgets with original values
            for row in range(self.table.rowCount()):
                if row < len(self.original_values):
                    original_value = self.original_values[row]
                    widget = self.table.cellWidget(row, 1)
                    self._update_widget_with_value(widget, original_value)

            # Update internal values
            self.values = list(self.original_values)
            self.status_label.setText("Values reset to original state")

    def _update_widget_with_value(self, widget, value):
        """Update a widget with a specific value."""
        if isinstance(widget, QDoubleSpinBox):
            try:
                widget.setValue(float(value))
            except (ValueError, TypeError):
                log.warning(f"Could not convert {value} to float for DoubleSpinBox")
        elif isinstance(widget, QSpinBox):
            try:
                widget.setValue(int(value))
            except (ValueError, TypeError):
                log.warning(f"Could not convert {value} to int for SpinBox")
        elif isinstance(widget, QCheckBox):
            if isinstance(value, bool):
                widget.setChecked(value)
            else:
                widget.setChecked(bool(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value))
        else:
            # For other widget types
            if hasattr(widget, 'setValue'):
                try:
                    widget.setValue(value)
                except:
                    log.warning(f"Could not set value {value} for widget {type(widget)}")
            elif hasattr(widget, 'setText'):
                widget.setText(str(value))
            elif hasattr(widget, 'setChecked'):
                widget.setChecked(bool(value))

    def _parse_array_dimensions(self, type_str: str) -> List[int]:
        """Parse array dimensions from type string (e.g., 'float[8][4]' -> [8, 4])."""
        if not type_str:
            return []
        import re
        dims = [int(n) for n in re.findall(r"\[(\d+)\]", type_str)]
        return dims

    def _populate_elements(self):
        """Fill table with array elements (index and value)."""
        self.table.setRowCount(0)
        for idx, value in enumerate(self.values):
            # Calculate multi-dimensional index representation if applicable
            element_label = f"[{idx}]"
            if self.dimensions:
                # For multi-dimensional arrays, show the flattened index with multi-dim representation
                multi_dim_idx = self._calculate_multi_dim_indices(idx, self.dimensions)
                if len(multi_dim_idx) > 1:
                    element_label = f"[{idx}] ({'[' + ']['.join(map(str, multi_dim_idx)) + ']'})"

            elem_item = QTableWidgetItem(element_label)
            elem_item.setFlags(elem_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.insertRow(self.table.rowCount())
            self.table.setItem(self.table.rowCount()-1, 0, elem_item)

            # Determine the appropriate widget based on value type and dataref type
            val_widget = self._create_widget_for_value(value, self.dataref_type)
            self.table.setCellWidget(self.table.rowCount()-1, 1, val_widget)

    def _create_widget_for_value(self, value, dataref_type):
        """Create appropriate input widget based on value type and dataref type."""
        # Check if the dataref type specifies a particular type
        if "int" in dataref_type:
            # Integer type
            from PyQt6.QtWidgets import QSpinBox
            widget = QSpinBox()
            # Determine range based on potential dataref specifications
            if "[int" in dataref_type and "]" in dataref_type:
                # Look for specific integer size in type string like "int[8]" or "int[16]"
                import re
                match = re.search(r'int\[(\d+)\]', dataref_type)
                if match:
                    bits = int(match.group(1))
                    if bits <= 8:
                        widget.setRange(-128, 127)
                    elif bits <= 16:
                        widget.setRange(-32768, 32767)
                    elif bits <= 32:
                        widget.setRange(-2147483648, 2147483647)
                    else:
                        widget.setRange(-2147483648, 2147483647)  # Max 32-bit range
                else:
                    widget.setRange(-2147483648, 2147483647)  # Default 32-bit range
            else:
                widget.setRange(-2147483648, 2147483647)  # Default 32-bit range
            widget.setValue(int(value) if isinstance(value, (int, float)) else 0)
        elif "float" in dataref_type or isinstance(value, float):
            # Float type
            widget = QDoubleSpinBox()
            # Set range based on dataref type specification if available
            if "[float" in dataref_type and "]" in dataref_type:
                # Look for specific float precision in type string
                import re
                match = re.search(r'float\[(\d+)(?:\.(\d+))?\]', dataref_type)
                if match:
                    # Extract precision information if available
                    total_digits = int(match.group(1)) if match.group(1) else 10
                    decimal_places = int(match.group(2)) if match.group(2) else 6
                    widget.setDecimals(decimal_places)
                else:
                    widget.setDecimals(6)  # Default precision for floats
            else:
                widget.setDecimals(6)  # Default precision for floats
            widget.setRange(-999999, 999999)
            widget.setValue(float(value) if isinstance(value, (int, float)) else 0.0)
        elif "bool" in dataref_type or isinstance(value, bool):
            # Boolean type
            from PyQt6.QtWidgets import QCheckBox
            widget = QCheckBox()
            widget.setChecked(bool(value) if isinstance(value, (bool, int, float)) else False)
        elif "string" in dataref_type or isinstance(value, str):
            # String type
            widget = QLineEdit()
            widget.setText(str(value))
            # Add validator for string length if specified in type
            if "[string" in dataref_type and "]" in dataref_type:
                import re
                match = re.search(r'string\[(\d+)\]', dataref_type)
                if match:
                    max_length = int(match.group(1))
                    widget.setMaxLength(max_length)
        else:
            # Default to float for numeric values or string for others
            if isinstance(value, (int, float)):
                widget = QDoubleSpinBox()
                widget.setRange(-999999, 999999)
                widget.setDecimals(4 if isinstance(value, float) else 0)
                widget.setValue(float(value))
            else:
                widget = QLineEdit()
                widget.setText(str(value))

        # Add validation based on dataref type
        self._apply_validation(widget, dataref_type)

        return widget

    def _apply_validation(self, widget, dataref_type):
        """Apply appropriate validation based on dataref type."""
        from PyQt6.QtGui import QIntValidator, QDoubleValidator, QRegularExpressionValidator
        from PyQt6.QtCore import QRegularExpression

        if isinstance(widget, QLineEdit):
            # Apply validation based on dataref type
            if "int" in dataref_type:
                # Integer validation
                validator = QIntValidator()
                widget.setValidator(validator)
            elif "float" in dataref_type:
                # Float validation
                validator = QDoubleValidator()
                widget.setValidator(validator)
            elif "bool" in dataref_type:
                # Boolean validation - only allow valid boolean strings
                regex = QRegularExpression(r'^(true|false|True|False|TRUE|FALSE|0|1|yes|no|YES|NO)$')
                validator = QRegularExpressionValidator(regex)
                widget.setValidator(validator)

    def _calculate_multi_dim_indices(self, flat_index: int, dimensions: List[int]) -> List[int]:
        """Convert a flat index to multi-dimensional indices."""
        if not dimensions:
            return [flat_index]

        indices = []
        remaining = flat_index

        # Process dimensions from outermost to innermost
        for dim_size in reversed(dimensions[1:]):  # All except the first
            indices.insert(0, remaining % dim_size)
            remaining //= dim_size

        # Add the outermost dimension
        indices.insert(0, remaining)

        return indices

    def _accept_and_send(self):
        """Collect all element values and return to caller with proper data conversion and error handling."""
        new_values = []
        errors = []
        validation_errors = []

        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 1)
            element_idx = row  # This corresponds to the array index

            try:
                if isinstance(widget, QDoubleSpinBox):
                    new_values.append(widget.value())
                elif isinstance(widget, QSpinBox):
                    new_values.append(widget.value())
                elif isinstance(widget, QCheckBox):
                    new_values.append(widget.isChecked())
                elif isinstance(widget, QLineEdit):
                    # For QLineEdit, try to determine the appropriate type based on the dataref type
                    text_value = widget.text()

                    # Validate the input first if there's a validator
                    if widget.validator():
                        state, _, _ = widget.validator().validate(text_value, 0)
                        if state == widget.validator().State.Invalid:
                            validation_errors.append(f"Invalid format at index {element_idx}: '{text_value}'")

                    # Check the expected type based on the original dataref type
                    if "int" in self.dataref_type:
                        try:
                            new_values.append(int(text_value))
                        except ValueError:
                            # If conversion fails, try float then default to 0
                            try:
                                new_values.append(int(float(text_value)))
                            except ValueError:
                                errors.append(f"Invalid integer value at index {element_idx}: '{text_value}'")
                                new_values.append(0)  # Default value
                    elif "float" in self.dataref_type:
                        try:
                            new_values.append(float(text_value))
                        except ValueError:
                            errors.append(f"Invalid float value at index {element_idx}: '{text_value}'")
                            new_values.append(0.0)  # Default value
                    elif "bool" in self.dataref_type:
                        # Convert string to boolean (true/1/yes = True, false/0/no = False)
                        lower_text = text_value.lower().strip()
                        if lower_text in ('true', '1', 'yes', 'on'):
                            new_values.append(True)
                        elif lower_text in ('false', '0', 'no', 'off', ''):
                            new_values.append(False)
                        else:
                            # Try to interpret as numeric (non-zero = True)
                            try:
                                num_val = float(text_value)
                                new_values.append(num_val != 0)
                            except ValueError:
                                errors.append(f"Invalid boolean value at index {element_idx}: '{text_value}'")
                                new_values.append(False)  # Default value
                    else:
                        # Default to float conversion, fallback to string
                        try:
                            new_values.append(float(text_value))
                        except ValueError:
                            new_values.append(text_value)  # Keep as string
                else:
                    # Fallback for any other widget type
                    if hasattr(widget, 'value'):
                        new_values.append(widget.value())
                    elif hasattr(widget, 'text'):
                        new_values.append(widget.text())
                    elif hasattr(widget, 'isChecked'):
                        new_values.append(widget.isChecked())
                    else:
                        new_values.append(str(widget))
            except Exception as e:
                errors.append(f"Error processing value at index {element_idx}: {str(e)}")
                # Add a default value based on expected type
                if "int" in self.dataref_type:
                    new_values.append(0)
                elif "float" in self.dataref_type:
                    new_values.append(0.0)
                elif "bool" in self.dataref_type:
                    new_values.append(False)
                else:
                    new_values.append(0.0)

        # Combine all errors
        all_errors = validation_errors + errors

        # If there were errors, show them to the user
        if all_errors:
            from PyQt6.QtWidgets import QMessageBox
            error_msg = "\n".join(all_errors)
            result = QMessageBox.warning(self, "Validation Errors",
                                       f"Some values had validation errors and were set to defaults:\n\n{error_msg}",
                                       QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel,
                                       QMessageBox.StandardButton.Ok)

            # If user clicked Retry, return without accepting
            if result == QMessageBox.StandardButton.Retry:
                return
            elif result == QMessageBox.StandardButton.Cancel:
                self.reject()
                return

        # Check if this is a large array update and warn the user
        if len(new_values) > 50:  # Threshold for large arrays
            reply = QMessageBox.question(
                self,
                "Large Array Update",
                f"You are about to update {len(new_values)} array elements. This may take a moment. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return  # Cancel the update

        self.values = new_values
        self.status_label.setText(f"Updated {len(new_values)} array elements")
        self.accept()

    def _update_element(self, index: int, new_value):
        """
        Update a single element in the array without refreshing the entire table.

        Args:
            index: The index of the element to update
            new_value: The new value for the element
        """
        if 0 <= index < self.table.rowCount():
            widget = self.table.cellWidget(index, 1)

            # Update the widget based on its type
            if isinstance(widget, QDoubleSpinBox):
                try:
                    widget.setValue(float(new_value))
                except (ValueError, TypeError):
                    log.warning(f"Could not convert {new_value} to float for DoubleSpinBox")
            elif isinstance(widget, QSpinBox):
                try:
                    widget.setValue(int(new_value))
                except (ValueError, TypeError):
                    log.warning(f"Could not convert {new_value} to int for SpinBox")
            elif isinstance(widget, QCheckBox):
                if isinstance(new_value, bool):
                    widget.setChecked(new_value)
                else:
                    # Convert to boolean: non-zero numbers and non-empty strings are True
                    widget.setChecked(bool(new_value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(new_value))
            else:
                # For other widget types, try to update appropriately
                if hasattr(widget, 'setValue'):
                    try:
                        widget.setValue(new_value)
                    except:
                        log.warning(f"Could not set value {new_value} for widget {type(widget)}")
                elif hasattr(widget, 'setText'):
                    widget.setText(str(new_value))
                elif hasattr(widget, 'setChecked'):
                    widget.setChecked(bool(new_value))

            # Update our internal values list as well
            if index < len(self.values):
                self.values[index] = new_value