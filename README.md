# X-Plane Dataref Bridge

A Python-based application that bridges X-Plane flight simulator datarefs to Arduino and HID devices, allowing for custom hardware interfaces and control systems.

## Arduino sketches (included)
- handshake.ino: simple two way handshake over Serial with a heartbeat
- read_dataref.ino: read a dataref message and save to a variable
- write_dataref.ino: trigger writes to the host (dataref writer)
- read_write_basic_types.ino: read and write int, float, bool, and byte datarefs
- array_dataref.ino: read/write array datarefs for int/float/bool/byte
- command_dataref.ino: call/execute command-type datarefs
- array_elements_read_write.ino: read/write single elements and multiple elements of arrays

Code snippets (copy-paste into separate .ino files)
1. handshake.ino
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

2. read_dataref.ino
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
        String rest = line.substring(5).trim();
        int sp = rest.indexOf(' ');
        if (sp > 0) {
          String name = rest.substring(0, sp);
          String type = rest.substring(sp + 1).trim();
          if (name == "sensorA" && type == "float") {
            lastFloat = 12.3456;
            Serial.print("VALUE "); Serial.print(name); Serial.print(" "); Serial.print(type); Serial.print(" "); Serial.println(lastFloat, 6);
          } else if (name == "sensorB" && type == "int") {
            lastInt = 42; Serial.print("VALUE "); Serial.print(name); Serial.print(" "); Serial.print(type); Serial.print(" "); Serial.println(lastInt);
          } else if (name == "flag" && type == "bool") {
            lastBool = true; Serial.print("VALUE "); Serial.print(name); Serial.print(" "); Serial.print(type); Serial.print(" "); Serial.println(lastBool ? 1 : 0);
          } else if (name == "byteA" && type == "byte") {
            lastByte = 0x5A; Serial.print("VALUE "); Serial.print(name); Serial.print(" "); Serial.print(type); Serial.print(" "); Serial.println(lastByte);
          } else {
            Serial.print("UNKNOWN "); Serial.println(name);
          }
        }
      }
      line = "";
    } else {
      line += c;
    }
  }
}

3. write_dataref.ino
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
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("WRITE ")) {
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

          Serial.print("OKWriting "); Serial.print(name); Serial.print(" "); Serial.print(type); Serial.print(" "); Serial.println(valueStr);
        }
      }
    }
  }
}

5. array_dataref.ino
// array_dataref.ino
// Read/write array datarefs for int, float, bool, and byte.
// Copy to a new file named array_dataref.ino

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
      // You can reuse the parsing logic from read/write as needed
      line = "";
    } else {
      line += c;
    }
  }
}

6. command_dataref.ino
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
  if (ledState && (millis() - lastBlink) > 500) {
    lastBlink = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
}

void executeCommand(const String &cmd) {
  if (cmd == "toggleLED") { ledState = !ledState; digitalWrite(LED_PIN, ledState ? HIGH : LOW); }
  else if (cmd == "pulseLED") { for (int i = 0; i < 3; i++) { digitalWrite(LED_PIN, HIGH); delay(100); digitalWrite(LED_PIN, LOW); delay(100);} }
  else if (cmd == "reset") { Serial.println("RESET_CMD_RECEIVED"); }
}

7. array_elements_read_write.ino
// array_elements_read_write.ino
// Read/write array elements and entire arrays.
// Copy to a new file named array_elements_read_write.ino

int arrInt[4] = {0, 0, 0, 0};
float arrFloat[4] = {0.0f, 0.0f, 0.0f, 0.0f};
bool arrBool[4] = {false, false, false, false};
byte arrByte[4] = {0, 0, 0, 0};

void setup() { Serial.begin(115200); }
void loop() { /* omitted for brevity in README excerpt */ }
