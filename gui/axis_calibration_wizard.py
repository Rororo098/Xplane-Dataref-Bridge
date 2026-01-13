from __future__ import annotations
import logging
from typing import Dict, Callable, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

log = logging.getLogger(__name__)

class AxisVisualizer(QFrame):
    """Visual bar showing the live axis position."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self.setMinimumHeight(60)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 5px;")

    def update_value(self, value: float):
        self._value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        cy = h / 2
        
        # 1. Draw Center Line
        painter.setPen(QPen(QColor("#aaa"), 2, Qt.PenStyle.DashLine))
        painter.drawLine(int(w/2), 10, int(w/2), int(h-10))
        
        # 2. Draw Bar Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#eee"))
        painter.drawRect(10, int(cy - 4), int(w-20), 8)
        
        # 3. Draw Current Position Indicator
        # Map 0..65535 to 10..w-10 (Assuming RAW values for calibration)
        # normalize to 0..1
        val_norm = self._value / 65535.0
        # Clamp visual
        val_norm = max(0.0, min(1.0, val_norm))
        
        indicator_x = 10 + (val_norm * (w - 20))
        
        painter.setBrush(QColor("#0078d4"))
        painter.drawEllipse(int(indicator_x - 6), int(cy - 6), 12, 12)
        
        # Draw Text
        painter.setPen(QColor("#333"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, int(h-5), f"{int(self._value)}")


class AxisCalibrationWizard(QDialog):
    """
    3-Step Wizard:
    1. Center
    2. Max
    3. Min
    
    Calculates Min, Max, and Deadzone automatically.
    """
    
    def __init__(self, input_key: str, current_settings: Dict, get_live_value: Callable, parent=None):
        """
        Args:
            get_live_value: A function/callback that returns current float value for input_key.
        """
        super().__init__(parent)
        self.input_key = input_key
        self.current_settings = current_settings
        self.get_live_value = get_live_value # Function to poll hardware
        
        # Data Storage
        self.val_center = 32768.0
        self.val_max = 65535.0
        self.val_min = 0.0
        self.val_drift = 0.0
        
        self._step = 0 # 0: Center, 1: Max, 2: Min, 3: Finish
        
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_value)
        
        self.setWindowTitle(f"Calibrate: {input_key}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)
        self.setModal(True)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header / Instructions
        self.lbl_instruction = QLabel("Step 1 of 3: Center the Axis")
        self.lbl_instruction.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.lbl_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_instruction.setStyleSheet("padding: 15px; background-color: #e7f3ff; border-radius: 8px;")
        layout.addWidget(self.lbl_instruction)
        
        self.lbl_detail = QLabel("Release the stick and let it settle naturally.")
        self.lbl_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_detail.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.lbl_detail)
        
        # Visualizer
        self.viz = AxisVisualizer(self)
        layout.addWidget(self.viz)
        
        # Value Readout
        self.lbl_readout = QLabel("0")
        self.lbl_readout.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        self.lbl_readout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_readout)
        
        # Controls
        ctrl_layout = QHBoxLayout()
        
        self.btn_capture = QPushButton("📌 Capture Position")
        self.btn_capture.setFixedHeight(50)
        self.btn_capture.setStyleSheet("""
            QPushButton { 
                background-color: #28a745; color: white; 
                font-weight: bold; font-size: 14px; border-radius: 6px; 
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.btn_capture.clicked.connect(self._on_capture)
        ctrl_layout.addWidget(self.btn_capture)
        
        layout.addLayout(ctrl_layout)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(1, 4)
        self.progress.setValue(1)
        self.progress.setFormat("Step %v / 3")
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)

    def showEvent(self, event):
        """Start polling when shown."""
        super().showEvent(event)
        self._poll_timer.start(50) # 20Hz update rate

    def hideEvent(self, event):
        """Stop polling when hidden."""
        super().hideEvent(event)
        self._poll_timer.stop()

    def _poll_value(self):
        """Update visuals from live hardware."""
        try:
            val = self.get_live_value(self.input_key)
            if val is not None:
                self.viz.update_value(val)
                self.lbl_readout.setText(f"{int(val)}")
        except Exception as e:
            log.error(f"Error polling axis value: {e}")

    def _on_capture(self):
        """Handle Capture button click based on current step."""
        try:
            current_val = float(self.lbl_readout.text())
        except ValueError:
            return

        if self._step == 0:
            # Capture Center
            self.val_center = current_val
            self._step = 1
            self._update_ui(
                "Step 2 of 3: Max Position", 
                "Move the stick to the maximum extent (e.g., Top-Right)."
            )
            
        elif self._step == 1:
            # Capture Max
            self.val_max = current_val
            self._step = 2
            self._update_ui(
                "Step 3 of 3: Min Position", 
                "Move the stick to the minimum extent (e.g., Bottom-Left)."
            )
            
        elif self._step == 2:
            # Capture Min
            self.val_min = current_val
            self._step = 3
            self.accept() # Done

    def _update_ui(self, title: str, detail: str):
        self.lbl_instruction.setText(title)
        self.lbl_detail.setText(detail)
        self.progress.setValue(self._step + 1)

    def get_results(self) -> Dict:
        """Calculate and return calibration values."""
        
        # Calculate Deadzone (Drift from center 32768)
        # Note: User provided code assumed 0.0 center. 
        # But we found out earlier we are dealing with RAW 0..65535 or similiar.
        # Adjusted visualization to expect 0..65535 range.
        
        # 2. Return dict
        # We also need normalized deadzone for the app (0.0 - 1.0 range usually for deadzone logic?)
        # Let's assume the calling dialog expects raw min/max but percentage deadzone?
        # The dialog expects: axis_min_spin (int/float?), axis_max_spin, dz_slider (0-100%)
        
        # Calculate deadzone as percentage of full range
        full_range = self.val_max - self.val_min
        if full_range == 0: full_range = 1
        
        # How much drift from "ideal" center?
        # Ideally center is (Max+Min)/2
        ideal_center = (self.val_max + self.val_min) / 2
        drift = abs(self.val_center - ideal_center)
        
        # Safe margin: drift + 1%
        dz_padding = full_range * 0.01
        required_dz = drift + dz_padding
        
        # Convert to percentage (0.0 - 1.0)
        dz_percent = required_dz / (full_range / 2) # Deadzone is usually from center out
        dz_percent = max(0.02, min(0.90, dz_percent))
        
        return {
            "axis_min": self.val_min,
            "axis_max": self.val_max,
            "axis_deadzone": dz_percent,
        }