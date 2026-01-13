/*
 * X-Plane Dataref Bridge - LCD Display Example (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates how to display textual data from X-Plane on an LCD.
 * Useful for Radio Frequencies, Autopilot Modes, or Speed/Altitude readouts.
 *
 * Requirements:
 * - LiquidCrystal_I2C Library (for 16x2 I2C displays).
 * - I2C Connection (SDA/SCL pins).
 *
 * Features:
 * - Buffer Parsing: Can handle multiple Datarefs ("ALTITUDE", "HEADING").
 * - Hybrid-Ready: Safe to run on ESP32-S2/S3.
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

// UNCOMMENT THIS TO USE LCD
// #include <LiquidCrystal_I2C.h>

// ================================================================
// 2. CONFIGURATION
// ================================================================

const char *DEVICE_NAME = "AutopilotDisp";
String inputBuffer = "";

// Variables to store latest values from Sim
float currentAlt = 0;
float currentHdg = 0;

// LCD Object (Addr 0x27, 16 chars, 2 lines)
// LiquidCrystal_I2C lcd(0x27, 16, 2);

// ================================================================
// 3. SETUP
// ================================================================
void setup() {
  Serial.begin(115200);

// Initialize HID (Hybrid Fix)
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.begin();
#elif defined(ARDUINO_ARCH_ESP32)
  MyJoystick.begin();
  USB.begin();
#endif

  // lcd.init();
  // lcd.backlight();
  // lcd.print("Waiting for Sim...");
}

// ================================================================
// 4. MAIN LOOP
// ================================================================
void loop() {
  checkSerial(); // Update values
  // updateLCD(); // Draw values (Could be done inside checkSerial to save
  // cycles)
}

// ================================================================
// 5. PROTOCOL & LOGIC
// ================================================================

void checkSerial() {
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

void processLine(String line) {
  line.trim();
  // Handshake
  if (line == "HELLO") {
    Serial.print("XPDR;fw=1.0;board=");
    Serial.print(BOARD_TYPE);
    Serial.println(";name=AutopilotDisp");
  }
  // Data Update
  else if (line.startsWith("SET ")) {
    parseSet(line);
  }
}

void parseSet(String line) {
  int firstSpace = line.indexOf(' ');
  int secondSpace = line.lastIndexOf(' ');

  if (firstSpace > 0 && secondSpace > firstSpace) {
    String key = line.substring(firstSpace + 1, secondSpace);
    float value = line.substring(secondSpace + 1).toFloat();

    // Check which value we received and update variable
    if (key == "ALTITUDE") {
      currentAlt = value;
      // Request redraw
      // updateLCD();
    } else if (key == "HEADING") {
      currentHdg = value;
      // Request redraw
      // updateLCD();
    }
  }
}

/*
void updateLCD() {
  lcd.setCursor(0, 0);
  lcd.print("ALT: "); lcd.print(currentAlt, 0);
  lcd.setCursor(0, 1);
  lcd.print("HDG: "); lcd.print(currentHdg, 0);
}
*/
