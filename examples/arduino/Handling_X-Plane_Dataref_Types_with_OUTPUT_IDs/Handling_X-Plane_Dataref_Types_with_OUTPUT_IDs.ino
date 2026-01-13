/*

This comprehensive script handles all X-Plane dataref types:

Commands (no value, just execution):

CMD GEAR_TOGGLE - Executes gear toggle command
CMD BEACON_TOGGLE - Executes beacon toggle command
Float datarefs (decimal values):

SET THROTTLE_SETTING 0.75 - Sets float value (0.0-1.0 range)
Int datarefs (integer values):

SET GEAR_POS 1 - Sets integer value (0-1 range)
Bool datarefs (0/1 values):

SET BEACON_LIGHT 1 - Sets boolean value (0=false, 1=true)
Byte arrays (0-255 values):

SET LED_STATE[3] 150 - Sets specific array element
SET LED_STATE_ARRAY 255,128,64,32,0,100,200,50 - Sets entire array
The script uses the same OUTPUT ID system for all data types and properly handles the different value ranges and constraints for each type.

*/

// Arduino Sample Script for Handling All X-Plane Dataref Types with OUTPUT IDs
//
// This script demonstrates:
// - Handling X-Plane commands (no value, just execution)
// - Handling float datarefs (decimal values)
// - Handling int datarefs (integer values) 
// - Handling bool datarefs (0/1 values)
// - Handling byte arrays (0-255 values)
// - Using assigned OUTPUT IDs for communication

#include <Arduino.h>

// Configuration for the Handshake details
const int BAUD_RATE = 115200;
const char* DEVICE_NAME = "MultiTypeDemoDevice";
const char* FW_VERSION = "1.0";
const char* BOARD_TYPE = "ESP32";

// Storage for different data types
float throttle_setting = 0.0;      // Float dataref example
int gear_position = 0;             // Int dataref example (0=up, 1=down)
bool beacon_light = false;         // Bool dataref example (0=false, 1=true)
uint8_t led_states[8] = {0};       // Byte array example

// Pin assignments
const int THROTTLE_PIN = 32;
const int GEAR_PIN = 33;
const int BEACON_PIN = 25;
const int LED_PINS[8] = {2, 4, 5, 12, 13, 14, 15, 16};

// Helper function to parse array index from key like "LED_STATE[3]"
bool parseArrayIndex(String key, String& baseKey, int& index) {
  int bracketStart = key.indexOf('[');
  int bracketEnd = key.indexOf(']', bracketStart);
  
  if (bracketStart != -1 && bracketEnd != -1) {
    baseKey = key.substring(0, bracketStart);
    String indexStr = key.substring(bracketStart + 1, bracketEnd);
    index = indexStr.toInt();
    return true;
  }
  return false;
}

// Handle command type datarefs (no value, just execution)
void handleCommand(String key) {
  bool handled = false;
  
  if (key == "GEAR_TOGGLE") {
    // Execute gear toggle command
    gear_position = !gear_position;  // Toggle between 0 and 1
    digitalWrite(GEAR_PIN, gear_position ? HIGH : LOW);
    Serial.println("STATUS Executed GEAR_TOGGLE command");
    handled = true;
  }
  else if (key == "BEACON_TOGGLE") {
    // Execute beacon toggle command
    beacon_light = !beacon_light;
    digitalWrite(BEACON_PIN, beacon_light ? HIGH : LOW);
    Serial.println("STATUS Executed BEACON_TOGGLE command");
    handled = true;
  }
  
  if (handled) {
    Serial.print("ACK CMD ");
    Serial.println(key);
  } else {
    Serial.print("ERROR Unknown command: ");
    Serial.println(key);
  }
}

// Handle float datarefs
void handleFloatDataref(String key, float value) {
  bool handled = false;
  
  if (key == "THROTTLE_SETTING") {
    throttle_setting = constrain(value, 0.0, 1.0);  // Constrain to 0.0-1.0 range
    // Map 0.0-1.0 to PWM range 0-255
    int pwmValue = (int)(throttle_setting * 255);
    analogWrite(THROTTLE_PIN, pwmValue);
    
    Serial.print("STATUS Updated THROTTLE_SETTING = ");
    Serial.println(throttle_setting, 4);  // 4 decimal places
    handled = true;
  }
  
  if (handled) {
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(value, 4);
  } else {
    Serial.print("ERROR Unknown float dataref: ");
    Serial.println(key);
  }
}

