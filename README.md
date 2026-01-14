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

The repository includes seven Arduino sketches demonstrating a serial-based bridge for datarefs. Each file is a standalone example you can drop into the Arduino IDE.

- handshake.ino: simple two way handshake over Serial with a heartbeat
- read_dataref.ino: read a dataref message and save to a variable
- write_dataref.ino: trigger writes to the host (dataref writer)
- read_write_basic_types.ino: read and write int, float, bool, and byte datarefs
- array_dataref.ino: read/write array datarefs for int/float/bool/byte
- command_dataref.ino: call/execute command-type datarefs
- array_elements_read_write.ino: read/write single elements and multiple elements of arrays

## Code snippets (copy-paste into separate .ino files)

### 1. handshake.ino
```cpp
// handshake.ino
// Simple two-way handshake over Serial with heartbeat.
// Copy to a new file named handshake.ino

const unsigned long HANDSHAKE_TIMEOUT = 5000;      // 5 seconds
const unsigned long HEARTBEAT_INTERVAL = 1000;     // 1 second
bool handshakeComplete = false;
unsigned long handshakeStart = 0;
unsigned long lastHeartbeat = 0;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
  while (!Serial) { ; } // wait for serial to be ready on boards like Leonardo/Micro
  Serial.println("XP_HANDSHAKE_REQ");
  handshakeStart = millis();
  digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
  if (!handshakeComplete) {
    // Listen for handshake response
    if (Serial.available()) {
      String line = Serial.readStringUntil('\n');
      line.trim();
      if (line == "XP_HANDSHAKE_RES" || line == "XP_HANDSHAKE_OK" || line == "XP_READY") {
        handshakeComplete = true;
        Serial.println("XP_HANDSHAKE_OK");
        digitalWrite(LED_BUILTIN, HIGH);
      }
    }

    // Timeout fallback: resend request
    if (millis() - handshakeStart > HANDSHAKE_TIMEOUT) {
      Serial.println("XP_HANDSHAKE_REQ");
      handshakeStart = millis();
    }
  } else {
    // Heartbeat after handshake
    if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
      lastHeartbeat = millis();
      Serial.println("HEARTBEAT");
    }
  }
}
```

### 2. read_dataref.ino
```cpp
// read_dataref.ino
// Read a dataref description over Serial and save the value to a local variable.
// Copy to a new file named read_dataref.ino

float lastFloat = 0.0f;
int lastInt = 0;
bool lastBool = false;
byte lastByte = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  static String line = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      if (line.startsWith("READ ")) {
        String rest = line.substring(5);
        rest.trim();
        int sp = rest.indexOf(' ');
        if (sp > 0) {
          String name = rest.substring(0, sp);
          String type = rest.substring(sp + 1);
          type.trim();

          if (name == "sensorA" && type == "float") {
            // Example: host provides the actual value by a separate WRITE path;
            // here we simulate a read
            lastFloat = 12.3456;
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastFloat, 6);
          } else if (name == "sensorB" && type == "int") {
            lastInt = 42;
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastInt);
          } else if (name == "flag" && type == "bool") {
            lastBool = true;
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastBool ? 1 : 0);
          } else if (name == "byteA" && type == "byte") {
            lastByte = 0x5A;
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastByte);
          } else {
            Serial.print("UNKNOWN ");
            Serial.println(name);
          }
        }
      }
      line = "";
    } else {
      line += c;
    }
  }
}
```

### 3. write_dataref.ino
```cpp
// write_dataref.ino
// Send/write datarefs to the host (dataref writer).
// Copy to a new file named write_dataref.ino

const int LED_PIN = LED_BUILTIN;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  Serial.begin(115200);
}

void loop() {
  // Example: act on a simple trigger (porting to a real button would be easy)
  // Here we just respond to serial commands for demonstration.

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("WRITE ")) {
      // Expected format: WRITE <name> <type> <value>
      String rest = line.substring(6);
      rest.trim();
      int sp1 = rest.indexOf(' ');
      if (sp1 > 0) {
        String name = rest.substring(0, sp1);
        String rest2 = rest.substring(sp1 + 1);
        rest2.trim();
        int sp2 = rest2.indexOf(' ');
        if (sp2 > 0) {
          String type = rest2.substring(0, sp2);
          String valueStr = rest2.substring(sp2 + 1);
          valueStr.trim();

          // Demonstrative internal state
          // You would map to actual variables in a real implementation
          Serial.print("OKWriting ");
          Serial.print(name);
          Serial.print(" ");
          Serial.print(type);
          Serial.print(" ");
          Serial.println(valueStr);
        }
      }
    }
  }
}
```

