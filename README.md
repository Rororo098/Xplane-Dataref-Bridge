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
- Download latest `X-Plane Dataref Bridge-Windows.zip` from releases
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

## Arduino sketches (included)

The repository includes seven Arduino sketches demonstrating a serial-based bridge for datarefs. Each file is a standalone example you can drop into the Arduino IDE. **All sketches include a unified handshake API** so they are immediately compatible with the bridge system for testing and integration.

### Overview of Sketches

- **handshake.ino**: Simple two-way handshake over Serial with a heartbeat
- **read_dataref.ino**: Read a dataref message and save to a variable
- **write_dataref.ino**: Trigger writes to the host (dataref writer)
- **read_write_basic_types.ino**: Read and write int, float, bool, and byte datarefs
- **array_dataref.ino**: Read/write array datarefs for int/float/bool/byte
- **command_dataref.ino**: Call/execute command-type datarefs
- **array_elements_read_write.ino**: Read/write single elements and multiple elements of arrays

### Bridge Handshake Protocol

All sketches implement a standardized handshake protocol that ensures the bridge can recognize and communicate with any device:

1. **Initialization**: Device sends `BRIDGE_HELLO` to announce presence
2. **Acknowledgment**: Host responds with `BRIDGE_HELLO_ACK` or `BRIDGE_HANDSHAKE_OK`
3. **Ready State**: Device sends `BRIDGE_READY` and begins normal operation
4. **Heartbeat**: Device sends `HB` every 1 second when ready
5. **Optional Ack**: Host may respond with `HB_ACK` to acknowledge heartbeat

This handshake ensures reliable communication and allows the bridge to detect device presence and connectivity status.

## Arduino Sketch Code Library

The following seven Arduino sketches are ready to copy into separate `.ino` files. Each includes:
- **Full bridge handshake implementation** for automatic recognition
- **Detailed line-by-line comments** explaining functionality
- **Example Output IDs** for testing and verification
- **Comprehensive error handling** and robust parsing

### 1. handshake.ino
**Example Output ID: HANDSHAKE-EX-001**

Demonstrates the fundamental handshake protocol with heartbeat functionality.

```cpp
/*
  handshake.ino
  - Simple two-way handshake over Serial with a heartbeat after handshake.
  - Bridge-like handshake API included so the "bridge" (test harness) can recognize
    and talk to every sketch consistently.
  - Handshake protocol (simple, text-based, line-delimited):
    1) Device sends BRIDGE_HELLO to host to announce presence.
    2) Host responds BRIDGE_HELLO_ACK (or BRIDGE_HANDSHAKE_OK) to confirm.
    3) Device marks bridge as ready and starts a heartbeat (HB) every 1s.
    4) Host can reply HB_ACK to acknowledge each heartbeat.
  - This file includes the handshake helpers so the bridge can reuse them in tests.

 IMPORTANT: All tests assume newline-terminated lines.
*/

// --------- Configuration ---------
const int SERIAL_BAUD = 115200;      // Serial baud rate
const unsigned long HB_INTERVAL = 1000; // Heartbeat interval (ms)

// --------- Internal state ---------
char lineBuf[128];          // Buffer for incoming lines
int lineLen = 0;              // Current line length
bool g_bridgeReady = false;     // Bridge/handshake state
unsigned long g_lastHB = 0;       // Last heartbeat time

// --------- Handshake API (shared pattern for all inodes) ---------
void bridgeHandshakeInit();                 // send initial handshake hello
void bridgeHandshakeOnLine(const char*);    // process a line for handshake
bool bridgeIsReady();                         // query handshake state

// --------- Setup & Loop ---------
void setup() {
  Serial.begin(SERIAL_BAUD);
  // Kick off handshake immediately
  bridgeHandshakeInit();
}

void loop() {
  // Read available serial data into a line buffer
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        if (!bridgeIsReady()) {
          bridgeHandshakeOnLine(lineBuf);
        } else {
          // Bridge is ready; echo the received line for visibility
          Serial.print("BRIDGE-RAW: ");
          Serial.println(lineBuf);
        }
        lineLen = 0;
      }
    } else {
      if (lineLen < (int)sizeof(lineBuf) - 1) lineBuf[lineLen++] = c;
    }
  }

  // After handshake, emit a heartbeat at regular intervals
  if (bridgeIsReady()) {
    unsigned long now = millis();
    if (now - g_lastHB >= HB_INTERVAL) {
      g_lastHB = now;
      Serial.println("HB"); // heartbeat
    }
  }
}

// --------- Handshake helpers ---------
void bridgeHandshakeInit() {
  // Announce presence to host
  Serial.println("BRIDGE_HELLO");
}

void bridgeHandshakeOnLine(const char* line) {
  // Only process handshake pre-Ready. Any post-ready lines are ignored here.
  if (!g_bridgeReady) {
    if (strcmp(line, "BRIDGE_HELLO_ACK") == 0 ||
        strcmp(line, "BRIDGE_HANDSHAKE_OK") == 0) {
      g_bridgeReady = true;
      Serial.println("BRIDGE_READY"); // acknowledge bridge readiness
      g_lastHB = millis();
    } else if (strcmp(line, "HB_ACK") == 0) {
      Serial.println("HB_ACK_RECEIVED");
    } else {
      Serial.println("BRIDGE_WAIT");
    }
  }
}

bool bridgeIsReady() {
  return g_bridgeReady;
}

// --------- End of file ---------
```

