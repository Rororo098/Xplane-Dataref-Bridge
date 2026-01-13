/*
 * ESP32-S2 Simple Bridge Test
 * 
 * This is the MINIMAL firmware to test communication.
 * Uses USB CDC (serial) only - no HID yet.
 */

// For ESP32-S2, we need USB CDC
#if CONFIG_IDF_TARGET_ESP32S2 || CONFIG_IDF_TARGET_ESP32S3
  #include <USB.h>
  #define SerialPort Serial
#else
  // For regular Arduino (Nano, Pro Micro, Leonardo)
  #define SerialPort Serial
#endif

// Configuration
#define FIRMWARE_VERSION "1.0"
#define DEVICE_NAME "TestDevice"

#if CONFIG_IDF_TARGET_ESP32S2
  #define BOARD_TYPE "ESP32S2"
#elif CONFIG_IDF_TARGET_ESP32S3
  #define BOARD_TYPE "ESP32S3"
#else
  #define BOARD_TYPE "Arduino"
#endif

// Built-in LED (most ESP32-S2 boards have one)
#ifndef LED_BUILTIN
  #define LED_BUILTIN 15  // Change this to your board's LED pin
#endif

// Variables
String inputBuffer = "";
unsigned long lastBlink = 0;
unsigned long lastHeartbeat = 0;
bool ledState = false;
int messageCount = 0;

void setup() {
    // Initialize LED
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);

    #if CONFIG_IDF_TARGET_ESP32S2 || CONFIG_IDF_TARGET_ESP32S3
        // Initialize USB for ESP32-S2/S3
        USB.begin();
        delay(1000); // Give USB time to initialize
        Serial.begin(115200);

        // Wait for USB connection (with timeout)
        unsigned long start = millis();
        while (!Serial && (millis() - start) < 5000) {
            delay(100);
        }

        // Additional delay to ensure USB CDC is fully ready
        delay(1000);
    #else
        // Regular Arduino
        Serial.begin(115200);
        while (!Serial && millis() < 5000) {
            delay(100);
        }
    #endif

    // Startup blink
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(100);
        digitalWrite(LED_BUILTIN, LOW);
        delay(100);
    }

    SerialPort.println("READY");
}

void loop() {
    // Handle incoming serial data
    handleSerial();
    
    // Blink LED every 500ms to show we're alive
    if (millis() - lastBlink > 500) {
        ledState = !ledState;
        digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);
        lastBlink = millis();
    }
    
    // Send heartbeat every 5 seconds
    if (millis() - lastHeartbeat > 5000) {
        SerialPort.print("HEARTBEAT ");
        SerialPort.println(millis() / 1000);
        lastHeartbeat = millis();
    }
}

void handleSerial() {
    while (SerialPort.available()) {
        char c = SerialPort.read();
        
        if (c == '\n' || c == '\r') {
            if (inputBuffer.length() > 0) {
                processCommand(inputBuffer);
                inputBuffer = "";
            }
        } else {
            inputBuffer += c;
            
            // Prevent buffer overflow
            if (inputBuffer.length() > 128) {
                inputBuffer = "";
            }
        }
    }
}

void processCommand(String cmd) {
    cmd.trim();
    messageCount++;
    
    // Echo what we received
    SerialPort.print("RECV: ");
    SerialPort.println(cmd);
    
    // Handle specific commands
    if (cmd == "HELLO") {
        // Handshake response - this is what the Bridge expects
        SerialPort.print("XPDR;fw=");
        SerialPort.print(FIRMWARE_VERSION);
        SerialPort.print(";board=");
        SerialPort.print(BOARD_TYPE);
        SerialPort.print(";name=");
        SerialPort.println(DEVICE_NAME);
    }
    else if (cmd.startsWith("SET ")) {
        // Parse: SET <key> <value>
        // Example: SET LED 1
        int firstSpace = cmd.indexOf(' ', 4);
        if (firstSpace > 0) {
            String key = cmd.substring(4, firstSpace);
            String valueStr = cmd.substring(firstSpace + 1);
            float value = valueStr.toFloat();
            
            // Handle the command
            handleSet(key, value);
            
            // Acknowledge
            SerialPort.print("ACK ");
            SerialPort.print(key);
            SerialPort.print(" ");
            SerialPort.println(value);
        }
    }
    else if (cmd == "LED ON") {
        digitalWrite(LED_BUILTIN, HIGH);
        SerialPort.println("LED is ON");
    }
    else if (cmd == "LED OFF") {
        digitalWrite(LED_BUILTIN, LOW);
        SerialPort.println("LED is OFF");
    }
    else if (cmd == "STATUS") {
        SerialPort.print("STATUS;uptime=");
        SerialPort.print(millis() / 1000);
        SerialPort.print(";messages=");
        SerialPort.print(messageCount);
        SerialPort.print(";board=");
        SerialPort.println(BOARD_TYPE);
    }
    else if (cmd == "PING") {
        SerialPort.println("PONG");
    }
    else {
        SerialPort.print("UNKNOWN: ");
        SerialPort.println(cmd);
    }
}

void handleSet(String key, float value) {
    // Handle SET commands here
    
    if (key == "LED") {
        digitalWrite(LED_BUILTIN, value > 0.5 ? HIGH : LOW);
        SerialPort.print("LED set to ");
        SerialPort.println(value > 0.5 ? "ON" : "OFF");
    }
    else {
        SerialPort.print("Unknown key: ");
        SerialPort.println(key);
    }
}