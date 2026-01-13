/*
 * ESP32-S2 Debug Firmware
 * 
 * Simulates LED outputs via serial print - no physical LEDs needed!
 * Perfect for development and testing.
 */

#include <USB.h>

#define FIRMWARE_VERSION "2.1"
#define DEVICE_NAME "DebugDevice"
#define BOARD_TYPE "ESP32S2"

// Built-in LED (optional - only one we'll actually use)
#ifndef LED_BUILTIN
  #define LED_BUILTIN 15
#endif

// ============================================================
// Simulated LED Outputs (no physical pins needed!)
// ============================================================

struct VirtualLED {
    const char* name;
    bool state;
    float lastValue;
};

VirtualLED leds[] = {
    {"LED",      false, 0.0},   // Generic test LED (uses built-in)
    {"GEAR",     false, 0.0},   // Gear status
    {"AP",       false, 0.0},   // Autopilot master
    {"AP_ALT",   false, 0.0},   // AP Altitude hold
    {"AP_HDG",   false, 0.0},   // AP Heading hold
    {"AP_NAV",   false, 0.0},   // AP NAV mode
    {"AP_APR",   false, 0.0},   // AP Approach mode
    {"AP_VS",    false, 0.0},   // AP Vertical Speed
    {"AP_FD",    false, 0.0},   // Flight Director
    {"WARN",     false, 0.0},   // Master Warning
    {"CAUT",     false, 0.0},   // Master Caution
    {"BEACON",   false, 0.0},   // Beacon light
    {"LAND",     false, 0.0},   // Landing lights
    {"NAV",      false, 0.0},   // Nav lights
    {"STROBE",   false, 0.0},   // Strobe lights
    {"TAXI",     false, 0.0},   // Taxi light
    {"FUEL_LOW", false, 0.0},   // Low fuel warning
    {"OIL_LOW",  false, 0.0},   // Low oil pressure
    {"STALL",    false, 0.0},   // Stall warning
    {"FIRE",     false, 0.0},   // Fire warning
};

const int numLeds = sizeof(leds) / sizeof(leds[0]);

// ============================================================
// Variables
// ============================================================

String inputBuffer = "";
unsigned long lastHeartbeat = 0;
int messageCount = 0;
int setCount = 0;
bool verboseMode = true;  // Print all LED changes

// ============================================================
// Setup
// ============================================================

void setup() {
    USB.begin();
    Serial.begin(115200);
    
    delay(1000);
    
    unsigned long start = millis();
    while (!Serial && (millis() - start) < 5000) {
        delay(100);
    }
    
    delay(1000);
    
    // Only use built-in LED
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);
    
    // Startup blink
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(100);
        digitalWrite(LED_BUILTIN, LOW);
        delay(100);
    }
    
    Serial.println("");
    Serial.println("========================================");
    Serial.println("  ESP32-S2 Debug Firmware");
    Serial.println("  LED outputs are SIMULATED (printed)");
    Serial.println("========================================");
    Serial.print("Version: ");
    Serial.println(FIRMWARE_VERSION);
    Serial.print("Virtual LEDs: ");
    Serial.println(numLeds);
    Serial.println("");
    Serial.println("Commands: HELLO, STATUS, LIST, VERBOSE ON/OFF");
    Serial.println("          SET <key> <value>, TEST, ALL ON/OFF");
    Serial.println("========================================");
    Serial.println("");
    Serial.println("READY");
}

// ============================================================
// Main Loop
// ============================================================

void loop() {
    handleSerial();
    
    // Heartbeat every 10 seconds
    if (millis() - lastHeartbeat > 10000) {
        Serial.print("HEARTBEAT ");
        Serial.print(millis() / 1000);
        Serial.print("s | msgs=");
        Serial.print(messageCount);
        Serial.print(" | sets=");
        Serial.println(setCount);
        lastHeartbeat = millis();
    }
}

// ============================================================
// Serial Handling
// ============================================================

void handleSerial() {
    while (Serial.available()) {
        char c = Serial.read();
        
        if (c == '\n' || c == '\r') {
            if (inputBuffer.length() > 0) {
                processCommand(inputBuffer);
                inputBuffer = "";
            }
        } else {
            inputBuffer += c;
            if (inputBuffer.length() > 128) {
                inputBuffer = "";
            }
        }
    }
}