### 2. read_dataref.ino
**Example Output ID: DATAREF-READ-EX-002**

Reads dataref messages and saves values to typed variables with full handshake support.

```cpp
/*
  read_dataref.ino
  - Handshake-enabled: reads a dataref message and saves the value to a local variable.
  - Incoming format: DATAREF:<name>:<type>:<value>
  - Supported types: int, float, bool, byte
  - After handshake, the sketch updates internal state and echoes changes.
  - Includes handshake helpers so bridge compatibility is preserved.
  - Example test: send DATAREF:testInt:int:123

  Note: This file includes the bridge handshake helpers (same pattern across inodes).
*/

// --------- Configuration ---------
const int SERIAL_BAUD = 115200;

// --------- Internal state ---------
char lineBuf[128];
int lineLen = 0;

// Stored dataref values
int storedInt = 0;
float storedFloat = 0.0f;
bool storedBool = false;
uint8_t storedByte = 0;

// Bridge/handshake state shared with handshake helpers
bool g_bridgeReady = false;
unsigned long g_lastHB = 0;
const unsigned long HB_INTERVAL = 1000;

// --------- Handshake API (shared pattern) ---------
void bridgeHandshakeInit();
void bridgeHandshakeOnLine(const char* line);
bool bridgeIsReady();

// --------- Helpers: parsing
void handleDatarefLine(const char* line);

void setup() {
  Serial.begin(SERIAL_BAUD);
  bridgeHandshakeInit(); // initiate handshake
  Serial.println("READ_DATAREF_READY"); // local readiness indicator
}

void loop() {
  // Read incoming data
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        if (!bridgeIsReady()) {
          bridgeHandshakeOnLine(lineBuf);
        } else {
          handleDatarefLine(lineBuf);
        }
        lineLen = 0;
      }
    } else {
      if (lineLen < (int)sizeof(lineBuf) - 1) lineLen++;
      lineBuf[lineLen - 1] = c;
    }
  }

  // Heartbeat (optional) once bridge is ready
  if (bridgeIsReady()) {
    unsigned long now = millis();
    if (now - g_lastHB >= HB_INTERVAL) {
      g_lastHB = now;
      Serial.println("HB"); // keep-alive
    }
  }
}

// --------- Handshake helpers (same API across inodes) ---------
void bridgeHandshakeInit() {
  Serial.println("BRIDGE_HELLO");
}

void bridgeHandshakeOnLine(const char* line) {
  if (!g_bridgeReady) {
    if (strcmp(line, "BRIDGE_HELLO_ACK") == 0 ||
        strcmp(line, "BRIDGE_HANDSHAKE_OK") == 0) {
      g_bridgeReady = true;
      Serial.println("BRIDGE_READY");
      g_lastHB = millis();
    } else {
      Serial.println("BRIDGE_WAIT");
    }
  }
}

bool bridgeIsReady() {
  return g_bridgeReady;
}

// --------- Dataref parsing ---------
void handleDatarefLine(const char* line) {
  // Expect: DATAREF:<name>:<type>:<value>
  if (strncmp(line, "DATAREF:", 8) != 0) {
    Serial.print("UNRECOGNIZED: ");
    Serial.println(line);
    return;
  }
  char tail[120];
  strncpy(tail, line + 8, sizeof(tail) - 1);
  tail[sizeof(tail) - 1] = '\0';

  // Tokenize: name:type:value
  char* token = strtok(tail, ":");
  if (!token) return;
  const char* name = token;

  token = strtok(NULL, ":");
  if (!token) return;
  const char* type = token;

  token = strtok(NULL, "");
  if (!token) return;
  const char* value = token;

  if (strcmp(type, "int") == 0) {
    storedInt = atoi(value);
    Serial.print("READ int ");
    Serial.print(name);
    Serial.print(" = ");
    Serial.println(storedInt);
  } else if (strcmp(type, "float") == 0) {
    storedFloat = atof(value);
    Serial.print("READ float ");
    Serial.print(name);
    Serial.print(" = ");
    Serial.println(storedFloat, 6);
  } else if (strcmp(type, "bool") == 0) {
    storedBool = (strcmp(value, "1") == 0 || strcmp(value, "true") == 0);
    Serial.print("READ bool ");
    Serial.print(name);
    Serial.print(" = ");
    Serial.println(storedBool ? "true" : "false");
  } else if (strcmp(type, "byte") == 0) {
    storedByte = (uint8_t)strtol(value, NULL, 10);
    Serial.print("READ byte ");
    Serial.print(name);
    Serial.print(" = ");
    Serial.println(storedByte);
  } else {
    Serial.print("UNKNOWN TYPE ");
    Serial.println(type);
  }
}
```

### 3. write_dataref.ino
**Example Output ID: DATAREF-WRITE-EX-003**

Periodically writes dataref values to the host, demonstrating outbound communication.

