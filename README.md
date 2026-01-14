# X-Plane Dataref Bridge

A Python-based application that bridges X-Plane flight simulator datarefs to Arduino and HID devices, allowing for custom hardware interfaces and control systems.

## Features

- Real-time communication with X-Plane flight simulator
- Support for Arduino devices (ESP32, etc.)
- HID device integration
- Customizable dataref mappings
- GUI interface for configuration
- Profile management for different aircraft/hardware setups

## Prerequisites

- Python 3.8 or higher
- X-Plane flight simulator (tested with X-Plane 11/12 -- needs more testing)

## Installation

### Option 1: Download Pre-built Executable

**Windows:**
- Download the latest `X-Plane Dataref Bridge-Windows.zip` from releases
- Extract and run `X-Plane Dataref Bridge.exe` (no installation required)
- Admin privileges recommended for serial port access

**Linux/macOS:**
- Follow build instructions below or download from releases (if available)

### Option 2: Build from Source

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/x-plane-dataref-bridge.git
cd x-plane-dataref-bridge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Build for your platform:
```bash
# Windows (automatic)
powershell -ExecutionPolicy Bypass -File build_multi_platform.ps1

# Linux/macOS
python setup_cross_platform.py build
```

## Cross-Platform Building

This project includes automated cross-platform build scripts:

### Build Scripts
- `setup_cross_platform.py` - Cross-platform build script
- `build_multi_platform.ps1` - Windows PowerShell build script

### Build Requirements
```bash
pip install PyQt6 cx_Freeze==8.5.3 serial pyserial hidapi Pillow
```

### Platform-Specific Builds

**Windows:**
- GUI executable with taskbar icon
- No console window
- Icon displays in taskbar and title bar ✅

**Linux:**
- Console executable
- Full library bundling
- Standard Linux application

**macOS:**
- Console executable with PNG icon support
- Automatic .icns generation for proper app bundle

### Features
- ✅ Real dataref descriptions (from database)
- ✅ Icon display in taskbar and window title
- ✅ Cross-platform compatibility
- ✅ Automated dependency bundling

## Usage

Run the application:
```bash
python main.py
```

## Building Executable

To build a standalone executable with PyInstaller:
```bash
pyinstaller main.spec
```

The executable will be created in the `dist/` folder with the custom icon.

## Configuration

- Dataref mappings can be configured through the GUI
- Profiles can be saved and loaded for different aircraft/hardware setups
- Arduino sketches are available in the `Arduino libraries/examples` folder

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms specified in the LICENSE file.
