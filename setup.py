import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically included with cx_Freeze
# but we can specify additional packages here
build_exe_options = {
    "include_files": [
        ("config", "config"),
        ("resources", "resources"),
        ("gui", "gui"),
        ("core", "core"),
        ("hooks", "hooks"),
    ],
    "zip_exclude_packages": [
        "PyQt6",
        "qasync",
        "serial",
        "hidapi",
    ],  # Keep GUI and hardware libs accessible
}

# GUI applications require a different base
base = "gui" if sys.platform == "win32" else None

executables = [
    Executable(
        "main.py",
        base=base,
        icon="resources/icon.ico",
        target_name="X-Plane Dataref Bridge",
    )
]

setup(
    name="X-Plane Dataref Bridge",
    version="1.0",
    description="Hardware Interface for X-Plane Flight Simulator",
    options={"build_exe": build_exe_options},
    executables=executables,
)
