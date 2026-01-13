/*
 * X-Plane Dataref Bridge - Hybrid Radio Panel Example (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This is an ADVANCED example showing a "Two-Way" device.
 * It simulates a COM/NAV Radio Panel.
 *
 * Features:
 * 1. INPUT: Rotary Encoder changes Frequency (Serial + HID Pulse).
 * 2. INPUT: Swap Button switches Active/Standby freq.
 * 3. OUTPUT: Should display the frequency on a 7-Segment Display (TM1637).
 *    (Commented out by default to avoid missing library errors).
 *
 * Use Case: Building a realistic Flight Sim Radio Stack.
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

// Requires "TM1637" Library by Avishay Orpaz
// #include <TM1637Display.h>

// ================================================================
// 2. CONFIGURATION
// ================================================================

// Pins for Encoder
#define CLK_PIN 2
#define DT_PIN 3
#define SW_PIN 4

// Pins for 7-Segment Display
#define DIO_PIN 5
#define CLK_DISP_PIN 6

const char *DEVICE_NAME = "NavRadio1";
String inputBuffer = "";

// State Tracking
int lastStateCLK;
unsigned long lastDebounce = 0;
float currentFreq = 108.00;

// ESP32 HID
int8_t espX = 0, espY = 0;
uint32_t espButtons = 0;

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

  pinMode(CLK_PIN, INPUT);
  pinMode(DT_PIN, INPUT);
  pinMode(SW_PIN, INPUT_PULLUP);
  lastStateCLK = digitalRead(CLK_PIN);
}

// ================================================================
// 4. MAIN LOOP
// ================================================================
void loop() {
  checkSerial();  // Listen for Frequency Updates coming from Sim
  checkEncoder(); // Listen for User Rotation
}

// ================================================================
// 5. SERIAL PROTOCOL (INCOMING)
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
    Serial.print("XPDR;fw=1.1;board=");
    Serial.print(BOARD_TYPE);
    Serial.println(";name=NavRadio1");
  }
  // Data Update
  else if (line.startsWith("SET ")) {
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      String valStr = line.substring(secondSpace + 1);
      float value = valStr.toFloat();

      // Update local variable
      if (key == "NAV1_FREQ") {
        currentFreq = value;
        // updateDisplay(currentFreq);
      }
    }
  }
}

// ================================================================
// 6. ENCODER LOGIC (INPUT)
// ================================================================

void checkEncoder() {
  int currentStateCLK = digitalRead(CLK_PIN);

  // 1. Rotation Check
  if (currentStateCLK != lastStateCLK && currentStateCLK == 1) {
    // Determine Direction
    int dir = (digitalRead(DT_PIN) != currentStateCLK) ? 1 : -1;

    // ACTION A: Send to Serial Bridge
    // "INPUT NAV1_KNOB 1" (Up) or "-1" (Down)
    Serial.print("INPUT NAV1_KNOB ");
    Serial.println(dir);

    // ACTION B: Hybrid HID Pulse
    // Press Button 0 for Up, Button 1 for Down
    int btn = (dir == 1) ? 0 : 1;

#if defined(ARDUINO_ARCH_AVR)
    MyJoystick.press(btn);
    delay(10);
    MyJoystick.release(btn);
#elif defined(ARDUINO_ARCH_ESP32)
    espButtons |= (1 << btn);
    MyJoystick.send(espX, espY, 0, 0, 0, 0, 0, espButtons);
    delay(10);
    espButtons &= ~(1 << btn);
    MyJoystick.send(espX, espY, 0, 0, 0, 0, 0, espButtons);
#endif
  }
  lastStateCLK = currentStateCLK;

  // 2. Button Check (Frequency Swap)
  if (digitalRead(SW_PIN) == LOW) {
    if (millis() - lastDebounce > 200) {
      Serial.println("INPUT NAV1_SWAP 1");
      lastDebounce = millis();
    }
  }
}
