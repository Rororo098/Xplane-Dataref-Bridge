/*
 * X-Plane Dataref Bridge - Relay Control Example (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates how to switch high-current loads (Fans, Cockpit
 * Lighting) using a Relay Module.
 *
 * Features:
 * - Active Low Logic Support: Many Relay modules trigger on LOW (Ground).
 * - Safety: Relays often control higher voltages. BE CAREFUL.
 * - Hybrid-Ready: Compiles cleanly on ESP32-S2/S3.
 * =========================================================================
 */

// ================================================================
// 1. LIBRARIES & DEFINITIONS
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

const char *DEVICE_NAME = "CockpitPower";
String inputBuffer = "";

// Relay Connection
#define RELAY_PIN 8

// IMPORTANT: Most cheap relay modules are "Active LOW".
// This means writing LOW (0) turns them ON, and HIGH (1) turns them OFF.
// Set this to 'true' if your relay works this way.
const bool RELAY_ACTIVE_LOW = true;

// ================================================================
// 3. SETUP
// ================================================================
void setup() {
  Serial.begin(115200);

// Initialize HID (Architecture Specific)
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.begin();
#elif defined(ARDUINO_ARCH_ESP32)
  MyJoystick.begin();
  USB.begin();
#endif

  pinMode(RELAY_PIN, OUTPUT);

  // Initialize to OFF state immediately
  setRelay(false);
}

// ================================================================
// 4. MAIN LOOP
// ================================================================
void loop() {
  // Listen for serial commands
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
// 5. PROTOCOL & LOGIC
// ================================================================

void processLine(String line) {
  line.trim();

  // Handshake
  if (line == "HELLO") {
    Serial.print("XPDR;fw=1.0;board=");
    Serial.print(BOARD_TYPE);
    Serial.println(";name=CockpitRelay");
  }
  // Data Update
  else if (line.startsWith("SET ")) {
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      // float value = line.substring(secondSpace + 1).toFloat(); // One-liner
      String valStr = line.substring(secondSpace + 1);
      float value = valStr.toFloat();

      handleUpdate(key, value);
    }
  }
}

void handleUpdate(String key, float value) {
  // Example 1: Bus Voltage triggers relay (Under-voltage protection simulator?)
  // Or simply: If Bus Volts > 24, Relay ON.
  if (key == "BUS_VOLTS") {
    setRelay(value > 24.0);
  }

  // Example 2: Cabin Fan Control
  else if (key == "CABIN_FAN") {
    setRelay(value > 0.5);
  }
}

// ================================================================
// 6. HELPER FUNCTIONS
// ================================================================

// Handles the Active Low / Active High logic in one place
void setRelay(bool on) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(RELAY_PIN, on ? LOW : HIGH); // Inverted
  } else {
    digitalWrite(RELAY_PIN, on ? HIGH : LOW); // Normal
  }
}
