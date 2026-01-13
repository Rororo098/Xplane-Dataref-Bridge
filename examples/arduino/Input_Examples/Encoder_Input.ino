/*
 * X-Plane Dataref Bridge - Rotary Encoder Example (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates how to interface a generic rotary encoder (KY-040).
 * Rotary encoders are great for Radio Frequency knobs, autopilot
 * heading/altitude, or GPS inputs.
 *
 * Features:
 * - Decodes Quadrature signals (A and B pulses) to determine direction.
 * - Hybrid: Sends BOTH a Serial command ("INPUT NAV1_KNOB 1") AND
 *           a Joystick Button press (Button 0 or 1).
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

// Pins for the Encoder (KY-040 usually has CLK, DT, SW)
#define CLK_PIN 2 // Clock Signal
#define DT_PIN 3  // Data Signal
#define SW_PIN 4  // Push Button Switch

// Configuration Flag:
// If true, turning the knob will ALSO simulate a Joystick Button click.
// This is useful if you want to map the knob directly in X-Plane's joystick
// menu.
#define USE_HID_FOR_ENCODER true

// ================================================================
// 3. VARIABLES
// ================================================================

int lastStateCLK;        // Tracks the previous state of the Clock pin
String inputBuffer = ""; // Bucket for Serial commands

// ESP32 HID State
int8_t espX = 0, espY = 0;
uint32_t espButtons = 0;

// ================================================================
// 4. SETUP
// ================================================================
void setup() {
  Serial.begin(115200);

// Initialize HID depending on architecture
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.begin();
#elif defined(ARDUINO_ARCH_ESP32)
  MyJoystick.begin();
  USB.begin();
#endif

  // Encoder pins do not usually need Pullups if the module has them,
  // but it's safer to use INPUT for signal pins and PULLUP for the switch.
  pinMode(CLK_PIN, INPUT);
  pinMode(DT_PIN, INPUT);
  pinMode(SW_PIN, INPUT_PULLUP);

  // Read initial state
  lastStateCLK = digitalRead(CLK_PIN);
}

// ================================================================
// 5. MAIN LOOP
// ================================================================
void loop() {
  checkSerial();  // Listen for PC
  checkEncoder(); // Monitor Rotation
  checkButton();  // Monitor Push Switch
}

// ================================================================
// 6. ENCODER ROTATION LOGIC
// ================================================================
void checkEncoder() {
  int currentStateCLK = digitalRead(CLK_PIN);

  // If CLK has changed from LOW to HIGH (Rising Edge), a step has occurred
  if (currentStateCLK != lastStateCLK && currentStateCLK == 1) {

    // Determine Direction:
    // If DT state is different from CLK state, we rely on the Quadrature logic:
    // CW (Clockwise) or CCW (Counter-Clockwise).
    bool cw = (digitalRead(DT_PIN) != currentStateCLK);

    // Values to send
    String key = "NAV1_FREQ_KNOB";
    int val = cw ? 1 : -1;

    // ACTION A: Send to Serial Bridge
    // Result: "INPUT NAV1_FREQ_KNOB 1" (or -1)
    Serial.print("INPUT ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(val);

    // ACTION B: Pulse HID Button (Hybrid Feature)
    if (USE_HID_FOR_ENCODER) {
      // Map CW to Button 0, CCW to Button 1
      int btn = cw ? 0 : 1;
      pulseButton(btn); // Use helper function to "Click" it quickly
    }
  }
  lastStateCLK = currentStateCLK; // Update tracking variable
}

// ================================================================
// 7. PUSH BUTTON LOGIC
// ================================================================
void checkButton() {
  static int lastBtnState = HIGH;
  int btnState = digitalRead(SW_PIN);

  if (btnState != lastBtnState) {
    // Button Pressed (LOW)
    if (btnState == LOW) {
      Serial.println("INPUT NAV1_SW 1");

// Hold Joystick Button 2
#if defined(ARDUINO_ARCH_AVR)
      MyJoystick.press(2);
#elif defined(ARDUINO_ARCH_ESP32)
      espButtons |= (1 << 2);
      sendESPReport();
#endif

    }
    // Button Released (HIGH)
    else {
      Serial.println("INPUT NAV1_SW 0");

// Release Joystick Button 2
#if defined(ARDUINO_ARCH_AVR)
      MyJoystick.release(2);
#elif defined(ARDUINO_ARCH_ESP32)
      espButtons &= ~(1 << 2);
      sendESPReport();
#endif
    }
    lastBtnState = btnState;
  }
}

// ================================================================
// 8. HELPERS (Pulsing & Reporting)
// ================================================================

/*
 * pulseButton:
 * Simulates a very quick "Press and Release" of a joystick button.
 * Necessary for Encoders because they don't have a "hold" state, just a "tick".
 */
void pulseButton(int btn) {
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.press(btn);
  delay(20); // Hold for 20ms so Windows detects it
  MyJoystick.release(btn);
#elif defined(ARDUINO_ARCH_ESP32)
  espButtons |= (1 << btn);
  sendESPReport();
  delay(20);
  espButtons &= ~(1 << btn);
  sendESPReport();
#endif
}

void sendESPReport() {
#if defined(ARDUINO_ARCH_ESP32)
  MyJoystick.send(espX, espY, 0, 0, 0, 0, 0, espButtons);
#endif
}

// ================================================================
// 9. PROTOCOL HANDLER
// ================================================================
void checkSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (inputBuffer == "HELLO") {
        Serial.print("XPDR;fw=1.0;board=");
        Serial.print(BOARD_TYPE);
        Serial.println(";name=EncoderHybrid");
      }
      inputBuffer = "";
    } else if (c != '\r') {
      inputBuffer += c;
    }
  }
}