### 4. read_write_basic_types.ino
```cpp
// read_write_basic_types.ino
// Read/write int, float, bool, and byte datarefs.
// Copy to a new file named read_write_basic_types.ino

int dataInt = 0;
float dataFloat = 0.0f;
bool dataBool = false;
byte dataByte = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  static String line = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      processLine(line);
      line = "";
    } else {
      line += c;
    }
  }
}

void processLine(const String &line) {
  if (line.startsWith("READ ")) {
    String rest = line.substring(5);
    rest.trim();
    int sp = rest.indexOf(' ');
    if (sp > 0) {
      String name = rest.substring(0, sp);
      String type = rest.substring(sp + 1);
      type.trim();

      if (name == "counter" && type == "int") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataInt);
      } else if (name == "rate" && type == "float") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataFloat, 6);
      } else if (name == "armed" && type == "bool") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataBool ? 1 : 0);
      } else if (name == "mode" && type == "byte") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println((int)dataByte);
      } else {
        Serial.println("UNKNOWN");
      }
    }
  } else if (line.startsWith("WRITE ")) {
    String rest = line.substring(6);
    rest.trim();
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);
      String rest2 = rest.substring(sp1 + 1);
      rest2.trim();
      int sp2 = rest2.indexOf(' ');
      if (sp2 > 0) {
        String type = rest2.substring(0, sp2);
        String valueStr = rest2.substring(sp2 + 1);
        valueStr.trim();

        if (name == "counter" && type == "int") {
          dataInt = valueStr.toInt();
          Serial.println("OK");
        } else if (name == "rate" && type == "float") {
          dataFloat = valueStr.toFloat();
          Serial.println("OK");
        } else if (name == "armed" && type == "bool") {
          dataBool = (valueStr == "1" || valueStr.equalsIgnoreCase("true"));
          Serial.println("OK");
        } else if (name == "mode" && type == "byte") {
          dataByte = (byte)valueStr.toInt();
          Serial.println("OK");
        } else {
          Serial.println("ERR");
        }
      }
    }
  }
}
```

