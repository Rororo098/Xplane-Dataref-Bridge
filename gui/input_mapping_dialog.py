from __future__ import annotations
import logging
import math
from typing import Optional, List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox,
    QFormLayout, QDoubleSpinBox, QSpinBox, QGroupBox,
    QDialogButtonBox, QStackedWidget, QWidget, QMessageBox,
    QCompleter, QSlider, QFrame, QScrollArea, QListWidget,
    QListWidgetItem, QSizePolicy, QGridLayout, QRadioButton,
    QButtonGroup, QTextEdit, QToolButton, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QIcon, QPainter, QPen, QBrush, QColor, QPainterPath

from core.input_mapper import InputMapping, InputAction, SequenceAction, TargetAction, Condition
from .axis_calibration_wizard import AxisCalibrationWizard # NEW: Import Wizard

log = logging.getLogger(__name__)

# Constants for commonly used literals
FONT_SEGOE_UI = "Segoe UI"
CSS_DESCRIPTION_STYLE = "color: #555; background: #fafafa; padding: 8px; border-radius: 4px;"


class AxisPreviewWidget(QWidget):
    """
    Live preview widget showing axis input, deadzone, and processed output.
    Visualizes the relationship between raw input and processed output.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setMaximumHeight(150)
        
        # Axis state
        self._raw_value = 0.0
        self._processed_value = 0.0
        self._deadzone = 0.05
        self._deadzone_pos = "center"
        self._curve = "linear"
        self._inverted = False
        
        # Animation
        self._demo_mode = True
        self._demo_timer = QTimer()
        self._demo_timer.timeout.connect(self._animate_demo)
        self._demo_timer.start(50)
        self._demo_angle = 0.0
    
    def set_raw_value(self, value: float):
        """Set the raw input value (-1.0 to 1.0)."""
        self._raw_value = max(-1.0, min(1.0, value))
        self._update_processed_value()
        self.update()
    
    def set_deadzone(self, value: float):
        """Set deadzone size (0.0 to 0.5)."""
        self._deadzone = max(0.0, min(0.5, value))
        self._update_processed_value()
        self.update()
    
    def set_deadzone_position(self, position: str):
        """Set deadzone position: center, left, right, ends."""
        self._deadzone_pos = position
        self._update_processed_value()
        self.update()
    
    def set_curve(self, curve: str):
        """Set response curve type."""
        self._curve = curve
        self._update_processed_value()
        self.update()
    
    def set_inverted(self, inverted: bool):
        """Set axis inversion."""
        self._inverted = inverted
        self._update_processed_value()
        self.update()
    
    def set_demo_mode(self, enabled: bool):
        """Enable/disable demo animation."""
        self._demo_mode = enabled
        if enabled:
            self._demo_timer.start(50)
        else:
            self._demo_timer.stop()
    
    def _animate_demo(self):
        """Animate the axis in demo mode."""
        if self._demo_mode:
            self._demo_angle += 0.05
            self._raw_value = math.sin(self._demo_angle) * 0.85
            self._update_processed_value()
            self.update()
    
    def _update_processed_value(self):
        """Calculate processed value based on current settings."""
        value = self._raw_value

        # Apply deadzone
        value = self._apply_deadzone(value)

        # Apply curve
        value = self._apply_curve(value)

        # Apply inversion
        if self._inverted:
            value = -value

        self._processed_value = max(-1.0, min(1.0, value))

    def _apply_deadzone(self, value: float) -> float:
        """Apply deadzone based on position setting."""
        dz = self._deadzone
        if dz <= 0:
            return value

        if self._deadzone_pos == "center":
            return self._apply_center_deadzone(value, dz)
        elif self._deadzone_pos == "left":
            return self._apply_left_deadzone(value, dz)
        elif self._deadzone_pos == "right":
            return self._apply_right_deadzone(value, dz)
        elif self._deadzone_pos == "ends":
            return self._apply_ends_deadzone(value, dz)
        else:
            return value

    def _apply_center_deadzone(self, value: float, dz: float) -> float:
        """Apply deadzone at center."""
        if abs(value) < dz:
            return 0.0
        else:
            sign = 1.0 if value > 0 else -1.0
            return sign * (abs(value) - dz) / (1.0 - dz)

    def _apply_left_deadzone(self, value: float, dz: float) -> float:
        """Apply deadzone at left (minimum)."""
        val_01 = (value + 1.0) / 2.0
        if val_01 < dz:
            return -1.0
        else:
            scaled = (val_01 - dz) / (1.0 - dz)
            return scaled * 2.0 - 1.0

    def _apply_right_deadzone(self, value: float, dz: float) -> float:
        """Apply deadzone at right (maximum)."""
        val_01 = (value + 1.0) / 2.0
        if val_01 > (1.0 - dz):
            return 1.0
        else:
            scaled = val_01 / (1.0 - dz)
            return scaled * 2.0 - 1.0

    def _apply_ends_deadzone(self, value: float, dz: float) -> float:
        """Apply deadzone at both ends."""
        val_01 = (value + 1.0) / 2.0
        dz_half = dz / 2.0
        if val_01 < dz_half:
            return -1.0
        elif val_01 > (1.0 - dz_half):
            return 1.0
        else:
            scaled = (val_01 - dz_half) / (1.0 - dz)
            return scaled * 2.0 - 1.0

    def _apply_curve(self, value: float) -> float:
        """Apply response curve to the value."""
        sign = 1.0 if value >= 0 else -1.0
        abs_val = abs(value)

        if self._curve == "aggressive":
            return sign * math.pow(abs_val, 0.5)
        elif self._curve == "soft":
            return sign * math.pow(abs_val, 2.0)
        elif self._curve == "smooth":
            return sign * math.pow(abs_val, 1.5)
        elif self._curve == "ultra_fine":
            return sign * math.pow(abs_val, 3.0)
        elif self._curve == "s_curve":
            # S-curve using smoothstep
            t = abs_val
            return sign * (t * t * (3.0 - 2.0 * t))
        elif self._curve == "exponential":
            return sign * ((math.exp(abs_val) - 1) / (math.e - 1))
        else:
            return value  # Linear (no curve)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, _ = self.width(), self.height()
        margin = 15
        bar_height = 24
        
        # Colors
        bg_color = QColor("#e0e0e0")
        dz_color = QColor(255, 200, 200, 150)
        active_gradient_start = QColor("#0078d4")
        active_gradient_end = QColor("#28a745")
        indicator_color = QColor("#333333")
        text_color = QColor("#333333")
        
        # === Raw Input Bar ===
        raw_y = margin
        painter.setPen(QPen(QColor("#999"), 1))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(margin, raw_y, w - 2*margin, bar_height, 4, 4)
        
        # Draw deadzone region
        dz = self._deadzone
        dz_pen = QPen(QColor("#e74c3c"), 1, Qt.PenStyle.DashLine)
        
        if self._deadzone_pos == "center" and dz > 0:
            dz_left = margin + (w - 2*margin) * (0.5 - dz/2)
            dz_width = (w - 2*margin) * dz
            painter.fillRect(int(dz_left), raw_y, int(dz_width), bar_height, dz_color)
            painter.setPen(dz_pen)
            painter.drawLine(int(dz_left), raw_y, int(dz_left), raw_y + bar_height)
            painter.drawLine(int(dz_left + dz_width), raw_y, int(dz_left + dz_width), raw_y + bar_height)
        
        elif self._deadzone_pos == "left" and dz > 0:
            dz_width = (w - 2*margin) * dz
            painter.fillRect(margin, raw_y, int(dz_width), bar_height, dz_color)
            painter.setPen(dz_pen)
            painter.drawLine(int(margin + dz_width), raw_y, int(margin + dz_width), raw_y + bar_height)
        
        elif self._deadzone_pos == "right" and dz > 0:
            dz_width = (w - 2*margin) * dz
            dz_left = w - margin - dz_width
            painter.fillRect(int(dz_left), raw_y, int(dz_width), bar_height, dz_color)
            painter.setPen(dz_pen)
            painter.drawLine(int(dz_left), raw_y, int(dz_left), raw_y + bar_height)
        
        elif self._deadzone_pos == "ends" and dz > 0:
            dz_width = (w - 2*margin) * dz / 2
            painter.fillRect(margin, raw_y, int(dz_width), bar_height, dz_color)
            painter.fillRect(int(w - margin - dz_width), raw_y, int(dz_width), bar_height, dz_color)
            painter.setPen(dz_pen)
            painter.drawLine(int(margin + dz_width), raw_y, int(margin + dz_width), raw_y + bar_height)
            painter.drawLine(int(w - margin - dz_width), raw_y, int(w - margin - dz_width), raw_y + bar_height)
        
        # Draw raw input indicator
        raw_pos = margin + (self._raw_value + 1.0) / 2.0 * (w - 2*margin)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(indicator_color))
        painter.drawRoundedRect(int(raw_pos) - 3, raw_y - 3, 6, bar_height + 6, 3, 3)
        
        # Labels
        painter.setPen(text_color)
        painter.setFont(QFont(FONT_SEGOE_UI, 8))
        painter.drawText(margin, raw_y - 3, "Raw Input")
        painter.drawText(w - margin - 50, raw_y - 3, f"{self._raw_value:.2f}")
        
        # === Processed Output Bar ===
        proc_y = raw_y + bar_height + 25
        painter.setPen(QPen(QColor("#999"), 1))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(margin, proc_y, w - 2*margin, bar_height, 4, 4)
        
        # Draw active fill gradient
        fill_width = abs(self._processed_value) * (w - 2*margin) / 2
        if self._processed_value >= 0:
            fill_x = margin + (w - 2*margin) / 2
        else:
            fill_x = margin + (w - 2*margin) / 2 - fill_width
        
        gradient_rect = QRectF(fill_x, proc_y, fill_width, bar_height)
        painter.fillRect(gradient_rect, QBrush(active_gradient_end if self._processed_value >= 0 else active_gradient_start))
        
        # Draw processed indicator
        proc_pos = margin + (self._processed_value + 1.0) / 2.0 * (w - 2*margin)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#28a745")))
        painter.drawRoundedRect(int(proc_pos) - 4, proc_y - 4, 8, bar_height + 8, 4, 4)
        
        # Labels
        painter.setPen(text_color)
        painter.drawText(margin, proc_y - 3, "Processed Output")
        painter.drawText(w - margin - 50, proc_y - 3, f"{self._processed_value:.2f}")
        
        # Center line
        center_x = margin + (w - 2*margin) / 2
        painter.setPen(QPen(QColor("#666"), 1, Qt.PenStyle.DotLine))
        painter.drawLine(int(center_x), raw_y, int(center_x), proc_y + bar_height)
        
        # Scale labels
        painter.setFont(QFont(FONT_SEGOE_UI, 7))
        painter.setPen(QColor("#888"))
        painter.drawText(margin, proc_y + bar_height + 12, "-1.0")
        painter.drawText(int(center_x) - 5, proc_y + bar_height + 12, "0")
        painter.drawText(w - margin - 20, proc_y + bar_height + 12, "1.0")


class CurvePreviewWidget(QWidget):
    """
    Visualizes response curves with a graph.
    Shows linear reference and the selected curve.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 100)
        self.setMaximumSize(200, 120)
        self._curve = "linear"
    
    def set_curve(self, curve: str):
        self._curve = curve
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        margin = 10

        # Background
        painter.fillRect(0, 0, w, h, QColor("#1e1e1e"))

        # Grid
        painter.setPen(QPen(QColor("#333"), 0.5))
        painter.drawLine(margin, h - margin, w - margin, h - margin)  # X axis
        painter.drawLine(margin, margin, margin, h - margin)  # Y axis
        painter.drawLine(margin, margin, w - margin, h - margin)  # Diagonal (linear reference)
        
        # Linear reference (dashed)
        painter.setPen(QPen(QColor("#444"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(margin, h - margin, w - margin, margin)
        
        # Curve
        painter.setPen(QPen(QColor("#4ec9b0"), 2))
        
        path = QPainterPath()
        steps = 50
        
        for i in range(steps + 1):
            x_ratio = i / steps
            x = margin + x_ratio * (w - 2*margin)
            
            # Calculate curve value
            if self._curve == "linear":
                y_ratio = x_ratio
            elif self._curve == "aggressive":
                y_ratio = math.pow(x_ratio, 0.5)
            elif self._curve == "soft":
                y_ratio = math.pow(x_ratio, 2.0)
            elif self._curve == "smooth":
                y_ratio = math.pow(x_ratio, 1.5)
            elif self._curve == "ultra_fine":
                y_ratio = math.pow(x_ratio, 3.0)
            elif self._curve == "s_curve":
                t = x_ratio
                y_ratio = t * t * (3.0 - 2.0 * t)
            elif self._curve == "exponential":
                y_ratio = (math.exp(x_ratio) - 1) / (math.e - 1)
            else:
                y_ratio = x_ratio
            
            y = h - margin - y_ratio * (h - 2*margin)
            
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        painter.drawPath(path)
        
        # Labels
        painter.setPen(QColor("#666"))
        painter.setFont(QFont(FONT_SEGOE_UI, 7))
        painter.drawText(margin + 2, h - 2, "In")
        painter.drawText(w - margin - 15, margin + 10, "Out")


class CollapsibleSection(QWidget):
    """A collapsible section widget with header and content."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._is_collapsed = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header = QPushButton(f"▼ {title}")
        self.header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                background: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e5e5e5;
            }
        """)
        self.header.clicked.connect(self.toggle)
        layout.addWidget(self.header)
        
        # Content container
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.content)
        
        self._title = title
    
    def toggle(self):
        self._is_collapsed = not self._is_collapsed
        self.content.setVisible(not self._is_collapsed)
        arrow = "▶" if self._is_collapsed else "▼"
        self.header.setText(f"{arrow} {self._title}")
    
    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


class SequenceActionWidget(QFrame):
    """Widget representing a single action in a sequence."""
    
    removed = pyqtSignal(object)  # Emits self when removed
    
    def __init__(self, step_num: int, dataref_manager=None, action: SequenceAction = None, parent=None):
        super().__init__(parent)
        self.step_num = step_num
        self.dataref_manager = dataref_manager
        self.action = action or SequenceAction("command", "")
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            SequenceActionWidget {
                background: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            SequenceActionWidget:hover {
                border-color: #0078d4;
                background: #f5f9ff;
            }
        """)
        
        self._setup_ui()
        self._populate()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Step number
        self.step_label = QLabel(f"{self.step_num}")
        self.step_label.setFixedSize(26, 26)
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label.setStyleSheet("""
            QLabel {
                background: #0078d4;
                color: white;
                border-radius: 13px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.step_label)
        
        # Action type
        self.type_combo = QComboBox()
        self.type_combo.addItem("Command", "command")
        self.type_combo.addItem("Dataref", "dataref")
        self.type_combo.setFixedWidth(100)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)
        
        # Target
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g., sim/autopilot/heading_up")
        if self.dataref_manager:
            valid_targets = self.dataref_manager.get_all_dataref_names()
            # Add universal output keys (but exclude variables)
            if self.arduino_manager:
                all_mappings = self.arduino_manager.get_all_universal_mappings()
                valid_targets.extend([f"ID:{key}" for key, info in all_mappings.items() if not info.get('is_variable', False)])
            completer = QCompleter(valid_targets)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(20)
            self.target_input.setCompleter(completer)
        layout.addWidget(self.target_input, 1)
        
        # Value (for dataref)
        self.value_label = QLabel("=")
        layout.addWidget(self.value_label)
        
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setRange(-999999, 999999)
        self.value_spin.setDecimals(2)
        self.value_spin.setFixedWidth(80)
        layout.addWidget(self.value_spin)
        
        # Delay
        layout.addWidget(QLabel("then wait"))
        
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 60000)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.setFixedWidth(90)
        layout.addWidget(self.delay_spin)
        
        # Remove button
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setStyleSheet("""
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
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))
        layout.addWidget(self.remove_btn)
        
        self._on_type_changed()
    
    def _on_type_changed(self):
        is_dataref = self.type_combo.currentData() == "dataref"
        self.value_label.setVisible(is_dataref)
        self.value_spin.setVisible(is_dataref)
    
    def _populate(self):
        idx = self.type_combo.findData(self.action.action_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.target_input.setText(self.action.target)
        self.value_spin.setValue(self.action.value)
        self.delay_spin.setValue(self.action.delay_ms)
    
    def set_step_number(self, num: int):
        self.step_num = num
        self.step_label.setText(str(num))
    
    def get_action(self) -> SequenceAction:
        return SequenceAction(
            action_type=self.type_combo.currentData(),
            target=self.target_input.text().strip(),
            value=self.value_spin.value(),
            delay_ms=self.delay_spin.value()
        )


class ConditionWidget(QFrame):
    removed = pyqtSignal(object)
    def __init__(self, dataref_manager=None, cond=None, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(self)
        self.dref_input = QLineEdit()
        self.dref_input.setPlaceholderText("Condition Dataref")
        if dataref_manager:
            completer = QCompleter(dataref_manager.get_all_dataref_names())
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(20)
            self.dref_input.setCompleter(completer)
        
        self.op_combo = QComboBox()
        self.op_combo.addItems(["<", "<=", ">", ">=", "==", "!="])
        self.val_input = QDoubleSpinBox()
        self.val_input.setRange(-999999, 999999)
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))
        
        layout.addWidget(self.dref_input, 2)
        layout.addWidget(self.op_combo)
        layout.addWidget(self.val_input)
        layout.addWidget(self.remove_btn)
        
        if cond:
            self.dref_input.setText(cond.dataref)
            self.op_combo.setCurrentText(cond.operator)
            self.val_input.setValue(cond.value)

class TargetWidget(QFrame):
    removed = pyqtSignal(object)
    def __init__(self, dataref_manager=None, target=None, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(self)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target Dataref/Command")
        if dataref_manager:
            completer = QCompleter(dataref_manager.get_all_dataref_names())
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(20)
            self.target_input.setCompleter(completer)
        
        self.on_val = QDoubleSpinBox()
        self.on_val.setRange(-999999, 999999)
        self.off_val = QDoubleSpinBox()
        self.off_val.setRange(-999999, 999999)
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))
        
        layout.addWidget(QLabel("Target:"))
        layout.addWidget(self.target_input, 2)
        layout.addWidget(QLabel("On:"))
        layout.addWidget(self.on_val)
        layout.addWidget(QLabel("Off:"))
        layout.addWidget(self.off_val)
        layout.addWidget(self.remove_btn)

        if target:
            self.target_input.setText(target.target)
            self.on_val.setValue(target.value_on)
            self.off_val.setValue(target.value_off)

class InputMappingDialog(QDialog):
    def __init__(self, parent=None, mapping: Optional[InputMapping] = None, 
                 dataref_manager=None, variable_store=None, fixed_input=False):
        super().__init__(parent)
        self.mapping = mapping
        self.dataref_manager = dataref_manager
        self.variable_store = variable_store
        self.fixed_input = fixed_input
        self.setWindowTitle("Advanced Input Mapping")
        self.setMinimumWidth(850)
        self.setMinimumHeight(700)
        
        self._input_key = mapping.input_key if mapping else ""
        self._device_port = mapping.device_port if mapping else "*"
        self._condition_widgets = []
        self._target_widgets = []
        self._sequence_widgets = []
        
        self._setup_ui()
        if mapping: self._populate_from_mapping(mapping)
        else: self._toggle_learn(True)

    def _setup_ui(self):
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(12)
        
        # === Step 1: Input Trigger ===
        self._setup_step1_input(layout)
        
        # === Step 2: Action Type ===
        self._setup_step2_action(layout)
        
        # === Step 3: Conditions ===
        self._setup_step3_conditions(layout)
        
        # === Step 4: Description ===
        self._setup_step4_description(layout)
        
        # Setup helpers
        self._setup_autocomplete()
        
        layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # === Dialog Buttons ===
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._save)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)

    def _setup_step1_input(self, layout: QVBoxLayout):
        """Setup Step 1: Input Trigger section."""
        if self.fixed_input and self.mapping:
            # Simple header when input is pre-selected
            header = QLabel(f"<b>Configuring:</b> {self.mapping.input_key} on {self.mapping.device_port}")
            header.setStyleSheet("font-size: 14px; padding: 10px; background: #e7f3ff; border-radius: 4px;")
            layout.addWidget(header)
            return
        
        group = QGroupBox("1. Input Trigger")
        group_layout = QVBoxLayout(group)
        
        # Description
        desc = QLabel(
            "<b>What is this?</b> Select which physical control (button, switch, axis, or encoder) "
            "on your hardware will trigger this action. Click 'Detect Input' and then press/move "
            "the control you want to map."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(CSS_DESCRIPTION_STYLE)
        group_layout.addWidget(desc)
        
        # Learn controls
        learn_layout = QHBoxLayout()
        
        self.learn_status = QLabel("Waiting for input...")
        self.learn_status.setStyleSheet("font-size: 14px; font-weight: bold; color: gray;")
        learn_layout.addWidget(self.learn_status)
        
        self.learn_btn = QPushButton("🔴 Detect Input")
        self.learn_btn.setCheckable(True)
        self.learn_btn.setMinimumHeight(40)
        self.learn_btn.clicked.connect(self._toggle_learn)
        learn_layout.addWidget(self.learn_btn)
        
        group_layout.addLayout(learn_layout)
        
        # Technical details
        details_layout = QHBoxLayout()
        self.detected_key_label = QLabel("ID: -")
        self.detected_key_label.setStyleSheet("color: gray; font-size: 10px;")
        details_layout.addWidget(self.detected_key_label)
        
        self.detected_port_label = QLabel("Device: -")
        self.detected_port_label.setStyleSheet("color: gray; font-size: 10px;")
        details_layout.addWidget(self.detected_port_label)
        details_layout.addStretch()
        
        group_layout.addLayout(details_layout)
        
        layout.addWidget(group)

    def _setup_step2_action(self, layout: QVBoxLayout):
        """Setup Step 2: Action Type section."""
        group = QGroupBox("2. Action Type")
        group_layout = QVBoxLayout(group)

        self._setup_action_description(group_layout)
        self._setup_action_selector(group_layout)
        self._setup_action_help(group_layout)
        self._setup_targets_section(group_layout)
        self._setup_options_stack(group_layout)

        layout.addWidget(group)

    def _setup_action_description(self, parent_layout: QVBoxLayout):
        """Setup the action description."""
        desc = QLabel(
            "<b>What should happen?</b> Choose what X-Plane should do when you use this control. "
            "Different action types are suited for different hardware (buttons vs switches vs knobs)."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(CSS_DESCRIPTION_STYLE)
        parent_layout.addWidget(desc)

    def _setup_action_selector(self, parent_layout: QVBoxLayout):
        """Setup the action type selector."""
        form = QFormLayout()

        self.action_combo = QComboBox()
        self.action_combo.addItem("🖱️ Trigger Command (Button Press)", InputAction.COMMAND)
        self.action_combo.addItem("🔘 Set Exact Value (Switch/Lever)", InputAction.DATAREF_SET)
        self.action_combo.addItem("🔄 Toggle On/Off (Button)", InputAction.DATAREF_TOGGLE)
        self.action_combo.addItem("⬆️ Increase Value (Encoder CW)", InputAction.DATAREF_INC)
        self.action_combo.addItem("⬇️ Decrease Value (Encoder CCW)", InputAction.DATAREF_DEC)
        self.action_combo.addItem("📊 Axis (Throttle/Slider)", InputAction.AXIS)
        self.action_combo.addItem("📜 Sequence (Multiple Actions)", InputAction.SEQUENCE)
        self.action_combo.currentIndexChanged.connect(self._update_ui_state)
        form.addRow("Action Type:", self.action_combo)

        parent_layout.addLayout(form)

    def _setup_action_help(self, parent_layout: QVBoxLayout):
        """Setup the action help section."""
        self.action_help_box = QFrame()
        self.action_help_box.setStyleSheet("""
            QFrame {
                background: #e7f3ff;
                border: 1px solid #b3d7ff;
                border-left: 4px solid #0078d4;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        help_layout = QVBoxLayout(self.action_help_box)
        help_layout.setContentsMargins(10, 10, 10, 10)

        self.action_help_title = QLabel()
        self.action_help_title.setStyleSheet("font-weight: bold;")
        help_layout.addWidget(self.action_help_title)

        self.action_help_content = QLabel()
        self.action_help_content.setWordWrap(True)
        self.action_help_content.setStyleSheet("color: #333;")
        help_layout.addWidget(self.action_help_content)

        self.action_help_examples = QLabel()
        self.action_help_examples.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        help_layout.addWidget(self.action_help_examples)

        parent_layout.addWidget(self.action_help_box)

    def _setup_targets_section(self, parent_layout: QVBoxLayout):
        """Setup the targets section."""
        self.targets_container = QWidget()
        self.targets_layout = QVBoxLayout(self.targets_container)

        # Legacy target (for simple mode)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Primary Target Dataref/Command")
        self.targets_layout.addWidget(self.target_input)

        # List for extra target widgets
        self.target_list_layout = QVBoxLayout()
        self.targets_layout.addLayout(self.target_list_layout)

        add_target_btn = QPushButton("+ Add Multiple Dataref Action")
        add_target_btn.clicked.connect(self._add_target_widget)
        self.targets_layout.addWidget(add_target_btn)

        parent_layout.addWidget(self.targets_container)

    def _setup_options_stack(self, parent_layout: QVBoxLayout):
        """Setup the options stack for different action types."""
        self.options_stack = QStackedWidget()

        # Page 0: Command (empty)
        self.options_stack.addWidget(QWidget())

        # Page 1: Set Value
        self._setup_set_value_page()

        # Page 2: Toggle (empty)
        self.options_stack.addWidget(QWidget())

        # Page 3: Increment/Decrement
        self._setup_increment_page()

        # Page 4: Axis
        self._setup_axis_page()

        # Page 5: Sequence
        self._setup_sequence_page()

        parent_layout.addWidget(self.options_stack)

    def _add_target_widget(self, target=None):
        w = TargetWidget(self.dataref_manager, target)
        w.removed.connect(self._remove_target_widget)
        self.target_list_layout.addWidget(w)
        self._target_widgets.append(w)
    
    def _remove_target_widget(self, widget):
        self.target_list_layout.removeWidget(widget)
        self._target_widgets.remove(widget)
        widget.deleteLater()

    def _setup_set_value_page(self):
        """Setup the Set Value options page."""
        page = QWidget()
        layout = QFormLayout(page)
        
        desc = QLabel("Set the dataref to specific values when the button is pressed and released.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-style: italic;")
        layout.addRow(desc)
        
        self.val_on_spin = QDoubleSpinBox()
        self.val_on_spin.setRange(-999999, 999999)
        self.val_on_spin.setValue(1.0)
        layout.addRow("Value when Pressed:", self.val_on_spin)
        
        self.val_off_spin = QDoubleSpinBox()
        self.val_off_spin.setRange(-999999, 999999)
        self.val_off_spin.setValue(0.0)
        layout.addRow("Value when Released:", self.val_off_spin)
        
        self.options_stack.addWidget(page)

    def _setup_increment_page(self):
        """Setup the Increment/Decrement options page."""
        page = QWidget()
        layout = QFormLayout(page)
        
        desc = QLabel("Adjust how much the value changes with each encoder click or button press.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-style: italic;")
        layout.addRow(desc)
        
        self.inc_spin = QDoubleSpinBox()
        self.inc_spin.setRange(0.001, 999999)
        self.inc_spin.setValue(1.0)
        self.inc_spin.setDecimals(3)
        layout.addRow("Change Amount:", self.inc_spin)
        
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(-999999, 999999)
        self.min_spin.setValue(0.0)
        layout.addRow("Minimum Limit:", self.min_spin)
        
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(-999999, 999999)
        self.max_spin.setValue(360.0)
        layout.addRow("Maximum Limit:", self.max_spin)
        
        self.wrap_check = QCheckBox("Wrap around (e.g., 359° → 0°)")
        layout.addRow("", self.wrap_check)
        
        self.mult_spin = QDoubleSpinBox()
        self.mult_spin.setRange(0.1, 100.0)
        self.mult_spin.setValue(1.0)
        layout.addRow("Speed Multiplier:", self.mult_spin)
        
        self.options_stack.addWidget(page)

    def _setup_axis_page(self):
        """Setup the Axis options page with calibration and curves."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # === Live Axis Preview ===
        preview_group = QGroupBox("📊 Live Axis Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        preview_desc = QLabel(
            "<b>Real-time visualization:</b> See how your settings affect the axis response. "
            "The top bar shows raw input, the bottom shows processed output after deadzone and curve."
        )
        preview_desc.setWordWrap(True)
        preview_desc.setStyleSheet("color: #555; font-size: 11px;")
        preview_layout.addWidget(preview_desc)
        
        self.axis_preview = AxisPreviewWidget()
        preview_layout.addWidget(self.axis_preview)
        
        # Demo mode toggle
        demo_layout = QHBoxLayout()
        self.demo_mode_check = QCheckBox("Demo Animation (uncheck when testing real input)")
        self.demo_mode_check.setChecked(True)
        self.demo_mode_check.toggled.connect(self.axis_preview.set_demo_mode)
        demo_layout.addWidget(self.demo_mode_check)
        demo_layout.addStretch()
        preview_layout.addLayout(demo_layout)
        
        layout.addWidget(preview_group)
        
        # === Input Calibration ===
        cal_group = QGroupBox("📥 Input Calibration")
        cal_layout = QVBoxLayout(cal_group)
        
        cal_desc = QLabel(
            "<b>Tip:</b> Move your axis to both extremes while watching the 'Raw Value' "
            "to find your hardware's actual min/max values. Most HID devices are already "
            "normalized to -1.0 to 1.0."
        )
        cal_desc.setWordWrap(True)
        cal_desc.setStyleSheet("color: #555; background: #e7f3ff; padding: 8px; border-radius: 4px;")
        cal_layout.addWidget(cal_desc)

        # --- NEW: Wizard Button ---
        wizard_layout = QHBoxLayout()
        wizard_layout.addStretch()
        
        btn_wizard = QPushButton("🧪 Launch Auto-Calibration Wizard")
        btn_wizard.clicked.connect(self._start_axis_wizard)
        btn_wizard.setStyleSheet("background-color: #0078d4; color: white; padding: 5px;")
        wizard_layout.addWidget(btn_wizard)
        
        cal_layout.addLayout(wizard_layout)
        # ----------------------------------
        
        cal_form = QHBoxLayout()
        
        cal_form.addWidget(QLabel("Raw Min:"))
        self.axis_min_spin = QDoubleSpinBox()
        self.axis_min_spin.setRange(-999999, 999999)
        self.axis_min_spin.setValue(-1.0)
        self.axis_min_spin.setDecimals(2)
        cal_form.addWidget(self.axis_min_spin)
        
        cal_form.addSpacing(20)
        
        cal_form.addWidget(QLabel("Raw Max:"))
        self.axis_max_spin = QDoubleSpinBox()
        self.axis_max_spin.setRange(-999999, 999999)
        self.axis_max_spin.setValue(1.0)
        self.axis_max_spin.setDecimals(2)
        cal_form.addWidget(self.axis_max_spin)
        
        cal_form.addStretch()
        cal_layout.addLayout(cal_form)
        
        layout.addWidget(cal_group)
        
        # === Deadzone Position ===
        dz_group = QGroupBox("🎯 Deadzone Settings")
        dz_layout = QVBoxLayout(dz_group)
        
        dz_desc = QLabel(
            "<b>What is Deadzone?</b> An unresponsive area where small movements are ignored. "
            "Useful for preventing drift from jittery hardware or centering issues."
        )
        dz_desc.setWordWrap(True)
        dz_desc.setStyleSheet(CSS_DESCRIPTION_STYLE)
        dz_layout.addWidget(dz_desc)
        
        # Deadzone position selector
        pos_label = QLabel("<b>Deadzone Position:</b>")
        dz_layout.addWidget(pos_label)
        
        self.dz_pos_group = QButtonGroup(self)
        self.dz_pos_group.buttonClicked.connect(self._on_dz_position_changed)
        pos_grid = QGridLayout()
        
        positions = [
            ("center", "🎯 Center", "Ignores small movements around neutral", "Best for: Joysticks, Yokes, Rudder Pedals"),
            ("ends", "↔ Both Ends", "Ignores noise at min and max", "Best for: Worn potentiometers"),
            ("left", "⬅️ Left/Bottom", "Ignores values near minimum", "Best for: Throttle idle cutoff"),
            ("right", "➡️ Right/Top", "Ignores values near maximum", "Best for: Full brake detent"),
        ]
        
        for i, (value, title, desc, example) in enumerate(positions):
            radio = QRadioButton()
            radio.setProperty("dz_position", value)
            self.dz_pos_group.addButton(radio, i)
            
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    border: 2px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 8px;
                    background: white;
                }
                QFrame:hover {
                    border-color: #0078d4;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            
            header = QHBoxLayout()
            header.addWidget(radio)
            title_lbl = QLabel(f"<b>{title}</b>")
            header.addWidget(title_lbl)
            header.addStretch()
            card_layout.addLayout(header)
            
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #666; font-size: 11px;")
            card_layout.addWidget(desc_lbl)
            
            example_lbl = QLabel(example)
            example_lbl.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            card_layout.addWidget(example_lbl)
            
            pos_grid.addWidget(card, i // 2, i % 2)
            
            if value == "center":
                radio.setChecked(True)
        
        dz_layout.addLayout(pos_grid)
        
        # Deadzone size slider
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Deadzone Size:"))
        
        self.dz_slider = QSlider(Qt.Orientation.Horizontal)
        self.dz_slider.setRange(0, 50)
        self.dz_slider.setValue(5)
        self.dz_slider.valueChanged.connect(self._on_dz_slider_changed)
        size_layout.addWidget(self.dz_slider)
        
        self.dz_value_label = QLabel("5%")
        self.dz_value_label.setMinimumWidth(40)
        size_layout.addWidget(self.dz_value_label)
        
        dz_layout.addLayout(size_layout)
        
        layout.addWidget(dz_group)
        
        # === Response Curve ===
        curve_group = QGroupBox("📈 Response Curve")
        curve_layout = QVBoxLayout(curve_group)
        
        curve_desc = QLabel(
            "<b>What is Response Curve?</b> Controls how input movement translates to output. "
            "Aggressive = precise near center. Soft = gradual acceleration."
        )
        curve_desc.setWordWrap(True)
        curve_desc.setStyleSheet(CSS_DESCRIPTION_STYLE)
        curve_layout.addWidget(curve_desc)
        
        curve_row = QHBoxLayout()
        
        # Curve selector
        curve_form = QVBoxLayout()
        curve_form.addWidget(QLabel("Curve Type:"))
        
        self.curve_combo = QComboBox()
        self.curve_combo.addItem("📏 Linear - Direct 1:1 response", "linear")
        self.curve_combo.addItem("🌊 Smooth - Gentle acceleration (x^1.5)", "smooth")
        self.curve_combo.addItem("⚡ Aggressive - Fine center, quick extremes (√x)", "aggressive")
        self.curve_combo.addItem("🪶 Soft - Very precise center (x²)", "soft")
        self.curve_combo.addItem("🎯 Ultra Fine - Maximum precision center (x³)", "ultra_fine")
        self.curve_combo.addItem("〰️ S-Curve - Smooth start and end", "s_curve")
        self.curve_combo.addItem("📈 Exponential - Slow start, fast finish", "exponential")
        self.curve_combo.currentIndexChanged.connect(self._on_curve_changed)
        curve_form.addWidget(self.curve_combo)
        
        # Curve description
        self.curve_desc_label = QLabel()
        self.curve_desc_label.setWordWrap(True)
        self.curve_desc_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 5px;")
        curve_form.addWidget(self.curve_desc_label)
        
        curve_row.addLayout(curve_form, 2)
        
        # Curve preview graph
        curve_preview_layout = QVBoxLayout()
        curve_preview_layout.addWidget(QLabel("Curve Shape:"))
        self.curve_preview = CurvePreviewWidget()
        curve_preview_layout.addWidget(self.curve_preview)
        curve_row.addLayout(curve_preview_layout, 1)
        
        curve_layout.addLayout(curve_row)
        
        # Invert checkbox
        self.invert_check = QCheckBox("Invert Axis (reverses direction)")
        self.invert_check.toggled.connect(self._on_invert_changed)
        curve_layout.addWidget(self.invert_check)
        
        layout.addWidget(curve_group)
        
        # Initialize curve description
        self._on_curve_changed()
        
        # === Output Mapping ===
        out_group = QGroupBox("📤 Output Mapping")
        out_layout = QVBoxLayout(out_group)
        
        out_desc = QLabel(
            "<b>Output Range:</b> Map your axis to X-Plane's expected values. "
            "Throttle = 0.0-1.0, Flight controls = -1.0 to 1.0"
        )
        out_desc.setWordWrap(True)
        out_desc.setStyleSheet(CSS_DESCRIPTION_STYLE)
        out_layout.addWidget(out_desc)
        
        out_form = QHBoxLayout()
        
        out_form.addWidget(QLabel("Output Min:"))
        self.out_min_spin = QDoubleSpinBox()
        self.out_min_spin.setRange(-999999, 999999)
        self.out_min_spin.setValue(0.0)
        self.out_min_spin.setDecimals(2)
        out_form.addWidget(self.out_min_spin)
        
        out_form.addSpacing(20)
        
        out_form.addWidget(QLabel("Output Max:"))
        self.out_max_spin = QDoubleSpinBox()
        self.out_max_spin.setRange(-999999, 999999)
        self.out_max_spin.setValue(1.0)
        self.out_max_spin.setDecimals(2)
        out_form.addWidget(self.out_max_spin)
        
        out_form.addStretch()
        out_layout.addLayout(out_form)
        
        # Common presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Quick Presets:"))
        
        preset_btn1 = QPushButton("Throttle (0-1)")
        preset_btn1.clicked.connect(lambda: self._set_output_preset(0.0, 1.0))
        presets_layout.addWidget(preset_btn1)
        
        preset_btn2 = QPushButton("Flight Ctrl (-1 to 1)")
        preset_btn2.clicked.connect(lambda: self._set_output_preset(-1.0, 1.0))
        presets_layout.addWidget(preset_btn2)
        
        preset_btn3 = QPushButton("Prop/Mix (0-1)")
        preset_btn3.clicked.connect(lambda: self._set_output_preset(0.0, 1.0))
        presets_layout.addWidget(preset_btn3)
        
        presets_layout.addStretch()
        out_layout.addLayout(presets_layout)
        
        layout.addWidget(out_group)
        
        self.options_stack.addWidget(page)
    
    def _setup_sequence_page(self):
        """Setup the Sequence/Macro options page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Description
        desc = QLabel(
            "<b>What are Sequences?</b> A sequence lets you trigger multiple X-Plane actions "
            "with a single button press. Perfect for checklists, complex procedures, or automating "
            "repetitive tasks like 'Landing Configuration' or 'Engine Start'."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #555; background: #e7f3ff; padding: 10px; border-radius: 4px;")
        layout.addWidget(desc)
        
        # Examples
        examples = QLabel(
            "💡 <b>Examples:</b> Landing Config (Flaps → Gear → Lights), "
            "Engine Start (Fuel → Ignition → Starter), Go Around (TOGA → Gear Up → Flaps)"
        )
        examples.setWordWrap(True)
        examples.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(examples)
        
        # Actions list
        actions_group = QGroupBox("📋 Actions (Executed in Order)")
        actions_layout = QVBoxLayout(actions_group)
        
        # Scroll area for action items
        self.seq_scroll = QScrollArea()
        self.seq_scroll.setWidgetResizable(True)
        self.seq_scroll.setMaximumHeight(200)
        self.seq_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.seq_container = QWidget()
        self.seq_container_layout = QVBoxLayout(self.seq_container)
        self.seq_container_layout.setSpacing(6)
        self.seq_container_layout.setContentsMargins(0, 0, 0, 0)
        self.seq_container_layout.addStretch()
        
        self.seq_scroll.setWidget(self.seq_container)
        actions_layout.addWidget(self.seq_scroll)
        
        # Add buttons
        add_layout = QHBoxLayout()
        
        add_cmd_btn = QPushButton("➕ Add Command")
        add_cmd_btn.clicked.connect(lambda: self._add_sequence_action("command"))
        add_layout.addWidget(add_cmd_btn)
        
        add_dref_btn = QPushButton("➕ Add Dataref")
        add_dref_btn.clicked.connect(lambda: self._add_sequence_action("dataref"))
        add_layout.addWidget(add_dref_btn)
        
        actions_layout.addLayout(add_layout)
        
        layout.addWidget(actions_group)
        
        # Sequence behavior options
        behavior_group = QGroupBox("⚙️ Sequence Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.seq_stop_on_error = QCheckBox("Stop on Error")
        self.seq_stop_on_error.setToolTip(
            "If any action fails (e.g., condition not met), stop the sequence immediately"
        )
        behavior_layout.addWidget(self.seq_stop_on_error)
        
        self.seq_repeat = QCheckBox("Repeat While Held")
        self.seq_repeat.setToolTip(
            "Keep executing the sequence as long as the button is held down"
        )
        behavior_layout.addWidget(self.seq_repeat)
        
        self.seq_reverse = QCheckBox("Reverse on Release")
        self.seq_reverse.setToolTip(
            "When button is released, execute the sequence in reverse order with opposite values"
        )
        behavior_layout.addWidget(self.seq_reverse)
        
        layout.addWidget(behavior_group)
        
        self.options_stack.addWidget(page)

    def _setup_step3_conditions(self, layout: QVBoxLayout):
        """Setup Step 3: Advanced Multiple Conditions section."""
        self.condition_section = CollapsibleSection("3. Logic & Conditions")
        
        self.condition_enabled = QCheckBox("Enable conditional execution logic")
        self.condition_enabled.toggled.connect(self._on_condition_toggled)
        self.condition_section.add_widget(self.condition_enabled)
        
        self.condition_fields = QWidget()
        self.cond_fields_layout = QVBoxLayout(self.condition_fields)
        
        # Logic Selector (AND/OR)
        logic_row = QHBoxLayout()
        logic_row.addWidget(QLabel("Execute if:"))
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["ALL conditions are true (AND)", "ANY condition is true (OR)"])
        logic_row.addWidget(self.logic_combo)
        logic_row.addStretch()
        self.cond_fields_layout.addLayout(logic_row)
        
        # List for condition widgets
        self.cond_list_layout = QVBoxLayout()
        self.cond_fields_layout.addLayout(self.cond_list_layout)
        
        add_cond_btn = QPushButton("+ Add Logic Condition")
        add_cond_btn.clicked.connect(self._add_condition_widget)
        self.cond_fields_layout.addWidget(add_cond_btn)
        
        # Visual Aid (Schematic)
        self.logic_viz = QLabel("Logic: Trigger -> (Action)")
        self.logic_viz.setStyleSheet("padding: 10px; background: #eee; border: 1px dashed #999; border-radius: 4px; font-family: monospace;")
        self.cond_fields_layout.addWidget(self.logic_viz)

        self.condition_fields.setEnabled(False)
        self.condition_section.add_widget(self.condition_fields)
        layout.addWidget(self.condition_section)

    def _add_condition_widget(self, cond=None):
        w = ConditionWidget(self.dataref_manager, cond)
        w.removed.connect(self._remove_condition_widget)
        self.cond_list_layout.addWidget(w)
        self._condition_widgets.append(w)
        self._update_logic_viz()

    def _remove_condition_widget(self, widget):
        self.cond_list_layout.removeWidget(widget)
        self._condition_widgets.remove(widget)
        widget.deleteLater()
        self._update_logic_viz()

    def _update_logic_viz(self):
        # Determine logic operator
        if "ALL" in self.logic_combo.currentText():
            logic = "AND"
        else:
            logic = "OR"

        cond_count = len(self._condition_widgets)

        if cond_count == 0:
            text = "Action runs ALWAYS"
        else:
            # Build condition list
            conditions = []
            for i in range(cond_count):
                conditions.append(f'C{i+1}')
            conditions_str = f' {logic} '.join(conditions)
            text = f"Action runs if ({conditions_str})"

        self.logic_viz.setText(f"Logic Flow: {text}")

    def _setup_step4_description(self, layout: QVBoxLayout):
        """Setup Step 4: Description section."""
        group = QGroupBox("4. Label & Notes")
        group_layout = QVBoxLayout(group)
        
        desc = QLabel(
            "Give this mapping a descriptive name. This helps you identify it later in the mapping list."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #555;")
        group_layout.addWidget(desc)
        
        form = QFormLayout()
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("e.g., Gear Toggle (Safe Speed Only)")
        form.addRow("Description:", self.desc_input)
        
        # Initial Value Sync
        self.sync_on_connect_check = QCheckBox("Sync hardware state to X-Plane on connect")
        self.sync_on_connect_check.setChecked(True)
        form.addRow("Auto-Sync:", self.sync_on_connect_check)
        
        self.init_val_enabled = QCheckBox("Set specific value on connect")
        self.init_val_spin = QDoubleSpinBox()
        self.init_val_spin.setRange(-999999, 999999)
        self.init_val_spin.setDecimals(4)
        self.init_val_spin.setEnabled(False)
        self.init_val_enabled.toggled.connect(self.init_val_spin.setEnabled)
        
        init_layout = QHBoxLayout()
        init_layout.addWidget(self.init_val_enabled)
        init_layout.addWidget(self.init_val_spin)
        form.addRow("Initial Value:", init_layout)
        
        group_layout.addLayout(form)
        
        layout.addWidget(group)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _setup_autocomplete(self):
        """Set up autocomplete for dataref input fields."""
        if not self.dataref_manager:
            return
        
        try:
            all_datarefs = self.dataref_manager.get_all_dataref_names()
            
            # Main target input
            completer = QCompleter(all_datarefs)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(20)
            self.target_input.setCompleter(completer)
            
            # Condition dataref input
            cond_completer = QCompleter(all_datarefs)
            cond_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            cond_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            cond_completer.setMaxVisibleItems(20)

        except Exception as e:
            log.warning("Could not set up autocomplete: %s", e)

    def _update_ui_state(self):
        """Update UI based on selected action type."""
        action = self.action_combo.currentData()
        
        # Update help text
        help_data = {
            InputAction.COMMAND: (
                "🖱️ Trigger Command",
                "Sends a one-time command to X-Plane, like clicking a button in the cockpit. "
                "The command fires once when you press the button.",
                "Best for: Gear Toggle, Pause Sim, View Changes"
            ),
            InputAction.DATAREF_SET: (
                "🔘 Set Exact Value",
                "Sets a dataref to a specific value when pressed, and optionally a different value "
                "when released. Perfect for physical ON/OFF switches.",
                "Best for: 2-Position Switches, Master Battery, Fuel Pumps"
            ),
            InputAction.DATAREF_TOGGLE: (
                "🔄 Toggle On/Off",
                "Each press flips the value between 0 and 1. Great for momentary push buttons "
                "that control toggle states.",
                "Best for: Gear Toggle, Light Switches, AP Modes"
            ),
            InputAction.DATAREF_INC: (
                "⬆️ Increase Value",
                "Adds to the current value each time triggered. Use for rotary encoders "
                "turning clockwise or '+/-' buttons.",
                "Best for: Heading Bug +, Altitude +100, Radio Freq Up"
            ),
            InputAction.DATAREF_DEC: (
                "⬇️ Decrease Value",
                "Subtracts from the current value. Pair with 'Increase' for the other "
                "direction of your encoder.",
                "Best for: Heading Bug -, Altitude -100, Radio Freq Down"
            ),
            InputAction.AXIS: (
                "📊 Axis Mapping",
                "Maps a continuous analog input (like a slider or joystick) to a dataref range. "
                "Includes calibration, deadzone, and response curve options.",
                "Best for: Throttle, Mixture, Prop RPM, Flight Controls"
            ),
            InputAction.SEQUENCE: (
                "📜 Sequence / Macro",
                "Executes multiple actions in order with optional delays between them. "
                "One button press can trigger a whole checklist!",
                "Best for: Landing Config, Engine Start, Go Around"
            ),
        }
        
        title, content, examples = help_data.get(action, ("", "", ""))
        self.action_help_title.setText(title)
        self.action_help_content.setText(content)
        self.action_help_examples.setText(examples)
        
        # Show appropriate options page
        page_map = {
            InputAction.COMMAND: 0,
            InputAction.DATAREF_SET: 1,
            InputAction.DATAREF_TOGGLE: 2,
            InputAction.DATAREF_INC: 3,
            InputAction.DATAREF_DEC: 3,
            InputAction.AXIS: 4,
            InputAction.SEQUENCE: 5,
        }
        self.options_stack.setCurrentIndex(page_map.get(action, 0))
        
        # Show/hide target input for sequence (uses its own action list)
        self.target_input.setVisible(action != InputAction.SEQUENCE)

    def _on_condition_toggled(self, checked: bool):
        """Handle condition enable/disable."""
        self.condition_fields.setEnabled(checked)

    def _on_dz_slider_changed(self, value: int):
        """Update deadzone value label and preview."""
        self.dz_value_label.setText(f"{value}%")
        if hasattr(self, 'axis_preview'):
            self.axis_preview.set_deadzone(value / 100.0)

    def _on_dz_position_changed(self):
        """Update axis preview when deadzone position changes."""
        for btn in self.dz_pos_group.buttons():
            if btn.isChecked():
                position = btn.property("dz_position")
                if hasattr(self, 'axis_preview'):
                    self.axis_preview.set_deadzone_position(position)
                break

    def _on_curve_changed(self):
        """Update curve description and preview."""
        curve = self.curve_combo.currentData()

        # Update preview widget
        self._update_curve_previews(curve)

        # Update description
        if hasattr(self, 'curve_desc_label'):
            self.curve_desc_label.setText(self._get_curve_description(curve))

    def _update_curve_previews(self, curve: str):
        """Update curve preview widgets."""
        if hasattr(self, 'curve_preview'):
            self.curve_preview.set_curve(curve)
        if hasattr(self, 'axis_preview'):
            self.axis_preview.set_curve(curve)

    def _get_curve_description(self, curve: str) -> str:
        """Get description for the specified curve."""
        descriptions = {
            "linear": "Direct 1:1 mapping. Input directly equals output. Simple and predictable.",
            "smooth": "Gentle acceleration using x^1.5. Good balance for general flight controls.",
            "aggressive": "Square root curve (√x). Very responsive with fine control near center. Great for combat flight sims.",
            "soft": "Quadratic curve (x²). Very precise near center, accelerates toward extremes. Good for airliners.",
            "ultra_fine": "Cubic curve (x³). Maximum precision near center. For when you need very fine adjustments.",
            "s_curve": "Smoothstep function. Eases in and out for natural feeling movement.",
            "exponential": "Slow start that accelerates exponentially. Good for throttle/brake feel.",
        }
        return descriptions.get(curve, "")

    def _on_invert_changed(self, checked: bool):
        """Update axis preview when invert changes."""
        if hasattr(self, 'axis_preview'):
            self.axis_preview.set_inverted(checked)

    def _set_output_preset(self, min_val: float, max_val: float):
        """Apply output range preset."""
        self.out_min_spin.setValue(min_val)
        self.out_max_spin.setValue(max_val)
    
    def update_axis_preview_value(self, value: float):
        """Update the axis preview with a real input value."""
        if hasattr(self, 'axis_preview'):
            self.axis_preview.set_demo_mode(False)
            self.demo_mode_check.setChecked(False)
        if self._sequence_widgets:
            return SequenceAction.to_list_str(self._sequence_widgets)
        return ""

    def _start_axis_wizard(self):
        """Opens the calibration wizard."""
        if not self._check_hid_manager_available():
            return

        wizard = self._create_axis_calibration_wizard()

        if wizard.exec():
            self._apply_calibration_results(wizard.get_results())

    def _check_hid_manager_available(self) -> bool:
        """Check if HID manager is available and warn if not."""
        if not hasattr(self, '_hid_manager'):
            QMessageBox.warning(self, "Error", "Hardware access not available for calibration.")
            return False
        return True

    def _create_axis_calibration_wizard(self):
        """Create the axis calibration wizard with the live value getter."""
        return AxisCalibrationWizard(
            input_key=self._input_key,
            current_settings={
                "min": self.axis_min_spin.value(),
                "max": self.axis_max_spin.value()
            },
            get_live_value=self._get_live_axis_value,
            parent=self
        )

    def _get_live_axis_value(self, key: str) -> float:
        """Get live axis value from HID manager."""
        # Default fallback value
        default_value = 32768.0

        # Try to get from HIDManager directly (most accurate)
        if not (hasattr(self, '_hid_manager') and self._hid_manager):
            return default_value

        return self._get_axis_value_from_hid_manager(key, default_value)

    def _get_axis_value_from_hid_manager(self, key: str, default_value: float) -> float:
        """Helper method to get axis value from HID manager."""
        dev = self._hid_manager.get_device(self._device_port)
        if not (dev and dev.connected):
            return default_value

        return self._extract_axis_value(dev, key, default_value)

    def _extract_axis_value(self, dev, key: str, default_value: float) -> float:
        """Helper method to extract axis value from device."""
        if not key.startswith("AXIS_"):
            return default_value

        try:
            idx = self._parse_axis_index(key)
            if hasattr(dev, 'raw_axes') and len(dev.raw_axes) > idx:
                return float(dev.raw_axes[idx])
            # Fallback if raw_axes not populated yet (should be by now)
            return default_value
        except (IndexError, ValueError):
            return default_value

    def _parse_axis_index(self, key: str) -> int:
        """Parse the axis index from the key string."""
        return int(key.split("_")[1])

    def _apply_calibration_results(self, results: dict):
        """Apply the calibration results to the UI."""
        self.axis_min_spin.setValue(results['axis_min'])
        self.axis_max_spin.setValue(results['axis_max'])
        self.dz_slider.setValue(int(results['axis_deadzone'] * 100))

        # Set Deadzone Position to Center (default for wizard)
        for btn in self.dz_pos_group.buttons():
            if btn.property("dz_position") == "center":
                btn.setChecked(True)


    def _add_sequence_action(self, action_type: str):
        """Add a new action to the sequence."""
        step_num = len(self._sequence_widgets) + 1
        action = SequenceAction(action_type, "")
        
        widget = SequenceActionWidget(step_num, self.dataref_manager, action)
        widget.removed.connect(self._remove_sequence_action)
        
        # Insert before the stretch
        self.seq_container_layout.insertWidget(
            self.seq_container_layout.count() - 1, 
            widget
        )
        self._sequence_widgets.append(widget)

    def _remove_sequence_action(self, widget: SequenceActionWidget):
        """Remove an action from the sequence."""
        if widget in self._sequence_widgets:
            self._sequence_widgets.remove(widget)
            self.seq_container_layout.removeWidget(widget)
            widget.deleteLater()
            
            # Renumber remaining steps
            for i, w in enumerate(self._sequence_widgets):
                w.set_step_number(i + 1)

    def _toggle_learn(self, checked: bool):
        """Toggle learn mode for input detection."""
        if not hasattr(self, 'learn_btn'):
            return
            
        if checked:
            self.learn_btn.setText("🔴 Listening... Press Input Now")
            self.learn_btn.setStyleSheet("background-color: #ffcccc; font-weight: bold;")
            self.learn_status.setText("Waiting for input...")
            self.learn_status.setStyleSheet("color: orange; font-size: 14px; font-weight: bold;")
        else:
            self.learn_btn.setText("🔴 Detect Input")
            self.learn_btn.setStyleSheet("")

    def on_input_detected(self, key: str, port: str):
        """Called by parent when in learn mode and input received."""
        if hasattr(self, 'learn_btn') and self.learn_btn.isChecked():
            self._input_key = key
            self._device_port = port
            
            self.learn_status.setText(f"✓ Detected: {key}")
            self.learn_status.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            
            self.detected_key_label.setText(f"ID: {key}")
            self.detected_port_label.setText(f"Device: {port}")
            
            self.learn_btn.setChecked(False)
            self._toggle_learn(False)
            
            if not self.desc_input.text():
                self.desc_input.setText(f"Input {key}")

    def _populate_from_mapping(self, m: InputMapping):
        """Populate dialog from existing mapping."""
        self._input_key = m.input_key
        self._device_port = m.device_port
        
        # Update learn status if visible
        if hasattr(self, 'learn_status'):
            self.learn_status.setText(f"Current: {m.input_key}")
            self.learn_status.setStyleSheet("color: black; font-weight: bold;")
            self.detected_key_label.setText(f"ID: {m.input_key}")
            self.detected_port_label.setText(f"Device: {m.device_port}")
        
        # Action type
        idx = self.action_combo.findData(m.action)
        if idx >= 0:
            self.action_combo.setCurrentIndex(idx)
        
        # Target
        self.target_input.setText(m.target)
        
        # Set value options
        self.val_on_spin.setValue(m.value_on)
        self.val_off_spin.setValue(m.value_off)
        
        # Increment options
        self.inc_spin.setValue(m.increment)
        self.min_spin.setValue(m.min_value)
        self.max_spin.setValue(m.max_value)
        self.wrap_check.setChecked(m.wrap)
        self.mult_spin.setValue(m.multiplier)
        
        # Axis options
        self.axis_min_spin.setValue(m.axis_min)
        self.axis_max_spin.setValue(m.axis_max)
        self.dz_slider.setValue(int(m.axis_deadzone * 100))
        
        # Deadzone position
        for btn in self.dz_pos_group.buttons():
            if btn.property("dz_position") == m.axis_deadzone_pos:
                btn.setChecked(True)
                break
        
        # Curve
        idx = self.curve_combo.findData(m.axis_curve)
        if idx >= 0:
            self.curve_combo.setCurrentIndex(idx)
        
        self.invert_check.setChecked(m.axis_invert)
        self.out_min_spin.setValue(m.min_value)
        self.out_max_spin.setValue(m.max_value)
        
        # Conditions
        self.condition_enabled.setChecked(m.condition_enabled)

        # Populate Conditions List
        self.logic_combo.setCurrentIndex(0 if m.condition_logic == "AND" else 1)
        for cond in m.conditions:
            w = ConditionWidget(self.dataref_manager, cond)
            w.removed.connect(self._remove_condition_widget)
            self.cond_list_layout.addWidget(w)
            self._condition_widgets.append(w)
        self._update_logic_viz()

        # Populate Multi-Targets
        for t in m.targets:
             w = TargetWidget(self.dataref_manager, t)
             w.removed.connect(self._remove_target_widget)
             self.target_list_layout.addWidget(w)
             self._target_widgets.append(w)
        
        # Sequence actions
        for action in m.sequence_actions:
            step_num = len(self._sequence_widgets) + 1
            widget = SequenceActionWidget(step_num, self.dataref_manager, action)
            widget.removed.connect(self._remove_sequence_action)
            self.seq_container_layout.insertWidget(
                self.seq_container_layout.count() - 1,
                widget
            )
            self._sequence_widgets.append(widget)
        
        self.seq_stop_on_error.setChecked(m.sequence_stop_on_error)
        self.seq_repeat.setChecked(m.sequence_repeat_while_held)
        self.seq_reverse.setChecked(m.sequence_reverse_on_release)
        
        # Description & Sync
        self.desc_input.setText(m.description)
        self.sync_on_connect_check.setChecked(m.sync_on_connect)
        if m.init_value is not None:
             self.init_val_enabled.setChecked(True)
             self.init_val_spin.setValue(m.init_value)
        else:
             self.init_val_enabled.setChecked(False)
             self.init_val_spin.setValue(0.0)
        
        # Update UI state
        self._update_ui_state()
        
        if hasattr(self, 'learn_btn'):
            self.learn_btn.setChecked(False)

    def _save(self):
        """Validate and save the mapping."""
        if not self._input_key:
            QMessageBox.warning(
                self, "Error", 
                "No input detected. Click 'Detect Input' and press a button."
            )
            return
        
        action = self.action_combo.currentData()
        
        # Check target requirement (unless sequence, or unless using Multi-Target)
        has_primary_target = bool(self.target_input.text().strip())
        has_multi_targets = len(self._target_widgets) > 0
        
        if action != InputAction.SEQUENCE and not has_primary_target and not has_multi_targets:
             # It's okay if we have multi-targets but no primary
             if not has_multi_targets:
                QMessageBox.warning(
                    self, "Error", 
                    "Target dataref/command is required (or add multiple targets)."
                )
                return
        
        if action == InputAction.SEQUENCE and len(self._sequence_widgets) == 0:
            QMessageBox.warning(
                self, "Error", 
                "Sequence requires at least one action. Click 'Add Command' or 'Add Dataref'."
            )
            return
        
        self.accept()

    def get_mapping(self) -> InputMapping:
        action = self.action_combo.currentData()
        seq_actions = [w.get_action() for w in self._sequence_widgets]
        conds = [Condition(w.dref_input.text(), w.op_combo.currentText(), w.val_input.value()) for w in self._condition_widgets if w.dref_input.text()]
        trgs = [TargetAction(w.target_input.text(), w.on_val.value(), w.off_val.value()) for w in self._target_widgets if w.target_input.text()]
        
        dz_pos = "center"
        for btn in self.dz_pos_group.buttons():
            if btn.isChecked(): dz_pos = btn.property("dz_position"); break
            
        m = InputMapping(
            input_key=self._input_key,
            device_port=self._device_port,
            action=action,
            target=self.target_input.text().strip(),
            value_on=self.val_on_spin.value(),
            value_off=self.val_off_spin.value(),
            targets=trgs,
            condition_enabled=self.condition_enabled.isChecked(),
            conditions=conds,
            condition_logic="AND" if "ALL" in self.logic_combo.currentText() else "OR",
            increment=self.inc_spin.value(),
            min_value=self.out_min_spin.value() if action == InputAction.AXIS else self.min_spin.value(),
            max_value=self.out_max_spin.value() if action == InputAction.AXIS else self.max_spin.value(),
            wrap=self.wrap_check.isChecked(),
            multiplier=self.mult_spin.value(),
            axis_min=self.axis_min_spin.value(),
            axis_max=self.axis_max_spin.value(),
            axis_deadzone=self.dz_slider.value() / 100.0,
            axis_deadzone_pos=dz_pos,
            axis_curve=self.curve_combo.currentData(),
            axis_invert=self.invert_check.isChecked(),
            sequence_actions=seq_actions,
            sequence_stop_on_error=self.seq_stop_on_error.isChecked(),
            sequence_repeat_while_held=self.seq_repeat.isChecked(),
            sequence_reverse_on_release=self.seq_reverse.isChecked(),
            description=self.desc_input.text().strip(),
            sync_on_connect=self.sync_on_connect_check.isChecked(),
            init_value=self.init_val_spin.value() if self.init_val_enabled.isChecked() else None
        )
        return m