```cpp
/*
  write_dataref.ino
  - After handshake, periodically writes dataref values to the host.
  - Outbound messages look like: DATAREF:<name>:<type>:<value>
  - Demonstrates host-originated dataref writing without host-side interpretation.
  - Includes handshake helpers for bridge compatibility.

  Tests: you should see hostCounter, hostVoltage, hostArmed, hostStatus every interval.
*/

// --------- Configuration ---------
const int SERIAL_BAUD = 115200;
const unsigned long SEND_INTERVAL = 2000; // 2 seconds

// --------- Demo values to publish ---------
int demoInt = 0;
float demoFloat = 0.0f;
bool  demoBool = false;
uint8_t demoByte = 0;

// Bridge/handshake state
bool g_bridgeReady = false;
unsigned long g_lastSend = 0;

// --------- Handshake API (shared pattern) ---------
void bridgeHandshakeInit();
void bridgeHandshakeOnLine(const char* line);
bool bridgeIsReady();

// --------- Publish helpers ---------
void publishInt(const char* name, int val);
void publishFloat(const char* name, float val);
void publishBool(const char* name, bool val);
void publishByte(const char* name, uint8_t val);

void setup() {
  Serial.begin(SERIAL_BAUD);
  bridgeHandshakeInit(); // initiate handshake
  Serial.println("WRITE_DATAREF_READY");
}

void loop() {
  // Read handshake lines first if not ready
  while (Serial.available() > 0) {
    static char tmp[128];
    static int tlen = 0;
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (tlen > 0) {
        tmp[tlen] = '\0';
        bridgeHandshakeOnLine(tmp);
        tlen = 0;
      }
    } else {
      if (tlen < (int)sizeof(tmp) - 1) tmp[tlen++] = c;
    }
  }

  if (!bridgeIsReady()) return; // wait for bridge

  // After handshake, publish datarefs on a timer
  unsigned long now = millis();
  if (now - g_lastSend >= SEND_INTERVAL) {
    g_lastSend = now;
    // Increment/demo values to show dynamic changes
    demoInt++;
    demoFloat += 0.15f;
    demoBool = !demoBool;
    demoByte = (demoByte + 1) & 0xFF;

    publishInt("hostCounter", demoInt);
    publishFloat("hostVoltage", demoFloat);
    publishBool("hostArmed", demoBool);
    publishByte("hostStatus", demoByte);
  }
}

// --------- Handshake Helpers (same API across inodes) ---------
void bridgeHandshakeInit() {
  Serial.println("BRIDGE_HELLO");
}

void bridgeHandshakeOnLine(const char* line) {
  if (!g_bridgeReady) {
    if (strcmp(line, "BRIDGE_HELLO_ACK") == 0 ||
        strcmp(line, "BRIDGE_HANDSHAKE_OK") == 0) {
      g_bridgeReady = true;
      Serial.println("BRIDGE_READY");
    } else {
      Serial.println("BRIDGE_WAIT");
    }
  } else {
    // After ready, allow HB_ACK or any other lines to pass
    if (strcmp(line, "HB_ACK") == 0) {
      Serial.println("HB_ACK_RECEIVED");
    } else {
      Serial.print("UNEXPECTED: ");
      Serial.println(line);
    }
  }
}

bool bridgeIsReady() {
  return g_bridgeReady;
}

// --------- Publish helpers ---------
void publishInt(const char* name, int val) {
  Serial.print("DATAREF:");
  Serial.print(name);
  Serial.print(":int:");
  Serial.println(val);
}
void publishFloat(const char* name, float val) {
  Serial.print("DATAREF:");
  Serial.print(name);
  Serial.print(":float:");
  Serial.println(val, 6);
}
void publishBool(const char* name, bool val) {
  Serial.print("DATAREF:");
  Serial.print(name);
  Serial.print(":bool:");
  Serial.println(val ? "1" : "0");
}
void publishByte(const char* name, uint8_t val) {
  Serial.print("DATAREF:");
  Serial.print(name);
  Serial.print(":byte:");
  Serial.println(val);
}
```

### 4. read_write_basic_types.ino
**Example Output ID: BASIC-TYPES-EX-004**

Full bidirectional communication for basic data types with periodic publishing.

