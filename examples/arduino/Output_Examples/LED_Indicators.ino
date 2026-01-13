/*
 * X-Plane Dataref Bridge - LED Indicator Example (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates how to control LEDs based on Data received from
 * X-Plane. Examples: Landing Gear Lights, Flaps indicators, Warning Lights.
 *
 * Features:
 * - Parses "SET" commands from the PC.
 * - Extracts Float values and turns LEDs ON/OFF based on thresholds.
 * - Hybrid-Ready: Includes HID headers so it compiles on ESP32-S2/S3.
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

const char *DEVICE_NAME = "AnnunciatorPanel";
String inputBuffer = "";

// Connect LEDs to these pins + Request (Resistor in series) -> Ground
#define GEAR_LED_PIN 13 // Built-in LED on most boards
#define FLAPS_LED_PIN 12
#define BRAKE_LED_PIN 11

// ================================================================
// 3. SETUP
// ================================================================
void setup() {
  Serial.begin(115200);

// Initialize HID (Even if we don't use inputs, we need this for
// ESP32 S2/S3 to be recognized correctly by the OS)
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.begin();
#elif defined(ARDUINO_ARCH_ESP32)
  MyJoystick.begin();
  USB.begin();
#endif

  pinMode(GEAR_LED_PIN, OUTPUT);
  pinMode(FLAPS_LED_PIN, OUTPUT);
  pinMode(BRAKE_LED_PIN, OUTPUT);
}

// ================================================================
// 4. MAIN LOOP
// ================================================================
void loop() {
  // We only need to listen. Outputs are event-driven by incoming Serial data.
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
// 5. PROTOCOL HANDLER & OUTPUT LOGIC
// ================================================================

void processLine(String line) {
  line.trim();

  // Handshake
  if (line == "HELLO") {
    Serial.print("XPDR;fw=1.0;board=");
    Serial.print(BOARD_TYPE);
    Serial.print(";name=");
    Serial.println(DEVICE_NAME);
  }
  // Data Received: "SET <key> <value>"
  else if (line.startsWith("SET ")) {
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');

    if (firstSpace > 0 && secondSpace > firstSpace) {
      // Extract Key and Value
      String key = line.substring(firstSpace + 1, secondSpace);
      String valStr = line.substring(secondSpace + 1);
      float value = valStr.toFloat();

      handleUpdate(key, value);
    }
  }
}

/*
 * handleUpdate:
 * Matches the 'key' (from Mapping Tab) to a physical action.
 */
void handleUpdate(String key, float value) {

  // Logic 1: Gear Handle Status (0 = Up, 1 = Down)
  if (key == "GEAR_DOWN_IND") {
    // If > 0.9 (mostly fully down), turn ON.
    digitalWrite(GEAR_LED_PIN, (value > 0.9) ? HIGH : LOW);
  }

  // Logic 2: Parking Brake (0 = Off, 1 = On)
  else if (key == "PARKING_BRAKE_IND") {
    digitalWrite(BRAKE_LED_PIN, (value > 0.5) ? HIGH : LOW);
  }

  // Logic 3: Flaps (Any deployment > 1%)
  else if (key == "FLAPS_POS") {
    digitalWrite(FLAPS_LED_PIN, (value > 0.01) ? HIGH : LOW);
  }
}
