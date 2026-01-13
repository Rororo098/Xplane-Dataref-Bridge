// Arduino Sample Script for Handling X-Plane Arrays with OUTPUT IDs
//
// This script demonstrates:
// - Reading arrays and printing to serial monitor
// - Reading specific elements of arrays
// - Writing arrays (full and partial)
// - Using assigned OUTPUT IDs for communication

/*

This Arduino script demonstrates:

Reading arrays and printing to serial monitor:

The PRINT_ARRAY command prints all array elements
Full array reads return the entire array as comma-separated values
Reading specific elements of arrays:

The GET AILERON_DEF[3] command reads element 3 of the array
Uses bracket notation to specify which element to read
Writing arrays (full and partial):

SET AILERON_DEF_ARRAY 0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8 writes all elements
SET AILERON_DEF[3] 0.5 writes a specific element
Using assigned OUTPUT IDs:

Each array or array element has an OUTPUT ID (like “AILERON_DEF”)
The system uses these IDs to route data from X-Plane to the correct array

*/

#include <Arduino.h>

// Configuration
const int BAUD_RATE = 115200;
const char* DEVICE_NAME = "ArrayDemoDevice";
const char* FW_VERSION = "1.0";
const char* BOARD_TYPE = "ESP32";

// Array storage - example for aileron deflection array [8] 
float aileron_deflections[8] = {0.0};  // Simulates sim/flightmodel/controls/ail1_def

// Helper function to parse array index from key like "AILERON_DEF[3]"
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

// Helper function to handle array element access
void handleArrayElement(String baseKey, int index, String valueStr) {
  bool handled = false;
  
  // Example: Handle aileron deflection array
  if (baseKey == "AILERON_DEF") {
    if (index >= 0 && index < 8) {
      float value = valueStr.toFloat();
      aileron_deflections[index] = value;
      
      Serial.print("STATUS Updated AILERON_DEF[");
      Serial.print(index);
      Serial.print("] = ");
      Serial.println(value);
      
      // Example: Update servo position based on array element
      // analogWrite(AILERON_SERVO_PIN, mapFloatToPWM(value));
      
      handled = true;
    } else {
      Serial.print("ERROR Index out of bounds for AILERON_DEF: ");
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

// Handle SET command for arrays
void handleSet(String key, String valueStr) {
  bool handled = false;
  
  // Check if this is an array element access (e.g., AILERON_DEF[3])
  if (key.indexOf('[') != -1 && key.indexOf(']') != -1) {
    String baseKey;
    int index;
    
    if (parseArrayIndex(key, baseKey, index)) {
      handleArrayElement(baseKey, index, valueStr);
      return; // Already handled as array element
    }
  }
  
  // Handle full array updates (comma-separated values)
  if (key == "AILERON_DEF_ARRAY") {
    // Parse comma-separated values: "0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8"
    int startIndex = 0;
    int arrayIndex = 0;
    
    for (int i = 0; i <= valueStr.length(); i++) {
      if (i == valueStr.length() || valueStr.charAt(i) == ',') {
        String elementStr = valueStr.substring(startIndex, i);
        if (arrayIndex < 8) {
          aileron_deflections[arrayIndex] = elementStr.toFloat();
        }
        arrayIndex++;
        startIndex = i + 1;
      }
    }
    
    Serial.print("STATUS Updated AILERON_DEF array with ");
    Serial.print(arrayIndex);
    Serial.println(" elements");
    
    // Print entire array to serial monitor
    Serial.print("AILERON_DEF_ARRAY: [");
    for (int i = 0; i < 8; i++) {
      Serial.print(aileron_deflections[i]);
      if (i < 7) Serial.print(", ");
    }
    Serial.println("]");
    
    handled = true;
  }
  
  if (handled) {
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(valueStr);
  }
}

// Handle GET command to read arrays/elements
void handleGet(String key) {
  bool handled = false;
  
  // Check if this is an array element read (e.g., GET AILERON_DEF[3])
  if (key.indexOf('[') != -1 && key.indexOf(']') != -1) {
    String baseKey;
    int index;
    
    if (parseArrayIndex(key, baseKey, index)) {
      if (baseKey == "AILERON_DEF" && index >= 0 && index < 8) {
        Serial.print("VALUE ");
        Serial.print(key);
        Serial.print(" ");
        Serial.println(aileron_deflections[index]);
        handled = true;
      }
    }
  }
  
  // Handle full array read
  if (key == "AILERON_DEF_ARRAY") {
    Serial.print("ARRAY AILERON_DEF: [");
    for (int i = 0; i < 8; i++) {
      Serial.print(aileron_deflections[i]);
      if (i < 7) Serial.print(", ");
    }
    Serial.println("]");
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
  // Array operations
  else if (line.startsWith("SET ")) {
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');
    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      String valueStr = line.substring(secondSpace + 1);
      handleSet(key, valueStr);
    }
  }
  else if (line.startsWith("GET ")) {
    String key = line.substring(4);
    handleGet(key);
  }
  // Debug: Print array values
  else if (line == "PRINT_ARRAY") {
    Serial.println("=== AILERON_DEF ARRAY VALUES ===");
    for (int i = 0; i < 8; i++) {
      Serial.print("AILERON_DEF[");
      Serial.print(i);
      Serial.print("] = ");
      Serial.println(aileron_deflections[i]);
    }
    Serial.println("================================");
  }
  else {
    Serial.print("STATUS Echo: ");
    Serial.println(line);
  }
}

void setup() {
  Serial.begin(BAUD_RATE);
  Serial.println("Array Demo Device Ready - Send HELLO to begin");
  
  // Initialize array with some default values
  for (int i = 0; i < 8; i++) {
    aileron_deflections[i] = 0.0;
  }
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    processLine(line);
  }
}