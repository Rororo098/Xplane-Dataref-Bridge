// Arduino Sample Script for Handling X-Plane Byte Arrays with OUTPUT IDs
//
// This script demonstrates:
// - Reading byte arrays and printing to serial monitor
// - Reading specific elements of byte arrays
// - Writing byte arrays (full and partial)
// - Using assigned OUTPUT IDs for communication
// - Proper handling of byte range (0-255)
/*

* This complete Arduino script demonstrates byte array handling with:
* 
* Reading byte arrays and printing to serial monitor:
* 
* The PRINT_BYTE_ARRAY command prints all array elements with both decimal and hexadecimal representations
* Full array reads return the entire array as comma-separated byte values
* Reading specific elements of byte arrays:
* 
* The GET LED_STATE[3] command reads element 3 of the byte array
* Returns both decimal and hexadecimal values for clarity
* Writing byte arrays (full and partial):
* 
* SET LED_STATE_ARRAY 255,128,64,32,0,... writes all elements (constrained to 0-255)
* SET LED_STATE[3] 150 writes a specific element (constrained to 0-255)
* Using assigned OUTPUT IDs:
* 
* Each byte array or element has an OUTPUT ID (like “LED_STATE”)
* The system uses these IDs to route data from X-Plane to the correct byte array
* Hardware updates happen automatically when array elements change
* The script properly handles the byte range constraint (0-255) and shows both decimal and hexadecimal representations for clarity.

*/

#include <Arduino.h>

// Configuration
const int BAUD_RATE = 115200;
const char* DEVICE_NAME = "ByteArrDemoDevice";
const char* FW_VERSION = "1.0";
const char* BOARD_TYPE = "ESP32";

// Byte array storage - example for LED states [16] 
uint8_t led_states[16] = {0};  // Simulates byte array dataref values (0-255)

// Pin assignments for LEDs (example)
int ledPins[16] = {2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26};

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

// Helper function to handle byte array element access
void handleByteArrayElement(String baseKey, int index, String valueStr) {
  bool handled = false;
  
  // Example: Handle LED state array
  if (baseKey == "LED_STATE") {
    if (index >= 0 && index < 16) {
      int rawValue = valueStr.toInt();
      uint8_t byteValue = constrain(rawValue, 0, 255);  // Constrain to byte range
      led_states[index] = byteValue;
      
      // Update actual hardware
      analogWrite(ledPins[index], byteValue);
      
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

// Handle SET command for byte arrays
void handleSet(String key, String valueStr) {
  bool handled = false;
  
  // Check if this is a byte array element access (e.g., LED_STATE[3])
  if (key.indexOf('[') != -1 && key.indexOf(']') != -1) {
    String baseKey;
    int index;
    
    if (parseArrayIndex(key, baseKey, index)) {
      handleByteArrayElement(baseKey, index, valueStr);
      return; // Already handled as array element
    }
  }
  
  // Handle full byte array updates (comma-separated values)
  if (key == "LED_STATE_ARRAY") {
    // Parse comma-separated byte values: "255,128,64,32,0,100,200,50,255,128,64,32,0,100,200,50"
    int startIndex = 0;
    int arrayIndex = 0;
    
    for (int i = 0; i <= valueStr.length(); i++) {
      if (i == valueStr.length() || valueStr.charAt(i) == ',') {
        String elementStr = valueStr.substring(startIndex, i);
        if (arrayIndex < 16) {
          int rawValue = elementStr.toInt();
          uint8_t byteValue = constrain(rawValue, 0, 255);  // Constrain to byte range
          led_states[arrayIndex] = byteValue;
          
          // Update hardware
          analogWrite(ledPins[arrayIndex], byteValue);
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
    for (int i = 0; i < 16; i++) {
      Serial.print(led_states[i]);
      Serial.print("(0x");
      Serial.print(led_states[i], HEX);
      Serial.print(")");
      if (i < 15) Serial.print(", ");
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

// Handle GET command to read byte arrays/elements
void handleGet(String key) {
  bool handled = false;
  
  // Check if this is a byte array element read (e.g., GET LED_STATE[3])
  if (key.indexOf('[') != -1 && key.indexOf(']') != -1) {
    String baseKey;
    int index;
    
    if (parseArrayIndex(key, baseKey, index)) {
      if (baseKey == "LED_STATE" && index >= 0 && index < 16) {
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
  if (key == "LED_STATE_ARRAY") {
    Serial.print("ARRAY LED_STATE: [");
    for (int i = 0; i < 16; i++) {
      Serial.print(led_states[i]);
      Serial.print("(0x");
      Serial.print(led_states[i], HEX);
      Serial.print(")");
      if (i < 15) Serial.print(", ");
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
  // Byte array operations
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
  // Debug: Print byte array values
  else if (line == "PRINT_BYTE_ARRAY") {
    Serial.println("=== LED_STATE BYTE ARRAY VALUES ===");
    for (int i = 0; i < 16; i++) {
      Serial.print("LED_STATE[");
      Serial.print(i);
      Serial.print("] = ");
      Serial.print(led_states[i]);
      Serial.print(" (0x");
      Serial.print(led_states[i], HEX);
      Serial.println(")");
    }
    Serial.println("==================================");
  }
  else {
    Serial.print("STATUS Echo: ");
    Serial.println(line);
  }
}

void setup() {
  Serial.begin(BAUD_RATE);
  Serial.println("Byte Array Demo Device Ready - Send HELLO to begin");
  
  // Initialize LED pins
  for (int i = 0; i < 16; i++) {
    pinMode(ledPins[i], OUTPUT);
    led_states[i] = 0;
    analogWrite(ledPins[i], 0);
  }
  
  Serial.println("Initialized 16 LED pins for byte array demonstration");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    processLine(line);
  }
}