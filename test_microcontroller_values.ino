/*
 * Test Microcontroller Firmware for XP11 Dataref Bridge
 * Reads both live values (from X-Plane) and virtual values (written by user/system)
 */

#include <Arduino.h>

// Define pins for outputs
const int LED_LIVE_PIN = 2;      // LED to indicate live values from X-Plane
const int LED_VIRTUAL_PIN = 3;   // LED to indicate virtual values (written values)
const int ANALOG_OUTPUT_PIN = 9; // PWM output for value demonstration

// Variables to store values
float live_gear_value = 0.0;      // Example: gear position from X-Plane
float virtual_gear_value = 0.0;   // Example: gear position written by user
bool live_value_updated = false;
bool virtual_value_updated = false;

#define BOARD_TYPE "ESP32"

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(LED_LIVE_PIN, OUTPUT);
  pinMode(LED_VIRTUAL_PIN, OUTPUT);
  pinMode(ANALOG_OUTPUT_PIN, OUTPUT);
  
  // Turn off LEDs initially
  digitalWrite(LED_LIVE_PIN, LOW);
  digitalWrite(LED_VIRTUAL_PIN, LOW);
  
  Serial.println("Microcontroller ready - waiting for HELLO command");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    processLine(line);
  }
  
  // Update outputs based on values
  updateOutputs();
  
  delay(10); // Small delay to prevent overwhelming the serial buffer
}

void processLine(String line) {
  line.trim();

  // --- HANDSHAKE ---
  if (line == "HELLO") {
    Serial.print("XPDR;fw=1.0;board=");
    Serial.print(BOARD_TYPE);
    Serial.println(";name=FullDemo");
  }
  else if (line.startsWith("SET ")) {
    // Parse SET command: "SET KEY VALUE"
    line.remove(0, 4); // Remove "SET "
    
    int spaceIndex = line.indexOf(' ');
    if (spaceIndex > 0) {
      String key = line.substring(0, spaceIndex);
      String valueStr = line.substring(spaceIndex + 1);
      float value = valueStr.toFloat();
      
      // Handle different keys
      if (key == "GEAR_POS") {
        // Determine if this is a live or virtual value based on source
        // In practice, the PC app would send different indicators
        if (line.indexOf("(LIVE)") >= 0) {
          live_gear_value = value;
          live_value_updated = true;
          handleLiveValue(key, value);
        } else if (line.indexOf("(VIRTUAL)") >= 0) {
          virtual_gear_value = value;
          virtual_value_updated = true;
          handleVirtualValue(key, value);
        } else {
          // Default behavior: treat as live value
          live_gear_value = value;
          live_value_updated = true;
          handleLiveValue(key, value);
        }
      } else if (key == "FLAPS_POS") {
        if (line.indexOf("(LIVE)") >= 0) {
          handleLiveValue(key, value);
        } else if (line.indexOf("(VIRTUAL)") >= 0) {
          handleVirtualValue(key, value);
        } else {
          handleLiveValue(key, value);
        }
      } else {
        // Generic handling for other keys
        if (line.indexOf("(LIVE)") >= 0) {
          handleLiveValue(key, value);
        } else if (line.indexOf("(VIRTUAL)") >= 0) {
          handleVirtualValue(key, value);
        } else {
          handleLiveValue(key, value);
        }
      }
      
      // Send acknowledgment
      Serial.print("ACK ");
      Serial.print(key);
      Serial.print(" ");
      Serial.println(value);
    }
  } else if (line.startsWith("GET_VALUES")) {
    // Return current values for both live and virtual
    Serial.print("LIVE_GEAR:");
    Serial.println(live_gear_value);
    Serial.print("VIRTUAL_GEAR:");
    Serial.println(virtual_gear_value);
  } else if (line.startsWith("INPUT ")) {
    // Handle input from microcontroller (buttons, knobs, etc.)
    // Format: INPUT KEY VALUE
    line.remove(0, 6); // Remove "INPUT "
    
    int spaceIndex = line.indexOf(' ');
    if (spaceIndex > 0) {
      String key = line.substring(0, spaceIndex);
      String valueStr = line.substring(spaceIndex + 1);
      float value = valueStr.toFloat();
      
      // Send to PC application
      Serial.print("INPUT ");
      Serial.print(key);
      Serial.print(" ");
      Serial.println(value);
    }
  } else if (line.startsWith("DREF ")) {
    // Handle DREF command from microcontroller to write to X-Plane
    // Format: DREF sim/dataref_name value
    line.remove(0, 5); // Remove "DREF "
    
    int lastSpaceIndex = line.lastIndexOf(' ');
    if (lastSpaceIndex > 0) {
      String dataref = line.substring(0, lastSpaceIndex);
      String valueStr = line.substring(lastSpaceIndex + 1);
      float value = valueStr.toFloat();
      
      // This would normally be sent back to the PC app to forward to X-Plane
      Serial.print("DREF ");
      Serial.print(dataref);
      Serial.print(" ");
      Serial.println(value);
    }
  } else if (line.startsWith("CMD ")) {
    // Handle CMD command from microcontroller to send command to X-Plane
    // Format: CMD sim/cockpit/switches/...
    line.remove(0, 4); // Remove "CMD "
    
    // This would normally be sent back to the PC app to forward to X-Plane
    Serial.print("CMD ");
    Serial.println(line);
  }
}

