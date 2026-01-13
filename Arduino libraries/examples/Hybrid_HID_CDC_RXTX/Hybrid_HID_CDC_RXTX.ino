/*
 * ESP32-S2 Enhanced Hybrid Test V3
 *
 * Target: Landing Lights & Beacon Test with bidirectional communication
 * 1. HID: Auto-presses Button 1 (for Landing Lights) & Button 2 (for Beacon)
 * 2. Serial: Listens for "LDG", "BCN", "DREF", and "CMD" commands
 * 3. Serial: Can send "DREF" and "CMD" commands back to PC
 */

#ifndef ARDUINO_USB_MODE
#error Select "USB-OTG (TinyUSB)" in Tools->USB Mode
#endif

#include "USB.h"
#include "USBHIDGamepad.h"
#include "USBCDC.h"

#define FIRMWARE_VERSION "Enhanced 3.0"
#define DEVICE_NAME "EnhancedController"
#define BOARD_TYPE "ESP32S2"

#ifndef LED_BUILTIN
  #define LED_BUILTIN 15
#endif

USBHIDGamepad Gamepad;
String inputBuffer = "";
unsigned long lastUpdate = 0;
int counter = 0;

// Simulated button states
bool landingLightPressed = false;
bool beaconPressed = false;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.begin(115200);
  Gamepad.begin();
  USB.begin();

  // Wait for USB
  delay(2000);
  Serial.println("READY");
  
  // Example: Send a DREF command to PC when device starts
  Serial.println("DREF sim/operation/failed_sim 0.0");  // Indicate system is operational
}

void loop() {
  // 1. Read Serial (PC -> ESP32)
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

  // 2. Simulate HID Inputs (ESP32 -> PC) - only for demonstration
  if (millis() - lastUpdate > 1000) { // 1Hz update for demo
    lastUpdate = millis();
    counter++;

    // Toggle Button 1 every 4 seconds (Landing Lights Toggle)
    // Press for 200ms
    bool btn1_press = (counter % 40) < 2;

    // Toggle Button 2 every 2 seconds (Beacon Toggle)
    bool btn2_press = (counter % 20) < 2;

    if (counter % 40 == 0) Serial.println("LOG: Pressing Landing Light Button");
    if (counter % 20 == 0) Serial.println("LOG: Pressing Beacon Button");

    // Send Report
    uint32_t buttons = 0;
    if (btn1_press) buttons |= (1 << 0);
    if (btn2_press) buttons |= (1 << 1);

    Gamepad.send(0, 0, 0, 0, 0, 0, 0, buttons);

    // Every 10 seconds, send a sample DREF command back to PC
    if (counter % 10 == 0) {
      Serial.println("DREF sim/operation/failed_sim 0.0");  // System operational
    }
  }
}

void processCommand(String cmd) {
  cmd.trim();

  if (cmd == "HELLO") {
    Serial.print("XPDR;fw="); Serial.print(FIRMWARE_VERSION);
    Serial.print(";board="); Serial.print(BOARD_TYPE);
    Serial.print(";name="); Serial.println(DEVICE_NAME);
  }
  else if (cmd.startsWith("SET ")) {
    int firstSpace = cmd.indexOf(' ', 4);
    if (firstSpace > 0) {
      String key = cmd.substring(4, firstSpace);
      float value = cmd.substring(firstSpace + 1).toFloat();
      bool state = (value > 0.5);

      if (key == "LDG") {
        Serial.print("LOG: Landing Lights are "); Serial.println(state ? "ON" : "OFF");
        digitalWrite(LED_BUILTIN, state ? HIGH : LOW); // Sync LED with Landing Lights
        Serial.print("ACK LDG "); Serial.println(value);
      }
      else if (key == "BCN") {
        Serial.print("LOG: Beacon is "); Serial.println(state ? "ON" : "OFF");
        Serial.print("ACK BCN "); Serial.println(value);
      }
    }
  }
  else if (cmd.startsWith("DREF ")) {
    // Handle DREF command from PC
    // Format: DREF sim/dataref_name value
    int firstSpace = cmd.indexOf(' ', 5); // After "DREF "
    if (firstSpace > 0) {
      String datarefPart = cmd.substring(5); // Everything after "DREF "
      int lastSpace = datarefPart.lastIndexOf(' ');
      if (lastSpace > 0) {
        String dataref = datarefPart.substring(0, lastSpace);
        float value = datarefPart.substring(lastSpace + 1).toFloat();
        
        Serial.print("LOG: Received DREF command - "); 
        Serial.print(dataref); 
        Serial.print(" = "); 
        Serial.println(value);
        
        // Here you could update local state based on the dataref
        if (dataref == "sim/lights/landing_lights_on") {
          // Update local landing light state
          landingLightPressed = (value > 0.5);
        } else if (dataref == "sim/lights/beacon_lights_on") {
          // Update local beacon state
          beaconPressed = (value > 0.5);
        }
        
        Serial.print("ACK DREF "); Serial.print(dataref); Serial.print(" "); Serial.println(value);
      }
    }
  }
  else if (cmd.startsWith("CMD ")) {
    // Handle CMD command from PC
    // Format: CMD sim/command_name
    String command = cmd.substring(4); // Everything after "CMD "
    
    Serial.print("LOG: Received CMD command - "); 
    Serial.println(command);
    
    // Process specific commands
    if (command == "sim/lights/landing_lights_toggle") {
      // Toggle landing lights locally
      landingLightPressed = !landingLightPressed;
      Serial.println("LOG: Toggling landing lights locally");
    } else if (command == "sim/lights/beacon_lights_toggle") {
      // Toggle beacon lights locally
      beaconPressed = !beaconPressed;
      Serial.println("LOG: Toggling beacon lights locally");
    }
    
    Serial.print("ACK CMD "); Serial.println(command);
  }
  else {
    Serial.print("UNKNOWN: "); Serial.println(cmd);
  }
}