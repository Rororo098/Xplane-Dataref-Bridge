/*
 * ESP32-S2 Hybrid Master
 * 
 * 1. HID Gamepad: Shows in joy.cpl, buttons work.
 * 2. Serial Bridge: Sends DREF writes to X-Plane.
 * 3. Feedback: LED toggles when X-Plane confirms value change.
 */

#ifndef ARDUINO_USB_MODE
#error Select "USB-OTG (TinyUSB)" in Tools->USB Mode
#endif

#include "USB.h"
#include "USBHIDGamepad.h"
#include "USBCDC.h"

// --- Config ---
#define FIRMWARE_VERSION "Hybrid 3.0"
#define DEVICE_NAME "HybridMaster"
#define BOARD_TYPE "ESP32S2"

#ifndef LED_BUILTIN
  #define LED_BUILTIN 15
#endif

// --- Objects ---
USBHIDGamepad Gamepad;
// Note: We use the global 'Serial' which maps to USBCDC in TinyUSB mode

// --- State ---
String inputBuffer = "";
unsigned long lastSim = 0;
bool toggleState = false;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  // 1. Initialize USB Stack (Composite) This block tells Windows "I am a Serial Port". Without this, no COM port appears.


  Gamepad.begin(); 
Serial.begin(115200); // 1. Prepares the buffer
USB.begin();          // 2. Starts the USB hardware (Device appears in Windows)
delay(2000);          // 3. Waits for Windows to install/mount the driver

  Serial.println("READY");
}

void loop() {
  // 1. Handle Serial (From X-Plane)
  if (Serial.available()) {
    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n' || c == '\r') {
        if (inputBuffer.length() > 0) {
          processCommand(inputBuffer);
          inputBuffer = "";
        }
      } else {
        inputBuffer += c;
      }
    }
  }

  // 2. Simulation Loop (Every 3 seconds)
  if (millis() - lastSim > 3000) {
    lastSim = millis();
    toggleState = !toggleState;
    
    // A. Send HID Input (Visual check in joy.cpl)
    uint32_t buttons = 0;
    if (toggleState) {
      buttons |= (1 << 0); // Press Button 1
    }
    // Send the complete HID report
    Gamepad.send(0, 0, 0, 0, 0, 0, 0, buttons);
    
    // B. Send Dataref Write (Actual Control)
    // We force the landing lights to 1 (On) or 0 (Off)
    // Format: DREF <dataref> <value>
    Serial.print("DREF sim/cockpit2/switches/landing_lights_on ");
    Serial.println(toggleState ? "1.0" : "0.0");
    
    Serial.println(toggleState ? "LOG: Setting Lights ON" : "LOG: Setting Lights OFF");
  }
}

void processCommand(String cmd) {
  cmd.trim();
  
/* Handshake  The Handshake (Logical Connection)
This is the most important part. When the Python App connects, 
it immediately sends the text HELLO. 
It waits for a specific reply starting with XPDR. 
If it doesn't get this exact format, it disconnects.
*/
  if (cmd == "HELLO") {
// MUST start with "XPDR"
// MUST contain ";fw=", ";board=", ";name="
    Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
    Serial.print(";board="); Serial.print(BOARD_TYPE);
    Serial.print(";name="); Serial.println(DEVICE_NAME);
  }
  
// Receive Value from X-Plane
  else if (cmd.startsWith("SET ")) {
    int firstSpace = cmd.indexOf(' ', 4);
    if (firstSpace > 0) {
      String key = cmd.substring(4, firstSpace);
      float value = cmd.substring(firstSpace + 1).toFloat();
      
      // If X-Plane confirms the light changed, toggle LED
      if (key == "LDG" || key == "LED") {
        bool isOn = (value > 0.5);
        digitalWrite(LED_BUILTIN, isOn ? HIGH : LOW);
        Serial.print("ACK LDG "); Serial.println(value);
      }
    }
  }
}