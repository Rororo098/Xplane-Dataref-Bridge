/*
 * X-Plane Dataref Bridge - Full Function Demo (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates ALL features of the Bridge Protocol.
 * It is designed to work with the "Monitor" tab in the Bridge App.
 *
 * Features:
 * 1. LIST: Responds with a list of all supported keys.
 * 2. STATUS: Responds with the current value of all keys.
 * 3. TEST: Runs a visual test sequence (Blinks LED, Sweeps Servo).
 * 4. SET: Accepts data from X-Plane.
 * 5. SEND: You can send "Test" commands from the Monitor input.
 *
 * =========================================================================
 */

// ================================================================
// 1. HYBRID SETUP & LIBRARIES
// ================================================================

#if defined(ARDUINO_ARCH_AVR)
#include <Joystick.h>
#include <Servo.h> // Standard Servo for AVR

Joystick_ MyJoystick(0x03, JOYSTICK_TYPE_GAMEPAD, 32, 0, true, true, false,
                     false, false, false, false, false, false, false, false);
const char *BOARD_TYPE = "AVR";

#elif defined(ARDUINO_ARCH_ESP32)
#include "USB.h"
#include "USBHIDGamepad.h"
#include <ESP32Servo.h> // Special Servo library for ESP32

USBHIDGamepad MyJoystick;
const char *BOARD_TYPE = "ESP32";

#else
const char *BOARD_TYPE = "ARDUINO";
#endif

// ================================================================
// 2. CONFIGURATION
// ================================================================

const char *DEVICE_NAME = "FullFunctionDemo";
String inputBuffer = "";

// Hardware Pins
#define LED_PIN 13  // Built-in LED
// NOTE: On ESP32-S3, GPIO 13 might be connected to JTAG or used by USB.
// If the LED doesn't blink, try pin 2 or check your board pinout.
#define SERVO_PIN 9 // Optional Servo
// #define RELAY_PIN 8   // Optional Relay

Servo myServo;

// Internal State
float gearPos = 0.0;
float testVal = 0.0;

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

  pinMode(LED_PIN, OUTPUT);
  
  // ESP32 Servo library defaults to 50Hz, standard is usually fine
  myServo.attach(SERVO_PIN); 
  myServo.write(0);
}

// ================================================================
// 4. MAIN LOOP
// ================================================================
void loop() {
  if (Serial.available()) {
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
// 5. PROTOCOL & COMMAND HANDLERS
// ================================================================

void processLine(String line) {
  line.trim();

  // --- HANDSHAKE ---
  if (line == "HELLO") {
    Serial.print("XPDR;fw=1.0;board=");
    Serial.print(BOARD_TYPE);
    Serial.println(";name=FullDemo");
  }

  // --- MONITOR COMMANDS ---
  else if (line.equalsIgnoreCase("LIST")) {
    // Reply with available keys
    Serial.println("STATUS Available Keys:");
    Serial.println("STATUS - GEAR (Output: LED + Servo)");
    Serial.println("STATUS - TEST_VAR (Arbitrary Value)");
  } else if (line.equalsIgnoreCase("STATUS")) {
    // Reply with current state
    Serial.print("STATUS [GEAR]: ");
    Serial.println(gearPos);
    Serial.print("STATUS [TEST_VAR]: ");
    Serial.println(testVal);
  } else if (line.equalsIgnoreCase("TEST")) {
    // Run Test Sequence
    Serial.println("STATUS Running Test Sequence...");
    runSelfTest();
    Serial.println("STATUS Test Complete.");
  }

  // --- DATA UPDATES (SET) ---
  else if (line.startsWith("SET ")) {
    handleSet(line);
  }

  // --- GENERIC MESSAGE (from Monitor input) ---
  else {
    // Echo back whatever was sent
    Serial.print("STATUS Echo: ");
    Serial.println(line);
  }
}

void handleSet(String line) {
  // Parsing "SET <key> <value>"
  int firstSpace = line.indexOf(' ');
  int secondSpace = line.lastIndexOf(' ');

  if (firstSpace > 0 && secondSpace > firstSpace) {
    String key = line.substring(firstSpace + 1, secondSpace);
    float value = line.substring(secondSpace + 1).toFloat();

    // Logic
    if (key == "GEAR") {
      gearPos = value;
      digitalWrite(LED_PIN, value > 0.5 ? HIGH : LOW);
      if (myServo.attached()) {
        myServo.write((int)(value * 180)); // 0-180
      }
    } else if (key == "TEST_VAR") {
      testVal = value;
    }

    // Acknowledge receipt (visible in Monitor)
    Serial.print("STATUS Updated ");
    Serial.print(key);
    Serial.print(" = ");
    Serial.println(value);
  }
}

// ================================================================
// 6. HELPER FUNCTIONS
// ================================================================

void runSelfTest() {
  // Blink LED 3 times
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }

  // Sweep Servo
  if (myServo.attached()) {
    myServo.write(180);
    delay(500);
    myServo.write(0);
    delay(500);
  }
}
