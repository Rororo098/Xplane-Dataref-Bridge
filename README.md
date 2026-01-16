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
- **Real-time Dataref Monitoring:** Monitor any X-Plane dataref in real-time
- **Bidirectional Communication:** Both read from and write to X-Plane
- **Multiple Data Types:** Support for int, float, bool, byte, string, and array datarefs
- **Command Execution:** Execute X-Plane commands from hardware
- **Hardware Abstraction:** Works with Arduino, ESP32, and other serial devices
- **GUI Interface:** Intuitive PyQt6-based user interface
- **Input Mapping:** Map hardware inputs (buttons, encoders, pots) to X-Plane actions
- **Output Mapping:** Map X-Plane datarefs to hardware outputs (LEDs, servos, displays)
- **Auto-Discovery:** Automatic detection of X-Plane and connected devices
- **Cross-Platform:** Runs on Windows, macOS, and Linux


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

/* ==========================================================================
   DEVICE IDENTIFICATION SECTION
   These constants identify your device to bridge application
   ========================================================================== */

const char* DEVICE_NAME = "FourButtonController";     // Human-readable name for your device
const char* FIRMWARE_VERSION = "1.0";                 // Version number for updates/tracking
const char* BOARD_TYPE = "UNO";                        // Arduino board type (UNO, MEGA, etc.)

/* ==========================================================================
   OUTPUT_ID DEFINITIONS SECTION
   These are friendly names we'll use instead of hardcoding X-Plane datarefs
   ========================================================================== */

const char* OUTPUT_ID_GEAR = "GEAR_HANDLE";           // Landing gear control
const char* OUTPUT_ID_HEADING = "HEADING_SYNC";       // Heading sync command
const char* OUTPUT_ID_LED_ELEM = "LED_STATE_ELEM0";   // Individual LED element
const char* OUTPUT_ID_LED_ARRAY = "LED_STATE_ARRAY";  // Full LED array

/* ==========================================================================
   HARDWARE PIN CONFIGURATION SECTION
   Define which Arduino pins each physical component is connected to
   ========================================================================== */

const int BUTTON1_PIN = 2;  // Button for GEAR_HANDLE
const int BUTTON2_PIN = 3;  // Button for HEADING_SYNC
const int BUTTON3_PIN = 4;  // Button for LED_STATE_ELEM0
const int BUTTON4_PIN = 5;  // Button for LED_STATE_ARRAY

/* ==========================================================================
   BUTTON STATE TRACKING SECTION
   Variables to remember previous button states for proper detection
   ========================================================================== */

// Boolean variables to track if each button was pressed in previous loop
bool lastButton1State = false;  // Previous state of Button 1
bool lastButton2State = false;  // Previous state of Button 2
bool lastButton3State = false;  // Previous state of Button 3
bool lastButton4State = false;  // Previous state of Button 4

/* ==========================================================================
   DEBOUNCING TIMERS SECTION
   Debouncing prevents one physical button press from registering multiple times
   ========================================================================== */

// Timer variables to track when each button last changed state
unsigned long lastDebounceTime1 = 0;  // Timer for Button 1
unsigned long lastDebounceTime2 = 0;  // Timer for Button 2
unsigned long lastDebounceTime3 = 0;  // Timer for Button 3
unsigned long lastDebounceTime4 = 0;  // Timer for Button 4

// Time in milliseconds to wait between button state changes
const unsigned long DEBOUNCE_DELAY = 50;  // 50ms = 0.05 seconds debounce time

/* ==========================================================================
   SERIAL COMMUNICATION SECTION
   Buffer for building messages from PC character by character
   ========================================================================== */

String inputBuffer = "";  // Storage for incoming serial messages

/* ==========================================================================
   SETUP FUNCTION
   This runs once when Arduino boots up - initializes all hardware and settings
   ========================================================================== */

void setup() {
  // --- Initialize Button Pins ---
  // Set each button pin as an input with internal pull-up resistor
  // INPUT_PULLUP means: pin reads HIGH when not pressed, LOW when pressed
  pinMode(BUTTON1_PIN, INPUT_PULLUP);  // Enable pull-up for Button 1
  pinMode(BUTTON2_PIN, INPUT_PULLUP);  // Enable pull-up for Button 2
  pinMode(BUTTON3_PIN, INPUT_PULLUP);  // Enable pull-up for Button 3
  pinMode(BUTTON4_PIN, INPUT_PULLUP);  // Enable pull-up for Button 4

  // --- Initialize Serial Communication ---
  // Start serial communication at 115200 baud (bits per second)
  // This is the speed required by X-Plane Dataref Bridge
  Serial.begin(115200);

  // --- Wait for Serial Connection ---
  // Some boards (like Leonardo) need time to establish serial connection
  // This waits up to 5 seconds for serial to be ready
  while (!Serial && millis() < 5000) {
    delay(10);  // Small delay to prevent overwhelming the processor
  }

  // --- Send Startup Messages ---
  // These messages help with debugging and confirm device is working
  Serial.println("// Four Button Controller Started");  // Startup confirmation
  Serial.print("// Device: ");
  Serial.println(DEVICE_NAME);                        // Send device name
  Serial.println("// Button 1: GEAR_HANDLE | Button 2: HEADING_SYNC | Button 3: LED_ELEM | Button 4: LED_ARRAY");  // Function guide
}

