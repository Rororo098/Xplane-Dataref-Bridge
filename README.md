# X-Plane Dataref Bridge

A comprehensive bridge connecting X-Plane flight simulator to Arduino and other microcontrollers

**License:** MIT
**Technologies:** Python, X-Plane

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Arduino Sketches](#arduino-sketches)
- [Protocol Documentation](#protocol-documentation)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Overview

The X-Plane Dataref Bridge is a Python/PyQt6 application that creates a communication bridge between X-Plane flight simulator and Arduino microcontrollers. It enables you to build custom hardware cockpits with authentic instruments, switches, and controls that interact with X-Plane in real-time.

### How it works:
- X-Plane sends datarefs via UDP
- The bridge application receives and processes these datarefs
- Microcontroller (Arduino/ESP32) communicates via USB serial
- Bidirectional communication: read from X-Plane, write to X-Plane

## Features

✅ **Real-time Dataref Monitoring:** Monitor any X-Plane dataref in real-time
✅ **Bidirectional Communication:** Both read from and write to X-Plane
✅ **Multiple Data Types:** Support for int, float, bool, byte, string, and array datarefs
✅ **Command Execution:** Execute X-Plane commands from hardware
✅ **Hardware Abstraction:** Works with Arduino, ESP32, and other serial devices
✅ **GUI Interface:** Intuitive PyQt6-based user interface
✅ **Input Mapping:** Map hardware inputs (buttons, encoders, pots) to X-Plane actions
✅ **Output Mapping:** Map X-Plane datarefs to hardware outputs (LEDs, servos, displays)
✅ **Auto-Discovery:** Automatic detection of X-Plane and connected devices
✅ **Cross-Platform:** Runs on Windows, macOS, and Linux

## Installation

### Prerequisites
- Python 3.8 or higher
- X-Plane 11 or 12
- Arduino IDE (for microcontroller programming)

### Cross-Platform Installation

#### Windows
```bash
# Clone the repository
git clone https://github.com/Rororo098/Xplane-Dataref-Bridge.git
cd Xplane-Dataref-Bridge

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

#### macOS
```bash
# Clone the repository
git clone https://github.com/Rororo098/Xplane-Dataref-Bridge.git
cd Xplane-Dataref-Bridge

# Install dependencies (use python3 and pip3 on macOS)
pip3 install -r requirements.txt

# Run the application
python3 main.py
```

#### Linux
```bash
# Clone the repository
git clone https://github.com/Rororo098/Xplane-Dataref-Bridge.git
cd Xplane-Dataref-Bridge

# Install dependencies (use python3 and pip3 on Linux)
pip3 install -r requirements.txt

# Run the application
python3 main.py
```

**Note for Linux users:** You may need to install additional system packages:

- Ubuntu/Debian: `sudo apt install python3-pyqt6 python3-serial`
- Fedora: `sudo dnf install python3-PyQt6 python3-pyserial`
- Arch: `sudo pacman -S python-pyqt6 python-pyserial`

You may also need to add your user to the dialout group for serial access:

```bash
sudo usermod -a -G dialout $USER
# Then log out and log back in for changes to take effect
```

### Standalone Executable
Pre-built executables are available in the releases section for Windows, macOS, and Linux.

## Quick Start

1. Start X-Plane with your aircraft loaded
2. Upload Arduino sketch (see Arduino Sketches section below)
3. Connect Arduino via USB to your computer
4. Run the Bridge application
5. Connect to X-Plane using the Connect button
6. Configure datarefs in the Output Config tab
7. Map hardware in the Input Config tab

## Arduino Sketches

Comprehensive Arduino sketches demonstrating communication with the X-Plane Dataref Bridge. Each sketch focuses on a specific capability of the protocol.

### 1. 4-Button Controller with Proper Protocol

**File:** `4_button_controller_corrected.ino`

A 4-button controller that sends different types of commands using the correct protocol.

**Features:** Button debouncing, multiple operations, proper serial protocol
**Output ID:** FourButtonController

```cpp
/*
===============================================================================
X-Plane Dataref Bridge - 4 Button Controller with OUTPUT_IDs (Beginner Version)
===============================================================================

PURPOSE:
This sketch creates a 4-button controller that sends different types of commands
to X-Plane through Dataref Bridge application. Each button demonstrates a
different type of dataref operation.

REQUIRED HARDWARE:
- Arduino UNO (or compatible board)
- 4x Push buttons (momentary switches)
- 4x 10kΩ resistors (optional, if not using internal pull-ups)
- Jumper wires
- USB cable for programming and communication

WIRING INSTRUCTIONS:
- Connect Button 1 between Pin 2 and GND
- Connect Button 2 between Pin 3 and GND
- Connect Button 3 between Pin 4 and GND
- Connect Button 4 between Pin 5 and GND
- Arduino GND to common ground rail
- USB connects to computer running X-Plane Dataref Bridge

BUTTON FUNCTIONALITY:
Button 1 (Pin 2): Sends GEAR_HANDLE command - controls landing gear
Button 2 (Pin 3): Sends HEADING_SYNC command - synchronizes heading
Button 3 (Pin 4): Sends LED_STATE_ELEM0 - controls individual LED array element
Button 4 (Pin 5): Sends LED_STATE_ARRAY - controls multiple LED array elements

OUTPUT_ID SYSTEM:
OUTPUT_IDs are user-friendly names that you configure in bridge application
to map to actual X-Plane datarefs. This makes your Arduino code reusable across
different aircraft and easier to understand.

BRIDGE CONFIGURATION:
In your X-Plane Dataref Bridge application, map these OUTPUT_IDs:
GEAR_HANDLE → sim/cockpit2/switches/gear_handle_status
HEADING_SYNC → sim/autopilot/heading_sync
LED_STATE_ELEM0 → LED_STATE[0]
LED_STATE_ARRAY → LED_STATE (full array)

TROUBLESHOOTING:
- Buttons not working? Check wiring and GND connection
- No communication? Verify 115200 baud rate in Serial Monitor
- Multiple triggers per press? Increase DEBOUNCE_DELAY value
===============================================================================
*/
```

### 2. 4-Axis Input Controller with Proper Protocol

**File:** `4_axis_input_controller_corrected.ino`

A 4-axis input controller with different functionality per axis using correct protocol.

**Features:** Analog input handling, threshold detection, proper serial protocol
**Output ID:** 4AxisController

```cpp
/*
===============================================================================
X-Plane Dataref Bridge - 4 Axis Input Controller with OUTPUT_IDs (Beginner Version)
===============================================================================

PURPOSE:
This sketch creates a 4-axis input controller using analog inputs (potentiometers or
joystick axes) to control different X-Plane systems. Each axis demonstrates a
different type of dataref operation.

REQUIRED HARDWARE:
- Arduino UNO (or compatible board)
- 4x Potentiometers (10kΩ recommended) OR 2-axis joystick + 2x potentiometers
- Breadboard and jumper wires
- USB cable for programming and communication

WIRING INSTRUCTIONS (for 4x potentiometers):
- Potentiometer 1: Center pin → A0, Outer pins → 5V and GND
- Potentiometer 2: Center pin → A1, Outer pins → 5V and GND
- Potentiometer 3: Center pin → A2, Outer pins → 5V and GND
- Potentiometer 4: Center pin → A3, Outer pins → 5V and GND

AXIS FUNCTIONALITY:
Axis 1 (A0): THROTTLE_AXIS - Smooth throttle control (0.0 to 1.0)
Axis 2 (A1): AUTOPILOT_TOGGLE - Binary control for autopilot on/off
Axis 3 (A2): DOOR_ELEM[n] - Controls specific door elements based on position
Axis 4 (A3): DOOR_ARRAY - Controls multiple door elements simultaneously

OUTPUT_ID SYSTEM:
OUTPUT_IDs are user-friendly names that you configure in bridge application
to map to actual X-Plane datarefs. This makes your code reusable across different
aircraft and much easier to understand than hardcoded X-Plane paths.

BRIDGE CONFIGURATION:
In your X-Plane Dataref Bridge application, map these OUTPUT_IDs:
THROTTLE_AXIS → sim/cockpit2/engine/actuators/throttle_ratio_all
AUTOPILOT_TOGGLE → sim/autopilot/autopilot_on (1) / sim/autopilot/autopilot_off (0)
DOOR_ELEM[n] → sim/flightmodel2/misc/door_open_ratio[n]
DOOR_ARRAY → sim/flightmodel2/misc/door_open_ratio (full array)

ANALOG INPUT BASICS:
- Arduino reads analog values from 0 (0V) to 1023 (5V)
- We convert these to useful ranges (0.0-1.0 for percentages)
- Potentiometers provide smooth, continuous control
- Higher analog readings = higher voltage = higher control value

TROUBLESHOOTING:
- Erratic readings? Check power supply stability and ground connections
- No response? Verify analog pins and potentiometer wiring
- Jumping values? Add small capacitor (10nF) across potentiometer outer pins
===============================================================================
*/
```

### 3. Digital Outputs Controller with Proper Protocol

**File:** `digital_outputs_controller_corrected.ino`

4 digital outputs that respond to different dataref types using correct protocol.

**Features:** Digital output control, value parsing, proper serial protocol
**Output ID:** DigitalOutputsController

```cpp
/*
===============================================================================
X-Plane Dataref Bridge - Digital Outputs Controller with OUTPUT_IDs (Beginner Version)
===============================================================================

PURPOSE:
This sketch creates a digital outputs controller that responds to X-Plane dataref
changes received through bridge application. It demonstrates how to control
LEDs, indicators, or other digital outputs based on different types of data.

REQUIRED HARDWARE:
- Arduino UNO (or compatible board)
- 4x LEDs (any color) or digital output devices
- 4x 220Ω resistors (for LEDs)
- Breadboard and jumper wires
- USB cable for programming and communication

WIRING INSTRUCTIONS (for LEDs with resistors):
- LED 1: Arduino Pin 8 → 220Ω resistor → LED anode (+) → LED cathode (-) → GND
- LED 2: Arduino Pin 9 → 220Ω resistor → LED anode (+) → LED cathode (-) → GND
- LED 3: Arduino Pin 10 → 220Ω resistor → LED anode (+) → LED cathode (-) → GND
- LED 4: Arduino Pin 11 → 220Ω resistor → LED anode (+) → LED cathode (-) → GND
- Arduino GND to common ground rail

OUTPUT FUNCTIONALITY:
Output 1 (Pin 8): Responds to GEAR_STATUS - lights when landing gear is down
Output 2 (Pin 9): Pulses when COMMAND_EXECUTED - brief flash for commands
Output 3 (Pin 10): Responds to LED_STATE_ELEM - lights when array element > 0.5
Output 4 (Pin 11): Responds to LED_STATE_ARRAY - lights when array average > 0.5

OUTPUT_ID SYSTEM:
OUTPUT_IDs are friendly names you configure in bridge application to map
to actual X-Plane datarefs. The bridge sends "SET OUTPUT_ID value" messages
to your Arduino when associated X-Plane dataref changes.

BRIDGE CONFIGURATION:
In your X-Plane Dataref Bridge application, map these OUTPUT_IDs:
GEAR_STATUS → sim/cockpit2/switches/gear_handle_status
BEACON_STATUS → sim/cockpit2/switches/beacon_on
LED_STATE_ELEM → LED_STATE[n] (individual elements)
LED_STATE_ARRAY → LED_STATE (full array)
COMMAND_EXECUTED → Command execution notifications

DIGITAL OUTPUT BASICS:
- digitalWrite(pin, HIGH) turns output ON (LED lights up)
- digitalWrite(pin, LOW) turns output OFF (LED turns off)
- Arduino outputs can directly drive LEDs with current-limiting resistors
- Values > 0.5 (50%) typically trigger "ON" state for analog data

TROUBLESHOOTING:
- LEDs not working? Check polarity (long leg = anode/positive)
- Dim LEDs? Verify resistor values (220Ω standard for 5V Arduino)
- No data received? Check serial connection and bridge configuration
- Incorrect behavior? Verify OUTPUT_ID mappings in bridge application
===============================================================================
*/
```

## Protocol Documentation

### Handshake Protocol
```
Bridge: HELLO
Arduino: XPDR;fw=<version>;board=<type>;name=<device_name>
```

### Dataref Operations
```
Read: READ <dataref_name> <type>
Resp: VALUE <dataref_name> <value>

Write: WRITE <dataref_name> <type> <value>
Resp: OK

Set (compat): SETDREF <dataref_name> <value>
Resp: ACK <key> <value>

Read Array: READARRAY <array_name> <type>
Resp: ARRAYVALUE <array_name> <type> <csv_values>

Write Array: WRITEARRAY <array_name> <type> <csv_values>
Resp: OK

Read Elem: READELEM <array_name[index]> <type>
Resp: ELEMVALUE <array_name[index]> <type> <value>

Write Elem: WRITEELEM <array_name[index]> <type> <value>
Resp: OK

Multi-Read: MULTIREAD <array_name[start,end]> <type>
Resp: MULTIVALUE <array_name[start,end]> <type> <csv_values>

Command: CMD <command_name>
Resp: CMD_EXECUTED <command_name>
```

## Examples

### Basic LED Control
```cpp
// Arduino code to control an LED based on X-Plane dataref
const int LED_PIN = 8;

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.startsWith("SET GEAR_LED ")) {
      int value = line.substring(11).toInt();
      digitalWrite(LED_PIN, value > 0 ? HIGH : LOW);
      Serial.print("ACK GEAR_LED "); Serial.println(value);
    }
  }
}
```

### Reading Airspeed
```cpp
// Arduino code to read airspeed from X-Plane
float airspeed = 0.0;

