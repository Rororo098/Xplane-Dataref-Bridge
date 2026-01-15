# X-Plane Dataref Bridge - Arduino Sketches Documentation

Comprehensive Arduino sketches demonstrating communication with the X-Plane Dataref Bridge. Each sketch focuses on a specific capability of the protocol.


## Table of Contents

1. [Handshake Protocol](#handshake-protocol)
2. [Reading Datarefs](#reading-datarefs)
3. [Writing Datarefs](#writing-datarefs)
4. [Basic Types Read/Write](#basic-types-readwrite)
5. [Array Datarefs](#array-datarefs)
6. [Command Datarefs](#command-datarefs)
7. [Array Elements Read/Write](#array-elements-readwrite)
8. [Communication Protocol](#communication-protocol)
9. [Setup Instructions](#setup-instructions)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [License](#license)
13. [Contributing](#contributing)

---

## Handshake Protocol

### handshake.ino
Establishes the initial two-way handshake so the bridge recognizes your device and maintains a heartbeat.

- Features: Two-way Serial handshake, heartbeat, device identification
- Output ID: `HANDSHAKE_DEMO`

```cpp
// handshake.ino
#include <Arduino.h>

const long BAUD_RATE = 115200;
const unsigned long HEARTBEAT_INTERVAL = 5000;
unsigned long lastHeartbeat = 0;

// Identification
const char* DEVICE_NAME = "HandshakeDemo";
const char* FIRMWARE_VERSION = "1.0";
const char* BOARD_TYPE = "UNO";

void sendIdentity() {
  Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
  Serial.print(";board="); Serial.print(BOARD_TYPE);
  Serial.print(";name="); Serial.println(DEVICE_NAME);
}

void setup() {
  Serial.begin(BAUD_RATE);
}

void loop() {
  // Listen for HELLO and respond with identity
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.equals("HELLO")) {
      sendIdentity();
    }
  }

  // Heartbeat (optional)
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    Serial.println("STATUS HB");
    lastHeartbeat = millis();
  }
}
```

---

## Reading Datarefs

### read_dataref.ino
Requests values for specific datarefs and parses VALUE responses.

- Features: Request values, store locally, periodic polling
- Output ID: `DATA_READER`

```cpp
// read_dataref.ino
#include <Arduino.h>

const long BAUD_RATE = 115200;
const unsigned long READ_INTERVAL = 1000; // ms
unsigned long lastReadRequest = 0;

float receivedFloatValue = 0.0f;
int receivedIntValue = 0;
bool receivedBoolValue = false;

// Example datarefs
const char* DREF_FLOAT = "sim/cockpit2/controls/flap_ratio";
const char* DREF_INT   = "sim/cockpit2/switches/gear_handle_status";
const char* DREF_BOOL  = "sim/cockpit2/switches/beacon_on";

void requestRead(const char* name, const char* type) {
  Serial.print("READ "); Serial.print(name); Serial.print(" "); Serial.println(type);
}

void parseValue(const String& line) {
  // Format: VALUE <name> <value>
  if (!line.startsWith("VALUE ")) return;
  int sp1 = line.indexOf(' ');
  int sp2 = line.indexOf(' ', sp1 + 1);
  if (sp1 < 0 || sp2 < 0) return;
  String name = line.substring(sp1 + 1, sp2);
  String valueStr = line.substring(sp2 + 1);
  if (name == DREF_FLOAT)      receivedFloatValue = valueStr.toFloat();
  else if (name == DREF_INT)   receivedIntValue   = valueStr.toInt();
  else if (name == DREF_BOOL)  receivedBoolValue  = (valueStr.toInt() != 0);
}

void setup() { Serial.begin(BAUD_RATE); }

void loop() {
  // Polling
  if (millis() - lastReadRequest >= READ_INTERVAL) {
    requestRead(DREF_FLOAT, "float");
    requestRead(DREF_INT,   "int");
    requestRead(DREF_BOOL,  "bool");
    lastReadRequest = millis();
  }

  // Handle incoming values
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    parseValue(line);
  }
}
```

---

## Writing Datarefs

### write_dataref.ino
Sends SETDREF commands and handles acknowledgments.

- Features: Write values, acknowledgments, periodic updates
- Output ID: `DATA_WRITER`

```cpp
// write_dataref.ino
#include <Arduino.h>

const long BAUD_RATE = 115200;
const unsigned long WRITE_INTERVAL = 2000; // ms
unsigned long lastWrite = 0;

float throttleValue = 0.0f; // 0.0..1.0
int gearPosition = 0;       // 0 or 1
bool beaconOn = false;

void setDref(const char* name, const String& value) {
  Serial.print("SETDREF "); Serial.print(name); Serial.print(" "); Serial.println(value);
}

void setup() { Serial.begin(BAUD_RATE); }

void loop() {
  if (millis() - lastWrite >= WRITE_INTERVAL) {
    throttleValue = fmod(throttleValue + 0.1f, 1.1f);
    gearPosition = (gearPosition == 0) ? 1 : 0;
    beaconOn = !beaconOn;

    setDref("sim/cockpit2/engine/actuators/throttle_ratio_all", String(throttleValue, 3));
    setDref("sim/cockpit2/switches/gear_handle_status", String(gearPosition));
    setDref("sim/cockpit2/switches/beacon_on", String(beaconOn ? 1 : 0));
    lastWrite = millis();
  }

  // Optional: read back ACK lines: "ACK <key> <value>"
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    // Handle ACK if needed
  }
}
```

---

## Basic Types Read/Write

### read_write_basic_types.ino
Bi-directional example for int, float, bool, and byte.

- Features: Bi-directional, dynamic updates
- Output ID: `BASIC_TYPES_RW`

```cpp
// read_write_basic_types.ino
#include <Arduino.h>

const long BAUD_RATE = 115200;

int counterValue = 0;
float rateValue = 0.0f;
bool armedValue = false;
byte modeValue = 0;

void writeValue(const char* name, const String& type, const String& value) {
  Serial.print("WRITE "); Serial.print(name); Serial.print(" "); Serial.print(type);
  Serial.print(" "); Serial.println(value);
}

void setup() { Serial.begin(BAUD_RATE); }

void loop() {
  // Example: periodically write and then read back
  static unsigned long t0 = 0;
  if (millis() - t0 > 1000) {
    counterValue = (counterValue + 1) % 100;
    rateValue += 0.25f;
    armedValue = !armedValue;
    modeValue++;

    writeValue("sim/cockpit/autopilot/heading_mag", "float", String(rateValue, 2));
    writeValue("sim/cockpit2/switches/navigation_lights_on", "bool", String(armedValue ? 1 : 0));
    t0 = millis();
  }

  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("VALUE ")) {
      // Parse incoming values if needed (same pattern as read_dataref.ino)
    }
  }
}
```

---

## Array Datarefs

### array_dataref.ino
Reads and writes entire arrays using comma-separated values.

- Features: Array read/write across types
- Output ID: `ARRAY_DATA_REF`

```cpp
// array_dataref.ino
#include <Arduino.h>

const long BAUD_RATE = 115200;

float floatArray[10] = {0};
int intArray[10] = {0};
bool boolArray[10] = {false};
byte byteArray[10] = {0};

void readArray(const char* name, const char* type) {
  Serial.print("READARRAY "); Serial.print(name); Serial.print(" "); Serial.println(type);
}

void writeArray(const char* name, const char* type, const String& csv) {
  Serial.print("WRITEARRAY "); Serial.print(name); Serial.print(" "); Serial.print(type);
  Serial.print(" "); Serial.println(csv);
}

void setup() { Serial.begin(BAUD_RATE); }

void loop() {
  // Example read
  readArray("sim/flightmodel2/misc/door_open_ratio", "float");

  // Example write (first three elements)
  String csv = String(0.1f, 2) + "," + String(0.2f, 2) + "," + String(0.3f, 2);
  writeArray("sim/flightmodel2/misc/door_open_ratio", "float", csv);

  delay(1000);
}
```

---

## Command Datarefs

### command_dataref.ino
Executes command-type datarefs and provides simple LED feedback.

- Features: Command execution, LED feedback
- Output ID: `CMD_DEVICE`

```cpp
// command_dataref.ino
#include <Arduino.h>

const long BAUD_RATE = 115200;
const int LED_PIN = LED_BUILTIN;
bool ledState = false;

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (!line.startsWith("CMD ")) continue;

    String cmd = line.substring(4);
    if (cmd == "toggleLED") {
      ledState = !ledState;
      digitalWrite(LED_PIN, ledState ? HIGH : LOW);
    } else if (cmd == "pulseLED") {
      for (int i = 0; i < 3; i++) { digitalWrite(LED_PIN, HIGH); delay(150); digitalWrite(LED_PIN, LOW); delay(150);}    
    } else if (cmd == "reset") {
      // Implement device-specific reset
    } else if (cmd == "flash") {
      digitalWrite(LED_PIN, HIGH); delay(50); digitalWrite(LED_PIN, LOW);
    }

    Serial.print("CMD_EXECUTED "); Serial.println(cmd);
  }
}
```

---

## Array Elements Read/Write

### array_elements_read_write.ino
Reads/writes individual array elements or ranges.

- Features: Element access, ranges, multi-element ops
- Output ID: `ARRAY_ELEMENTS_RW`

```cpp
// array_elements_read_write.ino
#include <Arduino.h>

const long BAUD_RATE = 115200;

void readElem(const char* nameIdx, const char* type) {
  Serial.print("READELEM "); Serial.print(nameIdx); Serial.print(" "); Serial.println(type);
}

void writeElem(const char* nameIdx, const char* type, const String& value) {
  Serial.print("WRITEELEM "); Serial.print(nameIdx); Serial.print(" "); Serial.print(type);
  Serial.print(" "); Serial.println(value);
}

void multiRead(const char* nameRange, const char* type) {
  Serial.print("MULTIREAD "); Serial.print(nameRange); Serial.print(" "); Serial.println(type);
}

void setup() { Serial.begin(BAUD_RATE); }

void loop() {
  readElem("sim/flightmodel2/misc/door_open_ratio[0]", "float");
  writeElem("sim/flightmodel2/misc/door_open_ratio[1]", "float", String(0.75f, 2));
  multiRead("sim/flightmodel2/misc/door_open_ratio[0,4]", "float");
  delay(1000);
}
```

---

## Communication Protocol

### Handshake
```
Bridge: HELLO
Arduino: XPDR;fw=1.0;board=UNO;name=DeviceName
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
```

---

## Setup Instructions

1. Install Arduino IDE (1.8.0+)
2. Connect Arduino via USB
3. Tools → Board → Select your board (e.g., Arduino Uno)
4. Tools → Port → Select the COM port
5. Open a sketch (e.g., `handshake.ino`) and Upload
6. Open the X-Plane Dataref Bridge and connect to the same COM port

---

## Testing

Use these example Output IDs for quick testing:
- `HANDSHAKE_DEMO`
- `DATA_READER`
- `DATA_WRITER`
- `BASIC_TYPES_RW`
- `ARRAY_DATA_REF`
- `CMD_DEVICE`
- `ARRAY_ELEMENTS_RW`

---

## Troubleshooting

- Device not recognized: verify handshake response format
- No communication: confirm baud rate 115200 on both ends
- Wrong data: double-check types (int/float/bool/byte)
- Connection drops: implement heartbeat (STATUS HB) or increase timeout

---

## License

MIT License (see LICENSE file)

---

## Contributing

Issues and pull requests welcome. Please follow conventional commits and include reproduction steps for bugs.