```cpp
/*
  read_write_basic_types.ino
  - Handshake-enabled: demonstrates two-way datarefs for int, float, bool, and byte.
  - After handshake, incoming DATAREF:<name>:<type>:<value> updates locals.
  - Periodically publishes current values to the host to test both read and write paths.

  Includes handshake helpers so bridge compatibility is preserved.
*/

// --------- Configuration ---------
const int SERIAL_BAUD = 115200;
const unsigned long PUBLISH_INTERVAL = 3000; // 3 seconds

// --------- Internal state ---------
bool g_bridgeReady = false;
unsigned long g_lastPublish = 0;
unsigned long g_lastHB = 0;
const unsigned long HB_INTERVAL = 1000;

// Datarefs
int curInt = 0;
float curFloat = 0.0f;
bool curBool = false;
uint8_t curByte = 0;

// ---------- Handshake API (shared) ----------
void bridgeHandshakeInit();
void bridgeHandshakeOnLine(const char* line);
bool bridgeIsReady();

// ---------- Helpers ----------
void processDatarefLine(const char* line);

void setup() {
  Serial.begin(SERIAL_BAUD);
  bridgeHandshakeInit();
  Serial.println("BASIC_TYPES_READY");
}

void loop() {
  // Read lines
  static char lineBuf[128];
  static int lineLen = 0;

  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        if (!bridgeIsReady()) {
          bridgeHandshakeOnLine(lineBuf);
        } else {
          processDatarefLine(lineBuf);
        }
        lineLen = 0;
      }
    } else {
      if (lineLen < (int)sizeof(lineBuf) - 1) lineBuf[lineLen++] = c;
    }
  }

  // Periodic publishes after handshake
  if (bridgeIsReady()) {
    unsigned long now = millis();
    if (now - g_lastPublish >= PUBLISH_INTERVAL) {
      g_lastPublish = now;
      Serial.print("DATAREF:demoInt:int:");
      Serial.println(curInt);
      Serial.print("DATAREF:demoFloat:float:");
      Serial.println(curFloat, 6);
      Serial.print("DATAREF:demoBool:bool:");
      Serial.println(curBool ? "1" : "0");
      Serial.print("DATAREF:demoByte:byte:");
      Serial.println(curByte);
    }
  }
}

// --------- Handshake (shared) ----------
void bridgeHandshakeInit() {
  Serial.println("BRIDGE_HELLO");
}
void bridgeHandshakeOnLine(const char* line) {
  if (!g_bridgeReady) {
    if (strcmp(line, "BRIDGE_HELLO_ACK") == 0 ||
        strcmp(line, "BRIDGE_HANDSHAKE_OK") == 0) {
      g_bridgeReady = true;
      Serial.println("BRIDGE_READY");
      g_lastPublish = millis();
    } else {
      Serial.println("BRIDGE_WAIT");
    }
  } else {
    if (strcmp(line, "HB_ACK") == 0) {
      Serial.println("HB_ACK_RECEIVED");
    } else {
      // Handle as a data line if it looks like DATAREF
      processDatarefLine(line);
    }
  }
}
bool bridgeIsReady() { return g_bridgeReady; }

// --------- Data processing ----------
void processDatarefLine(const char* line) {
  // Expect: DATAREF:<name>:<type>:<value>
  if (strncmp(line, "DATAREF:", 8) != 0) {
    Serial.print("UNRECOGNIZED: ");
    Serial.println(line);
    return;
  }
  char tail[120];
  strncpy(tail, line + 8, sizeof(tail) - 1);
  tail[sizeof(tail) - 1] = '\0';
  char* token = strtok(tail, ":");
  if (!token) return;
  const char* name = token;
  token = strtok(NULL, ":"); if (!token) return;
  const char* type = token;
  token = strtok(NULL, ""); if (!token) return;
  const char* value = token;

  if (strcmp(type, "int") == 0) {
    curInt = atoi(value);
  } else if (strcmp(type, "float") == 0) {
    curFloat = atof(value);
  } else if (strcmp(type, "bool") == 0) {
    curBool = (strcmp(value, "1") == 0 || strcmp(value, "true") == 0);
  } else if (strcmp(type, "byte") == 0) {
    curByte = (uint8_t)strtol(value, NULL, 10);
  } else {
    Serial.print("UNKNOWN_TYPE: "); Serial.println(type);
  }

  // Optional echo
  Serial.print("SET ");
  Serial.print(name);
  Serial.print("=");
  if (strcmp(type, "float") == 0) Serial.println(curFloat, 6);
  else if (strcmp(type, "int") == 0) Serial.println(curInt);
  else if (strcmp(type, "bool") == 0) Serial.println(curBool ? "true" : "false");
  else if (strcmp(type, "byte") == 0) Serial.println(curByte);
}
```

### 5. array_dataref.ino
**Example Output ID: ARRAY-DATA-EX-005**

Comprehensive array handling for all basic data types with comma-separated values.

