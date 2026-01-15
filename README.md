# X-Plane Dataref Bridge

**A comprehensive bridge connecting X-Plane flight simulator to Arduino and other microcontrollers**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![X-Plane](https://img.shields.io/badge/X--Plane-11%2F12-brightgreen.svg)](https://www.x-plane.com/)

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

**How it works:**
- X-Plane sends datarefs via UDP
- The bridge application receives and processes these datarefs
- Microcontroller (Arduino/ESP32) communicates via USB serial
- Bidirectional communication: read from X-Plane, write to X-Plane

## Features

- ✅ **Real-time Dataref Monitoring**: Monitor any X-Plane dataref in real-time
- ✅ **Bidirectional Communication**: Both read from and write to X-Plane
- ✅ **Multiple Data Types**: Support for int, float, bool, byte, string, and array datarefs
- ✅ **Command Execution**: Execute X-Plane commands from hardware
- ✅ **Hardware Abstraction**: Works with Arduino, ESP32, and other serial devices
- ✅ **GUI Interface**: Intuitive PyQt6-based user interface
- ✅ **Input Mapping**: Map hardware inputs (buttons, encoders, pots) to X-Plane actions
- ✅ **Output Mapping**: Map X-Plane datarefs to hardware outputs (LEDs, servos, displays)
- ✅ **Auto-Discovery**: Automatic detection of X-Plane and connected devices
- ✅ **Cross-Platform**: Runs on Windows, macOS, and Linux

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

**Note for Linux users**: You may need to install additional system packages:
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

1. **Start X-Plane** with your aircraft loaded
2. **Upload Arduino sketch** (see Arduino Sketches section below)
3. **Connect Arduino** via USB to your computer
4. **Run the Bridge application**
5. **Connect to X-Plane** using the Connect button
6. **Configure datarefs** in the Output Config tab
7. **Map hardware** in the Input Config tab

## Arduino Sketches

Comprehensive Arduino sketches demonstrating communication with the X-Plane Dataref Bridge. Each sketch focuses on a specific capability of the protocol.

### 1. Handshake Protocol

#### handshake.ino
Establishes the initial two-way handshake so the bridge recognizes your device and maintains a heartbeat.

- Features: Two-way Serial handshake, heartbeat, device identification
- Output ID: `HANDSHAKE_DEMO`

```cpp
/*
 * X-Plane Dataref Bridge - Handshake Protocol
 *
 * This sketch demonstrates the basic handshake protocol required for the bridge to recognize
 * your Arduino device. The handshake is the first communication step that establishes
 * the connection between your Arduino and the bridge app.
 */

// Device identification constants - these help the bridge recognize your device
const char* DEVICE_NAME = "HandshakeDemo";     // Human-readable name for your device
const char* FIRMWARE_VERSION = "1.0";         // Version of your Arduino firmware
const char* BOARD_TYPE = "UNO";               // Board type identifier

// Heartbeat timing - keeps the connection alive
unsigned long lastHeartbeat = 0;              // Timestamp of last heartbeat sent
const unsigned long HEARTBEAT_INTERVAL = 5000; // Send heartbeat every 5 seconds

void setup() {
  // Initialize serial communication at 115200 baud rate (standard for the bridge)
  Serial.begin(115200);

  // Wait for serial connection to be established (important for some boards)
  while (!Serial && millis() < 5000) {
    delay(10);
  }

  // Print startup message to serial monitor for debugging
  Serial.println("// Handshake Demo Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.print("// Waiting for HELLO command...");
}

void loop() {
  // Check for incoming serial commands
  checkSerial();

  // Send periodic heartbeat to maintain connection
  sendHeartbeat();

  // Small delay to prevent overwhelming the serial buffer
  delay(1);
}

void checkSerial() {
  // Process all available serial data
  while (Serial.available()) {
    // Read a complete line from serial input (terminated by newline)
    String line = Serial.readStringUntil('\n');
    // Remove leading/trailing whitespace
    line.trim();

    // Handle the handshake request from the bridge
    if (line == "HELLO") {
      // Send proper handshake response in the format expected by the bridge
      // Format: XPDR;fw=version;board=type;name=device_name
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);

      // Log the handshake for debugging
      Serial.println("// Handshake completed successfully");
    }
    // Handle LIST command to show available features
    else if (line == "LIST") {
      Serial.println("STATUS Available Commands:");
      Serial.println("STATUS - HELLO (establish connection)");
      Serial.println("STATUS - LIST (show available commands)");
      Serial.println("STATUS - STATUS (show device status)");
    }
    // Handle STATUS command to show current device status
    else if (line == "STATUS") {
      Serial.println("STATUS Device Status:");
      Serial.print("STATUS - Uptime: "); Serial.print(millis() / 1000); Serial.println(" seconds");
      Serial.print("STATUS - Device: "); Serial.println(DEVICE_NAME);
      Serial.print("STATUS - Next heartbeat in: ");
      Serial.print((HEARTBEAT_INTERVAL - (millis() - lastHeartbeat)) / 1000);
      Serial.println(" seconds");
    }
  }
}

void sendHeartbeat() {
  // Send periodic heartbeat every HEARTBEAT_INTERVAL milliseconds
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    // Send heartbeat message to indicate device is still alive
    Serial.print("HEARTBEAT;device="); Serial.println(DEVICE_NAME);
    lastHeartbeat = millis();
  }
}
```

### 2. Reading Datarefs

#### read_dataref.ino
Requests values for specific datarefs and parses VALUE responses.

- Features: Request values, store locally, periodic polling
- Output ID: `DATA_READER`

```cpp
/*
 * X-Plane Dataref Bridge - Read Dataref
 *
 * This sketch demonstrates how to read dataref values from the bridge app.
 * The Arduino sends a request to read a specific dataref, and the bridge
 * responds with the current value of that dataref.
 */

// Device identification constants
const char* DEVICE_NAME = "DataReader";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// Variables to store received dataref values
float receivedFloatValue = 0.0;      // Stores received float values
int receivedIntValue = 0;            // Stores received integer values
bool receivedBoolValue = false;      // Stores received boolean values

// Timing for periodic dataref requests
unsigned long lastReadRequest = 0;   // Time of last read request
const unsigned long READ_INTERVAL = 1000; // Request data every 1000ms

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 5000) {
    delay(10);
  }

  Serial.println("// Data Reader Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Will request dataref values periodically");
}

void loop() {
  checkSerial();
  requestReadDataref();
  delay(1);
}

void checkSerial() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    // Handle handshake request
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
    }
    // Handle incoming dataref values from the bridge
    // Format: VALUE dataref_name value
    else if (line.startsWith("VALUE ")) {
      // Parse the VALUE message: VALUE dataref_name value
      int firstSpace = line.indexOf(' ');
      int secondSpace = line.indexOf(' ', firstSpace + 1);

      if (firstSpace > 0 && secondSpace > firstSpace) {
        String datarefName = line.substring(firstSpace + 1, secondSpace);
        String valueStr = line.substring(secondSpace + 1);
        float value = valueStr.toFloat();

        // Store the received value based on dataref name
        if (datarefName == "sim/cockpit2/gauges/indicators/airspeed_kts_pilot") {
          receivedFloatValue = value;
          Serial.print("// Received airspeed: "); Serial.println(receivedFloatValue);
        }
        else if (datarefName == "sim/cockpit2/switches/gear_handle_status") {
          receivedIntValue = (int)value;
          Serial.print("// Received gear status: "); Serial.println(receivedIntValue);
        }
        else if (datarefName == "sim/cockpit/warnings/master_warning") {
          receivedBoolValue = (value != 0);
          Serial.print("// Received warning: "); Serial.println(receivedBoolValue ? "ON" : "OFF");
        }
      }
    }
  }
}

void requestReadDataref() {
  // Request dataref values periodically
  if (millis() - lastReadRequest > READ_INTERVAL) {
    // Request specific datarefs from the bridge
    // Format: READ dataref_name type
    Serial.println("READ sim/cockpit2/gauges/indicators/airspeed_kts_pilot float");
    Serial.println("READ sim/cockpit2/switches/gear_handle_status int");
    Serial.println("READ sim/cockpit/warnings/master_warning bool");

    lastReadRequest = millis();
  }
}
```

### 3. Writing Datarefs

#### write_dataref.ino
Sends SETDREF commands and handles acknowledgments.

- Features: Write values, acknowledgments, periodic updates
- Output ID: `DATA_WRITER`

```cpp
/*
 * X-Plane Dataref Bridge - Write Dataref
 *
 * This sketch demonstrates how to write dataref values to the bridge app.
 * The Arduino sends SETDREF commands to update specific dataref values in X-Plane.
 */

// Device identification constants
const char* DEVICE_NAME = "DataWriter";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// Variables for dataref values
float throttleValue = 0.0;           // Throttle position (0.0 to 1.0)
int gearPosition = 0;                // Gear position (0=up, 1=down)
bool beaconOn = false;               // Beacon light status

// Timing for periodic writes
unsigned long lastWrite = 0;         // Time of last write
const unsigned long WRITE_INTERVAL = 2000; // Write every 2000ms

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 5000) {
    delay(10);
  }

  Serial.println("// Data Writer Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Will write dataref values periodically");
}

void loop() {
  checkSerial();
  writeDatarefValues();
  delay(1);
}

void checkSerial() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    // Handle handshake request
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
    }
    // Handle SET commands from bridge (acknowledgment or direct values)
    else if (line.startsWith("SET ")) {
      // Parse SET command: SET key value
      int firstSpace = line.indexOf(' ');
      int secondSpace = line.indexOf(' ', firstSpace + 1);

      if (firstSpace > 0 && secondSpace > firstSpace) {
        String key = line.substring(firstSpace + 1, secondSpace);
        String valueStr = line.substring(secondSpace + 1);
        float value = valueStr.toFloat();

        // Acknowledge receipt of SET command
        Serial.print("ACK "); Serial.print(key); Serial.print(" "); Serial.println(value, 6);
      }
    }
  }
}

void writeDatarefValues() {
  // Write dataref values periodically
  if (millis() - lastWrite > WRITE_INTERVAL) {
    // Simulate changing values for demonstration
    throttleValue = (throttleValue + 0.1) > 1.0 ? 0.0 : throttleValue + 0.1;
    gearPosition = (gearPosition + 1) % 2;
    beaconOn = !beaconOn;

    // Write values to X-Plane datarefs using SETDREF command
    // Format: SETDREF dataref_name value
    Serial.print("SETDREF sim/cockpit2/engine/actuators/throttle_ratio_all ");
    Serial.println(throttleValue, 6);

    Serial.print("SETDREF sim/cockpit2/switches/gear_handle_status ");
    Serial.println(gearPosition);

    Serial.print("SETDREF sim/cockpit2/switches/beacon_on ");
    Serial.println(beaconOn ? 1 : 0);

    Serial.println("// Dataref values written to X-Plane");

    lastWrite = millis();
  }
}
```

### 4. Basic Types Read/Write

#### read_write_basic_types.ino
Bi-directional example for int, float, bool, and byte.

- Features: Bi-directional, dynamic updates
- Output ID: `BASIC_TYPES_RW`

```cpp
/*
 * X-Plane Dataref Bridge - Read/Write Basic Types
 *
 * This sketch demonstrates bidirectional communication for basic data types:
 * int, float, bool, and byte. It can both read values from the bridge and
 * write values back to X-Plane datarefs.
 */

// Device identification constants
const char* DEVICE_NAME = "BasicTypesRW";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// Storage for different data types
int counterValue = 0;                // Integer value storage
float rateValue = 0.0;               // Float value storage
bool armedValue = false;             // Boolean value storage
byte modeValue = 0;                  // Byte value storage

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 5000) {
    delay(10);
  }

  Serial.println("// Basic Types Read/Write Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Supports int, float, bool, and byte data types");
}

void loop() {
  checkSerial();
  delay(1);
}

void checkSerial() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    // Handle handshake request
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
    }
    // Handle READ requests from bridge
    // Format: READ dataref_name type
    else if (line.startsWith("READ ")) {
      String rest = line.substring(5);  // Remove "READ " prefix
      rest.trim();
      int spaceIndex = rest.indexOf(' ');

      if (spaceIndex > 0) {
        String name = rest.substring(0, spaceIndex);
        String type = rest.substring(spaceIndex + 1);
        type.trim();

        // Respond with current value based on dataref name and type
        if (name == "counter" && type == "int") {
          Serial.print("VALUE counter ");
          Serial.println(counterValue);
        }
        else if (name == "rate" && type == "float") {
          Serial.print("VALUE rate ");
          Serial.println(rateValue, 6);
        }
        else if (name == "armed" && type == "bool") {
          Serial.print("VALUE armed ");
          Serial.println(armedValue ? 1 : 0);
        }
        else if (name == "mode" && type == "byte") {
          Serial.print("VALUE mode ");
          Serial.println(modeValue);
        }
        else {
          Serial.println("UNKNOWN");
        }
      }
    }
    // Handle WRITE requests from bridge
    // Format: WRITE dataref_name type value
    else if (line.startsWith("WRITE ")) {
      String rest = line.substring(6);  // Remove "WRITE " prefix
      rest.trim();
      int firstSpace = rest.indexOf(' ');

      if (firstSpace > 0) {
        String name = rest.substring(0, firstSpace);
        String rest2 = rest.substring(firstSpace + 1);
        rest2.trim();
        int secondSpace = rest2.indexOf(' ');

        if (secondSpace > 0) {
          String type = rest2.substring(0, secondSpace);
          String valueStr = rest2.substring(secondSpace + 1);
          valueStr.trim();

          // Update internal storage based on dataref name and type
          if (name == "counter" && type == "int") {
            counterValue = valueStr.toInt();
            Serial.println("OK");
          }
          else if (name == "rate" && type == "float") {
            rateValue = valueStr.toFloat();
            Serial.println("OK");
          }
          else if (name == "armed" && type == "bool") {
            armedValue = (valueStr == "1" || valueStr.equalsIgnoreCase("true"));
            Serial.println("OK");
          }
          else if (name == "mode" && type == "byte") {
            modeValue = (byte)valueStr.toInt();
            Serial.println("OK");
          }
          else {
            Serial.println("ERR");
          }
        }
      }
    }
  }
}
```

### 5. Array Datarefs

#### array_dataref.ino
Reads and writes entire arrays using comma-separated values.

- Features: Array read/write across types
- Output ID: `ARRAY_DATA_REF`

```cpp
/*
 * X-Plane Dataref Bridge - Array Dataref
 *
 * This sketch demonstrates reading and writing array datarefs for different types:
 * int, float, bool, and byte arrays. It handles comma-separated values for arrays.
 */

// Device identification constants
const char* DEVICE_NAME = "ArrayDataRef";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// Array storage for different types
float floatArray[10] = {0};           // Float array with 10 elements
int intArray[10] = {0};              // Integer array with 10 elements
bool boolArray[10] = {false};        // Boolean array with 10 elements
byte byteArray[10] = {0};            // Byte array with 10 elements

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 5000) {
    delay(10);
  }

  Serial.println("// Array Dataref Handler Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Supports array datarefs for int, float, bool, byte");

  // Initialize arrays with sample values
  for (int i = 0; i < 10; i++) {
    floatArray[i] = i * 0.1;
    intArray[i] = i;
    boolArray[i] = (i % 2 == 0);
    byteArray[i] = i;
  }
}

void loop() {
  checkSerial();
  delay(1);
}

void checkSerial() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    // Handle handshake request
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
    }
    // Handle READ requests for array datarefs
    // Format: READARRAY array_name type
    else if (line.startsWith("READARRAY ")) {
      String rest = line.substring(10);  // Remove "READARRAY " prefix
      rest.trim();
      int spaceIndex = rest.indexOf(' ');

      if (spaceIndex > 0) {
        String name = rest.substring(0, spaceIndex);
        String type = rest.substring(spaceIndex + 1);
        type.trim();

        // Send array values as comma-separated string
        if (name == "float_array" && type == "float") {
          Serial.print("ARRAYVALUE float_array float ");
          sendFloatArray(floatArray, 10);
        }
        else if (name == "int_array" && type == "int") {
          Serial.print("ARRAYVALUE int_array int ");
          sendIntArray(intArray, 10);
        }
        else if (name == "bool_array" && type == "bool") {
          Serial.print("ARRAYVALUE bool_array bool ");
          sendBoolArray(boolArray, 10);
        }
        else if (name == "byte_array" && type == "byte") {
          Serial.print("ARRAYVALUE byte_array byte ");
          sendByteArray(byteArray, 10);
        }
        else {
          Serial.println("UNKNOWN");
        }
      }
    }
    // Handle WRITE requests for array datarefs
    // Format: WRITEARRAY array_name type value1,value2,value3,...
    else if (line.startsWith("WRITEARRAY ")) {
      String rest = line.substring(11);  // Remove "WRITEARRAY " prefix
      rest.trim();
      int firstSpace = rest.indexOf(' ');

      if (firstSpace > 0) {
        String name = rest.substring(0, firstSpace);
        String rest2 = rest.substring(firstSpace + 1);
        rest2.trim();
        int secondSpace = rest2.indexOf(' ');

        if (secondSpace > 0) {
          String type = rest2.substring(0, secondSpace);
          String valuesStr = rest2.substring(secondSpace + 1);

          // Parse and store array values
          if (name == "float_array" && type == "float") {
            parseFloatArray(valuesStr, floatArray, 10);
            Serial.println("OK");
          }
          else if (name == "int_array" && type == "int") {
            parseIntArray(valuesStr, intArray, 10);
            Serial.println("OK");
          }
          else if (name == "bool_array" && type == "bool") {
            parseBoolArray(valuesStr, boolArray, 10);
            Serial.println("OK");
          }
          else if (name == "byte_array" && type == "byte") {
            parseByteArray(valuesStr, byteArray, 10);
            Serial.println("OK");
          }
          else {
            Serial.println("ERR");
          }
        }
      }
    }
  }
}

// Helper functions to send arrays as comma-separated strings
void sendFloatArray(float arr[], int size) {
  for (int i = 0; i < size; i++) {
    Serial.print(arr[i], 6);
    if (i < size - 1) Serial.print(",");
  }
  Serial.println();
}

void sendIntArray(int arr[], int size) {
  for (int i = 0; i < size; i++) {
    Serial.print(arr[i]);
    if (i < size - 1) Serial.print(",");
  }
  Serial.println();
}

void sendBoolArray(bool arr[], int size) {
  for (int i = 0; i < size; i++) {
    Serial.print(arr[i] ? 1 : 0);
    if (i < size - 1) Serial.print(",");
  }
  Serial.println();
}

void sendByteArray(byte arr[], int size) {
  for (int i = 0; i < size; i++) {
    Serial.print(arr[i]);
    if (i < size - 1) Serial.print(",");
  }
  Serial.println();
}

// Helper functions to parse comma-separated strings into arrays
void parseFloatArray(String str, float arr[], int maxSize) {
  int index = 0;
  int start = 0;
  int commaIndex = 0;

  while (commaIndex >= 0 && index < maxSize) {
    commaIndex = str.indexOf(',', start);
    String valueStr;

    if (commaIndex >= 0) {
      valueStr = str.substring(start, commaIndex);
      start = commaIndex + 1;
    } else {
      valueStr = str.substring(start);
    }

    arr[index] = valueStr.toFloat();
    index++;
  }
}

void parseIntArray(String str, int arr[], int maxSize) {
  int index = 0;
  int start = 0;
  int commaIndex = 0;

  while (commaIndex >= 0 && index < maxSize) {
    commaIndex = str.indexOf(',', start);
    String valueStr;

    if (commaIndex >= 0) {
      valueStr = str.substring(start, commaIndex);
      start = commaIndex + 1;
    } else {
      valueStr = str.substring(start);
    }

    arr[index] = valueStr.toInt();
    index++;
  }
}

void parseBoolArray(String str, bool arr[], int maxSize) {
  int index = 0;
  int start = 0;
  int commaIndex = 0;

  while (commaIndex >= 0 && index < maxSize) {
    commaIndex = str.indexOf(',', start);
    String valueStr;

    if (commaIndex >= 0) {
      valueStr = str.substring(start, commaIndex);
      start = commaIndex + 1;
    } else {
      valueStr = str.substring(start);
    }

    arr[index] = (valueStr == "1" || valueStr.equalsIgnoreCase("true"));
    index++;
  }
}

void parseByteArray(String str, byte arr[], int maxSize) {
  int index = 0;
  int start = 0;
  int commaIndex = 0;

  while (commaIndex >= 0 && index < maxSize) {
    commaIndex = str.indexOf(',', start);
    String valueStr;

    if (commaIndex >= 0) {
      valueStr = str.substring(start, commaIndex);
      start = commaIndex + 1;
    } else {
      valueStr = str.substring(start);
    }

    arr[index] = (byte)valueStr.toInt();
    index++;
  }
}
```

### 6. Command Datarefs

#### command_dataref.ino
Executes command-type datarefs and provides simple LED feedback.

- Features: Command execution, LED feedback
- Output ID: `CMD_DEVICE`

```cpp
/*
 * X-Plane Dataref Bridge - Command Dataref
 *
 * This sketch demonstrates executing command-type datarefs. It listens for
 * CMD messages and executes specific actions based on the command received.
 */

// Device identification constants
const char* DEVICE_NAME = "CommandDevice";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// LED pin for visual feedback
const int LED_PIN = LED_BUILTIN;
bool ledState = false;               // Current LED state
unsigned long lastBlink = 0;         // Time of last blink

void setup() {
  // Initialize LED pin as output
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(115200);
  while (!Serial && millis() < 5000) {
    delay(10);
  }

  Serial.println("// Command Device Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Ready to execute commands");
}

void loop() {
  checkSerial();

  // Handle LED blinking for visual feedback
  handleLedBlinking();

  delay(1);
}

void checkSerial() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    // Handle handshake request
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
    }
    // Handle command execution
    // Format: CMD command_name
    else if (line.startsWith("CMD ")) {
      String command = line.substring(4);  // Remove "CMD " prefix
      command.trim();

      // Execute the command and send acknowledgment
      executeCommand(command);
      Serial.print("CMD_EXECUTED ");
      Serial.println(command);
    }
    // Handle LIST command to show available commands
    else if (line == "LIST") {
      Serial.println("STATUS Available Commands:");
      Serial.println("STATUS - toggleLED (toggle built-in LED)");
      Serial.println("STATUS - pulseLED (blink LED 3 times)");
      Serial.println("STATUS - reset (send reset signal)");
      Serial.println("STATUS - flash (quick LED flash)");
    }
  }
}

void executeCommand(const String &cmd) {
  if (cmd == "toggleLED") {
    // Toggle the built-in LED on/off
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
    Serial.println("STATUS LED toggled");
  }
  else if (cmd == "pulseLED") {
    // Make the LED blink rapidly 3 times
    Serial.println("STATUS LED pulsing...");
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
    // Return to current state
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
  }
  else if (cmd == "reset") {
    // Send reset acknowledgment
    Serial.println("RESET_CMD_RECEIVED");
    // Reset internal state if needed
    ledState = false;
    digitalWrite(LED_PIN, LOW);
  }
  else if (cmd == "flash") {
    // Quick flash the LED
    Serial.println("STATUS LED flashed");
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(50);
    // Return to current state
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
  }
  else {
    // Unknown command
    Serial.print("UNKNOWN_CMD: ");
    Serial.println(cmd);
  }
}

void handleLedBlinking() {
  // Optional: keep LED in a visible state for ongoing activity
  if (ledState && (millis() - lastBlink) > 500) {
    lastBlink = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
}
```

### 7. Array Elements Read/Write

#### array_elements_read_write.ino
Reads/writes individual array elements or ranges.

- Features: Element access, ranges, multi-element ops
- Output ID: `ARRAY_ELEMENTS_RW`

```cpp
/*
 * X-Plane Dataref Bridge - Array Elements Read/Write
 *
 * This sketch demonstrates reading and writing individual elements of array datarefs
 * as well as multiple elements at once. It supports element-specific operations.
 */

// Device identification constants
const char* DEVICE_NAME = "ArrayElementsRW";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// Array storage for different types
float floatArray[20] = {0};           // Float array with 20 elements
int intArray[20] = {0};              // Integer array with 20 elements
bool boolArray[20] = {false};        // Boolean array with 20 elements
byte byteArray[20] = {0};            // Byte array with 20 elements

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 5000) {
    delay(10);
  }

  Serial.println("// Array Elements Read/Write Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Supports individual and multiple array element operations");

  // Initialize arrays with sample values
  for (int i = 0; i < 20; i++) {
    floatArray[i] = i * 0.5;
    intArray[i] = i * 10;
    boolArray[i] = (i % 3 == 0);
    byteArray[i] = i + 100;
  }
}

void loop() {
  checkSerial();
  delay(1);
}

void checkSerial() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    // Handle handshake request
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
    }
    // Handle READ for single array element
    // Format: READELEM array_name[index] type
    else if (line.startsWith("READELEM ")) {
      String rest = line.substring(9);  // Remove "READELEM " prefix
      rest.trim();
      int spaceIndex = rest.indexOf(' ');

      if (spaceIndex > 0) {
        String nameWithIndex = rest.substring(0, spaceIndex);
        String type = rest.substring(spaceIndex + 1);
        type.trim();

        // Parse array name and index
        int bracketStart = nameWithIndex.indexOf('[');
        int bracketEnd = nameWithIndex.indexOf(']');

        if (bracketStart > 0 && bracketEnd > bracketStart) {
          String arrayName = nameWithIndex.substring(0, bracketStart);
          String indexStr = nameWithIndex.substring(bracketStart + 1, bracketEnd);
          int index = indexStr.toInt();

          // Send single element value
          if (arrayName == "float_array" && type == "float" && index >= 0 && index < 20) {
            Serial.print("ELEMVALUE float_array["); Serial.print(index); Serial.print("] float ");
            Serial.println(floatArray[index], 6);
          }
          else if (arrayName == "int_array" && type == "int" && index >= 0 && index < 20) {
            Serial.print("ELEMVALUE int_array["); Serial.print(index); Serial.print("] int ");
            Serial.println(intArray[index]);
          }
          else if (arrayName == "bool_array" && type == "bool" && index >= 0 && index < 20) {
            Serial.print("ELEMVALUE bool_array["); Serial.print(index); Serial.print("] bool ");
            Serial.println(boolArray[index] ? 1 : 0);
          }
          else if (arrayName == "byte_array" && type == "byte" && index >= 0 && index < 20) {
            Serial.print("ELEMVALUE byte_array["); Serial.print(index); Serial.print("] byte ");
            Serial.println(byteArray[index]);
          }
          else {
            Serial.println("UNKNOWN_ELEM");
          }
        }
      }
    }
    // Handle WRITE for single array element
    // Format: WRITEELEM array_name[index] type value
    else if (line.startsWith("WRITEELEM ")) {
      String rest = line.substring(10);  // Remove "WRITEELEM " prefix
      rest.trim();
      int firstSpace = rest.indexOf(' ');

      if (firstSpace > 0) {
        String nameWithIndex = rest.substring(0, firstSpace);
        String rest2 = rest.substring(firstSpace + 1);
        rest2.trim();
        int secondSpace = rest2.indexOf(' ');

        if (secondSpace > 0) {
          String type = rest2.substring(0, secondSpace);
          String valueStr = rest2.substring(secondSpace + 1);
          float value = valueStr.toFloat();

          // Parse array name and index
          int bracketStart = nameWithIndex.indexOf('[');
          int bracketEnd = nameWithIndex.indexOf(']');

          if (bracketStart > 0 && bracketEnd > bracketStart) {
            String arrayName = nameWithIndex.substring(0, bracketStart);
            String indexStr = nameWithIndex.substring(bracketStart + 1, bracketEnd);
            int index = indexStr.toInt();

            // Update single element
            if (arrayName == "float_array" && type == "float" && index >= 0 && index < 20) {
              floatArray[index] = value;
              Serial.println("OK");
            }
            else if (arrayName == "int_array" && type == "int" && index >= 0 && index < 20) {
              intArray[index] = (int)value;
              Serial.println("OK");
            }
            else if (arrayName == "bool_array" && type == "bool" && index >= 0 && index < 20) {
              boolArray[index] = (value != 0);
              Serial.println("OK");
            }
            else if (arrayName == "byte_array" && type == "byte" && index >= 0 && index < 20) {
              byteArray[index] = (byte)value;
              Serial.println("OK");
            }
            else {
              Serial.println("ERR");
            }
          }
        }
      }
    }
    // Handle MULTIREAD for multiple array elements
    // Format: MULTIREAD array_name[start_index,end_index] type
    else if (line.startsWith("MULTIREAD ")) {
      String rest = line.substring(10);  // Remove "MULTIREAD " prefix
      rest.trim();
      int spaceIndex = rest.indexOf(' ');

      if (spaceIndex > 0) {
        String nameWithRange = rest.substring(0, spaceIndex);
        String type = rest.substring(spaceIndex + 1);
        type.trim();

        // Parse array name and range
        int bracketStart = nameWithRange.indexOf('[');
        int bracketEnd = nameWithRange.indexOf(']');

        if (bracketStart > 0 && bracketEnd > bracketStart) {
          String arrayName = nameWithRange.substring(0, bracketStart);
          String rangeStr = nameWithRange.substring(bracketStart + 1, bracketEnd);

          int commaIndex = rangeStr.indexOf(',');
          if (commaIndex > 0) {
            int startIndex = rangeStr.substring(0, commaIndex).toInt();
            int endIndex = rangeStr.substring(commaIndex + 1).toInt();

            // Send multiple elements as comma-separated values
            if (arrayName == "float_array" && type == "float" &&
                startIndex >= 0 && endIndex < 20 && startIndex <= endIndex) {
              Serial.print("MULTIVALUE float_array["); Serial.print(startIndex);
              Serial.print(","); Serial.print(endIndex); Serial.print("] float ");

              for (int i = startIndex; i <= endIndex; i++) {
                Serial.print(floatArray[i], 6);
                if (i < endIndex) Serial.print(",");
              }
              Serial.println();
            }
            // Similar handling for other types...
          }
        }
      }
    }
  }
}
```

### 8. 4-Button Controller

#### 4_button_controller.ino
A 4-button controller that performs different operations.

- Features: Button debouncing, multiple operations
- Output ID: `FOUR_BUTTON_CONTROLLER`

```cpp
/*
 * X-Plane Dataref Bridge - 4 Button Controller
 * 
 * This sketch demonstrates a 4-button controller that performs different operations:
 * - Button 1: Writes to a dataref
 * - Button 2: Executes a command type dataref
 * - Button 3: Writes to a specific array element
 * - Button 4: Writes to multiple array elements
 */

// Device identification constants
const char* DEVICE_NAME = "FourButtonController";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// Button pin definitions
const int BUTTON1_PIN = 2;  // Write to dataref
const int BUTTON2_PIN = 3;  // Execute command
const int BUTTON3_PIN = 4;  // Write to array element
const int BUTTON4_PIN = 5;  // Write to multiple array elements

// Button state tracking
bool lastButton1State = false;
bool lastButton2State = false;
bool lastButton3State = false;
bool lastButton4State = false;

unsigned long lastDebounceTime1 = 0;
unsigned long lastDebounceTime2 = 0;
unsigned long lastDebounceTime3 = 0;
unsigned long lastDebounceTime4 = 0;

const unsigned long DEBOUNCE_DELAY = 50;  // Debounce delay in milliseconds

// Array for testing array operations
float testArray[10] = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0};

void setup() {
  // Initialize button pins as inputs with pull-up resistors
  pinMode(BUTTON1_PIN, INPUT_PULLUP);
  pinMode(BUTTON2_PIN, INPUT_PULLUP);
  pinMode(BUTTON3_PIN, INPUT_PULLUP);
  pinMode(BUTTON4_PIN, INPUT_PULLUP);
  
  // Initialize serial communication
  Serial.begin(115200);
  
  // Wait for serial connection to establish
  while (!Serial && millis() < 5000) {
    delay(10);
  }
  
  Serial.println("// Four Button Controller Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Button 1: Write dataref | Button 2: Execute command | Button 3: Array element | Button 4: Multiple elements");
}

void loop() {
  checkSerial();
  checkButtons();
  delay(10);  // Small delay to prevent overwhelming the processor
}

void checkSerial() {
  // Handle incoming serial commands from the bridge
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    
    // Handle handshake request from the bridge
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
    }
    // Handle LIST command to show available features
    else if (line == "LIST") {
      Serial.println("STATUS Available Functions:");
      Serial.println("STATUS - Button 1: Write to dataref (gear handle)");
      Serial.println("STATUS - Button 2: Execute command (heading sync)");
      Serial.println("STATUS - Button 3: Write to array element (LED_STATE[0])");
      Serial.println("STATUS - Button 4: Write to multiple array elements (LED_STATE[0-2])");
    }
    // Handle STATUS command
    else if (line == "STATUS") {
      Serial.println("STATUS Controller Status:");
      Serial.print("STATUS - Buttons: 4 configured");
      Serial.print("STATUS - Array size: 10 elements");
      Serial.println("STATUS - Ready for button presses");
    }
  }
}

void checkButtons() {
  // Read current button states (inverted because of pull-up resistors)
  bool currentButton1State = !digitalRead(BUTTON1_PIN);
  bool currentButton2State = !digitalRead(BUTTON2_PIN);
  bool currentButton3State = !digitalRead(BUTTON3_PIN);
  bool currentButton4State = !digitalRead(BUTTON4_PIN);
  
  // Check Button 1: Write to a dataref
  if (currentButton1State != lastButton1State) {
    if ((millis() - lastDebounceTime1) > DEBOUNCE_DELAY) {
      if (currentButton1State) {
        // Button 1 pressed - write to a dataref
        writeDataref();
        lastDebounceTime1 = millis();
      }
    }
    lastButton1State = currentButton1State;
  }
  
  // Check Button 2: Execute a command type dataref
  if (currentButton2State != lastButton2State) {
    if ((millis() - lastDebounceTime2) > DEBOUNCE_DELAY) {
      if (currentButton2State) {
        // Button 2 pressed - execute a command
        executeCommand();
        lastDebounceTime2 = millis();
      }
    }
    lastButton2State = currentButton2State;
  }
  
  // Check Button 3: Write to a specific array element
  if (currentButton3State != lastButton3State) {
    if ((millis() - lastDebounceTime3) > DEBOUNCE_DELAY) {
      if (currentButton3State) {
        // Button 3 pressed - write to a specific array element
        writeArrayElement();
        lastDebounceTime3 = millis();
      }
    }
    lastButton3State = currentButton3State;
  }
  
  // Check Button 4: Write to multiple array elements
  if (currentButton4State != lastButton4State) {
    if ((millis() - lastDebounceTime4) > DEBOUNCE_DELAY) {
      if (currentButton4State) {
        // Button 4 pressed - write to multiple array elements
        writeMultipleArrayElements();
        lastDebounceTime4 = millis();
      }
    }
    lastButton4State = currentButton4State;
  }
}

void writeDataref() {
  // Send a SETDREF command to write to a specific dataref
  // Example: Write to gear handle status
  Serial.println("SETDREF sim/cockpit2/switches/gear_handle_status 1");
  Serial.println("// Button 1: Wrote to gear handle dataref");
}

void executeCommand() {
  // Send a CMD command to execute a command-type dataref
  // Example: Execute heading sync command
  Serial.println("CMD sim/autopilot/heading_sync");
  Serial.println("// Button 2: Executed heading sync command");
}

void writeArrayElement() {
  // Send a WRITEELEM command to write to a specific array element
  // Example: Write to LED_STATE[0] element
  Serial.println("WRITEELEM LED_STATE[0] float 1.0");
  Serial.println("// Button 3: Wrote to LED_STATE[0]");
}

void writeMultipleArrayElements() {
  // Send a WRITEARRAY command to write to multiple array elements
  // Example: Write to LED_STATE array elements 0-2
  Serial.println("WRITEARRAY LED_STATE float 1.0,0.5,0.0");
  Serial.println("// Button 4: Wrote to LED_STATE[0], LED_STATE[1], LED_STATE[2]");
  
  // Alternative: Update our local test array
  testArray[0] = 1.0;
  testArray[1] = 0.5;
  testArray[2] = 0.0;
  Serial.println("// Local array updated: [0]=1.0, [1]=0.5, [2]=0.0");
}
```

### 9. 4-Axis Input Controller

#### 4_axis_input_controller.ino
A 4-axis input controller with different functionality per axis.

- Features: Analog input handling, threshold detection
- Output ID: `4_AXIS_INPUT_CONTROLLER`

```cpp
/*
 * X-Plane Dataref Bridge - 4 Axis Input Controller
 * 
 * This sketch demonstrates a 4-axis input controller that performs different actions:
 * 1st axis: Writes to a dataref (e.g., throttle, flap, etc.)
 * 2nd axis: Executes command-type datarefs (e.g., toggle switches)
 * 3rd axis: Writes to a specific array element
 * 4th axis: Writes to multiple array elements
 */

// Device identification constants
const char* DEVICE_NAME = "4AxisController";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// Pin assignments for analog axes (potentiometers or joystick)
const int AXIS_1_PIN = A0;  // Throttle or similar
const int AXIS_2_PIN = A1;  // Command trigger
const int AXIS_3_PIN = A2;  // Array element control
const int AXIS_4_PIN = A3;  // Multi-element control

// Threshold for command triggering (prevents accidental triggers)
const int COMMAND_THRESHOLD = 800;  // Out of 1024 (approx 78%)

// Previous values to prevent flooding updates
int prevAxis1Value = -1;
int prevAxis2Trigger = -1;
int prevAxis3Value = -1;
int prevAxis4Value = -1;

// Array for demonstration (we'll use this for array operations)
float demoArray[5] = {0.0, 0.0, 0.0, 0.0, 0.0};

void setup() {
  Serial.begin(115200);
  
  // Wait for serial connection to be established
  while (!Serial && millis() < 5000) {
    delay(10);
  }
  
  Serial.println("// 4-Axis Input Controller Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Axes: 1-Dataref, 2-Command, 3-Array Element, 4-Multi-Array");
  
  // Initialize analog pins (they are inputs by default)
  pinMode(AXIS_1_PIN, INPUT);
  pinMode(AXIS_2_PIN, INPUT);
  pinMode(AXIS_3_PIN, INPUT);
  pinMode(AXIS_4_PIN, INPUT);
}

void loop() {
  // Handle incoming serial commands (handshake, etc.)
  handleSerialCommands();
  
  // Read all axes
  int axis1Value = analogRead(AXIS_1_PIN);      // Raw: 0-1023
  int axis2Value = analogRead(AXIS_2_PIN);      // Raw: 0-1023
  int axis3Value = analogRead(AXIS_3_PIN);      // Raw: 0-1023
  int axis4Value = analogRead(AXIS_4_PIN);      // Raw: 0-1023
  
  // Process Axis 1: Write to dataref
  processAxis1(axis1Value);
  
  // Process Axis 2: Execute command
  processAxis2(axis2Value);
  
  // Process Axis 3: Write to specific array element
  processAxis3(axis3Value);
  
  // Process Axis 4: Write to multiple array elements
  processAxis4(axis4Value);
  
  // Small delay to prevent overwhelming the serial connection
  delay(50);
}

void handleSerialCommands() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    
    // Handle handshake request
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
      Serial.println("// Handshake completed successfully");
    }
    // Handle LIST command
    else if (line == "LIST") {
      Serial.println("STATUS Available Commands:");
      Serial.println("STATUS - HELLO (establish connection)");
      Serial.println("STATUS - LIST (show available commands)");
      Serial.println("STATUS - STATUS (show device status)");
    }
    // Handle STATUS command
    else if (line == "STATUS") {
      Serial.println("STATUS 4-Axis Input Controller Status:");
      Serial.print("STATUS - Device: "); Serial.println(DEVICE_NAME);
      Serial.print("STATUS - Axes readings - 1:"); Serial.print(analogRead(AXIS_1_PIN));
      Serial.print(", 2:"); Serial.print(analogRead(AXIS_2_PIN));
      Serial.print(", 3:"); Serial.print(analogRead(AXIS_3_PIN));
      Serial.print(", 4:"); Serial.println(analogRead(AXIS_4_PIN));
    }
  }
}

void processAxis1(int value) {
  // Normalize value from 0-1023 to 0.0-1.0 for dataref
  float normalizedValue = (float)value / 1023.0;
  
  // Only send update if value changed significantly (prevent flooding)
  if (abs(value - prevAxis1Value) > 10) {
    // Example: Write to throttle ratio
    Serial.print("SETDREF sim/cockpit2/engine/actuators/throttle_ratio_all ");
    Serial.println(normalizedValue, 4);
    
    // Alternative: Send via SET command (more compatible with bridge)
    Serial.print("SET THROTTLE_AXIS ");
    Serial.println(normalizedValue, 4);
    
    prevAxis1Value = value;
  }
}

void processAxis2(int value) {
  // Use axis value to trigger commands when it exceeds threshold
  bool shouldTrigger = (value > COMMAND_THRESHOLD);
  
  if (shouldTrigger && !prevAxis2Trigger) {
    // Execute command when threshold crossed from low to high
    Serial.println("CMD sim/autopilot/autopilot_on");
    Serial.println("// Command: Autopilot ON triggered");
    prevAxis2Trigger = true;
  } 
  else if (!shouldTrigger && prevAxis2Trigger) {
    // Execute command when threshold crossed from high to low
    Serial.println("CMD sim/autopilot/autopilot_off");
    Serial.println("// Command: Autopilot OFF triggered");
    prevAxis2Trigger = false;
  }
}

void processAxis3(int value) {
  // Normalize value from 0-1023 to 0.0-1.0
  float normalizedValue = (float)value / 1023.0;
  
  // Use axis value to determine which array element to update
  // Map 0-1023 to array index 0-4
  int arrayIndex = map(value, 0, 1023, 0, 4);
  
  // Only update if value changed significantly
  if (abs(value - prevAxis3Value) > 10) {
    // Update the specific array element
    demoArray[arrayIndex] = normalizedValue;
    
    // Send command to update specific array element
    Serial.print("WRITEELEM sim/flightmodel2/misc/door_open_ratio[");
    Serial.print(arrayIndex);
    Serial.print("] float ");
    Serial.println(normalizedValue, 4);
    
    Serial.print("// Updated array element ["); Serial.print(arrayIndex); 
    Serial.print("] to value: "); Serial.println(normalizedValue, 4);
    
    prevAxis3Value = value;
  }
}

void processAxis4(int value) {
  // Normalize value from 0-1023 to 0.0-1.0
  float normalizedValue = (float)value / 1023.0;
  
  // Only update if value changed significantly
  if (abs(value - prevAxis4Value) > 20) { // Higher threshold for multi-element to reduce traffic
    // Update multiple array elements based on the axis value
    // Distribute the value across multiple elements
    
    // Example: Update first 3 elements with variations of the value
    for (int i = 0; i < 3; i++) {
      // Create variation based on index
      float variedValue = constrain(normalizedValue + (i * 0.1 - 0.1), 0.0, 1.0);
      demoArray[i] = variedValue;
    }
    
    // Create comma-separated string for multiple values
    String csvValues = "";
    for (int i = 0; i < 3; i++) {
      if (i > 0) csvValues += ",";
      csvValues += String(demoArray[i], 4);
    }
    
    // Send command to update multiple array elements
    Serial.print("WRITEARRAY sim/flightmodel2/misc/door_open_ratio float ");
    Serial.println(csvValues);
    
    Serial.print("// Updated multiple array elements with values: ");
    Serial.println(csvValues);
    
    prevAxis4Value = value;
  }
}

// Helper function to map and constrain values
float mapAndConstrain(int inputValue, int inMin, int inMax, float outMin, float outMax) {
  float mappedValue = ((float)(inputValue - inMin) / (float)(inMax - inMin)) * (outMax - outMin) + outMin;
  return constrain(mappedValue, outMin, outMax);
}
```

### 10. Digital Outputs Controller

#### digital_outputs_controller.ino
4 digital outputs that respond to different dataref types.

- Features: Digital output control, value parsing
- Output ID: `DIGITAL_OUTPUTS_CONTROLLER`

```cpp
/*
 * X-Plane Dataref Bridge - Digital Outputs Controller
 * 
 * This sketch demonstrates 4 digital outputs that respond to different dataref types:
 * - Output 1: Reads from a dataref and controls a digital output
 * - Output 2: Reads command execution status and controls a digital output
 * - Output 3: Reads a specific array element and controls a digital output
 * - Output 4: Reads multiple array elements and controls a digital output
 */

// Device identification constants
const char* DEVICE_NAME = "DigitalOutputsController";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

// Digital output pin definitions
const int OUTPUT1_PIN = 8;   // Controlled by dataref value
const int OUTPUT2_PIN = 9;   // Controlled by command execution
const int OUTPUT3_PIN = 10;  // Controlled by array element
const int OUTPUT4_PIN = 11;  // Controlled by multiple array elements

// Storage for received values
float datarefValue = 0.0;           // Value from dataref
bool commandExecuted = false;       // Command execution status
float arrayElementValue = 0.0;      // Value from specific array element
float combinedArrayValue = 0.0;     // Combined value from multiple array elements

// Timing for periodic updates
unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 100;  // Update outputs every 100ms

void setup() {
  // Initialize digital output pins
  pinMode(OUTPUT1_PIN, OUTPUT);
  pinMode(OUTPUT2_PIN, OUTPUT);
  pinMode(OUTPUT3_PIN, OUTPUT);
  pinMode(OUTPUT4_PIN, OUTPUT);
  
  // Initialize outputs to LOW initially
  digitalWrite(OUTPUT1_PIN, LOW);
  digitalWrite(OUTPUT2_PIN, LOW);
  digitalWrite(OUTPUT3_PIN, LOW);
  digitalWrite(OUTPUT4_PIN, LOW);
  
  // Initialize serial communication
  Serial.begin(115200);
  
  // Wait for serial connection to establish
  while (!Serial && millis() < 5000) {
    delay(10);
  }
  
  Serial.println("// Digital Outputs Controller Started");
  Serial.print("// Device: "); Serial.println(DEVICE_NAME);
  Serial.println("// Outputs respond to dataref values and commands");
}

void loop() {
  checkSerial();
  updateOutputs();
  delay(10);  // Small delay to prevent overwhelming the processor
}

void checkSerial() {
  // Handle incoming serial commands from the bridge
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    
    // Handle handshake request from the bridge
    if (line == "HELLO") {
      Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
      Serial.print(";board="); Serial.print(BOARD_TYPE);
      Serial.print(";name="); Serial.println(DEVICE_NAME);
    }
    // Handle incoming dataref values from the bridge
    // Format: VALUE dataref_name value
    else if (line.startsWith("VALUE ")) {
      // Parse the VALUE message: VALUE dataref_name value
      int firstSpace = line.indexOf(' ');
      int secondSpace = line.indexOf(' ', firstSpace + 1);
      
      if (firstSpace > 0 && secondSpace > firstSpace) {
        String datarefName = line.substring(firstSpace + 1, secondSpace);
        String valueStr = line.substring(secondSpace + 1);
        float value = valueStr.toFloat();
        
        // Update storage based on dataref name
        if (datarefName == "sim/cockpit2/switches/gear_handle_status") {
          datarefValue = value;
          Serial.print("// Received gear status: "); Serial.println(datarefValue);
        }
        else if (datarefName == "sim/cockpit2/switches/beacon_on") {
          datarefValue = value;  // Could also control output 1
          Serial.print("// Received beacon status: "); Serial.println(datarefValue);
        }
      }
    }
    // Handle incoming array values
    // Format: ARRAYVALUE array_name type value1,value2,value3,...
    else if (line.startsWith("ARRAYVALUE ")) {
      // Parse array value message
      String rest = line.substring(11);  // Remove "ARRAYVALUE " prefix
      int firstSpace = rest.indexOf(' ');
      int secondSpace = rest.indexOf(' ', firstSpace + 1);
      
      if (firstSpace > 0 && secondSpace > firstSpace) {
        String arrayName = rest.substring(0, firstSpace);
        String type = rest.substring(firstSpace + 1, secondSpace);
        String valuesStr = rest.substring(secondSpace + 1);
        
        // Process array values based on array name
        if (arrayName == "LED_STATE_ARRAY") {
          // Parse the first value for array element control
          int commaIndex = valuesStr.indexOf(',');
          if (commaIndex > 0) {
            String firstValue = valuesStr.substring(0, commaIndex);
            arrayElementValue = firstValue.toFloat();
          } else {
            arrayElementValue = valuesStr.toFloat();
          }
          
          // Calculate average of multiple elements for output 4
          calculateCombinedArrayValue(valuesStr);
          
          Serial.print("// Received array values: "); Serial.println(valuesStr);
        }
      }
    }
    // Handle command execution notifications
    // Format: CMD_EXECUTED command_name
    else if (line.startsWith("CMD_EXECUTED ")) {
      String commandName = line.substring(11);  // Remove "CMD_EXECUTED " prefix
      commandExecuted = true;
      Serial.print("// Command executed: "); Serial.println(commandName);
      
      // Reset command status after a short period
      delay(50);  // Brief pulse for command execution
      commandExecuted = false;
    }
    // Handle LIST command to show available features
    else if (line == "LIST") {
      Serial.println("STATUS Available Functions:");
      Serial.println("STATUS - Output 1: Controlled by dataref value");
      Serial.println("STATUS - Output 2: Pulses when command executed");
      Serial.println("STATUS - Output 3: Controlled by array element");
      Serial.println("STATUS - Output 4: Controlled by multiple array elements");
    }
    // Handle STATUS command
    else if (line == "STATUS") {
      Serial.println("STATUS Controller Status:");
      Serial.print("STATUS - Outputs: 4 configured");
      Serial.print("STATUS - Dataref value: "); Serial.println(datarefValue);
      Serial.print("STATUS - Command executed: "); Serial.println(commandExecuted ? "YES" : "NO");
      Serial.print("STATUS - Array element value: "); Serial.println(arrayElementValue);
      Serial.print("STATUS - Combined array value: "); Serial.println(combinedArrayValue);
    }
  }
}

void updateOutputs() {
  // Update outputs periodically based on received values
  if (millis() - lastUpdate > UPDATE_INTERVAL) {
    // Output 1: Controlled by dataref value (turns on if value > 0.5)
    if (datarefValue > 0.5) {
      digitalWrite(OUTPUT1_PIN, HIGH);
    } else {
      digitalWrite(OUTPUT1_PIN, LOW);
    }
    
    // Output 2: Pulses when command is executed
    if (commandExecuted) {
      digitalWrite(OUTPUT2_PIN, HIGH);
    } else {
      digitalWrite(OUTPUT2_PIN, LOW);
    }
    
    // Output 3: Controlled by specific array element (turns on if value > 0.5)
    if (arrayElementValue > 0.5) {
      digitalWrite(OUTPUT3_PIN, HIGH);
    } else {
      digitalWrite(OUTPUT3_PIN, LOW);
    }
    
    // Output 4: Controlled by combined array elements (turns on if average > 0.5)
    if (combinedArrayValue > 0.5) {
      digitalWrite(OUTPUT4_PIN, HIGH);
    } else {
      digitalWrite(OUTPUT4_PIN, LOW);
    }
    
    lastUpdate = millis();
  }
}

void calculateCombinedArrayValue(String valuesStr) {
  // Parse comma-separated values and calculate average
  int count = 0;
  float sum = 0.0;
  int start = 0;
  int commaIndex = 0;
  
  while (commaIndex >= 0) {
    commaIndex = valuesStr.indexOf(',', start);
    String valueStr;
    
    if (commaIndex >= 0) {
      valueStr = valuesStr.substring(start, commaIndex);
      start = commaIndex + 1;
    } else {
      valueStr = valuesStr.substring(start);
    }
    
    sum += valueStr.toFloat();
    count++;
    
    if (commaIndex < 0) break;
  }
  
  if (count > 0) {
    combinedArrayValue = sum / count;
  } else {
    combinedArrayValue = 0.0;
  }
}
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

1. **Device not recognized**
   - Verify handshake response format: `XPDR;fw=1.0;board=UNO;name=MyDevice`
   - Check serial monitor for HELLO command from bridge
   - Ensure baud rate is 115200

2. **No communication**
   - Confirm baud rate 115200 on both ends
   - Check COM port selection in bridge application
   - Verify USB cable is properly connected

3. **Wrong data**
   - Double-check data types (int/float/bool/byte)
   - Verify dataref names match exactly
   - Check for typos in commands

4. **Connection drops**
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
For building standalone executables, see `How_to_Package_XPDRB_as_an_EXE.md`.

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---

**Happy Flight Simulation! 🛩️**