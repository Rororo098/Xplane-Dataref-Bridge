/*
 * X-Plane Dataref Bridge - Complete Reference Guide
 * ====================================================
 * DESCRIPTION:
 * This reference file demonstrates how to handle ALL X-Plane dataref types.
 * Use this as a starting point for your own projects.
 *
 * SUPPORTED DATA TYPES:
 * - Commands (no value, just execution)
 * - Float (decimal numbers: 0.75, -3.14)
 * - Int (whole numbers: 1, -5, 100)
 * - Bool (0 or 1, true/false)
 * - String (text: "ON", "OFF", "NAV1")
 * - Float Arrays [multiple decimal values]
 * - Int Arrays [multiple whole numbers]
 * - Bool Arrays [multiple 0/1 values]
 * - String Arrays [multiple text values]
 *
 * ====================================================
 * COMPATIBILITY:
 * - Any Arduino-compatible board with Serial
 * - Recommended: Arduino Uno, Nano, Mega, ESP32, etc.
 * ====================================================
 */

#include <Arduino.h>

// ====================================================
// CONFIGURATION
// ====================================================

const int BAUD_RATE = 115200;
const char* DEVICE_NAME = "MyReferenceDevice";
const char* FW_VERSION = "1.0";
const char* BOARD_TYPE = "ARDUINO";

// ====================================================
// STORAGE VARIABLES - Different Data Types
// ====================================================

// Command type - no value, just triggers an action
bool gearToggleState = false;

// Float type - decimal values (0.0 to 1.0, -10.5, etc.)
float throttleValue = 0.0;
float altitudeValue = 0.0;

// Int type - whole numbers (0, 1, 2, -1, etc.)
int gearPosition = 0;
int transponderCode = 0;

// Bool type - 0 (false) or 1 (true)
bool beaconLight = false;
bool landingLight = false;

// String type - text values
String radioFrequency = "";
String flightPhase = "";

// Float array - multiple decimal values
float aileronDeflection[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};

// Int array - multiple whole numbers
int engineStatus[4] = {0, 0, 0, 0};

// Bool array - multiple 0/1 values
bool warningLights[6] = {false, false, false, false, false, false};

// String array - multiple text values
String radioLabels[3] = {"", "", ""};

// ====================================================
// HELPER FUNCTION: Parse Array Index
// ====================================================
// Extracts the index from keys like "ARRAY_NAME[3]"
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

// ====================================================
// HANDLER: Commands (No Value)
// ====================================================
// Commands are actions, not data values
void handleCommand(String key) {
  if (key == "GEAR_TOGGLE") {
    gearToggleState = !gearToggleState;
    digitalWrite(LED_BUILTIN, gearToggleState ? HIGH : LOW);
    Serial.println("STATUS Executed GEAR_TOGGLE");
  }
  else if (key == "BEACON_TOGGLE") {
    beaconLight = !beaconLight;
    Serial.println("STATUS Executed BEACON_TOGGLE");
  }
  
  Serial.print("ACK CMD ");
  Serial.println(key);
}

