/*
 * X-Plane Dataref Bridge - Basic Template (Hybrid Ready)
 * =========================================================================
 * DESCRIPTION:
 * This sketch is the starting point for any custom project.
 * It handles the essential "glue" logic:
 * 1. Establishing a Serial Connection with the PC App.
 * 2. initializing the USB HID ("Joystick") capabilities for Hybrid support.
 * 3. Receiving "SET" commands from X-Plane.
 *
 * =========================================================================
 * COMPATIBILITY:
 * - AVR: Arduino Leonardo, Pro Micro (Requires "Joystick" lib)
 * - ESP32: s2/s3 (Requires "USB CDC On Boot" enabled)
 * =========================================================================
 */

// ================================================================
// 1. LIBRARIES & DEFINITIONS (HYBRID FIX)
// ================================================================
// This block selects the correct library based on which board you are using.
// It allows the same code to run on both an Arduino Leonardo and an ESP32-S2.

#if defined(ARDUINO_ARCH_AVR)
// --- AVR BOARDS (Leonardo, Micro) ---
#include <Joystick.h>
// Initializes a Joystick with ID 0x03, Gamepad Type, 32 Buttons, etc.
Joystick_ MyJoystick(0x03, JOYSTICK_TYPE_GAMEPAD, 32, 0, true, true, false,
                     false, false, false, false, false, false, false, false);
const char *BOARD_TYPE = "AVR";

#elif defined(ARDUINO_ARCH_ESP32)
// --- ESP32 S2/S3 ---
// Uses the native USB stack built into the ESP32 core
#include "USB.h"
#include "USBHIDGamepad.h"
USBHIDGamepad MyJoystick;
const char *BOARD_TYPE = "ESP32";
#else
// --- FALLBACK (Uno, Mega) ---
// These boards don't support Native USB HID, so they default to Serial only.
const char *BOARD_TYPE = "ARDUINO";
#endif

// ================================================================
// 2. CONFIGURATION
// ================================================================

// This name text is sent to the PC App during the "handshake".
// It helps you identify which device is which in the "Hardware" tab.
const char *DEVICE_NAME = "MyCustomPanel";

// ================================================================
// 3. VARIABLES
// ================================================================

/*
 * inputBuffer:
 * In the Arduino code, String inputBuffer = ""; is a storage variable used
 * to build up the full command message coming from the PC, character by
 * character.
 *
 * Why is it needed?
 * Serial data arrives one byte (character) at a time. The Arduino doesn't
 * receive the whole word "HELLO" instantly; it gets 'H', then 'E', then 'L',
 * etc.
 *
 * This variable acts like a bucket:
 * - Collects: As characters arrive, they are added to this string.
 * - Waits: It keeps collecting until it sees a "newline" character (\n).
 * - Process & Reset: Once the full line is ready, we read it and clear the
 * bucket.
 */
String inputBuffer = "";

/*
 * ESP32 HID State Variables:
 * The ESP32 USBHIDGamepad library functions differently than the AVR one.
 * It does not have individual 'press' or 'release' functions.
 * Instead, we must maintain the state of ALL buttons and axes in variables,
 * and send them ALL together in a single 'MyJoystick.send()' command.
 */
int8_t espX = 0, espY = 0, espZ = 0, espRz = 0, espRx = 0, espRy = 0;
uint8_t espHat = 0;
uint32_t espButtons = 0; // 32 Bits, each bit represents one button (0-31)

// ================================================================
// 4. SETUP
// ================================================================
void setup() {
  // Start Serial communication at 115200 baud.
  // This matches the baud rate used by the Python Bridge App.
  Serial.begin(115200);

  // Initialize HID Stack (Hybrid Fix)
  // This line is crucial. Without it, the PC might not detect the device
  // properly as a Gamepad, causing the "Hybrid" features to fail.
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.begin();
#elif defined(ARDUINO_ARCH_ESP32)
  MyJoystick.begin();
  USB.begin(); // Starts the internal USB stack on ESP32
#endif

  pinMode(LED_BUILTIN, OUTPUT);
}

// ================================================================
// 5. MAIN LOOP the "Input Listener". It’s the part of the sketch that
// constantly listens for new messages coming from the PC (Listens to Dataref
// output ID and values).
// ================================================================
void loop() {
  // Check if data is available from the PC
  while (
      Serial.available() >
      0) { //"Is there mail in the mailbox?" This checks if the PC has sent any
           //data bytes that are waiting to be read. If yes, it enters the loop.
    char c = (char)Serial.read();

    // If we receive a Newline character, the message is complete.
    if (c == '\n') {
      processLine(inputBuffer); // Act on the message
      inputBuffer = "";         // Clear buffer for next message
    }
    // Ignore Carriage Returns (Windows formatting)
    else if (c != '\r') {
      inputBuffer += c; // Add character to bucket
    }
  }

  // Add your custom input checking functions here
  // checkButtons();
}

// ================================================================
// 6. PROTOCOL HANDLER
// ================================================================

/*
 * processLine:
 * Decodes the text message received from the PC.
 * Supported Commands:
 * - HELLO: PC is asking "Who are you?". We reply with our Name and Board Type.
 * - SET <key> <value>: PC is telling us a Dataref value changed (e.g. Gear
 * LED).
 */
void processLine(String line) {
  line.trim(); // Remove whitespace

  // HANDSHAKE REQUEST
  if (line == "HELLO") {
    Serial.print("XPDR;fw=1.0;board=");
    Serial.print(BOARD_TYPE);
    Serial.print(";name=");
    Serial.println(DEVICE_NAME);

    // Flash LED to show we are connected
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
  }
  // DATA UPDATE
  else if (line.startsWith("SET ")) {
    // Parse format: "SET GEAR_LED 1.0"
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      String valStr = line.substring(secondSpace + 1);
      float value = valStr.toFloat();
      handleUpdate(key, value);
    }
  }
}

/*
 * handleUpdate:
 * This is where YOU write code to act on X-Plane data.
 * The 'key' matches the name you defined in the App's "Mappings" tab.
 */
void handleUpdate(String key, float value) {
  // Example: logical check for a Gear Light
  if (key == "GEAR_LED") {
    digitalWrite(LED_BUILTIN, (value > 0.5) ? HIGH : LOW);
  }
}

// ================================================================
// 7. HELPER FUNCTIONS
// ================================================================

/*
 * pressButton / releaseButton:
 * Wrappers that handle the differences between AVR and ESP32 libraries.
 * Use these instead of calling MyJoystick functions directly.
 */
void pressButton(int btnIndex) {
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.press(btnIndex);
#elif defined(ARDUINO_ARCH_ESP32)
  espButtons |= (1 << btnIndex); // Turn ON bit
  MyJoystick.send(espX, espY, espZ, espRz, espRx, espRy, espHat, espButtons);
#endif
}

void releaseButton(int btnIndex) {
#if defined(ARDUINO_ARCH_AVR)
  MyJoystick.release(btnIndex);
#elif defined(ARDUINO_ARCH_ESP32)
  espButtons &= ~(1 << btnIndex); // Turn OFF bit
  MyJoystick.send(espX, espY, espZ, espRz, espRx, espRy, espHat, espButtons);
#endif
}

void sendCommand(String commandPath) {
  // Sends a "CMD" execution request back to the PC
  Serial.print("CMD ");
  Serial.println(commandPath);
}
