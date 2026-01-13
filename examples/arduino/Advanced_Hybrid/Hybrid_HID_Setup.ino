/*
 * X-Plane Dataref Bridge - Hybrid HID + Serial Example
 *
 * -------------------------------------------------------------------------
 * WHAT IS "HYBRID"?
 * -------------------------------------------------------------------------
 * A Hybrid device acts as TWO things at once logic over the SAME USB cable:
 * 1. A USB Serial Device (COM Port) -> For receiving Data from the Bridge.
 * 2. A USB Gamepad/Joystick (HID)   -> For sending Button presses to X-Plane
 * directly.
 *
 * -------------------------------------------------------------------------
 * HARDWARE COMPATIBILITY
 * -------------------------------------------------------------------------
 * 1. AVR: Arduino Leonardo, Pro Micro (ATmega32u4).
 *    -> REQUIREMENT: Install "Joystick" library by MHeironimus in Library
 * Manager.
 *
 * 2. ESP32: ESP32-S2, ESP32-S3 (Native USB).
 *    -> REQUIREMENT: Enable "USB CDC On Boot" in Tools Menu.
 *    -> REQUIREMENT: Use ESP32 Board Manager version 2.0.0 or higher.
 *    -> NOTE: Standard ESP32 (ESP-WROOM-32) does NOT support this (No native
 * USB).
 *
 * -------------------------------------------------------------------------
 */

// ================================================================
// LIBRARIES & DEFINITIONS
// ================================================================

#if defined(ARDUINO_ARCH_AVR)
// AVR (Leonardo/Micro)
#include <Joystick.h>
// Create Joystick: ID 0x03, Joystick Type, 32 Buttons, 0 Hats, X/Y Axis
Joystick_ MyJoystick(0x03, JOYSTICK_TYPE_GAMEPAD, 32, 0, true, true, false,
                     false, false, false, false, false, false, false, false);
const char *BOARD_NAME = "AVR_LEONARDO";

#elif defined(ARDUINO_ARCH_ESP32)
// ESP32-S2 / S3
// Ensure you rely on the built-in USB stack
#include "USB.h"
#include "USBHIDGamepad.h"
USBHIDGamepad MyJoystick;
const char *BOARD_NAME = "ESP32_S2_S3";

#else
#error                                                                         \
    "This sketch only supports boards with Native USB (Leonardo, Micro, ESP32-S2, ESP32-S3)"
#endif

// ================================================================
// CONFIGURATION
// ================================================================

const char *DEVICE_NAME = "HybridPanel_v1";
const int BUTTON_PIN = 2; // Pin for our test button

// ================================================================
// VARIABLES
// ================================================================

String inputBuffer = "";
bool lastButtonState = false;

// ESP32 State Variables
// The ESP32 USBHIDGamepad library requires us to manually track the state
// of all axes and buttons and send them together in a single report.
int8_t espX = 0;
int8_t espY = 0;
int8_t espZ = 0;
int8_t espRz = 0;
int8_t espRx = 0;
int8_t espRy = 0;
uint8_t espHat = 0;      // 0 is centered
uint32_t espButtons = 0; // 32-bit integer to hold button states (bitmask)

// ================================================================
// SETUP
// ================================================================
void setup() {
  // 1. Setup Serial
  Serial.begin(115200);

// 2. Setup Joystick/HID
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.begin();
#elif defined(ARDUINO_ARCH_ESP32)
  MyJoystick.begin();
  USB.begin(); // Ensure USB stack is running
#endif

  // 3. Setup Hardware
  pinMode(BUTTON_PIN, INPUT_PULLUP);
}

// ================================================================
// MAIN LOOP
// ================================================================
void loop() {
  // A. Handle Serial (From Bridge)
  checkSerial();

  // B. Handle Inputs (To Bridge AND To Windows)
  checkInputs();
}

// ================================================================
// INPUT HANDLING
// ================================================================
void checkInputs() {
  // Read Button (Low = Pressed because Pullup)
  bool isPressed = !digitalRead(BUTTON_PIN);

  if (isPressed != lastButtonState) {
    lastButtonState = isPressed;

    // ACTION 1: Update Windows Joystick (HID)

#if defined(ARDUINO_ARCH_AVR)
    // --- AVR LOGIC (Joystick Library) ---
    // The library tracks state internally
    if (isPressed) {
      MyJoystick.press(0);
    } else {
      MyJoystick.release(0);
    }

#elif defined(ARDUINO_ARCH_ESP32)
    // --- ESP32 LOGIC (USBHIDGamepad) ---

    // 1. Update the Button Bitmask
    if (isPressed) {
      // Set Bit 0 (Button 1)
      espButtons |= (1 << 0);
    } else {
      // Clear Bit 0 (Button 1)
      espButtons &= ~(1 << 0);
    }

    // 2. Send the FULL Report
    // We must send X, Y, Z, Rz, Rx, Ry, Hat, and Buttons together.
    // We pass the variables defined at the top of the sketch.
    MyJoystick.send(espX, espY, espZ, espRz, espRx, espRy, espHat, espButtons);
#endif

    // ACTION 2: Send Serial Command to Bridge (Optional!)
    Serial.print("INPUT BTN_TEST ");
    Serial.println(isPressed ? 1 : 0);
  }
}

// ================================================================
// SERIAL PROTOCOL (Parsing)
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
    Serial.print(BOARD_NAME);
    Serial.print(";name=");
    Serial.println(DEVICE_NAME);
  }

  // Example Output handling
  else if (line.startsWith("SET ")) {
    // ... Parsing code from Basic Template ...
  }
}