```cpp
/*
  array_dataref.ino
  - Read/write array datarefs for int/float/bool/byte.
  - Incoming format:
      DATAREF:<name>:<type>:<len>:<values>
    Types: intarray, floatarray, boolarray, bytearray
  - Values are comma-separated. Example:
      DATAREF:myIntArray:intarray:4:1,2,3,4
  - Includes bridge handshake helpers (same API).

  Note: For brevity, arrays are fixed at 8 elements max in this demo.
*/

// --------- Configuration ---------
const int SERIAL_BAUD = 115200;

// --------- Arrays (demo) ---------
int intArr[8] = {0};
float floatArr[8] = {0.0f};
bool boolArr[8] = {false};
uint8_t byteArr[8] = {0};

// --------- Handshake state ---------
bool g_bridgeReady = false;
unsigned long g_lastHB = 0;
const unsigned long HB_INTERVAL = 1000;

// --------- Buffers ---------
char lineBuf[256];
int lineLen = 0;

// --------- Handshake APIs (shared) ---------
void bridgeHandshakeInit();
void bridgeHandshakeOnLine(const char* line);
bool bridgeIsReady();

// --------- Core ---------
void processArrayLine(const char* line);

void setup() {
  Serial.begin(SERIAL_BAUD);
  bridgeHandshakeInit();
  Serial.println("ARRAY_DATA_READY");
}

void loop() {
  // Read lines
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        if (!bridgeIsReady()) bridgeHandshakeOnLine(lineBuf);
        else processArrayLine(lineBuf);
        lineLen = 0;
      }
    } else {
      if (lineLen < (int)sizeof(lineBuf) - 1) lineBuf[lineLen++] = c;
    }
  }

  // Heartbeat
  if (bridgeIsReady()) {
    unsigned long now = millis();
    if (now - g_lastHB >= HB_INTERVAL) {
      g_lastHB = now;
      Serial.println("HB");
    }
  }
}

// --------- Handshake (shared) ----------
void bridgeHandshakeInit() { Serial.println("BRIDGE_HELLO"); }
void bridgeHandshakeOnLine(const char* line) {
  if (!g_bridgeReady) {
    if (strcmp(line, "BRIDGE_HELLO_ACK") == 0 ||
        strcmp(line, "BRIDGE_HANDSHAKE_OK") == 0) {
      g_bridgeReady = true;
      Serial.println("BRIDGE_READY");
    } else {
      Serial.println("BRIDGE_WAIT");
    }
  } else {
    if (strcmp(line, "HB_ACK") == 0) {
      Serial.println("HB_ACK_RECEIVED");
    } else {
      Serial.print("UNEXPECTED: "); Serial.println(line);
    }
  }
}
bool bridgeIsReady() { return g_bridgeReady; }

// --------- Array handling ----------
void processArrayLine(const char* line) {
  // DATAREF:<name>:<type>:<len>:<values>
  if (strncmp(line, "DATAREF:", 8) != 0) {
    Serial.print("UNRECOGNIZED: "); Serial.println(line);
    return;
  }
  char tail[240];
  strncpy(tail, line + 8, sizeof(tail) - 1);
  tail[sizeof(tail) - 1] = '\0';

  char* token = strtok(tail, ":");
  if (!token) return;
  const char* name = token;

  token = strtok(NULL, ":"); if (!token) return;
  const char* type = token;

  token = strtok(NULL, ":"); if (!token) return;
  int len = atoi(token);

  token = strtok(NULL, ""); if (!token) return;
  const char* values = token;

  // Tank to fill the appropriate array
  char buf[64];
  strncpy(buf, values, sizeof(buf) - 1);
  buf[sizeof(buf) - 1] = '\0';

  char* v = strtok(buf, ",");
  int idx = 0;
  while (v != NULL && idx < len) {
    if (strcmp(type, "intarray") == 0) intArr[idx] = atoi(v);
    else if (strcmp(type, "floatarray") == 0) floatArr[idx] = atof(v);
    else if (strcmp(type, "boolarray") == 0) boolArr[idx] = (strcmp(v, "1") == 0 || strcmp(v, "true") == 0);
    else if (strcmp(type, "bytearray") == 0) byteArr[idx] = (uint8_t)strtol(v, NULL, 10);
    else {
      Serial.print("UNKNOWN_ARRAY_TYPE: "); Serial.println(type);
      return;
    }
    idx++;
    v = strtok(NULL, ",");
  }

  Serial.print("READ_ARRAY ");
  Serial.print(name);
  Serial.print(" length=");
  Serial.println(len);
}
```

### 6. command_dataref.ino
**Example Output ID: CMD-DATA-EX-006**

Command execution interface for triggering actions and device operations.

```cpp
/*
  command_dataref.ino
  - Demonstrates command-type datarefs: host issues COMMAND:<name>[:<arg>]
  - Device simulates execution and replies with an acknowledgment.
  - Includes handshake helpers for bridge compatibility.
  - Example test: COMMAND:ResetFilters or COMMAND:SetMode:AUTO

  Handshake API is included for bridge compatibility across inodes.
*/

// --------- Configuration ---------
const int SERIAL_BAUD = 115200;

// --------- Handshake state ---------
bool g_bridgeReady = false;

// --------- Handshake API (shared) ---------
void bridgeHandshakeInit();
void bridgeHandshakeOnLine(const char* line);
bool bridgeIsReady();

// --------- Data ---------
char lineBuf[128];
int lineLen = 0;

void setup() {
  Serial.begin(SERIAL_BAUD);
  bridgeHandshakeInit();
  Serial.println("COMMAND_DATAREF_READY");
}

void loop() {
  // Read lines
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        if (!bridgeIsReady()) {
          bridgeHandshakeOnLine(lineBuf);
        } else {
          processCommandLine(lineBuf);
        }
        lineLen = 0;
      }
    } else {
      if (lineLen < (int)sizeof(lineBuf) - 1) lineBuf[lineLen++] = c;
    }
  }
}

// --------- Command processing ----------
void processCommandLine(const char* line) {
  // Expect: COMMAND:<name>[:<arg>]
  if (strncmp(line, "COMMAND:", 8) != 0) {
    Serial.print("UNKNOWN_LINE: "); Serial.println(line);
    return;
  }
  char tail[120];
  strncpy(tail, line + 8, sizeof(tail) - 1);
  tail[sizeof(tail) - 1] = '\0';

  char* name = strtok(tail, ":");
  if (!name) return;
  char* arg = strtok(NULL, "");

  Serial.print("COMMAND_EXECUTED: ");
  Serial.print(name);
  if (arg && strlen(arg) > 0) {
    Serial.print(" ARG=");
    Serial.print(arg);
  }
  Serial.println();
}

// --------- Handshake (shared) ----------
void bridgeHandshakeInit() { Serial.println("BRIDGE_HELLO"); }
void bridgeHandshakeOnLine(const char* line) {
  if (!g_bridgeReady) {
    if (strcmp(line, "BRIDGE_HELLO_ACK") == 0 ||
        strcmp(line, "BRIDGE_HANDSHAKE_OK") == 0) {
      g_bridgeReady = true;
      Serial.println("BRIDGE_READY");
    } else {
      Serial.println("BRIDGE_WAIT");
    }
  } else {
    if (strcmp(line, "HB_ACK") == 0) {
      Serial.println("HB_ACK_RECEIVED");
    }
  }
}
bool bridgeIsReady() { return g_bridgeReady; }
```

