import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'serial.serialwin32',
        'serial.win32',
        'serial.serialutil',
        'serial.threaded',
        'qasync',
        'PyQt6',
    ],
    "includes": [
        'serial.serialutil',
        'serial.threaded',
        'serial.urlhandler',
        'serial.urlhandler.protocol_socket',
        'serial.urlhandler.protocol_rfc2217',
        'serial.urlhandler.protocol_loop',
        'serial.urlhandler.protocol_alt',
        'serial.urlhandler.protocol_cp2110',
        'serial.urlhandler.protocol_hwgrep',
        'serial.urlhandler.protocol_spy',
    ],
    "excludes": [],
    "optimize": 0,
}

# For Windows GUI application without console
if sys.platform == "win32":
    base = "gui"  # Use 'gui' for Windows GUI applications
else:
    base = None

# Alternative base options:
# base = "console"  # For console applications
# base = "Win32GUI"  # Another option for Windows GUI (might not be available)

executables = [
    Executable(
        "main.py",
        base=base,
        target_name="X-Plane Dataref Bridge.exe",
        icon="resources/icon.ico"
    )
]

setup(
    name="X-Plane Dataref Bridge",
    version="1.0",
    description="X-Plane Dataref Bridge",
    options={"build_exe": build_exe_options},
    executables=executables
)