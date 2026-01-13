/*
 * X-Plane Dataref Bridge - Serial Debug Monitor
 * =========================================================================
 * DESCRIPTION:
 * This sketch helps you DEBUG inputs from X-Plane.
 * It listens for specific Datarefs (like "GEAR_LED", "FLAPS_POS") and
 * PRINTS the received value back to the PC.
 *
 * HOW TO VIEW THE DATA:
 * Since the Bridge App is using the USB Port, you cannot open the
 * Arduino Serial Monitor at the same time.
 * INSTEAD:
 * 1. Connect this device to the Bridge App.
 * 2. Go to the "Hardware" tab -> Click "Monitor" (or "Logs").
 * 3. You will see "STATUS Received: ..." messages appearing there.
 *
 * =========================================================================
 */

// ================================================================
// 1. HYBRID SETUP (Standard)
// ================================================================

#if defined(ARDUINO_ARCH_AVR)
#include <Joystick.h>
Joystick_ MyJoystick(0x03, JOYSTICK_TYPE_GAMEPAD, 32, 0, true, true, false,
                     false, false, false, false, false, false, false, false);
const char *BOARD_TYPE = "AVR";
#elif defined(ARDUINO_ARCH_ESP32)
#include "USB.h"
#include "USBHIDGamepad.h"
USBHIDGamepad MyJoystick;
const char *BOARD_TYPE = "ESP32";
#else
const char *BOARD_TYPE = "ARDUINO";
#endif

// ================================================================
// 2. CONFIGURATION
// ================================================================

const char *DEVICE_NAME = "DebugMonitor";
String inputBuffer = "";

// ================================================================
// 3. SETUP
// ================================================================
void setup() {
  Serial.begin(115200);

#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.begin();
#elif defined(ARDUINO_ARCH_ESP32)
  MyJoystick.begin();
  USB.begin();
#endif
}

// ================================================================
// 4. MAIN LOOP
// ================================================================
void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      processLine(inputBuffer);
      inputBuffer = "";
    } else if (c != '\r') {
      inputBuffer += c;
    }
  }
}

// ================================================================
// 5. PROTOCOL & DEBUG LOGIC
// ================================================================

void processLine(String line) {
  line.trim();

  // Handshake
  if (line == "HELLO") {
    Serial.print("XPDR;fw=1.0;board=");
    Serial.print(BOARD_TYPE);
    Serial.println(";name=DebugMonitor");
  }

  // Data Update: "SET <key> <value>"
  else if (line.startsWith("SET ")) {
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      String valStr = line.substring(secondSpace + 1);

      // We print it back using the "STATUS" keyword.
      // The Bridge App logs "STATUS" messages to the console/monitor.
      Serial.print("STATUS Received Update -> Key: [");
      Serial.print(key);
      Serial.print("] Value: [");
      Serial.print(valStr);
      Serial.println("]");
    }
  }
}
