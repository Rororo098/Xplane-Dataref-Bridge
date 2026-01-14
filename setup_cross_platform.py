import sys
import os
from cx_Freeze import setup, Executable
from PIL import Image

# Determine platform and build options
platform = sys.platform

# Common packages
common_packages = [
    "serial",
    "serial.tools",
    "serial.tools.list_ports",
    "asyncio",
    "json",
    "logging",
    "re",
    "pathlib",
    "typing",
    "os",
    "sys",
    "time",
    "threading",
    "queue",
    "collections",
    "dataclasses",
]

# Platform-specific packages
if platform.startswith("linux"):
    packages = common_packages + [
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "qasync",
        "core",
        "core.arduino",
        "core.input_mapper",
        "core.xplane_connection",
        "core.hid_manager",
        "core.variable_store",
        "core.dataref_manager",
        "gui",
        "gui.widgets",
        "utils",
    ]
    includes = [
        "hidapi",
        "requests",
        "aiohttp",
        "websockets",
        "lxml",
        "bs4",
    ]
    base = None  # Console on Linux
    executable_name = "x-plane-dataref-bridge"

elif platform == "darwin":  # macOS
    packages = common_packages + [
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "qasync",
        "core",
        "core.arduino",
        "core.input_mapper",
        "core.xplane_connection",
        "core.hid_manager",
        "core.variable_store",
        "core.dataref_manager",
        "gui",
        "gui.widgets",
        "utils",
    ]
    includes = [
        "hidapi",
        "requests",
        "aiohttp",
        "websockets",
        "lxml",
        "bs4",
    ]
    base = None  # Console on macOS
    executable_name = "X-Plane Dataref Bridge"

else:  # Windows
    packages = common_packages + [
        # Core packages
        "serial",
        "serial.tools",
        "serial.tools.list_ports",
        "serial.serialwin32",
        "serial.win32",
        "serial.serialutil",
        "serial.threaded",
        "serial.urlhandler",
        # PyQt6 packages
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        # Async packages
        "qasync",
        # Core application packages
        "core",
        "core.arduino",
        "core.input_mapper",
        "core.xplane_connection",
        "core.hid_manager",
        "core.variable_store",
        "core.dataref_manager",
        # GUI packages
        "gui",
        "gui.widgets",
        # Utility packages
        "utils",
    ]
    includes = [
        # Explicit includes for serial backends
        "serial.serialutil",
        "serial.threaded",
        "serial.urlhandler.protocol_socket",
        "serial.urlhandler.protocol_rfc2217",
        "serial.urlhandler.protocol_loop",
        "serial.urlhandler.protocol_alt",
        "serial.urlhandler.protocol_cp2110",
        "serial.urlhandler.protocol_hwgrep",
        "serial.urlhandler.protocol_spy",
        # Windows-specific serial modules
        "serial.serialwin32",
        "serial.win32",
        "serial.tools.list_ports_windows",
        # Additional modules
        "requests",
        "aiohttp",
        "websockets",
        "lxml",
        "bs4",
    ]
    base = "gui"  # GUI for Windows
    executable_name = "X-Plane Dataref Bridge"

# Common build options
build_exe_options = {
    "packages": packages,
    "includes": includes,
    "excludes": ["tkinter"],
    "include_files": [
        ("resources", "resources"),
        ("resources/dataref_database.json", "resources/dataref_database.json"),
    ],
    "optimize": 0,
}

# Icon setup
icon_path = None
if os.path.exists("resources/icon.ico"):
    icon_path = "resources/icon.ico"
elif os.path.exists("resources/icon.png"):
    icon_path = "resources/icon.png"

# Create .icns for macOS if needed
if platform == "darwin" and os.path.exists("resources/icon.png"):
    try:
        from PIL import Image

        img = Image.open("resources/icon.png")
        # Create different sizes for .icns
        sizes = [16, 32, 128, 256, 512]
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(f"resources/icon_{size}x{size}.png")
        icon_path = "resources/icon.icns"
    except ImportError:
        print("Warning: PIL not available for macOS icon creation")
        icon_path = "resources/icon.png"

executables = [
    Executable(
        "main.py",
        base=base,
        target_name=executable_name,
        icon=icon_path,
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
    executables=executables,
)