void handleLiveValue(String key, float value) {
  Serial.print("Received LIVE value for ");
  Serial.print(key);
  Serial.print(": ");
  Serial.println(value);
  
  // Turn on live LED
  digitalWrite(LED_LIVE_PIN, HIGH);
  digitalWrite(LED_VIRTUAL_PIN, LOW); // Turn off virtual LED
  
  // Update analog output based on value (0-1 range to 0-255 PWM)
  analogWrite(ANALOG_OUTPUT_PIN, (int)(value * 255));
  
  // Process the value based on the key
  if (key == "GEAR_POS") {
    // Example: gear position processing
    Serial.print("Processing GEAR position: ");
    Serial.println(value);
  } else if (key == "FLAPS_POS") {
    // Example: flaps position processing
    Serial.print("Processing FLAPS position: ");
    Serial.println(value);
  }
  
  live_value_updated = true;
}

void handleVirtualValue(String key, float value) {
  Serial.print("Received VIRTUAL value for ");
  Serial.print(key);
  Serial.print(": ");
  Serial.println(value);
  
  // Turn on virtual LED
  digitalWrite(LED_LIVE_PIN, LOW);  // Turn off live LED
  digitalWrite(LED_VIRTUAL_PIN, HIGH);
  
  // Update analog output based on value (0-1 range to 0-255 PWM)
  analogWrite(ANALOG_OUTPUT_PIN, (int)(value * 255));
  
  // Process the value based on the key
  if (key == "GEAR_POS") {
    // Example: gear position processing
    Serial.print("Processing VIRTUAL GEAR position: ");
    Serial.println(value);
  } else if (key == "FLAPS_POS") {
    // Example: flaps position processing
    Serial.print("Processing VIRTUAL FLAPS position: ");
    Serial.println(value);
  }
  
  virtual_value_updated = true;
}

void updateOutputs() {
  // Update outputs based on the most recent value type
  if (live_value_updated) {
    // Flash live LED briefly to indicate activity
    static unsigned long lastLiveFlash = 0;
    if (millis() - lastLiveFlash > 100) {
      digitalWrite(LED_LIVE_PIN, !digitalRead(LED_LIVE_PIN)); // Toggle
      lastLiveFlash = millis();
    }
  }
  
  if (virtual_value_updated) {
    // Flash virtual LED briefly to indicate activity
    static unsigned long lastVirtualFlash = 0;
    if (millis() - lastVirtualFlash > 100) {
      digitalWrite(LED_VIRTUAL_PIN, !digitalRead(LED_VIRTUAL_PIN)); // Toggle
      lastVirtualFlash = millis();
    }
  }
  
  // Reset update flags after a certain time
  static unsigned long lastReset = 0;
  if (millis() - lastReset > 500) {
    if (live_value_updated) {
      digitalWrite(LED_LIVE_PIN, HIGH); // Keep on when live values are active
    } else {
      digitalWrite(LED_LIVE_PIN, LOW);  // Turn off when no live values
    }
    
    if (virtual_value_updated) {
      digitalWrite(LED_VIRTUAL_PIN, HIGH); // Keep on when virtual values are active
    } else {
      digitalWrite(LED_VIRTUAL_PIN, LOW);  // Turn off when no virtual values
    }
    
    live_value_updated = false;
    virtual_value_updated = false;
    lastReset = millis();
  }
}

// Example function to send input back to PC
void sendInput(String key, float value) {
  Serial.print("INPUT ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value);
}