/*
 * X-Plane Dataref Bridge - Button Box Example (Hybrid HID + Serial)
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates how to build a physical Button Box.
 * It reads multiple switches/buttons connected to digital pins and:
 * 1. Sends "INPUT" commands to the PC App (for Dataref logic).
 * 2. Presses Joystick Buttons on the PC (Virtual Gamepad).
 *
 * Features:
 * - Debouncing: Prevents one press from registering as multiple clicks.
 * - Hybrid: Works as both a Serial device and a USB Gamepad simultaneously.
 * =========================================================================
 */

// ================================================================
// 1. LIBRARIES & DEFINITIONS
// ================================================================

#if defined(ARDUINO_ARCH_AVR)
#include <Joystick.h>
Joystick_ MyJoystick(0x03, JOYSTICK_TYPE_GAMEPAD, 32, 0, true, true, false,
                     false, false, false, false, false, false, false, false);
const char *BOARD_NAME = "AVR_LEONARDO";

#elif defined(ARDUINO_ARCH_ESP32)
#include "USB.h"
#include "USBHIDGamepad.h"
USBHIDGamepad MyJoystick;
const char *BOARD_NAME = "ESP32_S2_S3";
#else
#error "Native USB Required (Leonardo, Micro, ESP32-S2/S3)"
#endif

// ================================================================
// 2. CONFIGURATION
// ================================================================

// Define the physical pins your buttons are connected to.
// Connect buttons between PIN and GROUND. (We use Internal Pullups).
const int BUTTON_PINS[] = {2, 3, 4, 5};
const int NUM_BUTTONS = 4;

// Define names for the Serial Bridge inputs.
// "SW_GEAR" will show up in the App's mapping list when pressed.
const char *BUTTON_NAMES[] = {
    "SW_GEAR",      // Pin 2
    "BTN_FLAPS_DN", // Pin 3
    "BTN_FLAPS_UP", // Pin 4
    "SW_LIGHTS"     // Pin 5
};

const char *DEVICE_NAME = "HybridButtonBox_v1";

// ================================================================
// 3. VARIABLES
// ================================================================

// Arrays to track the state of each button individually
int lastButtonState[NUM_BUTTONS];
unsigned long lastDebounceTime[NUM_BUTTONS];
const unsigned long DEBOUNCE_DELAY =
    50; // Milliseconds to wait for signal to settle

String inputBuffer = "";

// ESP32 Joystick State
int8_t espX = 0, espY = 0, espZ = 0, espRz = 0, espRx = 0, espRy = 0;
uint8_t espHat = 0;
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

  // Initialize Pins
  for (int i = 0; i < NUM_BUTTONS; i++) {
    // INPUT_PULLUP means:
    // - Default State = HIGH (3.3V/5V)
    // - Pressed State = LOW (Ground)
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);

    // Read initial state so we don't trigger immediately on boot
    lastButtonState[i] = !digitalRead(BUTTON_PINS[i]);
    lastDebounceTime[i] = 0;
  }
}

// ================================================================
// 5. MAIN LOOP
// ================================================================
void loop() {
  checkSerial();  // Listen for Handshakes/Data from PC
  checkButtons(); // Scan physical hardware
}

// ================================================================
// 6. BUTTON LOGIC (The Core)
// ================================================================
void checkButtons() {
  bool stateChanged =
      false; // Flag to track if we need to send a USB Report (ESP32)

  for (int i = 0; i < NUM_BUTTONS; i++) {
    // Invert the reading because Pullup: LOW(0) is Pressed, HIGH(1) is Released
    // We want 1 = Pressed.
    int reading = !digitalRead(BUTTON_PINS[i]);

    // Only act if the physical state has changed from last known state
    if (reading != lastButtonState[i]) {

      // DEBOUNCE CHECK: Has enough time passed since the last change?
      if ((millis() - lastDebounceTime[i]) > DEBOUNCE_DELAY) {

        lastButtonState[i] = reading;   // Update stored state
        lastDebounceTime[i] = millis(); // Reset timer
        stateChanged = true;

        // ACTION A: Send "INPUT" command to Serial Bridge
        // Format: "INPUT SW_GEAR 1"
        Serial.print("INPUT ");
        Serial.print(BUTTON_NAMES[i]);
        Serial.print(" ");
        Serial.println(reading);

        // ACTION B: Update Windows Joystick (HID)
        // This makes the device appear as a gamepad in Windows

#if defined(ARDUINO_ARCH_AVR)
        if (reading)
          MyJoystick.press(i);
        else
          MyJoystick.release(i);

#elif defined(ARDUINO_ARCH_ESP32)
        // For ESP32, we manipulate the bitmask
        if (reading)
          espButtons |= (1 << i); // Set Bit
        else
          espButtons &= ~(1 << i); // Clear Bit
#endif
      }
    }
  }

// Finalize ESP32 Report
// We only send the USB packet if something actually changed to save bandwidth
#if defined(ARDUINO_ARCH_ESP32)
  if (stateChanged) {
    MyJoystick.send(espX, espY, espZ, espRz, espRx, espRy, espHat, espButtons);
  }
#endif
}

// ================================================================
// 7. PROTOCOL HANDLER
// ================================================================
void checkSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (inputBuffer == "HELLO") {
        Serial.print("XPDR;fw=1.0;board=");
        Serial.print(BOARD_NAME);
        Serial.print(";name=");
        Serial.println(DEVICE_NAME);
      }
      inputBuffer = "";
    } else if (c != '\r') {
      inputBuffer += c;
    }
  }
}
