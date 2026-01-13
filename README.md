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
- X-Plane flight simulator (tested with X-Plane 11/12)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/x-plane-dataref-bridge.git
cd x-plane-dataref-bridge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

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