### 7. array_elements_read_write.ino
**Example Output ID: ARR-ELEM-EX-007**

Granular array element access supporting both single and bulk operations.

```cpp
/*
  array_elements_read_write.ino
  - Read/write single elements and multiple elements of arrays.
  - Commands:
      SET_ELEMENT:<name>:<type>:<index>:<value>
      SET_ARRAY:<name>:<type>:<len>:<v1>,<v2>,...
  - Types supported: int, float, bool, byte
  - Includes handshake helpers to ensure bridge compatibility across inodes.
*/

// --------- Configuration ---------
const int SERIAL_BAUD = 115200;

// --------- Internal data (demo arrays) ---------
int intArr[8] = {0};
float floatArr[8] = {0.0f};
bool boolArr[8] = {false};
uint8_t byteArr[8] = {0};

// --------- Handshake state ---------
bool g_bridgeReady = false;

// --------- Buffers ---------
char lineBuf[256];
int lineLen = 0;

// --------- Handshake API (shared) ---------
void bridgeHandshakeInit();
void bridgeHandshakeOnLine(const char* line);
bool bridgeIsReady();

// --------- Helpers: element writes ----------
void setArrayElement(const char* name, const char* type, int index, const char* value);
void setArrayBulky(const char* name, const char* type, int len, const char* values);

// --------- Setup & Loop ---------
void setup() {
  Serial.begin(SERIAL_BAUD);
  bridgeHandshakeInit();
  Serial.println("ARR_ELEM_READY");
}

void loop() {
  // Read lines
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        if (!bridgeIsReady()) {
          bridgeHandshakeOnLine(lineBuf);
        } else {
          // Dispatch commands
          if (strncmp(lineBuf, "SET_ELEMENT:", 12) == 0) {
            char tmp[128];
            strncpy(tmp, lineBuf + 12, sizeof(tmp) - 1);
            tmp[sizeof(tmp) - 1] = '\0';
            char* name = strtok(tmp, ":");
            char* type = strtok(NULL, ":");
            char* idxStr = strtok(NULL, ":");
            char* val = strtok(NULL, "");
            int idx = atoi(idxStr);
            // Apply one element set
            if (strcmp(type, "int") == 0) intArr[idx] = atoi(val);
            else if (strcmp(type, "float") == 0) floatArr[idx] = atof(val);
            else if (strcmp(type, "bool") == 0) boolArr[idx] = (strcmp(val, "1") == 0 || strcmp(val, "true") == 0);
            else if (strcmp(type, "byte") == 0) byteArr[idx] = (uint8_t)strtol(val, NULL, 10);
            else {
              Serial.print("UNKNOWN_TYPE: "); Serial.println(type);
            }
            Serial.print("ELEMENT_SET: "); Serial.print(name);
            Serial.print(" idx="); Serial.print(idx);
            Serial.print(" val="); Serial.println(val);
          } else if (strncmp(lineBuf, "SET_ARRAY:", 10) == 0) {
            char tmp[256];
            strncpy(tmp, lineBuf + 10, sizeof(tmp) - 1);
            tmp[sizeof(tmp) - 1] = '\0';
            char* name = strtok(tmp, ":");
            char* type = strtok(NULL, ":");
            char* lenStr = strtok(NULL, ":");
            char* values = strtok(NULL, "");
            int len = atoi(lenStr);
            char buff[256];
            strncpy(buff, values, sizeof(buff) - 1);
            buff[sizeof(buff) - 1] = '\0';
            char* token = strtok(buff, ",");
            int idx = 0;
            while (token != NULL && idx < len) {
              if (strcmp(type, "int") == 0) intArr[idx] = atoi(token);
              else if (strcmp(type, "float") == 0) floatArr[idx] = atof(token);
              else if (strcmp(type, "bool") == 0) boolArr[idx] = (strcmp(token, "1") == 0 || strcmp(token, "true") == 0);
              else if (strcmp(type, "byte") == 0) byteArr[idx] = (uint8_t)strtol(token, NULL, 10);
              token = strtok(NULL, ",");
              idx++;
            }
            Serial.print("ARRAY_SET: "); Serial.print(name);
            Serial.print(" len="); Serial.println(len);
          } else {
            Serial.print("UNKNOWN_COMMAND: "); Serial.println(lineBuf);
          }
        }
        lineLen = 0;
      }
    } else {
      if (lineLen < (int)sizeof(lineBuf) - 1) lineBuf[lineLen++] = c;
    }
  }
}

// --------- Handshake (shared) ----------
void bridgeHandshakeInit() { Serial.println("BRIDGE_HELLO"); }
void bridgeHandshakeOnLine(const char* line) {
  if (!g_bridgeReady) {
    if (strcmp(line, "BRIDGE_HELLO_ACK") == 0 ||
        strcmp(line, "BRIDGE_HANDSHAKE_OK") == 0) {
      g_bridgeReady = true;
      Serial.println("BRIDGE_READY");
    } else {
      Serial.println("BRIDGE_WAIT");
    }
  } else {
    if (strcmp(line, "HB_ACK") == 0) {
      Serial.println("HB_ACK_RECEIVED");
    }
  }
}
bool bridgeIsReady() { return g_bridgeReady; }

// --------- Command helpers ----------
void setArrayElement(const char* name, const char* type, int index, const char* value) {
  Serial.print("SET_ELEMENT:"); Serial.print(name);
  Serial.print(":"); Serial.print(type);
  Serial.print(":"); Serial.print(index);
  Serial.print(":"); Serial.println(value);
}
void setArrayBulky(const char* name, const char* type, int len, const char* values) {
  Serial.print("SET_ARRAY:"); Serial.print(name);
  Serial.print(":"); Serial.print(type);
  Serial.print(":"); Serial.print(len);
  Serial.print(":"); Serial.println(values);
}
```

