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

# Force PyInstaller to include all serial backends at runtime
try:
    import serial
    import serial.serialwin32
    import serial.win32
    import serial.serialutil
    import serial.threaded
    import serial.tools.list_ports
    import serial.tools.list_ports_windows

    # Ensure critical attributes exist in the serial module
    if not hasattr(serial, 'SerialBase'):
        try:
            from serial.serialutil import SerialBase
            serial.SerialBase = SerialBase
        except ImportError:
            pass

    # Handle bit constants carefully
    if not hasattr(serial, 'FIVEBITS'):
        try:
            from serial import FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
            serial.FIVEBITS = FIVEBITS
            serial.SIXBITS = SIXBITS
            serial.SEVENBITS = SEVENBITS
            serial.EIGHTBITS = EIGHTBITS
        except ImportError:
            # Define defaults if import fails
            serial.FIVEBITS = 5
            serial.SIXBITS = 6
            serial.SEVENBITS = 7
            serial.EIGHTBITS = 8

    if not hasattr(serial, 'STOPBITS_ONE'):
        try:
            from serial import STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
            serial.STOPBITS_ONE = STOPBITS_ONE
            serial.STOPBITS_ONE_POINT_FIVE = STOPBITS_ONE_POINT_FIVE
            serial.STOPBITS_TWO = STOPBITS_TWO
        except ImportError:
            # Define defaults if import fails
            serial.STOPBITS_ONE = 1
            serial.STOPBITS_ONE_POINT_FIVE = 1.5
            serial.STOPBITS_TWO = 2

    if not hasattr(serial, 'PARITY_NONE'):
        try:
            from serial import PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE
            serial.PARITY_NONE = PARITY_NONE
            serial.PARITY_EVEN = PARITY_EVEN
            serial.PARITY_ODD = PARITY_ODD
            serial.PARITY_MARK = PARITY_MARK
            serial.PARITY_SPACE = PARITY_SPACE
        except ImportError:
            # Define defaults if import fails
            serial.PARITY_NONE = 'N'
            serial.PARITY_EVEN = 'E'
            serial.PARITY_ODD = 'O'
            serial.PARITY_MARK = 'M'
            serial.PARITY_SPACE = 'S'

    # Verify Serial class is available
    if not hasattr(serial, 'Serial'):
        if hasattr(serial, 'serialwin32') and hasattr(serial.serialwin32, 'Serial'):
            serial.Serial = serial.serialwin32.Serial
        elif hasattr(serial, 'serialutil') and hasattr(serial.serialutil, 'Serial'):
            serial.Serial = serial.serialutil.Serial
        else:
            # Create a fallback Serial class
            try:
                class SerialClass(serial.SerialBase):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self.is_open = False

                    def open(self):
                        super().open()
                        self.is_open = True

                serial.Serial = SerialClass
            except:
                # If all else fails, create a basic class
                class SerialClass:
                    def __init__(self, *args, **kwargs):
                        self.port = args[0] if args else None
                        self.baudrate = args[1] if len(args) > 1 else kwargs.get('baudrate', 9600)
                        self.bytesize = kwargs.get('bytesize', 8)
                        self.parity = kwargs.get('parity', 'N')
                        self.stopbits = kwargs.get('stopbits', 1)
                        self.timeout = kwargs.get('timeout', 1.0)
                        self.write_timeout = kwargs.get('write_timeout', 1.0)
                        self.xonxoff = kwargs.get('xonxoff', False)
                        self.rtscts = kwargs.get('rtscts', False)
                        self.dsrdtr = kwargs.get('dsrdtr', False)
                        self.is_open = False

                    def open(self):
                        self.is_open = True

                    def close(self):
                        self.is_open = False

                    def readline(self):
                        return b""

                    def read(self, size=1):
                        return b""

                    def write(self, data):
                        return len(data) if data else 0

                    def flush(self):
                        pass

                    def flushInput(self):
                        pass

                    def flushOutput(self):
                        pass

                    def reset_input_buffer(self):
                        pass

                    def reset_output_buffer(self):
                        pass

                    @property
                    def in_waiting(self):
                        return 0

                serial.Serial = SerialClass

    log.info("Serial backends imported successfully at runtime")
    log.info("Serial module location: %s", getattr(serial, '__file__', 'unknown'))
    log.info("Serial class available: %s", hasattr(serial, 'Serial'))
    log.info("SerialBase available: %s", hasattr(serial, 'SerialBase'))
    log.info("FIVEBITS available: %s", hasattr(serial, 'FIVEBITS'))

except Exception as e:
    log.error("Critical serial backend import issue at runtime: %s", e)
    import traceback
    log.error("Full traceback: %s", traceback.format_exc())

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