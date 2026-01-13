from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath

class LogicSchematicWidget(QWidget):
    """Visualizes a Logic Block's flow."""

    def __init__(self, conditions, logic_gate, outputs, parent=None):
        super().__init__(parent)
        self.conditions = conditions
        self.logic_gate = logic_gate
        self.outputs = outputs
        self.setMinimumHeight(120)
        self.setStyleSheet("background-color: #fafafa; border: 1px dashed #ccc; border-radius: 5px;")

    def update_data(self, conditions, logic_gate, outputs):
        """Update the widget with new data."""
        self.conditions = conditions
        self.logic_gate = logic_gate
        self.outputs = outputs
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        
        # 3 Columns: Inputs (Left), Logic (Center), Outputs (Right)
        col_x = [w * 0.15, w * 0.5, w * 0.85]
        center_y = h / 2

        # Colors
        gate_colors = {
            "AND": QColor("#0078d4"), "OR": QColor("#28a745"), 
            "NAND": QColor("#6610f2"), "NOR": QColor("#dc3545"),
            "XOR": QColor("#fd7e14"), "XNOR": QColor("#6f42c1")
        }
        gate_color = gate_colors.get(self.logic_gate, QColor("#333"))

        # 1. Draw Inputs Box
        painter.setBrush(QBrush(QColor("#e9ecef")))
        painter.setPen(QPen(QColor("#adb5bd")))
        box_h = max(60, len(self.conditions) * 20)
        painter.drawRect(int(col_x[0] - 40), int(center_y - box_h/2), 80, int(box_h))
        
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 8))
        painter.drawText(int(col_x[0] - 30), int(center_y - box_h/2 + 15), "INPUTS")
        
        for i, cond in enumerate(self.conditions):
            if cond.enabled:
                painter.setPen(QPen(QColor("#28a745"), 2))
                text = f"{cond.dataref.split('/')[-1]} {cond.operator} {cond.value}"
            else:
                painter.setPen(QPen(QColor("#999"), 1, Qt.PenStyle.DashLine))
                text = "(Disabled)"
            painter.drawText(int(col_x[0] - 35), int(center_y - box_h/2 + 35 + (i*15)), text)

        # 2. Draw Logic Gate Box
        painter.setBrush(QBrush(gate_color))
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawEllipse(int(col_x[1] - 25), int(center_y - 25), 50, 50)
        
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(int(col_x[1] - 10), int(center_y + 5), self.logic_gate)

        # 3. Draw Outputs Box
        painter.setBrush(QBrush(QColor("#fff3cd")))
        painter.setPen(QPen(QColor("#ffeeba")))
        box_h = max(60, len(self.outputs) * 20)
        painter.drawRect(int(col_x[2] - 40), int(center_y - box_h/2), 80, int(box_h))
        
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(int(col_x[2] - 35), int(center_y - box_h/2 + 15), "OUTPUTS")
        
        for i, out in enumerate(self.outputs):
            painter.setPen(QPen(QColor("#0078d4"), 2))
            text = f"{out.target.split('/')[-1]} = {out.value}"
            painter.drawText(int(col_x[2] - 35), int(center_y - box_h/2 + 35 + (i*15)), text)

        # 4. Draw Arrows
        pen = QPen(QColor("#555"), 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Inputs to Gate
        path = QPainterPath()
        path.moveTo(col_x[0] + 40, center_y)
        path.lineTo(col_x[1] - 25, center_y)
        painter.drawPath(path)

        # Gate to Outputs
        path2 = QPainterPath()
        path2.moveTo(col_x[1] + 25, center_y)
        path2.lineTo(col_x[2] - 40, center_y)
        painter.drawPath(path2)