// ====================================================
// HANDLER: Float Datarefs
// ====================================================
// Float values have decimal points: 0.75, -3.14, 100.5
void handleFloatDataref(String key, float value) {
  if (key == "THROTTLE") {
    throttleValue = value;
    Serial.print("STATUS THROTTLE = ");
    Serial.println(throttleValue, 4);
  }
  else if (key == "ALTITUDE") {
    altitudeValue = value;
    Serial.print("STATUS ALTITUDE = ");
    Serial.println(altitudeValue, 2);
  }
  
  Serial.print("ACK ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value, 4);
}

// ====================================================
// HANDLER: Int Datarefs
// ====================================================
// Int values are whole numbers: 0, 1, -5, 100
void handleIntDataref(String key, int value) {
  if (key == "GEAR_POS") {
    gearPosition = value;
    Serial.print("STATUS GEAR_POS = ");
    Serial.println(gearPosition);
  }
  else if (key == "XPDR_CODE") {
    transponderCode = value;
    Serial.print("STATUS XPDR_CODE = ");
    Serial.println(transponderCode);
  }
  
  Serial.print("ACK ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value);
}

// ====================================================
// HANDLER: Bool Datarefs
// ====================================================
// Bool values are only 0 (false) or 1 (true)
void handleBoolDataref(String key, int value) {
  if (key == "BEACON") {
    beaconLight = (value != 0);
    Serial.print("STATUS BEACON = ");
    Serial.println(beaconLight ? "ON" : "OFF");
  }
  else if (key == "LANDING_LIGHT") {
    landingLight = (value != 0);
    Serial.print("STATUS LANDING_LIGHT = ");
    Serial.println(landingLight ? "ON" : "OFF");
  }
  
  Serial.print("ACK ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value);
}

// ====================================================
// HANDLER: String Datarefs
// ====================================================
// String values are text: "NAV1", "OFF", "APPROACH"
void handleStringDataref(String key, String value) {
  if (key == "RADIO_FREQ") {
    radioFrequency = value;
    Serial.print("STATUS RADIO_FREQ = ");
    Serial.println(radioFrequency);
  }
  else if (key == "FLIGHT_PHASE") {
    flightPhase = value;
    Serial.print("STATUS FLIGHT_PHASE = ");
    Serial.println(flightPhase);
  }
  
  Serial.print("ACK ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value);
}

// ====================================================
// HANDLER: Float Array Element
// ====================================================
// Single element: SET AILERON_DEF[3] 0.5
void handleFloatArrayElement(String baseKey, int index, String valueStr) {
  if (baseKey == "AILERON_DEF") {
    if (index >= 0 && index < 8) {
      aileronDeflection[index] = valueStr.toFloat();
      Serial.print("STATUS AILERON_DEF[");
      Serial.print(index);
      Serial.print("] = ");
      Serial.println(aileronDeflection[index], 4);
      
      Serial.print("ACK ");
      Serial.print(baseKey);
      Serial.print("[");
      Serial.print(index);
      Serial.print("] ");
      Serial.println(valueStr);
    }
  }
}

// ====================================================
// HANDLER: Full Float Array
// ====================================================
// All elements: SET AILERON_DEF_ARRAY 0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8
void handleFloatArray(String key, String valueStr) {
  if (key == "AILERON_DEF_ARRAY") {
    int startIndex = 0;
    int arrayIndex = 0;
    
    for (int i = 0; i <= valueStr.length(); i++) {
      if (i == valueStr.length() || valueStr.charAt(i) == ',') {
        String elementStr = valueStr.substring(startIndex, i);
        if (arrayIndex < 8) {
          aileronDeflection[arrayIndex] = elementStr.toFloat();
        }
        arrayIndex++;
        startIndex = i + 1;
      }
    }
    
    Serial.print("STATUS Updated AILERON_DEF_ARRAY with ");
    Serial.print(arrayIndex);
    Serial.println(" elements");
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(valueStr);
  }
}

// ====================================================
// HANDLER: Int Array Element
// ====================================================
void handleIntArrayElement(String baseKey, int index, String valueStr) {
  if (baseKey == "ENGINE_STATUS") {
    if (index >= 0 && index < 4) {
      engineStatus[index] = valueStr.toInt();
      Serial.print("STATUS ENGINE_STATUS[");
      Serial.print(index);
      Serial.print("] = ");
      Serial.println(engineStatus[index]);
      
      Serial.print("ACK ");
      Serial.print(baseKey);
      Serial.print("[");
      Serial.print(index);
      Serial.print("] ");
      Serial.println(valueStr);
    }
  }
}

// ====================================================
// HANDLER: Full Int Array
// ====================================================
void handleIntArray(String key, String valueStr) {
  if (key == "ENGINE_STATUS_ARRAY") {
    int startIndex = 0;
    int arrayIndex = 0;
    
    for (int i = 0; i <= valueStr.length(); i++) {
      if (i == valueStr.length() || valueStr.charAt(i) == ',') {
        String elementStr = valueStr.substring(startIndex, i);
        if (arrayIndex < 4) {
          engineStatus[arrayIndex] = elementStr.toInt();
        }
        arrayIndex++;
        startIndex = i + 1;
      }
    }
    
    Serial.print("STATUS Updated ENGINE_STATUS_ARRAY with ");
    Serial.print(arrayIndex);
    Serial.println(" elements");
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(valueStr);
  }
}

// ====================================================
// HANDLER: Bool Array Element
// ====================================================
void handleBoolArrayElement(String baseKey, int index, String valueStr) {
  if (baseKey == "WARNING") {
    if (index >= 0 && index < 6) {
      warningLights[index] = (valueStr.toInt() != 0);
      Serial.print("STATUS WARNING[");
      Serial.print(index);
      Serial.print("] = ");
      Serial.println(warningLights[index] ? "ON" : "OFF");
      
      Serial.print("ACK ");
      Serial.print(baseKey);
      Serial.print("[");
      Serial.print(index);
      Serial.print("] ");
      Serial.println(valueStr);
    }
  }
}

// ====================================================
// HANDLER: Full Bool Array
// ====================================================
void handleBoolArray(String key, String valueStr) {
  if (key == "WARNING_ARRAY") {
    int startIndex = 0;
    int arrayIndex = 0;
    
    for (int i = 0; i <= valueStr.length(); i++) {
      if (i == valueStr.length() || valueStr.charAt(i) == ',') {
        String elementStr = valueStr.substring(startIndex, i);
        if (arrayIndex < 6) {
          warningLights[arrayIndex] = (elementStr.toInt() != 0);
        }
        arrayIndex++;
        startIndex = i + 1;
      }
    }
    
    Serial.print("STATUS Updated WARNING_ARRAY with ");
    Serial.print(arrayIndex);
    Serial.println(" elements");
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(valueStr);
  }
}

// ====================================================
// HANDLER: String Array Element
// ====================================================
void handleStringArrayElement(String baseKey, int index, String valueStr) {
  if (baseKey == "RADIO_LABEL") {
    if (index >= 0 && index < 3) {
      radioLabels[index] = valueStr;
      Serial.print("STATUS RADIO_LABEL[");
      Serial.print(index);
      Serial.print("] = ");
      Serial.println(radioLabels[index]);
      
      Serial.print("ACK ");
      Serial.print(baseKey);
      Serial.print("[");
      Serial.print(index);
      Serial.print("] ");
      Serial.println(valueStr);
    }
  }
}

// ====================================================
// HANDLER: Full String Array
// ====================================================
void handleStringArray(String key, String valueStr) {
  if (key == "RADIO_LABEL_ARRAY") {
    int startIndex = 0;
    int arrayIndex = 0;
    
    for (int i = 0; i <= valueStr.length(); i++) {
      if (i == valueStr.length() || valueStr.charAt(i) == ',') {
        String elementStr = valueStr.substring(startIndex, i);
        if (arrayIndex < 3) {
          radioLabels[arrayIndex] = elementStr;
        }
        arrayIndex++;
        startIndex = i + 1;
      }
    }
    
    Serial.print("STATUS Updated RADIO_LABEL_ARRAY with ");
    Serial.print(arrayIndex);
    Serial.println(" elements");
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(valueStr);
  }
}

// ====================================================
// MAIN SET HANDLER
// ====================================================
// Routes SET commands to appropriate handlers
void handleSet(String key, String valueStr) {
  bool handled = false;
  
  // Check if this is an array element access (e.g., AILERON_DEF[3])
  if (key.indexOf('[') != -1 && key.indexOf(']') != -1) {
    String baseKey;
    int index;
    
    if (parseArrayIndex(key, baseKey, index)) {
      // Route to appropriate array element handler
      if (baseKey == "AILERON_DEF") {
        handleFloatArrayElement(baseKey, index, valueStr);
        handled = true;
      }
      else if (baseKey == "ENGINE_STATUS") {
        handleIntArrayElement(baseKey, index, valueStr);
        handled = true;
      }
      else if (baseKey == "WARNING") {
        handleBoolArrayElement(baseKey, index, valueStr);
        handled = true;
      }
      else if (baseKey == "RADIO_LABEL") {
        handleStringArrayElement(baseKey, index, valueStr);
        handled = true;
      }
    }
  }
  
  // Handle full arrays (e.g., AILERON_DEF_ARRAY)
  else if (key == "AILERON_DEF_ARRAY") {
    handleFloatArray(key, valueStr);
    handled = true;
  }
  else if (key == "ENGINE_STATUS_ARRAY") {
    handleIntArray(key, valueStr);
    handled = true;
  }
  else if (key == "WARNING_ARRAY") {
    handleBoolArray(key, valueStr);
    handled = true;
  }
  else if (key == "RADIO_LABEL_ARRAY") {
    handleStringArray(key, valueStr);
    handled = true;
  }
  
  // Handle single values based on key type
  else if (key == "THROTTLE" || key == "ALTITUDE") {
    handleFloatDataref(key, valueStr.toFloat());
    handled = true;
  }
  else if (key == "GEAR_POS" || key == "XPDR_CODE") {
    handleIntDataref(key, valueStr.toInt());
    handled = true;
  }
  else if (key == "BEACON" || key == "LANDING_LIGHT") {
    handleBoolDataref(key, valueStr.toInt());
    handled = true;
  }
  else if (key == "RADIO_FREQ" || key == "FLIGHT_PHASE") {
    handleStringDataref(key, valueStr);
    handled = true;
  }
  
  if (!handled) {
    Serial.print("ERROR Unknown key: ");
    Serial.println(key);
  }
}

// ====================================================
// MAIN GET HANDLER
// ====================================================
void handleGet(String key) {
  bool handled = false;
  
  // Float values
  if (key == "THROTTLE") {
    Serial.print("VALUE THROTTLE ");
    Serial.println(throttleValue, 4);
    handled = true;
  }
  else if (key == "ALTITUDE") {
    Serial.print("VALUE ALTITUDE ");
    Serial.println(altitudeValue, 2);
    handled = true;
  }
  
  // Int values
  else if (key == "GEAR_POS") {
    Serial.print("VALUE GEAR_POS ");
    Serial.println(gearPosition);
    handled = true;
  }
  else if (key == "XPDR_CODE") {
    Serial.print("VALUE XPDR_CODE ");
    Serial.println(transponderCode);
    handled = true;
  }
  
  // Bool values
  else if (key == "BEACON") {
    Serial.print("VALUE BEACON ");
    Serial.println(beaconLight ? 1 : 0);
    handled = true;
  }
  else if (key == "LANDING_LIGHT") {
    Serial.print("VALUE LANDING_LIGHT ");
    Serial.println(landingLight ? 1 : 0);
    handled = true;
  }
  
  // String values
  else if (key == "RADIO_FREQ") {
    Serial.print("VALUE RADIO_FREQ ");
    Serial.println(radioFrequency);
    handled = true;
  }
  else if (key == "FLIGHT_PHASE") {
    Serial.print("VALUE FLIGHT_PHASE ");
    Serial.println(flightPhase);
    handled = true;
  }
  
  // Arrays
  else if (key == "AILERON_DEF_ARRAY") {
    Serial.print("ARRAY AILERON_DEF: [");
    for (int i = 0; i < 8; i++) {
      Serial.print(aileronDeflection[i], 4);
      if (i < 7) Serial.print(", ");
    }
    Serial.println("]");
    handled = true;
  }
  
  // Array elements
  else if (key.indexOf('[') != -1 && key.indexOf(']') != -1) {
    String baseKey;
    int index;
    
    if (parseArrayIndex(key, baseKey, index)) {
      if (baseKey == "AILERON_DEF" && index >= 0 && index < 8) {
        Serial.print("VALUE ");
        Serial.print(key);
        Serial.print(" ");
        Serial.println(aileronDeflection[index], 4);
        handled = true;
      }
    }
  }
  
  if (!handled) {
    Serial.print("ERROR Unknown key: ");
    Serial.println(key);
  }
}

// ====================================================
// PROTOCOL HANDLER
// ====================================================
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
  
  // Command execution
  else if (line.startsWith("CMD ")) {
    String key = line.substring(4);
    handleCommand(key);
  }
  
  // Set dataref value
  else if (line.startsWith("SET ")) {
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');
    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      String valueStr = line.substring(secondSpace + 1);
      handleSet(key, valueStr);
    }
  }
  
  // Get dataref value
  else if (line.startsWith("GET ")) {
    String key = line.substring(4);
    handleGet(key);
  }
  
  else if (line == "PRINT_ALL") {
    Serial.println("=== ALL VALUES ===");
    Serial.print("THROTTLE: ");
    Serial.println(throttleValue, 4);
    Serial.print("ALTITUDE: ");
    Serial.println(altitudeValue, 2);
    Serial.print("GEAR_POS: ");
    Serial.println(gearPosition);
    Serial.print("XPDR_CODE: ");
    Serial.println(transponderCode);
    Serial.print("BEACON: ");
    Serial.println(beaconLight ? "ON" : "OFF");
    Serial.print("LANDING_LIGHT: ");
    Serial.println(landingLight ? "ON" : "OFF");
    Serial.print("RADIO_FREQ: ");
    Serial.println(radioFrequency);
    Serial.print("FLIGHT_PHASE: ");
    Serial.println(flightPhase);
    Serial.println("=================");
  }
  
  else {
    Serial.print("STATUS Echo: ");
    Serial.println(line);
  }
}

// ====================================================
// SETUP
// ====================================================
void setup() {
  Serial.begin(BAUD_RATE);
  Serial.println("Reference Device Ready - Send HELLO to begin");
  
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
}

// ====================================================
// LOOP
// ====================================================
void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    processLine(line);
  }
}