// Handle int datarefs
void handleIntDataref(String key, int value) {
  bool handled = false;
  
  if (key == "GEAR_POS") {
    gear_position = constrain(value, 0, 1);  // Constrain to 0-1 range
    digitalWrite(GEAR_PIN, gear_position ? HIGH : LOW);
    
    Serial.print("STATUS Updated GEAR_POS = ");
    Serial.println(gear_position);
    handled = true;
  }
  
  if (handled) {
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(value);
  } else {
    Serial.print("ERROR Unknown int dataref: ");
    Serial.println(key);
  }
}

// Handle bool datarefs (represented as 0/1 integers)
void handleBoolDataref(String key, int value) {
  bool handled = false;
  
  if (key == "BEACON_LIGHT") {
    beacon_light = (value != 0);  // Convert to boolean
    digitalWrite(BEACON_PIN, beacon_light ? HIGH : LOW);
    
    Serial.print("STATUS Updated BEACON_LIGHT = ");
    Serial.println(beacon_light ? "ON" : "OFF");
    handled = true;
  }
  
  if (handled) {
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(value);
  } else {
    Serial.print("ERROR Unknown bool dataref: ");
    Serial.println(key);
  }
}

// Handle byte array element
void handleByteArrayElement(String baseKey, int index, String valueStr) {
  bool handled = false;
  
  if (baseKey == "LED_STATE") {
    if (index >= 0 && index < 8) {
      int rawValue = valueStr.toInt();
      uint8_t byteValue = constrain(rawValue, 0, 255);  // Constrain to byte range
      led_states[index] = byteValue;
      
      // Update actual hardware
      analogWrite(LED_PINS[index], byteValue);
      
      Serial.print("STATUS Updated LED_STATE[");
      Serial.print(index);
      Serial.print("] = ");
      Serial.print(byteValue);
      Serial.print(" (0x");
      Serial.print(byteValue, HEX);
      Serial.println(")");
      
      handled = true;
    } else {
      Serial.print("ERROR Index out of bounds for LED_STATE: ");
      Serial.println(index);
    }
  }
  
  if (handled) {
    Serial.print("ACK ");
    Serial.print(baseKey);
    Serial.print("[");
    Serial.print(index);
    Serial.print("] ");
    Serial.println(valueStr);
  } else {
    Serial.print("ERROR Unknown array key: ");
    Serial.println(baseKey);
  }
}

