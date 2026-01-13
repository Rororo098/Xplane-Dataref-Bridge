/*
 * X-Plane Dataref Bridge - Hybrid HID + Serial Setup (Documented)
 * =========================================================================
 * DESCRIPTION:
 * This sketch serves as the "Proof of Concept" for the Hybrid Architecture.
 * It combines a Standard Serial Device (for X-Plane parsing) with a
 * Standard USB Gamepad (for Direct Valid Mapping).
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
 *    -> NOTE: Standard ESP32 (ESP-WROOM-32) does NOT support this.
 * =========================================================================
 */

// ================================================================
// 1. LIBRARIES & DEFINITIONS
// ================================================================

#if defined(ARDUINO_ARCH_AVR)
// --- AVR (Leonardo/Micro) ---
#include <Joystick.h>
// Create Joystick: ID 0x03, Joystick Type, 32 Buttons, 0 Hats, X/Y Axis
Joystick_ MyJoystick(0x03, JOYSTICK_TYPE_GAMEPAD, 32, 0, true, true, false,
                     false, false, false, false, false, false, false, false);
const char *BOARD_NAME = "AVR_LEONARDO";

#elif defined(ARDUINO_ARCH_ESP32)
// --- ESP32-S2 / S3 ---
#include "USB.h"
#include "USBHIDGamepad.h"
USBHIDGamepad MyJoystick;
const char *BOARD_NAME = "ESP32_S2_S3";

#else
#error                                                                         \
    "This sketch only supports boards with Native USB (Leonardo, Micro, ESP32-S2, ESP32-S3)"
#endif

// ================================================================
// 2. CONFIGURATION
// ================================================================

const char *DEVICE_NAME = "HybridPanel_v1";
const int BUTTON_PIN = 2; // Pin for our test button

// ================================================================
// 3. VARIABLES
// ================================================================

String inputBuffer = "";
bool lastButtonState = false;

// ESP32 State Variables
// The ESP32 USBHIDGamepad library requires us to manually track the state
// of all axes and buttons and send them together in a single report.
int8_t espX = 0, espY = 0, espZ = 0, espRz = 0, espRx = 0, espRy = 0;
uint8_t espHat = 0;
uint32_t espButtons = 0; // 32-bit integer for 32 buttons

// ================================================================
// 4. SETUP
// ================================================================
void setup() {
  // 1. Setup Serial for X-Plane Bridge
  Serial.begin(115200);

// 2. Setup Joystick/HID for Windows Gamepad
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
// 5. MAIN LOOP
// ================================================================
void loop() {
  // A. Handle Serial (From Bridge)
  checkSerial();

  // B. Handle Inputs (To Bridge AND To Windows)
  checkInputs();
}

// ================================================================
// 6. INPUT HANDLING
// ================================================================
void checkInputs() {
  // Read Button (Low = Pressed because Pullup)
  bool isPressed = !digitalRead(BUTTON_PIN);

  if (isPressed != lastButtonState) {
    lastButtonState = isPressed;

    // ACTION 1: Update Windows Joystick (HID)

#if defined(ARDUINO_ARCH_AVR)
    // --- AVR LOGIC ---
    if (isPressed)
      MyJoystick.press(0);
    else
      MyJoystick.release(0);

#elif defined(ARDUINO_ARCH_ESP32)
    // --- ESP32 LOGIC ---

    // 1. Update Bitmask
    if (isPressed)
      espButtons |= (1 << 0);
    else
      espButtons &= ~(1 << 0);

    // 2. Send Report
    MyJoystick.send(espX, espY, espZ, espRz, espRx, espRy, espHat, espButtons);
#endif

    // ACTION 2: Send Serial Command to Bridge
    Serial.print("INPUT BTN_TEST ");
    Serial.println(isPressed ? 1 : 0);
  }
}

// ================================================================
// 7. SERIAL PROTOCOL
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
    // ... See Basic Template for parsing logic ...
  }
}