## Testing and Usage Guide

### Bridge Testing Workflow

All seven sketches include the unified handshake protocol and can be tested using the following approach:

#### 1. Basic Handshake Test (Any Sketch)
1. **Upload** the sketch to your Arduino board
2. **Open Serial Monitor** at 115200 baud, newline ending
3. **Observe**: Device sends `BRIDGE_HELLO` immediately
4. **Send**: `BRIDGE_HELLO_ACK` to complete handshake
5. **Observe**: Device responds with `BRIDGE_READY` and starts heartbeat `HB` every second
6. **Send**: `HB_ACK` to acknowledge heartbeat (optional)
7. **Verify**: Device responds with `HB_ACK_RECEIVED`

#### 2. Dataref Reading Test (`read_dataref.ino` - ID: DATAREF-READ-EX-002)
After handshake, test data parsing:
- **Send**: `DATAREF:testInt:int:123`
- **Observe**: `READ int testInt = 123`
- **Send**: `DATAREF:testFloat:float:12.3456`
- **Observe**: `READ float testFloat = 12.345600`
- **Send**: `DATAREF:testBool:bool:1`
- **Observe**: `READ bool testBool = true`

#### 3. Dataref Writing Test (`write_dataref.ino` - ID: DATAREF-WRITE-EX-003)
After handshake, observe periodic outbound messages:
- **Observe** every 2 seconds:
  - `DATAREF:hostCounter:int:1`
  - `DATAREF:hostVoltage:float:0.150000`
  - `DATAREF:hostArmed:bool:1`
  - `DATAREF:hostStatus:byte:1`

#### 4. Bidirectional Communication Test (`read_write_basic_types.ino` - ID: BASIC-TYPES-EX-004)
After handshake, test both directions:
- **Send**: `DATAREF:demoInt:int:42`
- **Observe**: `SET demoInt=42`
- **Send**: `DATAREF:demoFloat:float:3.14159`
- **Observe**: `SET demoFloat=3.141590`
- **Wait 3 seconds**: Device publishes current values automatically

#### 5. Array Operations Test (`array_dataref.ino` - ID: ARRAY-DATA-EX-005)
After handshake, test array parsing:
- **Send**: `DATAREF:myIntArray:intarray:4:1,2,3,4`
- **Observe**: `READ_ARRAY myIntArray length=4`
- **Send**: `DATAREF:myFloatArray:floatarray:3:1.1,2.2,3.3`
- **Observe**: `READ_ARRAY myFloatArray length=3`

#### 6. Command Execution Test (`command_dataref.ino` - ID: CMD-DATA-EX-006)
After handshake, test command processing:
- **Send**: `COMMAND:ResetFilters`
- **Observe**: `COMMAND_EXECUTED: ResetFilters`
- **Send**: `COMMAND:SetMode:AUTO`
- **Observe**: `COMMAND_EXECUTED: SetMode ARG=AUTO`

#### 7. Granular Array Test (`array_elements_read_write.ino` - ID: ARR-ELEM-EX-007)
After handshake, test element-level operations:
- **Send**: `SET_ELEMENT:myIntArray:int:2:99`
- **Observe**: `ELEMENT_SET: myIntArray idx=2 val=99`
- **Send**: `SET_ARRAY:myIntArray:int:4:7,8,9,10`
- **Observe**: `ARRAY_SET: myIntArray len=4`

### Integration Notes

#### Protocol Design
- **Line-based ASCII**: All messages are newline-terminated for easy parsing
- **Colon delimiters**: Structure: `COMMAND:name:type:value` or `DATAREF:name:type:value`
- **Type safety**: Explicit type tags ensure proper conversion and validation
- **Error handling**: Unknown commands and malformed data generate helpful responses

#### Hardware Compatibility
- **Arduino UNO/Nano**: Use built-in Serial (USB) for testing, consider SoftwareSerial for production
- **Arduino Mega**: Multiple hardware serials allow separation of debug and data channels
- **ESP32/ESP8266**: Native USB support makes testing straightforward; use Serial1/Serial2 for hardware interfaces
- **Teensy**: Multiple serial ports and high performance适合 demanding applications

#### Bridge Integration
- **Automatic discovery**: BRIDGE_HELLO protocol allows host to detect connected devices
- **Health monitoring**: Heartbeat system provides connection status
- **Scalability**: Unified API supports multiple device types simultaneously
- **Extensibility**: New data types and commands can be added without breaking compatibility