/* ==========================================================================
   MAIN LOOP FUNCTION
   This runs continuously after setup() - checks buttons and handles communication
   ========================================================================== */

void loop() {
  checkSerial();    // Listen for commands from bridge application
  checkButtons();   // Check if any buttons have been pressed
  delay(10);        // Small delay to prevent overwhelming processor
}

/* ==========================================================================
   SERIAL COMMUNICATION HANDLER
   Processes incoming messages from X-Plane Dataref Bridge using correct protocol
   ========================================================================== */

void checkSerial() {
  // Check if any data is available to read from serial port
  while (Serial.available() > 0) {
    // Read one character at a time
    char c = (char)Serial.read();

    // If we receive a newline character, the message is complete
    if (c == '\n') {
      processLine(inputBuffer);    // Process the complete message
      inputBuffer = "";             // Clear buffer for next message
    }
    // Ignore carriage return characters (Windows sometimes sends them)
    else if (c != '\r') {
      inputBuffer += c;    // Add character to buffer
    }
  }
}

/* ==========================================================================
   MESSAGE PROCESSING FUNCTION
   Decodes and handles messages received from the bridge application
   ========================================================================== */

void processLine(String line) {
  line.trim();  // Remove any whitespace from beginning and end

  // --- Handle Handshake Request ---
  // Bridge sends "HELLO" to check if device is responding
  if (line == "HELLO") {
    // Respond with device information in the exact expected format
    Serial.print("XPDR;fw=");
    Serial.print(FIRMWARE_VERSION);    // Send firmware version
    Serial.print(";board=");
    Serial.print(BOARD_TYPE);          // Send board type
    Serial.print(";name=");
    Serial.println(DEVICE_NAME);       // Send device name

    // Visual feedback - blink built-in LED to show connection established
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
  }

  // --- Handle SET Commands ---
  // Bridge sends "SET <KEY> <VALUE>" when X-Plane dataref changes
  else if (line.startsWith("SET ")) {
    // Parse format: "SET GEAR_LED 1.0"
    int firstSpace = line.indexOf(' ');      // Find first space
    int secondSpace = line.lastIndexOf(' '); // Find last space

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);  // Extract the OUTPUT_ID
      String valueStr = line.substring(secondSpace + 1);         // Extract the value
      float value = valueStr.toFloat();                        // Convert to float

      // Handle the SET command based on the key
      handleSetCommand(key, value);
    }
  }
}

/* ==========================================================================
   SET COMMAND HANDLER
   Processes SET commands and sends ACK responses for debugging
   ========================================================================== */

