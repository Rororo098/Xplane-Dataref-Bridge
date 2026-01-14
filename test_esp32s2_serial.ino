/*
 * ESP32-S2 Serial Test - For Debugging Connection Issues
 * =====================================================
 * Purpose: Test if your ESP32-S2 is communicating properly via Serial
 * 
 * INSTRUCTIONS:
 * 1. Enable "USB CDC On Boot" in Arduino IDE:
 *    - Tools -> USB CDC On Boot -> Enabled
 * 2. Upload this sketch
 * 3. Open Serial Monitor (115200 baud)
 * 4. It should print "Waiting for HELLO..."
 * 5. Type "HELLO" and click Send
 * 6. You should see the handshake response
 * 
 * If this works in Serial Monitor, it should work with the Bridge App.
 */

#include <Arduino.h>

const int BAUD_RATE = 115200;
const char* DEVICE_NAME = "ESP32S2_Test";
const char* FW_VERSION = "1.0";
const char* BOARD_TYPE = "ESP32S2";  // Use ESP32S2 for proper detection

String inputBuffer = "";

void setup() {
  Serial.begin(BAUD_RATE);
  
  // Wait a bit for serial to be ready
  delay(2000);
  
  Serial.println("========================================");
  Serial.println("ESP32-S2 Serial Test");
  Serial.println("========================================");
  Serial.println("Type 'HELLO' to test handshake");
  Serial.println("Type 'PING' to test basic response");
  Serial.println("========================================");
  Serial.println("");
  
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  // Check for incoming data
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    
    if (c == '\n') {
      inputBuffer.trim();
      Serial.print("Received: ");
      Serial.println(inputBuffer);
      
      processLine(inputBuffer);
      inputBuffer = "";
    }
    else if (c != '\r') {
      inputBuffer += c;
    }
  }
}

void processLine(String line) {
  if (line == "HELLO") {
    // Send handshake response (this is what the Bridge App expects)
    Serial.println("XPDR;fw=1.0;board=ESP32S2;name=ESP32S2_Test");
    
    // Flash LED to show handshake worked
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    
    Serial.println("Handshake sent successfully!");
    Serial.println("");
  }
  else if (line == "PING") {
    Serial.println("PONG - Serial is working!");
    Serial.println("");
  }
  else if (line == "STATUS") {
    Serial.println("=== Device Status ===");
    Serial.print("Board Type: ");
    Serial.println(BOARD_TYPE);
    Serial.print("Device Name: ");
    Serial.println(DEVICE_NAME);
    Serial.print("Firmware: ");
    Serial.println(FW_VERSION);
    Serial.println("=====================");
    Serial.println("");
  }
  else if (line.startsWith("SET ")) {
    // Parse SET command
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.lastIndexOf(' ');
    
    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);
      String valStr = line.substring(secondSpace + 1);
      
      Serial.print("ACK ");
      Serial.print(key);
      Serial.print(" ");
      Serial.println(valStr);
    }
  }
  else {
    Serial.print("Unknown command: ");
    Serial.println(line);
    Serial.println("");
  }
}
