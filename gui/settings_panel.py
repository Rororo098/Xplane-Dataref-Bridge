from __future__ import annotations
import logging
import json
from pathlib import Path
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QFormLayout,
    QSpinBox, QCheckBox, QMessageBox,
)

log = logging.getLogger(__name__)

SETTINGS_FILE = Path(__file__).parent.parent / "config" / "settings.json"


class SettingsPanel(QWidget):
    """Application settings panel."""
    
    def __init__(self) -> None:
        super().__init__()
        
        self.settings: Dict[str, Any] = {}
        
        self._setup_ui()
        self._connect_signals()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # X-Plane connection
        xplane_group = QGroupBox("X-Plane Connection")
        xplane_layout = QFormLayout(xplane_group)
        
        self.xplane_ip = QLineEdit("127.0.0.1")
        self.xplane_ip.setToolTip("IP address of the computer running X-Plane")
        
        self.xplane_port = QSpinBox()
        self.xplane_port.setRange(1, 65535)
        self.xplane_port.setValue(49000)
        self.xplane_port.setToolTip("Port X-Plane receives on (usually 49000)")
        
        self.recv_port = QSpinBox()
        self.recv_port.setRange(1, 65535)
        self.recv_port.setValue(49001)  # Changed from 49008 to 49001
        xplane_layout.addRow("X-Plane IP:", self.xplane_ip)
        xplane_layout.addRow("Send to Port:", self.xplane_port)
        xplane_layout.addRow("Receive on Port:", self.recv_port)
        
        # Help text
        help_label = QLabel(
            "<b>X-Plane Setup:</b><br>"
            "1. In X-Plane: Settings → Network<br>"
            "2. Under 'Data Output', set IP to 127.0.0.1<br>"
            "3. Set Port to match 'Receive on Port' above (49008)<br>"
            "4. Ensure 'Port we receive on (legacy)' is 49000"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: gray; font-size: 10px;")
        xplane_layout.addRow(help_label)
        
        layout.addWidget(xplane_group)
        
        # Arduino settings
        arduino_group = QGroupBox("Arduino Settings")
        arduino_layout = QFormLayout(arduino_group)
        
        self.arduino_baud = QSpinBox()
        self.arduino_baud.setRange(9600, 921600)
        self.arduino_baud.setValue(115200)
        
        self.auto_reconnect = QCheckBox()
        self.auto_reconnect.setChecked(True)
        
        arduino_layout.addRow("Baud Rate:", self.arduino_baud)
        arduino_layout.addRow("Auto-reconnect:", self.auto_reconnect)
        
        layout.addWidget(arduino_group)
        
        # Save and donation buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # Donation buttons
        self.paypal_btn = QPushButton("❤️ Donate via PayPal")
        self.paypal_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_layout.addWidget(self.paypal_btn)

        self.stripe_btn = QPushButton("💳 Donate via Stripe")
        self.stripe_btn.setStyleSheet("""
            QPushButton {
                background-color: #635bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5951e6;
            }
        """)
        btn_layout.addWidget(self.stripe_btn)

        self.save_btn = QPushButton("Save Settings")
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        self.save_btn.clicked.connect(self._save_settings)
        self.paypal_btn.clicked.connect(self._open_paypal_page)
        self.stripe_btn.clicked.connect(self._open_stripe_page)
    
    def _load_settings(self) -> None:
        """Load settings from file."""
        try:
            if SETTINGS_FILE.exists():
                self.settings = json.loads(SETTINGS_FILE.read_text())
                
                self.xplane_ip.setText(self.settings.get("xplane_ip", "127.0.0.1"))
                self.xplane_port.setValue(self.settings.get("xplane_port", 49000))
                self.recv_port.setValue(self.settings.get("recv_port", 49008))
                self.arduino_baud.setValue(self.settings.get("arduino_baud", 115200))
                self.auto_reconnect.setChecked(self.settings.get("auto_reconnect", True))
                
                log.info("Settings loaded")
        except Exception as e:
            log.error("Failed to load settings: %s", e)
    
    def _save_settings(self) -> None:
        """Save settings to file."""
        try:
            self.settings = {
                "xplane_ip": self.xplane_ip.text(),
                "xplane_port": self.xplane_port.value(),
                "recv_port": self.recv_port.value(),
                "arduino_baud": self.arduino_baud.value(),
                "auto_reconnect": self.auto_reconnect.isChecked(),
            }
            
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2))
            
            QMessageBox.information(self, "Settings", "Settings saved successfully.")
            log.info("Settings saved")
        except Exception as e:
            log.error("Failed to save settings: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def get_xplane_ip(self) -> str:
        return self.xplane_ip.text()
    
    def get_xplane_port(self) -> int:
        return self.xplane_port.value()
    
    def get_recv_port(self) -> int:
        return self.recv_port.value()
    
    def get_arduino_baud(self) -> int:
        return self.arduino_baud.value()

    def _open_paypal_page(self):
        """Open the PayPal donation page in the default browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://www.paypal.me/Ruzu26"))

    def _open_stripe_page(self):
        """Open the Stripe donation page in the default browser."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://donate.stripe.com/test_dRm14n4gE5Av51d0cV7Vm00"))