void handleSetCommand(String key, float value) {
  // --- Process Different Output_IDs ---
  // This section would handle any data coming FROM X-Plane TO your Arduino
  // For this input-only controller, we just acknowledge for debugging

  if (key == "GEAR_HANDLE") {
    // Example: If you had a gear status LED
    // digitalWrite(GEAR_LED_PIN, value > 0.5 ? HIGH : LOW);
    Serial.print("// Received GEAR_HANDLE: ");
    Serial.println(value);
  }
  else if (key == "HEADING_SYNC") {
    Serial.print("// Received HEADING_SYNC: ");
    Serial.println(value);
  }
  else if (key == "LED_STATE_ELEM0") {
    Serial.print("// Received LED_STATE_ELEM0: ");
    Serial.println(value);
  }
  else if (key == "LED_STATE_ARRAY") {
    Serial.print("// Received LED_STATE_ARRAY: ");
    Serial.println(value);
  }

  // Send acknowledgment for debugging (optional but helpful)
  Serial.print("ACK ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value);
}

/* ==========================================================================
   BUTTON CHECKING FUNCTION
   Checks all four buttons for state changes and handles debouncing
   ========================================================================== */

void checkButtons() {
  // --- Read Current Button States ---
  // digitalRead() returns HIGH or LOW
  // We invert (!) the reading because INPUT_PULLUP gives HIGH when not pressed
  bool currentButton1State = !digitalRead(BUTTON1_PIN);  // Read Button 1
  bool currentButton2State = !digitalRead(BUTTON2_PIN);  // Read Button 2
  bool currentButton3State = !digitalRead(BUTTON3_PIN);  // Read Button 3
  bool currentButton4State = !digitalRead(BUTTON4_PIN);  // Read Button 4

  /* ==========================================================================
     BUTTON 1 PROCESSING - GEAR_HANDLE
     ========================================================================== */
  if (currentButton1State != lastButton1State) {
    // Check if enough time has passed for debouncing
    if ((millis() - lastDebounceTime1) > DEBOUNCE_DELAY) {
      // Only act on button press (going from not pressed to pressed)
      if (currentButton1State) {
        writeDataref();                    // Send gear command
        lastDebounceTime1 = millis();      // Reset debounce timer
      }
    }
    lastButton1State = currentButton1State;  // Update stored state
  }

  /* ==========================================================================
     BUTTON 2 PROCESSING - HEADING_SYNC
     ========================================================================== */
  if (currentButton2State != lastButton2State) {
    if ((millis() - lastDebounceTime2) > DEBOUNCE_DELAY) {
      if (currentButton2State) {
        executeCommand();                  // Send heading sync command
        lastDebounceTime2 = millis();      // Reset debounce timer
      }
    }
    lastButton2State = currentButton2State;  // Update stored state
  }

  /* ==========================================================================
     BUTTON 3 PROCESSING - LED_STATE_ELEM0
     ========================================================================== */
  if (currentButton3State != lastButton3State) {
    if ((millis() - lastDebounceTime3) > DEBOUNCE_DELAY) {
      if (currentButton3State) {
        writeArrayElement();               // Send LED element command
        lastDebounceTime3 = millis();      // Reset debounce timer
      }
    }
    lastButton3State = currentButton3State;  // Update stored state
  }

  /* ==========================================================================
     BUTTON 4 PROCESSING - LED_STATE_ARRAY
     ========================================================================== */
  if (currentButton4State != lastButton4State) {
    if ((millis() - lastDebounceTime4) > DEBOUNCE_DELAY) {
      if (currentButton4State) {
        writeMultipleArrayElements();       // Send LED array command
        lastDebounceTime4 = millis();      // Reset debounce timer
      }
    }
    lastButton4State = currentButton4State;  // Update stored state
  }
}

/* ==========================================================================
   BUTTON ACTION FUNCTIONS
   These functions are called when buttons are pressed - they send commands to X-Plane
   ========================================================================== */

// Button 1 Action: Send gear handle command using OUTPUT_ID
void writeDataref() {
  Serial.print("INPUT ");          // Start of input message
  Serial.print(OUTPUT_ID_GEAR);    // Send OUTPUT_ID for gear
  Serial.print(" ");              // Space separator
  Serial.println("1");            // Send value 1 (gear down/engaged)
  Serial.println("// Button 1: Sent GEAR_HANDLE input");  // Debug message
}

// Button 2 Action: Send heading sync command using OUTPUT_ID
void executeCommand() {
  Serial.print("INPUT ");            // Start of input message
  Serial.print(OUTPUT_ID_HEADING);   // Send OUTPUT_ID for heading
  Serial.print(" ");               // Space separator
  Serial.println("1");              // Send value 1 (sync engaged)
  Serial.println("// Button 2: Sent HEADING_SYNC command");  // Debug message
}

// Button 3 Action: Send LED array element command using OUTPUT_ID
void writeArrayElement() {
  Serial.print("INPUT ");              // Start of input message
  Serial.print(OUTPUT_ID_LED_ELEM);    // Send OUTPUT_ID for LED element
  Serial.print(" ");                   // Space separator
  Serial.println("1.0");              // Send float value 1.0 (full brightness)
  Serial.println("// Button 3: Sent LED_STATE_ELEM0 input");  // Debug message
}

// Button 4 Action: Send LED array command using OUTPUT_ID
void writeMultipleArrayElements() {
  Serial.print("INPUT ");                // Start of input message
  Serial.print(OUTPUT_ID_LED_ARRAY);     // Send OUTPUT_ID for LED array
  Serial.print(" ");                     // Space separator
  Serial.println("1.0,0.5,0.0");      // Send multiple values (CSV format)
  Serial.println("// Button 4: Sent LED_STATE_ARRAY input");  // Debug message

  // Update local test array for demonstration (optional)
  // testArray[0] = 1.0;  // First element full brightness
  // testArray[1] = 0.5;  // Second element half brightness
  // testArray[2] = 0.0;  // Third element off
  // Serial.println("// Local array updated: [0]=1.0, [1]=0.5, [2]=0.0");  // Debug message
}

/* ==========================================================================
   END OF SKETCH
   Congratulations! You now have a working 4-button controller with proper protocol.
   ========================================================================== */
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

/* ==========================================================================
   DEVICE IDENTIFICATION SECTION
   These constants identify your device to bridge application
   ========================================================================== */

const char* DEVICE_NAME = "4AxisController";       // Human-readable device name
const char* FIRMWARE_VERSION = "1.0";             // Version for tracking updates
const char* BOARD_TYPE = "UNO";                    // Arduino board type

/* ==========================================================================
   OUTPUT_ID DEFINITIONS SECTION
   Friendly names for your controls instead of hardcoded X-Plane datarefs
   ========================================================================== */

const char* OUTPUT_ID_THROTTLE = "THROTTLE_AXIS";     // Main throttle control
const char* OUTPUT_ID_AUTOPILOT = "AUTOPILOT_TOGGLE";  // Autopilot on/off
const char* OUTPUT_ID_DOOR_ELEM_BASE = "DOOR_ELEM";    // Base for door elements
const char* OUTPUT_ID_DOOR_ARRAY = "DOOR_ARRAY";       // Full door array

/* ==========================================================================
   ANALOG PIN CONFIGURATION SECTION
   Define which Arduino analog pins each control is connected to
   ========================================================================== */

const int AXIS_1_PIN = A0;  // Throttle potentiometer
const int AXIS_2_PIN = A1;  // Autopilot trigger potentiometer
const int AXIS_3_PIN = A2;  // Door element selector potentiometer
const int AXIS_4_PIN = A3;  // Multi-door control potentiometer

/* ==========================================================================
   THRESHOLD AND SENSITIVITY SETTINGS
   Control how responsive each axis is to prevent unwanted triggers
   ========================================================================== */

// Threshold for triggering digital commands (Axis 2)
// Analog range: 0-1023, so 800 = ~78% of maximum
const int COMMAND_THRESHOLD = 800;

/* ==========================================================================
   PREVIOUS VALUE TRACKING SECTION
   Store previous readings to detect changes and prevent flooding
   ========================================================================== */

// Variables to remember the last reading from each axis
int prevAxis1Value = -1;  // Previous throttle reading
int prevAxis2Trigger = -1; // Previous autopilot trigger state
int prevAxis3Value = -1;  // Previous door element reading
int prevAxis4Value = -1;  // Previous door array reading

/* ==========================================================================
   DEMONSTRATION ARRAY SECTION
   Array to simulate door states for testing and demonstration
   ========================================================================== */

// Simulates door open ratios (0.0 = closed, 1.0 = fully open)
float demoArray[5] = {0.0, 0.0, 0.0, 0.0, 0.0};

/* ==========================================================================
   SERIAL COMMUNICATION SECTION
   Buffer for building messages from PC character by character
   ========================================================================== */

String inputBuffer = "";  // Storage for incoming serial messages

/* ==========================================================================
   SETUP FUNCTION
   Runs once at startup - initializes hardware and establishes communication
   ========================================================================== */

void setup() {
  // --- Initialize Serial Communication ---
  // Start serial at 115200 baud (required by X-Plane Dataref Bridge)
  Serial.begin(115200);

  // --- Wait for Serial Connection ---
  // Important for boards that don't immediately have serial available
  while (!Serial && millis() < 5000) {
    delay(10);  // Small delay to prevent CPU overload
  }

  // --- Send Startup Messages ---
  // These help with debugging and confirm proper initialization
  Serial.println("// 4-Axis Input Controller Started");
  Serial.print("// Device: ");
  Serial.println(DEVICE_NAME);
  Serial.println("// Axes: 1-THROTTLE, 2-AUTOPILOT, 3-DOOR_ELEM, 4-DOOR_ARRAY");

  // --- Initialize Analog Pins ---
  // Analog pins are inputs by default, but we set them explicitly for clarity
  pinMode(AXIS_1_PIN, INPUT);  // Throttle as input
  pinMode(AXIS_2_PIN, INPUT);  // Autopilot trigger as input
  pinMode(AXIS_3_PIN, INPUT);  // Door element selector as input
  pinMode(AXIS_4_PIN, INPUT);  // Door array control as input
}

/* ==========================================================================
   MAIN LOOP FUNCTION
   Runs continuously - reads all axes and processes their values
   ========================================================================== */

void loop() {
  checkSerialCommands();    // Check for messages from bridge

  // --- Read All Analog Inputs ---
  // analogRead() returns 0-1023 based on voltage (0V-5V)
  int axis1Value = analogRead(AXIS_1_PIN);  // Read throttle position
  int axis2Value = analogRead(AXIS_2_PIN);  // Read autopilot trigger
  int axis3Value = analogRead(AXIS_3_PIN);  // Read door element selector
  int axis4Value = analogRead(AXIS_4_PIN);  // Read door array control

  // --- Process Each Axis ---
  processAxis1(axis1Value);  // Handle throttle control
  processAxis2(axis2Value);  // Handle autopilot trigger
  processAxis3(axis3Value);  // Handle door element control
  processAxis4(axis4Value);  // Handle door array control

  delay(50);  // Small delay to prevent overwhelming serial connection
}

/* ==========================================================================
   SERIAL COMMAND HANDLER
   Processes incoming messages from X-Plane Dataref Bridge using correct protocol
   ========================================================================== */

void checkSerialCommands() {
  // Check if any data is available from serial port
  while (Serial.available() > 0) {
    // Read one character at a time
    char c = (char)Serial.read();

    // If we receive a newline character, the message is complete
    if (c == '\n') {
      processLine(inputBuffer);    // Process the complete message
      inputBuffer = "";             // Clear buffer for next message
    }
    // Ignore carriage return characters (Windows sometimes sends them)
    else if (c != '\r') {
      inputBuffer += c;    // Add character to buffer
    }
  }
}

/* ==========================================================================
   MESSAGE PROCESSING FUNCTION
   Decodes and handles messages received from the bridge application
   ========================================================================== */

void processLine(String line) {
  line.trim();  // Remove whitespace from beginning and end

  // --- Handle Handshake Request ---
  // Bridge sends "HELLO" to identify connected devices
  if (line == "HELLO") {
    // Respond with device identification in exact expected format
    Serial.print("XPDR;fw=");
    Serial.print(FIRMWARE_VERSION);    // Send firmware version
    Serial.print(";board=");
    Serial.print(BOARD_TYPE);          // Send board type
    Serial.print(";name=");
    Serial.println(DEVICE_NAME);       // Send device name
    Serial.println("// Handshake completed successfully");  // Confirmation
  }

  // --- Handle SET Commands ---
  // Bridge sends "SET <KEY> <VALUE>" when X-Plane dataref changes
  else if (line.startsWith("SET ")) {
    // Parse format: "SET THROTTLE_AXIS 0.75"
    int firstSpace = line.indexOf(' ');      // Find first space
    int secondSpace = line.lastIndexOf(' '); // Find last space

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);  // Extract the OUTPUT_ID
      String valueStr = line.substring(secondSpace + 1);         // Extract the value
      float value = valueStr.toFloat();                        // Convert to float

      // Handle the SET command based on the key
      handleSetCommand(key, value);
    }
  }
}