void loop() {
  // Request airspeed every second
  static unsigned long lastRequest = 0;
  if (millis() - lastRequest > 1000) {
    Serial.println("READ sim/cockpit2/gauges/indicators/airspeed_kts_pilot float");
    lastRequest = millis();
  }

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.startsWith("VALUE sim/cockpit2/gauges/indicators/airspeed_kts_pilot ")) {
      airspeed = line.substring(57).toFloat();
      // Use airspeed value for display or other purposes
    }
  }
}
```

## Troubleshooting

### Common Issues

#### Device not recognized
- Verify handshake response format: `XPDR;fw=1.0;board=UNO;name=MyDevice`
- Check serial monitor for HELLO command from bridge
- Ensure baud rate is 115200

#### No communication
- Confirm baud rate 115200 on both ends
- Check COM port selection in bridge application
- Verify USB cable is properly connected

#### Wrong data
- Double-check data types (int/float/bool/byte)
- Verify dataref names match exactly
- Check for typos in commands

#### Connection drops
- Implement heartbeat (STATUS HB) or increase timeout
- Check for serial buffer overflow
- Reduce frequency of data requests if needed

### Debugging Tips
- Use Arduino Serial Monitor to view raw communication
- Enable debug logging in the bridge application
- Test with simple handshake sketch first
- Verify X-Plane is running and accessible

## Development

### Project Structure
```
X-Plane Dataref Bridge/
├── core/                 # Core application logic
│   ├── arduino/          # Arduino communication
│   ├── hid/              # HID device management
│   └── xplane/           # X-Plane communication
├── gui/                  # PyQt6 GUI components
├── docs/                 # Documentation
├── examples/             # Example configurations
├── resources/            # Icons and assets
└── main.py               # Application entry point
```

### Building Executables
For building standalone executables, see How_to_Package_XPDRB_as_an_EXE.md.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write unit tests for new features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

**Happy Flight Simulation!** 🛩️
