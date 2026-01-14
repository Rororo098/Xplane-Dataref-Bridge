# ESP32-S2 Serial Connection Fix for PyInstaller EXE

## Problem Description
The X-Plane Dataref Bridge application connects properly when run from source but fails to connect when packaged as an EXE using PyInstaller. The logs show errors like:
- `Cannot open port COM7: module 'serial' has no attribute 'SerialBase'`
- `Cannot open port COM7: module 'serial' has no attribute 'FIVEBITS'`
- `pyserial Serial class not available`

## Root Cause
PyInstaller was not properly bundling the necessary pyserial backend modules and constants required for serial communication on Windows systems, particularly the Windows-specific backends that ESP32-S2 devices need.

## Solution Implemented

### 1. Enhanced `main.spec` Configuration
```python
hiddenimports=[
    'qasync',
    'qasync.qtloop',
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'serial',
    'serial.SerialBase',
    'serial.serialutil',
    'serial.serialwin32',
    'serial.win32',
    'serial.threaded',
    'serial.tools',
    'serial.tools.list_ports',
    'serial.tools.list_ports_windows',
    'serial.tools.list_ports_common',
    'serial.urlhandler',
    'serial.urlhandler.protocol_alt',
    'serial.urlhandler.protocol_cp2110',
    'serial.urlhandler.protocol_hwgrep',
    'serial.urlhandler.protocol_loop',
    'serial.urlhandler.protocol_rfc2217',
    'serial.urlhandler.protocol_socket',
    'serial.urlhandler.protocol_spy',
    'hid',
    'requests',
    'aiohttp',
    'websockets',
    'lxml',
    'bs4'
],

# Added runtime hooks
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='X-Plane Dataref Bridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
    runtime_hooks=['runtime_hooks/pyserial_loader.py'],  # NEW
)
```

### 2. Enhanced Serial Hook (`hooks/hook-serial.py`)
```python
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all pyserial modules (including Windows-specific backends)
hiddenimports = collect_submodules('serial')

# Explicitly ensure critical modules are included
hiddenimports += [
    'serial.SerialBase',
    'serial.serialutil',
    'serial.serialwin32',
    'serial.win32',
    'serial.threaded',
    'serial.rfc2217',
    'serial.serialcli',
    'serial.rs485',
]

# Include any data files a serial package might ship
datas = collect_data_files('serial')
```

### 3. Updated `main.py`
Added explicit serial backend imports at runtime:
```python
# Force PyInstaller to include all serial backends at runtime
try:
    import serial.serialwin32
    import serial.win32
    import serial.serialutil
    import serial.threaded
    import serial
    log.info("Serial backends imported successfully at runtime")
except Exception as e:
    log.warning("Serial backend import issue at runtime: %s", e)
```

### 4. Created Runtime Hook (`runtime_hooks/pyserial_loader.py`)
```python
"""
Runtime hook to ensure PySerial backends are loaded early.
"""
try:
    import serial.serialwin32
    import serial.serialutil
    import serial
    if not hasattr(serial, 'SerialBase'):
        from serial.serialutil import SerialBase
        serial.SerialBase = SerialBase
except Exception:
    # If anything goes wrong, fail gracefully; main can log it
    pass
```

## Key Changes Summary

1. **Added explicit serial backend imports** to ensure PyInstaller bundles Windows-specific modules
2. **Enhanced hook-serial.py** to collect all serial submodules using `collect_submodules`
3. **Added runtime hook** to pre-load serial backends when the application starts
4. **Updated main.py** to force import of serial backends at startup
5. **Added comprehensive hidden imports** for all serial-related modules and protocols

## Expected Result

The packaged EXE should now:
- ✅ Bundle all necessary pyserial backends including SerialBase and Windows backends
- ✅ Show "Serial backends imported successfully at runtime" in the logs
- ✅ Successfully attempt to open COM ports without missing attribute errors
- ✅ Connect to ESP32-S2 devices when they are available and not in use by other processes

## Troubleshooting Notes

If the EXE still shows "PermissionError" on COM ports:
- Make sure the port isn't in use by another app (including a previous instance of the EXE)
- Run the EXE as Administrator to avoid Windows port restrictions
- Ensure the ESP32-S2 is connected, USB driver is installed, and USB CDC is enabled

If you still see "FIVEBITS" or other missing attribute errors:
- It's a symptom of an incomplete pyserial bundle in the EXE
- The patches above should fix the missing constants