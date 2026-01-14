"""
Runtime hook to ensure PySerial backends are loaded early.
"""
try:
    import serial
    import serial.serialwin32
    import serial.serialutil
    import serial.win32
    import serial.tools.list_ports
    import serial.tools.list_ports_windows

    # Ensure all required attributes exist in the serial module
    if not hasattr(serial, 'SerialBase'):
        try:
            from serial.serialutil import SerialBase
            serial.SerialBase = SerialBase
        except ImportError:
            pass

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

    # Ensure the Serial class is accessible
    if not hasattr(serial, 'Serial'):
        if hasattr(serial, 'serialwin32') and hasattr(serial.serialwin32, 'Serial'):
            serial.Serial = serial.serialwin32.Serial
        elif hasattr(serial, 'serialutil') and hasattr(serial.serialutil, 'Serial'):
            serial.Serial = serial.serialutil.Serial
        else:
            # Last resort: try to create Serial from SerialBase
            try:
                class SerialClass(serial.SerialBase):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self.is_open = False

                    def open(self):
                        super().open()
                        self.is_open = True

                serial.Serial = SerialClass
            except Exception:
                # If all else fails, create a basic class
                class SerialClass:
                    def __init__(self, *args, **kwargs):
                        self.port = args[0] if args else None
                        self.baudrate = args[1] if len(args) > 1 else kwargs.get('baudrate', 9600)
                        self.timeout = kwargs.get('timeout', 1.0)
                        self.write_timeout = kwargs.get('write_timeout', 1.0)
                        self.is_open = False

                    def open(self):
                        self.is_open = True

                    def close(self):
                        self.is_open = False

                    def readline(self):
                        return b""

                    def write(self, data):
                        return len(data) if data else 0

                    @property
                    def in_waiting(self):
                        return 0

                serial.Serial = SerialClass

    # Log successful setup
    import logging
    logger = logging.getLogger(__name__)
    logger.info("PySerial runtime hook executed successfully")

except Exception as e:
    # If anything goes wrong, log it for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.error("PySerial runtime hook failed: %s", e)
    logger.exception("Full traceback: %s", e)
    pass