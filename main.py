#!/usr/bin/env python3
"""
X-Plane Dataref Bridge
Main entry point
"""
import sys
import logging
import asyncio

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bridge_log.txt", mode='w'),
        logging.StreamHandler()
    ]
)

# Quiet down noisy loggers
logging.getLogger("qasync").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

def exception_hook(exctype, value, traceback_obj):
    """Global exception handler to log crashes."""
    log.critical("Uncaught exception:", exc_info=(exctype, value, traceback_obj))
    sys.__excepthook__(exctype, value, traceback_obj)

sys.excepthook = exception_hook


def main() -> int:
    """Main entry point."""
    
    log.info("Starting X-Plane Dataref Bridge...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("X-Plane Dataref Bridge")

    # Set application icon
    from PyQt6.QtGui import QIcon
    import os
    # Try ICO format first (for Windows), fallback to PNG
    icon_path_ico = os.path.join(os.path.dirname(__file__), "resources", "icon.ico")
    icon_path_png = os.path.join(os.path.dirname(__file__), "resources", "Gemini_Generated_Image_5v3gkv5v3gkv5v3g-removebg-preview.png")

    if os.path.exists(icon_path_ico):
        app.setWindowIcon(QIcon(icon_path_ico))
    elif os.path.exists(icon_path_png):
        app.setWindowIcon(QIcon(icon_path_png))
    
    # Create async event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Import after Qt is initialized
    from core.hid_manager import HIDManager
    from core.arduino.arduino_manager import ArduinoManager
    from core.dataref_manager import DatarefManager
    from core.xplane_connection import XPlaneConnection
    from gui.main_window import MainWindow
    
    # Create variable store first (needed by other components)
    from core.variable_store import VariableStore
    variable_store = VariableStore()

    # Create managers
    arduino_manager = ArduinoManager(variable_store=variable_store)
    dataref_manager = DatarefManager(variable_store=variable_store, arduino_manager=arduino_manager)
    xplane_conn = XPlaneConnection()
    hid_manager = HIDManager()
    
    # Set references in arduino_manager
    arduino_manager.dataref_manager = dataref_manager
    arduino_manager.xplane_conn = xplane_conn
    
    # Create main window
    window = MainWindow(
        xplane_conn=xplane_conn,
        dataref_manager=dataref_manager,
        arduino_manager=arduino_manager,
        hid_manager=hid_manager,
        variable_store=variable_store,
    )
    window.show()
    
    log.info("Application ready")
    
    # Run event loop
    with loop:
        return loop.run_forever()


if __name__ == "__main__":
    sys.exit(main())