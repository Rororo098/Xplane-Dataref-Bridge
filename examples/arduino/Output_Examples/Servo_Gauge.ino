/*
 * X-Plane Dataref Bridge - Servo Gauge Example (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates how to drive a Servo Motor to act as a physical
 * gauge. Perfect for Flap Indicators, RPM Needles, or Speed Brakes.
 *
 * Features:
 * - Maps X-Plane Float (0.0 - 1.0) to Servo Angle (0 - 180).
 * - Clamping: Ensures values stay within safe mechanical limits.
 * - Hybrid-Ready.
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

#include <Servo.h> // Standard Arduino Servo Library

// ================================================================
// 2. CONFIGURATION
// ================================================================

const char *DEVICE_NAME = "FlapsGauge";
String inputBuffer = "";
Servo myServo;

#define SERVO_PIN 9
// Calibrate these angles for your physical needle!
#define SERVO_MIN_ANGLE 0
#define SERVO_MAX_ANGLE 180

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

  myServo.attach(SERVO_PIN);
  myServo.write(SERVO_MIN_ANGLE); // Zero out on startup
}

// ================================================================
// 4. MAIN LOOP the "Input Listener". It’s the part of the sketch that constantly listens for new messages coming from the PC (your Python app).
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
// 5. PROTOCOL & LOGIC
// ================================================================

void processLine(String line) {
  line.trim();

  // Handshake
  if (line == "HELLO") {
    Serial.print("XPDR;fw=1.0;board=");
    Serial.print(BOARD_TYPE);
    Serial.println(";name=FlapsGauge");
  }
  // Data Update
  else if (line.startsWith("SET ")) {
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      String valStr = line.substring(secondSpace + 1);
      float value = valStr.toFloat();

      // Logic: Flaps Position
      if (key == "FLAPS_POS") {
        // 1. Clamp Logic: Ensure value is 0.0 to 1.0
        if (value < 0.0)
          value = 0.0;
        if (value > 1.0)
          value = 1.0;

        // 2. Linear Scaling
        // Angle = Min + (Value * Range)
        int angle = SERVO_MIN_ANGLE +
                    (int)(value * (SERVO_MAX_ANGLE - SERVO_MIN_ANGLE));

        // 3. Move Servo
        myServo.write(angle);
      }
    }
  }
}