#### Performance Considerations
- **Buffer management**: Fixed-size buffers prevent memory exhaustion
- **Non-blocking design**: All operations use millis() timing instead of delay()
- **Error recovery**: Malformed commands are logged but don't crash the system
- **Memory efficiency**: Minimal dynamic allocation for reliable embedded operation

### Common Troubleshooting

#### Handshake Issues
- **No BRIDGE_HELLO**: Check baud rate (115200) and serial monitor settings
- **BRIDGE_WAIT**: Ensure newline termination (LF or CRLF)
- **Missing heartbeat**: Verify bridge completion with BRIDGE_HELLO_ACK

#### Data Parsing Issues
- **UNRECOGNIZED**: Check message format and colon delimiters
- **UNKNOWN TYPE**: Verify supported types (int, float, bool, byte, array variants)
- **No response**: Check buffer sizes and line length limits

#### Array Issues
- **Partial arrays**: Verify comma-separated values and length matching
- **Type mismatch**: Ensure array type matches value types
- **Index errors**: Check array bounds (0-7 in demo sketches)

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

The executable will be created in the `dist/` folder with a custom icon.

## Configuration

- Dataref mappings can be configured through the GUI
- Profiles can be saved and loaded for different aircraft/hardware setups
- Arduino sketches are available in the `Arduino libraries/examples` folder

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms specified in the LICENSE file.

## Comprehensive Guide

This guide provides a descriptive walkthrough of the project's structure, how to test and extend the seven Arduino INO sketches, and how to integrate them with the Python host bridge.

Contents:
- Architecture overview
- Prerequisites
- Quick test workflow (step-by-step)
- Data formats
- Sketch-by-Sketch reference (with Example Output IDs)
- Testing matrix
- Extensibility and customization
- Troubleshooting

1) Architecture Overview

- The X-Plane Dataref Bridge is composed of a Python host and a set of Arduino-based serial bridges.

- The host communicates with Arduinos via Serial, sending and receiving simple, line-delimited messages.

- All Arduino sketches implement a unified handshake API so the host can discover and engage.

2) Quick Test Workflow

- Ensure hardware is connected; PC runs the host application.

- Step-by-step handshake: The device prints BRIDGE_HELLO; the host responds BRIDGE_HELLO_ACK; device prints BRIDGE_READY.

- Heartbeat: After ready, the device issues HB messages at a defined interval.

- Data exchanges: Use DATAREF: messages to set or read values; use COMMAND: for command-type operations.

3) Data Formats

- DATAREF:<name>:<type>:<value> for datarefs.

- DATAREF:<name>:<type>:<len>:<values> for arrays.

- COMMAND:<name>[:<arg>] for commands.

4) Sketch-by-Sketch Reference (with Example Output IDs)

- handshake.ino — HANDSHAKE-EX-001 — Simple handshake with heartbeat.
- read_dataref.ino — DATAREF-READ-EX-002 — Read a dataref and save to variables.
- write_dataref.ino — DATAREF-WRITE-EX-003 — Trigger writes to the host.
- read_write_basic_types.ino — BASIC-TYPES-EX-004 — Read/write int, float, bool, and byte datarefs.
- array_dataref.ino — ARRAY-DATA-EX-005 — Read/write array datarefs for int/float/bool/byte.
- command_dataref.ino — CMD-DATA-EX-006 — Call/execute command-type datarefs.
- array_elements_read_write.ino — ARR-ELEM-EX-007 — Read/write single and multiple array elements.

5) Testing Matrix (for testers)

- For each snippet, provide test steps:
  - 1 handshake: power up, observe BRIDGE_HELLO, reply with BRIDGE_HELLO_ACK, verify BRIDGE_READY, observe HB every second.
  - 2 dataref read: send DATAREF:<name>:<type>:<value>, verify READ outputs.
  - 3 dataref write: observe outbound DATAREF lines.
  - 4 basic types: send/receive int/float/bool/byte datarefs and observe periodic publishes.
  - 5 arrays: send array dataref commands and verify READ_ARRAY logs.
  - 6 commands: send COMMAND:<name>[:<arg>] and observe COMMAND_EXECUTED.
  - 7 array elements: use SET_ELEMENT and SET_ARRAY, observe ELEMENT_SET/ARRAY_SET.

6) Extensibility and Customization

- How to extend with new data types by following existing parsing patterns.
- How to add new commands by following the COMMAND: structure.
- How to adapt message formats for JSON or alternative delimiting.

7) Troubleshooting

- Handshake issues: BRIDGE_WAIT, BRIDGE_READY, etc.
- Data parsing issues: UNRECOGNIZED, UNKNOWN TYPE, etc.
- Array issues: length mismatch, index bounds.

### Quick Start for Developers

1. Connect your Arduino board and ensure serial port access.
2. Run the host project (Python) as described in the main README.
3. Upload one of the Arduino sketches (handshake.ino first).
4. Use the Testing Matrix above to validate functionality.

### Notes

- You can reuse the Bridge Handshake Protocol across all sketches for consistent behavior.
- Adjust baud rate in sketches if needed to match your host application.
- This guide assumes newline-terminated messages for simplicity.