void processCommand(String cmd) {
    cmd.trim();
    messageCount++;
    
    // ---- HELLO (handshake) ----
    if (cmd == "HELLO") {
        Serial.print("XPDR;fw=");
        Serial.print(FIRMWARE_VERSION);
        Serial.print(";board=");
        Serial.print(BOARD_TYPE);
        Serial.print(";name=");
        Serial.print(DEVICE_NAME);
        Serial.print(";leds=");
        Serial.print(numLeds);
        Serial.println(";mode=debug");
        return;
    }
    
    // ---- SET <key> <value> ----
    if (cmd.startsWith("SET ")) {
        int firstSpace = cmd.indexOf(' ', 4);
        if (firstSpace > 0) {
            String key = cmd.substring(4, firstSpace);
            float value = cmd.substring(firstSpace + 1).toFloat();
            handleSet(key, value);
            setCount++;
        }
        return;
    }
    
    // ---- STATUS ----
    if (cmd == "STATUS") {
        Serial.println("");
        Serial.println("=== STATUS ===");
        Serial.print("Uptime: ");
        Serial.print(millis() / 1000);
        Serial.println(" seconds");
        Serial.print("Messages received: ");
        Serial.println(messageCount);
        Serial.print("SET commands: ");
        Serial.println(setCount);
        Serial.print("Virtual LEDs: ");
        Serial.println(numLeds);
        Serial.print("Verbose mode: ");
        Serial.println(verboseMode ? "ON" : "OFF");
        
        // Count active LEDs
        int activeCount = 0;
        for (int i = 0; i < numLeds; i++) {
            if (leds[i].state) activeCount++;
        }
        Serial.print("Active LEDs: ");
        Serial.print(activeCount);
        Serial.print("/");
        Serial.println(numLeds);
        Serial.println("==============");
        Serial.println("");
        return;
    }
    
    // ---- LIST ----
    if (cmd == "LIST") {
        Serial.println("");
        Serial.println("=== VIRTUAL LED STATUS ===");
        for (int i = 0; i < numLeds; i++) {
            Serial.print("  ");
            Serial.print(leds[i].name);
            // Pad name for alignment
            for (int p = strlen(leds[i].name); p < 10; p++) Serial.print(" ");
            Serial.print(": ");
            Serial.print(leds[i].state ? "ON " : "OFF");
            Serial.print("  (value: ");
            Serial.print(leds[i].lastValue, 2);
            Serial.println(")");
        }
        Serial.println("===========================");
        Serial.println("");
        return;
    }
    
    // ---- VERBOSE ON/OFF ----
    if (cmd == "VERBOSE ON") {
        verboseMode = true;
        Serial.println("Verbose mode ON - all LED changes will be printed");
        return;
    }
    if (cmd == "VERBOSE OFF") {
        verboseMode = false;
        Serial.println("Verbose mode OFF - only ACK messages");
        return;
    }
    
    // ---- TEST ----
    if (cmd == "TEST") {
        Serial.println("");
        Serial.println("=== LED TEST SEQUENCE ===");
        for (int i = 0; i < numLeds; i++) {
            Serial.print("  [");
            Serial.print(i + 1);
            Serial.print("/");
            Serial.print(numLeds);
            Serial.print("] ");
            Serial.print(leds[i].name);
            Serial.println(" → ON");
            leds[i].state = true;
            delay(100);
            leds[i].state = false;
        }
        Serial.println("=== TEST COMPLETE ===");
        Serial.println("");
        return;
    }
    
    // ---- ALL ON ----
    if (cmd == "ALL ON") {
        Serial.println("");
        Serial.println(">>> ALL LEDs ON <<<");
        for (int i = 0; i < numLeds; i++) {
            leds[i].state = true;
            leds[i].lastValue = 1.0;
        }
        digitalWrite(LED_BUILTIN, HIGH);
        return;
    }
    
    // ---- ALL OFF ----
    if (cmd == "ALL OFF") {
        Serial.println("");
        Serial.println(">>> ALL LEDs OFF <<<");
        for (int i = 0; i < numLeds; i++) {
            leds[i].state = false;
            leds[i].lastValue = 0.0;
        }
        digitalWrite(LED_BUILTIN, LOW);
        return;
    }
    
    // ---- PING ----
    if (cmd == "PING") {
        Serial.println("PONG");
        return;
    }
    
    // ---- HELP ----
    if (cmd == "HELP") {
        Serial.println("");
        Serial.println("=== COMMANDS ===");
        Serial.println("  HELLO          - Handshake (returns device info)");
        Serial.println("  SET <key> <val>- Set LED state (e.g., SET GEAR 1)");
        Serial.println("  STATUS         - Show device status");
        Serial.println("  LIST           - List all LED states");
        Serial.println("  TEST           - Cycle through all LEDs");
        Serial.println("  ALL ON         - Turn all LEDs on");
        Serial.println("  ALL OFF        - Turn all LEDs off");
        Serial.println("  VERBOSE ON/OFF - Toggle verbose output");
        Serial.println("  PING           - Connection test");
        Serial.println("  HELP           - This message");
        Serial.println("");
        Serial.println("Available LED keys:");
        Serial.print("  ");
        for (int i = 0; i < numLeds; i++) {
            Serial.print(leds[i].name);
            if (i < numLeds - 1) Serial.print(", ");
            if ((i + 1) % 6 == 0) {
                Serial.println("");
                Serial.print("  ");
            }
        }
        Serial.println("");
        Serial.println("================");
        return;
    }
    
    // Unknown command
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
}

// ============================================================
// LED Control (Simulated)
// ============================================================

void handleSet(String key, float value) {
    bool found = false;
    
    for (int i = 0; i < numLeds; i++) {
        if (key.equalsIgnoreCase(leds[i].name)) {
            bool newState = (value > 0.5);
            bool changed = (newState != leds[i].state);
            
            leds[i].state = newState;
            leds[i].lastValue = value;
            
            // Control built-in LED for the generic "LED" key
            if (i == 0) {
                digitalWrite(LED_BUILTIN, newState ? HIGH : LOW);
            }
            
            // Print change if verbose or if state changed
            if (verboseMode || changed) {
                Serial.print(">>> ");
                Serial.print(leds[i].name);
                Serial.print(" is now ");
                Serial.print(newState ? "ON" : "OFF");
                if (value != 0.0 && value != 1.0) {
                    Serial.print(" (value: ");
                    Serial.print(value, 2);
                    Serial.print(")");
                }
                Serial.println(" <<<");
            }
            
            // Always send ACK
            Serial.print("ACK ");
            Serial.print(key);
            Serial.print(" ");
            Serial.println(value, 2);
            
            found = true;
            break;
        }
    }
    
    if (!found) {
        Serial.print("ERROR: Unknown LED key '");
        Serial.print(key);
        Serial.println("'");
        Serial.print("ACK ");
        Serial.print(key);
        Serial.println(" ERROR");
    }
}