/* ==========================================================================
   SET COMMAND HANDLER
   Processes SET commands and sends ACK responses for debugging
   ========================================================================== */

void handleSetCommand(String key, float value) {
  // --- Process Different Output_IDs ---
  // This section would handle any data coming FROM X-Plane TO your Arduino
  // For this input-only controller, we just acknowledge for debugging

  if (key == "THROTTLE_AXIS") {
    Serial.print("// Received THROTTLE_AXIS: ");
    Serial.println(value);
  }
  else if (key == "AUTOPILOT_TOGGLE") {
    Serial.print("// Received AUTOPILOT_TOGGLE: ");
    Serial.println(value);
  }
  else if (key.startsWith("DOOR_ELEM")) {
    Serial.print("// Received ");
    Serial.print(key);
    Serial.print(": ");
    Serial.println(value);
  }
  else if (key == "DOOR_ARRAY") {
    Serial.print("// Received DOOR_ARRAY: ");
    Serial.println(value);
  }

  // Send acknowledgment for debugging (optional but helpful)
  Serial.print("ACK ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value);
}

/* ==========================================================================
   AXIS 1 PROCESSING - THROTTLE CONTROL
   Converts potentiometer position to smooth throttle command (0.0 to 1.0)
   ========================================================================== */

void processAxis1(int value) {
  // --- Normalize Analog Reading to 0.0-1.0 Range ---
  // analogRead() returns 0-1023, we convert to 0.0-1.0 (percentage)
  // 1023.0 = maximum reading, 0.0 = minimum reading
  float normalizedValue = (float)value / 1023.0;

  // --- Only Send Updates if Value Changed Significantly ---
  // This prevents flooding serial with identical values
  // Change must be >10 to trigger an update
  if (abs(value - prevAxis1Value) > 10) {
    // --- Send Throttle Command ---
    Serial.print("INPUT ");              // Start message
    Serial.print(OUTPUT_ID_THROTTLE);    // Send OUTPUT_ID
    Serial.print(" ");                   // Space separator
    Serial.println(normalizedValue, 4);   // Send value with 4 decimal places

    prevAxis1Value = value;  // Update stored previous value
  }
}

/* ==========================================================================
   AXIS 2 PROCESSING - AUTOPILOT TOGGLE
   Uses threshold to trigger autopilot on/off commands
   ========================================================================== */

void processAxis2(int value) {
  // --- Determine if Threshold is Exceeded ---
  // Should trigger when potentiometer is above 800 (~78% of maximum)
  bool shouldTrigger = (value > COMMAND_THRESHOLD);

  // --- Check State Change from Low to High ---
  if (shouldTrigger && !prevAxis2Trigger) {
    // --- Send Autopilot ON Command ---
    Serial.print("INPUT ");                // Start message
    Serial.print(OUTPUT_ID_AUTOPILOT);     // Send OUTPUT_ID
    Serial.print(" ");                   // Space separator
    Serial.println("1");                  // Value 1 = autopilot ON
    Serial.println("// Command: Autopilot ON triggered");  // Debug message
    prevAxis2Trigger = true;  // Update stored state
  }
  // --- Check State Change from High to Low ---
  else if (!shouldTrigger && prevAxis2Trigger) {
    // --- Send Autopilot OFF Command ---
    Serial.print("INPUT ");                // Start message
    Serial.print(OUTPUT_ID_AUTOPILOT);     // Send OUTPUT_ID
    Serial.print(" ");                   // Space separator
    Serial.println("0");                  // Value 0 = autopilot OFF
    Serial.println("// Command: Autopilot OFF triggered");  // Debug message
    prevAxis2Trigger = false;  // Update stored state
  }
}

/* ==========================================================================
   AXIS 3 PROCESSING - DOOR ELEMENT CONTROL
   Maps potentiometer position to specific door array elements
   ========================================================================== */

void processAxis3(int value) {
  // --- Normalize Reading to 0.0-1.0 ---
  float normalizedValue = (float)value / 1023.0;

  // --- Map Pot Position to Array Index ---
  // Convert 0-1023 range to 0-4 array index
  // This lets you select which door element to control
  int arrayIndex = map(value, 0, 1023, 0, 4);

  // --- Only Update if Value Changed Significantly ---
  if (abs(value - prevAxis3Value) > 10) {
    // --- Update Local Demo Array ---
    demoArray[arrayIndex] = normalizedValue;

    // --- Send Door Element Command ---
    Serial.print("INPUT ");                              // Start message
    Serial.print(OUTPUT_ID_DOOR_ELEM_BASE);              // Base OUTPUT_ID
    Serial.print(arrayIndex);                             // Add element number
    Serial.print(" ");                                   // Space separator
    Serial.println(normalizedValue, 4);                  // Send value with 4 decimals

    // --- Send Debug Information ---
    Serial.print("// Updated ");
    Serial.print(OUTPUT_ID_DOOR_ELEM_BASE);
    Serial.print(arrayIndex);
    Serial.print(" to value: ");
    Serial.println(normalizedValue, 4);

    prevAxis3Value = value;  // Update stored previous value
  }
}

/* ==========================================================================
   AXIS 4 PROCESSING - DOOR ARRAY CONTROL
   Controls multiple door elements simultaneously based on one potentiometer
   ========================================================================== */

void processAxis4(int value) {
  // --- Normalize Reading to 0.0-1.0 ---
  float normalizedValue = (float)value / 1023.0;

  // --- Only Update if Value Changed Significantly ---
  // Higher threshold (20) reduces traffic for multi-element operations
  if (abs(value - prevAxis4Value) > 20) {
    // --- Update Multiple Array Elements ---
    // Distribute potentiometer value across first 3 elements
    for (int i = 0; i < 3; i++) {
      // Create slight variations based on element position
      // Element 0: value - 0.1, Element 1: value, Element 2: value + 0.1
      float variedValue = constrain(normalizedValue + (i * 0.1 - 0.1), 0.0, 1.0);
      demoArray[i] = variedValue;
    }

    // --- Create Comma-Separated Values String ---
    String csvValues = "";
    for (int i = 0; i < 3; i++) {
      if (i > 0) csvValues += ",";  // Add comma between values
      csvValues += String(demoArray[i], 4);  // Add value with 4 decimals
    }

    // --- Send Door Array Command ---
    Serial.print("INPUT ");                  // Start message
    Serial.print(OUTPUT_ID_DOOR_ARRAY);      // Send OUTPUT_ID for array
    Serial.print(" ");                       // Space separator
    Serial.println(csvValues);               // Send CSV string

    // --- Send Debug Information ---
    Serial.print("// Updated DOOR_ARRAY with values: ");
    Serial.println(csvValues);

    prevAxis4Value = value;  // Update stored previous value
  }
}

/* ==========================================================================
   HELPER FUNCTIONS
   Utility functions for data conversion and processing
   ========================================================================== */

// --- Map and Constrain Helper Function ---
// Converts input range to output range while keeping values within bounds
float mapAndConstrain(int inputValue, int inMin, int inMax, float outMin, float outMax) {
  // Map input range to output range (like Arduino's map() but for floats)
  float mappedValue = ((float)(inputValue - inMin) / (float)(inMax - inMin)) * (outMax - outMin) + outMin;

  // Constrain value to be within output range
  return constrain(mappedValue, outMin, outMax);
}

/* ==========================================================================
   END OF SKETCH
   Congratulations! You now have a working 4-axis input controller with proper protocol.
   ========================================================================== */
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

/* ==========================================================================
   DEVICE IDENTIFICATION SECTION
   These constants identify your device to X-Plane Dataref Bridge
   ========================================================================== */

const char* DEVICE_NAME = "DigitalOutputsController";  // Human-readable name
const char* FIRMWARE_VERSION = "1.0";                // Version tracking
const char* BOARD_TYPE = "UNO";                       // Arduino board type

/* ==========================================================================
   OUTPUT_ID DEFINITIONS SECTION
   These are the friendly names the bridge will use to send data to your device
   ========================================================================== */

const char* OUTPUT_ID_GEAR = "GEAR_STATUS";           // Landing gear status
const char* OUTPUT_ID_BEACON = "BEACON_STATUS";       // Beacon light status
const char* OUTPUT_ID_LED_ELEM = "LED_STATE_ELEM";    // LED array elements
const char* OUTPUT_ID_LED_ARRAY = "LED_STATE_ARRAY";   // Full LED array

/* ==========================================================================
   DIGITAL OUTPUT PIN CONFIGURATION SECTION
   Define which Arduino pins each output device is connected to
   ========================================================================== */

const int OUTPUT1_PIN = 8;  // Controlled by GEAR_STATUS (landing gear indicator)
const int OUTPUT2_PIN = 9;  // Pulses for command execution (activity indicator)
const int OUTPUT3_PIN = 10; // Controlled by LED element (status indicator)
const int OUTPUT4_PIN = 11; // Controlled by LED array (overall status)

/* ==========================================================================
   DATA STORAGE SECTION
   Variables to store values received from bridge application
   ========================================================================== */

// --- Single Value Storage ---
float gearValue = 0.0;      // Current landing gear status (0.0=up, 1.0=down)
float beaconValue = 0.0;     // Current beacon light status (0.0=off, 1.0=on)

// --- Command Status ---
bool commandExecuted = false;  // Flag for command execution pulse

// --- Array Value Storage ---
float arrayElementValue = 0.0;  // Individual array element value
float combinedArrayValue = 0.0; // Average of multiple array elements

/* ==========================================================================
   TIMING CONTROL SECTION
   Manages when outputs are updated to prevent unnecessary rapid changes
   ========================================================================== */

unsigned long lastUpdate = 0;              // Timestamp of last output update
const unsigned long UPDATE_INTERVAL = 100;  // Update every 100ms (0.1 seconds)

/* ==========================================================================
   SERIAL COMMUNICATION SECTION
   Buffer for building messages from PC character by character
   ========================================================================== */

String inputBuffer = "";  // Storage for incoming serial messages

/* ==========================================================================
   SETUP FUNCTION
   Runs once at startup - initializes all outputs and establishes communication
   ========================================================================== */

void setup() {
  // --- Initialize Digital Output Pins ---
  // Set all output pins to OUTPUT mode to control LEDs or other devices
  pinMode(OUTPUT1_PIN, OUTPUT);  // Gear status pin as output
  pinMode(OUTPUT2_PIN, OUTPUT);  // Command pulse pin as output
  pinMode(OUTPUT3_PIN, OUTPUT);  // LED element pin as output
  pinMode(OUTPUT4_PIN, OUTPUT);  // LED array pin as output

  // --- Initialize All Outputs to OFF State ---
  digitalWrite(OUTPUT1_PIN, LOW);  // Turn off gear indicator
  digitalWrite(OUTPUT2_PIN, LOW);  // Turn off command indicator
  digitalWrite(OUTPUT3_PIN, LOW);  // Turn off LED element indicator
  digitalWrite(OUTPUT4_PIN, LOW);  // Turn off LED array indicator

  // --- Initialize Serial Communication ---
  Serial.begin(115200);  // Start serial at bridge's required baud rate

  // --- Wait for Serial Connection ---
  // Important for boards that need time to establish serial connection
  while (!Serial && millis() < 5000) {
    delay(10);  // Small delay to prevent CPU overload
  }

  // --- Send Startup Messages ---
  Serial.println("// Digital Outputs Controller Started");
  Serial.print("// Device: ");
  Serial.println(DEVICE_NAME);
  Serial.println("// Outputs respond to OUTPUT_ID values and commands");
}

/* ==========================================================================
   MAIN LOOP FUNCTION
   Runs continuously - checks for incoming data and updates outputs accordingly
   ========================================================================== */

void loop() {
  checkSerial();   // Listen for messages from bridge application
  updateOutputs();  // Update LED outputs based on received data
  delay(10);       // Small delay to prevent overwhelming processor
}

/* ==========================================================================
   SERIAL COMMUNICATION HANDLER
   Processes incoming messages from X-Plane Dataref Bridge using correct protocol
   ========================================================================== */

void checkSerial() {
  // Check if any data is available from serial port
  while (Serial.available() > 0) {
    // Read one character at a time
    char c = (char)Serial.read();

    // If we receive a newline character, the message is complete
    if (c == '\n') {
      processLine(inputBuffer);    // Process the complete message
      inputBuffer = "";             // Clear buffer for next message
    }
    // Ignore carriage return characters (Windows sometimes sends them)
    else if (c != '\r') {
      inputBuffer += c;    // Add character to buffer
    }
  }
}

/* ==========================================================================
   MESSAGE PROCESSING FUNCTION
   Decodes and handles messages received from the bridge application
   ========================================================================== */

void processLine(String line) {
  line.trim();  // Remove whitespace from beginning and end

  // --- Handle Handshake Request ---
  // Bridge sends "HELLO" to identify connected devices
  if (line == "HELLO") {
    // Respond with device identification in exact expected format
    Serial.print("XPDR;fw=");
    Serial.print(FIRMWARE_VERSION);    // Send firmware version
    Serial.print(";board=");
    Serial.print(BOARD_TYPE);          // Send board type
    Serial.print(";name=");
    Serial.println(DEVICE_NAME);       // Send device name

    // Visual feedback - blink built-in LED to show connection established
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
  }

  // --- Handle SET Commands ---
  // Bridge sends "SET <KEY> <VALUE>" when X-Plane dataref changes
  else if (line.startsWith("SET ")) {
    // Parse format: "SET GEAR_STATUS 1.0" or "SET LED_STATE_ARRAY 0.5,0.7,0.3"
    int firstSpace = line.indexOf(' ');      // Find first space
    int secondSpace = line.lastIndexOf(' '); // Find last space

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);  // Extract the OUTPUT_ID
      String valueStr = line.substring(secondSpace + 1);         // Extract the value
      float value = valueStr.toFloat();                        // Convert to float

      // Handle the SET command based on the key
      handleSetCommand(key, valueStr, value);
    }
  }
}

