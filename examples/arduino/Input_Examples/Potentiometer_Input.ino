/*
 * X-Plane Dataref Bridge - Potentiometer Example (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates how to read an analog potentiometer (slide or
 * rotary). Useful for Throttles, Mixtures, Flap levers, or Volume knobs.
 *
 * Features:
 * - Analog Reading: Reads 0-1023 or 0-4095 depending on board.
 * - Noise Filtering: Ignores tiny changes (jitter) using a Threshold.
 * - Normalization: Sends a clean 0.0 to 1.0 float to the PC.
 * - Hybrid: Moves a Joystick Axis (-127 to +127) simultaneously.
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

// Which Analog Pin is the wiper connected to?
#define POT_PIN A0

// Name of the input to send to the Serial Bridge
#define POT_NAME "THROTTLE_AXIS"

// Jitter Threshold:
// Analog sensors are noisy. We only send an update if the value changes
// by more than this amount. (e.g. 3 out of 1023 is ~0.3% noise margin)
const int THRESHOLD = 3;

// ================================================================
// 3. VARIABLES
// ================================================================

int lastAnalogValue = 0; // Stores the previous raw reading
String inputBuffer = ""; // Serial buffer

// ESP32 HID
int8_t espX = 0, espY = 0;
uint32_t espButtons = 0;

// ================================================================
// 4. SETUP
// ================================================================
void setup() {
  Serial.begin(115200);

#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.begin();
  MyJoystick.setXAxisRange(-127,
                           127); // Configure the Axis Range (8-bit signed)
#elif defined(ARDUINO_ARCH_ESP32)
  MyJoystick.begin();
  USB.begin();
#endif
}

// ================================================================
// 5. MAIN LOOP
// ================================================================
void loop() {
  checkSerial(); // Keep handshake alive
  checkPots();   // Read sensors

  // A small delay helps stabilise ADC readings
  delay(10);
}

// ================================================================
// 6. POTENTIOMETER LOGIC
// ================================================================
void checkPots() {
  // Read the raw voltage (0-1023 on AVR, 0-4095 on ESP32 usually)
  int currentValue = analogRead(POT_PIN);

  // ESP32 ADC is 12-bit (0-4095), AVR is 10-bit (0-1023).
  // For simplicity, let's assume standard Arduino or map accordingly.
  // Ideally, you might want to map(currentValue, 0, 4095, 0, 1023) on ESP32.

  // Check if value changed significantly
  if (abs(currentValue - lastAnalogValue) > THRESHOLD) {
    lastAnalogValue = currentValue;

    // ACTION A: Send to Serial Bridge (Normalized 0.0 - 1.0)
    // We divide by 1023.0 (AVR standard). If ESP32, this might go > 1.0 without
    // mapping. Recommended: Calibrate or Map first.
    float normalized = (float)currentValue / 1023.0;

    Serial.print("INPUT ");
    Serial.print(POT_NAME);
    Serial.print(" ");
    Serial.println(normalized, 4); // Send with 4 decimal places

    // ACTION B: Move Joystick Axis (Hybrid)
    // Standard HID Gamepad axes are often 8-bit (-127 to +127).
    int axisVal = map(currentValue, 0, 1023, -127, 127);

#if defined(ARDUINO_ARCH_AVR)
    MyJoystick.setXAxis(axisVal);
#elif defined(ARDUINO_ARCH_ESP32)
    espX = (int8_t)axisVal; // Cast to 8-bit signed
    // Apply correct axis and send report
    MyJoystick.send(espX, espY, 0, 0, 0, 0, 0, espButtons);
#endif
  }
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
        Serial.print(BOARD_TYPE);
        Serial.println(";name=PotHybrid");
      }
      inputBuffer = "";
    } else if (c != '\r') {
      inputBuffer += c;
    }
  }
}
