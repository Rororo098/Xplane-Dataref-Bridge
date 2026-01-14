import sys
from cx_Freeze import setup, Executable
import os

# Build options for cx_Freeze
build_exe_options = {
    "packages": [
        # Core packages
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'serial.serialwin32',
        'serial.win32',
        'serial.serialutil',
        'serial.threaded',
        'serial.urlhandler',

        # PyQt6 packages
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',

        # Async packages
        'qasync',

        # Core application packages
        'core',
        'core.arduino',
        'core.input_mapper',
        'core.xplane_connection',
        'core.hid_manager',
        'core.variable_store',
        'core.dataref_manager',

        # GUI packages
        'gui',
        'gui.widgets',

        # Utility packages
        'utils',

        # Standard library packages often needed
        'json',
        'logging',
        'asyncio',
        're',
        'pathlib',
        'typing',
        'os',
        'sys',
        'time',
        'threading',
        'queue',
        'collections',
        'dataclasses',
    ],
    "includes": [
        # Explicit includes for serial backends
        'serial.serialutil',
        'serial.threaded',
        'serial.urlhandler.protocol_socket',
        'serial.urlhandler.protocol_rfc2217',
        'serial.urlhandler.protocol_loop',
        'serial.urlhandler.protocol_alt',
        'serial.urlhandler.protocol_cp2110',
        'serial.urlhandler.protocol_hwgrep',
        'serial.urlhandler.protocol_spy',

        # Windows-specific serial modules
        'serial.serialwin32',
        'serial.win32',
        'serial.tools.list_ports_windows',

        # Additional modules that might be missed
        'hidapi',
        'requests',
        'aiohttp',
        'websockets',
        'lxml',
        'bs4',
        'bs4.BeautifulSoup',
    ],
    "excludes": [
        # Exclude modules that are not needed for Windows
        'tkinter',  # If not using tkinter
    ],
    "include_files": [
        # Include resources directory
        ("resources", "resources"),
        # Include dataref database
        ("resources/dataref_database.json", "resources/dataref_database.json"),
        # Include any other necessary files
        ("runtime_hooks", "runtime_hooks"),
    ],
    "optimize": 0,
    "compressed": True,
    "create_shared_zip": False,
    "include_in_path": ['DLLs', 'Lib'],
}

# For Windows GUI application without console
if sys.platform == "win32":
    base = "Win32GUI"  # Use 'Win32GUI' for Windows GUI applications without console
else:
    base = None

executables = [
    Executable(
        "main.py",
        base=base,
        target_name="X-Plane Dataref Bridge.exe",
        icon="resources/icon.ico",
        shortcut_name="X-Plane Dataref Bridge",
        shortcut_dir="ProgramMenuFolder",
    )
]

setup(
    name="X-Plane Dataref Bridge",
    version="1.0.0",
    description="X-Plane Dataref Bridge - Connect X-Plane to Arduino Hardware",
    author="X-Plane Dataref Bridge Team",
    options={"build_exe": build_exe_options},
    executables=executables
)