/* ==========================================================================
   SET COMMAND HANDLER
   Processes SET commands and controls outputs based on received values
   ========================================================================== */

void handleSetCommand(String key, String valueStr, float value) {
  // --- Handle Gear Status Updates ---
  if (key == OUTPUT_ID_GEAR) {
    gearValue = value;  // Store new gear status
    Serial.print("// Received ");
    Serial.print(OUTPUT_ID_GEAR);
    Serial.print(": ");
    Serial.println(gearValue);  // Debug message
  }

  // --- Handle Beacon Status Updates ---
  else if (key == OUTPUT_ID_BEACON) {
    beaconValue = value;  // Store new beacon status
    Serial.print("// Received ");
    Serial.print(OUTPUT_ID_BEACON);
    Serial.print(": ");
    Serial.println(beaconValue);  // Debug message
  }

  // --- Handle LED Element Updates ---
  else if (key.startsWith(OUTPUT_ID_LED_ELEM)) {
    // Extract index if present (e.g., LED_STATE_ELEM3 → index 3)
    int indexStart = String(OUTPUT_ID_LED_ELEM).length();  // Find where index starts
    String indexStr = key.substring(indexStart);        // Get index part

    if (indexStr.length() > 0) {  // If index was specified
      int index = indexStr.toInt();  // Convert to integer
      arrayElementValue = value;     // Store element value

      Serial.print("// Received ");
      Serial.print(key);
      Serial.print(": ");
      Serial.println(value);  // Debug message
    }
  }

  // --- Handle Full LED Array Updates ---
  else if (key == OUTPUT_ID_LED_ARRAY) {
    calculateCombinedArrayValue(valueStr);  // Process array values
    Serial.print("// Received ");
    Serial.print(OUTPUT_ID_LED_ARRAY);
    Serial.print(": ");
    Serial.println(valueStr);  // Debug message
  }

  // Send acknowledgment for debugging (optional but helpful)
  Serial.print("ACK ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value);
}

/* ==========================================================================
   OUTPUT UPDATE FUNCTION
   Updates all digital outputs based on current stored values
   ========================================================================== */

void updateOutputs() {
  // --- Check if It's Time to Update ---
  // Only update outputs at specified interval to prevent rapid flashing
  if (millis() - lastUpdate > UPDATE_INTERVAL) {

    // --- Update Output 1: Gear Status Indicator ---
    // Turn ON if gear is down (value > 0.5 = 50%)
    if (gearValue > 0.5) {
      digitalWrite(OUTPUT1_PIN, HIGH);  // Turn ON gear indicator
    } else {
      digitalWrite(OUTPUT1_PIN, LOW);   // Turn OFF gear indicator
    }

    // --- Update Output 2: Command Execution Pulse ---
    // Brief pulse when command is executed
    if (commandExecuted) {
      digitalWrite(OUTPUT2_PIN, HIGH);   // Turn ON command indicator
    } else {
      digitalWrite(OUTPUT2_PIN, LOW);    // Turn OFF command indicator
    }

    // --- Update Output 3: LED Element Indicator ---
    // Turn ON if array element is active (value > 0.5 = 50%)
    if (arrayElementValue > 0.5) {
      digitalWrite(OUTPUT3_PIN, HIGH);   // Turn ON element indicator
    } else {
      digitalWrite(OUTPUT3_PIN, LOW);    // Turn OFF element indicator
    }

    // --- Update Output 4: LED Array Indicator ---
    // Turn ON if average array value is active (value > 0.5 = 50%)
    if (combinedArrayValue > 0.5) {
      digitalWrite(OUTPUT4_PIN, HIGH);   // Turn ON array indicator
    } else {
      digitalWrite(OUTPUT4_PIN, LOW);    // Turn OFF array indicator
    }

    // --- Update Timestamp ---
    lastUpdate = millis();  // Record when we last updated
  }
}

/* ==========================================================================
   ARRAY PROCESSING HELPER FUNCTION
   Processes comma-separated array values and calculates average
   ========================================================================== */

void calculateCombinedArrayValue(String valuesStr) {
  // --- Initialize Variables ---
  int count = 0;           // Number of values processed
  float sum = 0.0;        // Running total of values
  int start = 0;           // Starting position for parsing
  int commaIndex = 0;      // Position of next comma

  // --- Parse Comma-Separated Values ---
  // String format: "0.5,0.7,0.3,0.8,0.1"
  while (commaIndex >= 0) {
    // Find next comma in the string
    commaIndex = valuesStr.indexOf(',', start);
    String valueStr;

    // Extract individual value
    if (commaIndex >= 0) {
      valueStr = valuesStr.substring(start, commaIndex);  // Get value before comma
      start = commaIndex + 1;                            // Move past comma
    } else {
      valueStr = valuesStr.substring(start);               // Get last value
    }

    // --- Process Individual Value ---
    sum += valueStr.toFloat();  // Add to running total
    count++;                    // Increment count

    // --- Exit Loop After Last Value ---
    if (commaIndex < 0) break;
  }

  // --- Calculate Average ---
  if (count > 0) {
    combinedArrayValue = sum / count;  // Calculate average
  } else {
    combinedArrayValue = 0.0;         // Default to zero if no values
  }
}

/* ==========================================================================
   END OF SKETCH
   Congratulations! You now have a working digital outputs controller with proper protocol.
   ========================================================================== */
```

## Protocol Documentation

### Handshake Protocol
- **Bridge:** `HELLO`
- **Arduino:** `XPDR;fw=<version>;board=<type>;name=<device_name>`

### Dataref Operations
- **Read:** `READ <dataref_name> <type>` → `VALUE <dataref_name> <value>`
- **Write:** `WRITE <dataref_name> <type> <value>` → `OK`
- **Set (compat):** `SETDREF <dataref_name> <value>` → `ACK <key> <value>`
- **Read Array:** `READARRAY <array_name> <type>` → `ARRAYVALUE <array_name> <type> <csv_values>`
- **Write Array:** `WRITEARRAY <array_name> <type> <csv_values>` → `OK`
- **Read Elem:** `READELEM <array_name[index]> <type>` → `ELEMVALUE <array_name[index]> <type> <value>`
- **Write Elem:** `WRITEELEM <array_name[index]> <type> <value>` → `OK`
- **Multi-Read:** `MULTIREAD <array_name[start,end]> <type>` → `MULTIVALUE <array_name[start,end]> <type> <csv_values>`
- **Command:** `CMD <command_name>` → `CMD_EXECUTED <command_name>`

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
