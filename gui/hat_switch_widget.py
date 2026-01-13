from __future__ import annotations
import logging
import math
from typing import Optional, Tuple

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF

log = logging.getLogger(__name__)

class HatSwitchWidget(QWidget):
    """Visualizes an 8-way Hat Switch."""
    
    # Signal for click on direction: (x, y) e.g., (0, 1) for North
    direction_clicked = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._directions = [0, 0, 0, 0, 0, 0, 0, 0] # N, NE, E, SE, S, SW, W, NW
        self._active_index = -1 # None
        self.setMinimumSize(100, 100)

    def set_direction(self, x: float, y: float):
        """Set active direction based on normalized X/Y (-1 to 1)."""
        # Check if the hat is in neutral position (both x and y are close to 0)
        if abs(x) < 0.1 and abs(y) < 0.1:
            # Neutral position - no active direction
            self._active_index = -1
        else:
            # Convert to angle (degrees)
            angle = math.degrees(math.atan2(y, x))
            if angle < 0: angle += 360

            # 8 zones (45 degrees each, centered)
            # N = 0 +/- 22.5
            # NE = 45 +/- 22.5
            # etc.

            # Shift angle by 22.5 degrees to align centers
            sector = int((angle + 22.5) // 45) % 8

            self._active_index = sector

        self.update()

    def reset(self):
        self._active_index = -1
        self.update()

    def mousePressEvent(self, event):
        # Calculate direction based on click position relative to center
        size = self.width()
        center = size / 2
        x = event.position().x() - center
        y = event.position().y() - center
        
        # Normalize
        dist = math.sqrt(x*x + y*y)
        if dist > (size/2) * 0.5: # Click outside inner circle but inside widget
            norm_x = x / (size/2)
            norm_y = y / (size/2)
            self.direction_clicked.emit(norm_x, norm_y)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 5
        
        # Draw Background Circle
        painter.setPen(QPen(QColor("#ccc"), 1))
        painter.setBrush(QColor("#f0f0f0"))
        painter.drawEllipse(int(cx-radius), int(cy-radius), int(radius*2), int(radius*2))
        
        # Draw 8 Directions
        # Order: N, NE, E, SE, S, SW, W, NW
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        for i, angle_deg in enumerate(angles):
            rad = math.radians(angle_deg)

            # Coordinates
            px = cx + (radius * 0.7) * math.cos(rad)
            py = cy + (radius * 0.7) * -math.sin(rad) # Y is inverted in screen coords

            is_active = (i == self._active_index)

            if is_active:
                painter.setBrush(QColor("#0078d4"))
                painter.setPen(QPen(Qt.GlobalColor.white, 2))
                # Draw active indicator (arrowhead or larger dot)
                painter.drawEllipse(int(px-5), int(py-5), 10, 10)
                painter.setPen(Qt.GlobalColor.white)
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor("#555"), 1))

            # Draw Label
            # painter.drawText(int(px-10), int(py+5), labels[i])

            # Draw small dot for center
            if not is_active:
                painter.setBrush(QColor("#999"))
                painter.drawEllipse(int(px-2), int(py-2), 4, 4)

        # Draw center indicator if no direction is active (neutral position)
        if self._active_index == -1:
            painter.setBrush(QColor("#0078d4"))
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawEllipse(int(cx-5), int(cy-5), 10, 10)