### 5. array_dataref.ino
```cpp
// array_dataref.ino
// Read/write array datarefs for int, float, bool, and byte.
// Copy to a new file named array_dataref.ino

int arrInt[4]   = {0, 0, 0, 0};
float arrFloat[4] = {0.0f, 0.0f, 0.0f, 0.0f};
bool arrBool[4]  = {false, false, false, false};
byte arrByte[4]  = {0, 0, 0, 0};

void setup() {
  Serial.begin(115200);
}

void loop() {
  static String line = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      processLine(line);
      line = "";
    } else {
      line += c;
    }
  }
}

void printAllInt() {
  Serial.print("ARR_INT: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrInt[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllFloat() {
  Serial.print("ARR_FLOAT: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrFloat[i], 4);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllBool() {
  Serial.print("ARR_BOOL: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrBool[i] ? "1" : "0");
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllByte() {
  Serial.print("ARR_BYTE: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print((int)arrByte[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void processLine(const String &line) {
  if (line.startsWith("READ ")) {
    // Format: READ <name> <type> [index]
    String rest = line.substring(5);
    rest.trim();
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);
      String rest2 = rest.substring(sp1 + 1);
      rest2.trim();
      int sp2 = rest2.indexOf(' ');
      String type;
      String idxStr;
      if (sp2 > 0) {
        type = rest2.substring(0, sp2);
        idxStr = rest2.substring(sp2 + 1);
      } else {
        type = rest2;
        idxStr = "";
      }
      idxStr.trim();

      if (name == "arrInt" && type == "int") {
        if (idxStr.length() > 0) {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrInt ");
          Serial.println(idx >= 0 && idx < 4 ? arrInt[idx] : 0);
        } else {
          printAllInt();
        }
      } else if (name == "arrFloat" && type == "float") {
        if (idxStr.length() > 0) {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrFloat ");
          Serial.println(idx >= 0 && idx < 4 ? arrFloat[idx] : 0.0f, 4);
        } else {
          printAllFloat();
        }
      } else if (name == "arrBool" && type == "bool") {
        if (idxStr.length() > 0) {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrBool ");
          Serial.println((idx >= 0 && idx < 4) ? (arrBool[idx] ? 1 : 0) : 0);
        } else {
          printAllBool();
        }
      } else if (name == "arrByte" && type == "byte") {
        if (idxStr.length() > 0) {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrByte ");
          Serial.println((idx >= 0 && idx < 4) ? (int)arrByte[idx] : 0);
        } else {
          printAllByte();
        }
      }
    }
  } else if (line.startsWith("WRITE ")) {
    // Format: WRITE <name> <type> <index> <value>
    String rest = line.substring(6);
    rest.trim();
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);
      String rest2 = rest.substring(sp1 + 1);
      rest2.trim();
      int sp2 = rest2.indexOf(' ');
      if (sp2 > 0) {
        String type = rest2.substring(0, sp2);
        String rest3 = rest2.substring(sp2 + 1);
        rest3.trim();
        int sp3 = rest3.indexOf(' ');
        if (sp3 > 0) {
          int idx = rest3.substring(0, sp3).toInt();
          String valStr = rest3.substring(sp3 + 1);
          valStr.trim();

          if (name == "arrInt" && type == "int") {
            if (idx >= 0 && idx < 4) arrInt[idx] = valStr.toInt();
          } else if (name == "arrFloat" && type == "float") {
            if (idx >= 0 && idx < 4) arrFloat[idx] = valStr.toFloat();
          } else if (name == "arrBool" && type == "bool") {
            if (idx >= 0 && idx < 4) arrBool[idx] = (valStr == "1" || valStr.equalsIgnoreCase("true"));
          } else if (name == "arrByte" && type == "byte") {
            if (idx >= 0 && idx < 4) arrByte[idx] = (byte)valStr.toInt();
          }
          Serial.println("OK");
        }
      }
    }
  }
}
```

### 6. command_dataref.ino
```cpp
// command_dataref.ino
// Execute command-type datarefs (e.g., toggle LED, reset, etc.)
// Copy to a new file named command_dataref.ino

const int LED_PIN = LED_BUILTIN;
unsigned long lastBlink = 0;
bool ledState = false;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("CMD ")) {
      String cmd = line.substring(4);
      cmd.trim();
      executeCommand(cmd);
      Serial.println("CMD_EXECUTED " + cmd);
    }
  }
  // Optional: keep LED in a visible state
  if (ledState && (millis() - lastBlink) > 500) {
    lastBlink = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
}

void executeCommand(const String &cmd) {
  if (cmd == "toggleLED") {
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
  } else if (cmd == "pulseLED") {
    // quick blink
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
  } else if (cmd == "reset") {
    // A graceful "soft reset" placeholder
    Serial.println("RESET_CMD_RECEIVED");
  }
  // Add more commands as needed
}
```