// Handle SET command for all data types
void handleSet(String key, String valueStr) {
  // Check if this is a byte array element access (e.g., LED_STATE[3])
  if (key.indexOf('[') != -1 && key.indexOf(']') != -1) {
    String baseKey;
    int index;
    
    if (parseArrayIndex(key, baseKey, index)) {
      handleByteArrayElement(baseKey, index, valueStr);
      return;
  }
  
  // Determine data type based on key pattern or value characteristics
  float floatValue = valueStr.toFloat();
  int intValue = valueStr.toInt();
  
  // Handle different dataref types based on key
  if (key == "THROTTLE_SETTING") {
    handleFloatDataref(key, floatValue);
  }
  else if (key == "GEAR_POS") {
    handleIntDataref(key, intValue);
  }
  else if (key == "BEACON_LIGHT") {
    handleBoolDataref(key, intValue);
  }
  // Handle full byte array updates
  else if (key == "LED_STATE_ARRAY") {
    // Parse comma-separated byte values: "255,128,64,32,0,100,200,50"
    int startIndex = 0;
    int arrayIndex = 0;
    
    for (int i = 0; i <= valueStr.length(); i++) {
      if (i == valueStr.length() || valueStr.charAt(i) == ',') {
        String elementStr = valueStr.substring(startIndex, i);
        if (arrayIndex < 8) {
          int rawValue = elementStr.toInt();
          uint8_t byteValue = constrain(rawValue, 0, 255);  // Constrain to byte range
          led_states[arrayIndex] = byteValue;
          
          // Update hardware
          analogWrite(LED_PINS[arrayIndex], byteValue);
        }
        arrayIndex++;
        startIndex = i + 1;
      }
    }
    
    Serial.print("STATUS Updated LED_STATE array with ");
    Serial.print(arrayIndex);
    Serial.println(" elements");
    
    // Print entire array to serial monitor
    Serial.print("LED_STATE_ARRAY: [");
    for (int i = 0; i < 8; i++) {
      Serial.print(led_states[i]);
      Serial.print("(0x");
      Serial.print(led_states[i], HEX);
      Serial.print(")");
      if (i < 7) Serial.print(", ");
    }
    Serial.println("]");
  }
  else {
    Serial.print("ERROR Unknown dataref key: ");
    Serial.println(key);
  }
}

// Handle GET command to read values
void handleGet(String key) {
  bool handled = false;
  
  // Check if this is a byte array element read (e.g., GET LED_STATE[3])
  if (key.indexOf('[') != -1 && key.indexOf(']') != -1) {
    String baseKey;
    int index;
    
    if (parseArrayIndex(key, baseKey, index)) {
      if (baseKey == "LED_STATE" && index >= 0 && index < 8) {
        Serial.print("VALUE ");
        Serial.print(key);
        Serial.print(" ");
        Serial.print(led_states[index]);
        Serial.print(" (0x");
        Serial.print(led_states[index], HEX);
        Serial.println(")");
        handled = true;
      }
    }
  }
  
  // Handle full byte array read
  else if (key == "LED_STATE_ARRAY") {
    Serial.print("ARRAY LED_STATE: [");
    for (int i = 0; i < 8; i++) {
      Serial.print(led_states[i]);
      Serial.print("(0x");
      Serial.print(led_states[i], HEX);
      Serial.print(")");
      if (i < 7) Serial.print(", ");
    }
    Serial.println("]");
    handled = true;
  }
  // Handle single value reads
  else if (key == "THROTTLE_SETTING") {
    Serial.print("VALUE THROTTLE_SETTING ");
    Serial.println(throttle_setting, 4);
    handled = true;
  }
  else if (key == "GEAR_POS") {
    Serial.print("VALUE GEAR_POS ");
    Serial.println(gear_position);
    handled = true;
  }
  else if (key == "BEACON_LIGHT") {
    Serial.print("VALUE BEACON_LIGHT ");
    Serial.println(beacon_light ? 1 : 0);
    handled = true;
  }
  
  if (!handled) {
    Serial.print("ERROR Unknown key: ");
    Serial.println(key);
  }
}

// Protocol handler
void processLine(String line) {
  line.trim();
  
  // Handshake
  if (line == "HELLO") {
    Serial.print("XPDR;fw=");
    Serial.print(FW_VERSION);
    Serial.print(";board=");
    Serial.print(BOARD_TYPE);
    Serial.print(";name=");
    Serial.println(DEVICE_NAME);
  }
  // Command execution (no value)
  else if (line.startsWith("CMD ")) {
    String key = line.substring(4);
    handleCommand(key);
  }
  // Dataref updates (with value)
  else if (line.startsWith("SET ")) {
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');
    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      String valueStr = line.substring(secondSpace + 1);
      handleSet(key, valueStr);
    }
  }
  // Dataref reads
  else if (line.startsWith("GET ")) {
    String key = line.substring(4);
    handleGet(key);
  }
  // Debug: Print all values
  else if (line == "PRINT_ALL") {
    Serial.println("=== CURRENT VALUES ===");
    Serial.print("THROTTLE_SETTING: ");
    Serial.println(throttle_setting, 4);
    Serial.print("GEAR_POS: ");
    Serial.println(gear_position);
    Serial.print("BEACON_LIGHT: ");
    Serial.println(beacon_light ? "ON" : "OFF");
    Serial.print("LED_STATE_ARRAY: [");
    for (int i = 0; i < 8; i++) {
      Serial.print(led_states[i]);
      if (i < 7) Serial.print(", ");
    }
    Serial.println("]");
    Serial.println("=====================");
  }
  else {
    Serial.print("STATUS Echo: ");
    Serial.println(line);
  }
}

void setup() {
  Serial.begin(BAUD_RATE);
  Serial.println("Multi-Type Demo Device Ready - Send HELLO to begin");
  
  // Initialize pins
  pinMode(THROTTLE_PIN, OUTPUT);
  pinMode(GEAR_PIN, OUTPUT);
  pinMode(BEACON_PIN, OUTPUT);
  
  for (int i = 0; i < 8; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    led_states[i] = 0;
    analogWrite(LED_PINS[i], 0);
  }
  
  Serial.println("Initialized pins for multi-type dataref demonstration");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    processLine(line);
  }
}