### 7. array_elements_read_write.ino
```cpp
// array_elements_read_write.ino
// Read/write single elements and multiple elements of dataref arrays.
// Copy to a new file named array_elements_read_write.ino

int arrInt[4] = {0, 0, 0, 0};
float arrFloat[4] = {0.0f, 0.0f, 0.0f, 0.0f};
bool arrBool[4] = {false, false, false, false};
byte arrByte[4] = {0, 0, 0, 0};

void setup() {
  Serial.begin(115200);
}

void loop() {
  static String line = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      processLine(line);
      line = "";
    } else {
      line += c;
    }
  }
}

void printAllInt() {
  Serial.print("arrInt: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrInt[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllFloat() {
  Serial.print("arrFloat: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrFloat[i], 4);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllBool() {
  Serial.print("arrBool: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrBool[i] ? 1 : 0);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllByte() {
  Serial.print("arrByte: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print((int)arrByte[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void processLine(const String &line) {
  if (line.startsWith("READ ")) {
    // Formats:
    // READ arrInt int 0
    // READ arrInt int ALL
    String rest = line.substring(5);
    rest.trim();
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);
      String rest2 = rest.substring(sp1 + 1);
      rest2.trim();

      int sp2 = rest2.indexOf(' ');
      String type;
      String idxStr;
      if (sp2 > 0) {
        type = rest2.substring(0, sp2);
        idxStr = rest2.substring(sp2 + 1);
      } else {
        type = rest2;
        idxStr = "";
      }

      if (name == "arrInt" && type == "int") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllInt();
        } else {
          int idx = idxStr.toInt();
          Serial.println("VALUE arrInt " + String(idx) + " " + String(arrInt[idx]));
        }
      } else if (name == "arrFloat" && type == "float") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllFloat();
        } else {
          int idx = idxStr.toInt();
          Serial.println("VALUE arrFloat " + String(idx) + " " + String(arrFloat[idx], 4));
        }
      } else if (name == "arrBool" && type == "bool") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllBool();
        } else {
          int idx = idxStr.toInt();
          Serial.println("VALUE arrBool " + String(idx) + " " + String(arrBool[idx] ? 1 : 0));
        }
      } else if (name == "arrByte" && type == "byte") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllByte();
        } else {
          int idx = idxStr.toInt();
          Serial.println("VALUE arrByte " + String(idx) + " " + String((int)arrByte[idx]));
        }
      }
    }
  } else if (line.startsWith("WRITE ")) {
    // Formats:
    // WRITE arrInt int 2 7
    String rest = line.substring(6);
    rest.trim();
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);
      String rest2 = rest.substring(sp1 + 1);
      rest2.trim();

      int sp2 = rest2.indexOf(' ');
      if (sp2 > 0) {
        String type = rest2.substring(0, sp2);
        String rest3 = rest2.substring(sp2 + 1);
        rest3.trim();

        int sp3 = rest3.indexOf(' ');
        String idxStr, valStr;
        if (sp3 > 0) {
          idxStr = rest3.substring(0, sp3);
          valStr = rest3.substring(sp3 + 1);
        } else {
          // For non-array writes, idx is not used
          idxStr = "";
          valStr = rest3;
        }

        if (name == "arrInt" && type == "int" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          arrInt[idx] = valStr.toInt();
        } else if (name == "arrFloat" && type == "float" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          arrFloat[idx] = valStr.toFloat();
        } else if (name == "arrBool" && type == "bool" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          arrBool[idx] = (valStr == "1" || valStr.equalsIgnoreCase("true"));
        } else if (name == "arrByte" && type == "byte" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          arrByte[idx] = (byte)valStr.toInt();
        }
        Serial.println("OK");
      }
    }
  }
}
```

## Notes and Guidance

- **Protocols**: The sketches above use a simple ASCII protocol over Serial (115200 baud). They're designed as educational scaffolds to illustrate how to handshake, read/write values, and manipulate arrays and commands in a microcontroller context.
- **DataRefs vs. host**: In a real X-Plane/DataRefs workflow, the host (PC running XP11) typically drives the actual datarefs. The Arduino sketches here demonstrate how you might structure the microcontroller side to receive typed commands from the host, store values in typed variables, and send back values for verification.
- **Extensions**: You can adapt the parsing rules, tokens, and types to match your actual RPC protocol or to match the XPDRB-style protocol you're using.
- **Hardware notes**: If you're using a UNO (single hardware serial), you may want to use a SoftwareSerial port for the Arduino side if you also connect the host via USB. For MEGA or boards with multiple hardware serials, you can map separate Serial1/Serial2 to the data path.

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