/*
 * ESP32-S2 Bridge with Input Support
 * 
 * Sends simulated button presses and encoder rotations for testing.
 * In production, replace with actual hardware inputs.
 */

#include <USB.h>

#define FIRMWARE_VERSION "3.0"
#define DEVICE_NAME "InputDevice"
#define BOARD_TYPE "ESP32S2"

#ifndef LED_BUILTIN
  #define LED_BUILTIN 15
#endif

// ============================================================
// Simulated/Virtual Inputs (replace with real pins in production)
// ============================================================

// Button pins (directly on GPIO)
#define BTN_AP_PIN      1   // Autopilot toggle
#define BTN_HDG_PIN     2   // Heading hold
#define BTN_NAV_PIN     3   // NAV mode
#define BTN_APR_PIN     4   // Approach mode
#define BTN_ALT_PIN     5   // Altitude hold
#define BTN_VS_PIN      6   // Vertical speed
#define BTN_GEAR_PIN    7   // Gear toggle

// Encoder pins
#define ENC_HDG_A       10  // Heading encoder
#define ENC_HDG_B       11
#define ENC_ALT_A       12  // Altitude encoder
#define ENC_ALT_B       13
#define ENC_VS_A        14  // VS encoder
#define ENC_VS_B        16

// ============================================================
// Virtual LED Outputs
// ============================================================

struct VirtualLED {
    const char* name;
    bool state;
    float lastValue;
};

VirtualLED leds[] = {
    {"LED", false, 0.0}, {"GEAR", false, 0.0}, {"AP", false, 0.0},
    {"AP_ALT", false, 0.0}, {"AP_HDG", false, 0.0}, {"AP_NAV", false, 0.0},
    {"AP_APR", false, 0.0}, {"AP_VS", false, 0.0}, {"WARN", false, 0.0},
    {"CAUT", false, 0.0}, {"BEACON", false, 0.0}, {"LAND", false, 0.0},
};
const int numLeds = sizeof(leds) / sizeof(leds[0]);

// ============================================================
// Virtual Inputs (for testing without hardware)
// ============================================================

struct VirtualInput {
    const char* name;
    const char* description;
    bool lastState;
    unsigned long lastChange;
};

VirtualInput buttons[] = {
    {"BTN_AP", "Autopilot Toggle", false, 0},
    {"BTN_HDG", "Heading Hold", false, 0},
    {"BTN_NAV", "NAV Mode", false, 0},
    {"BTN_APR", "Approach Mode", false, 0},
    {"BTN_ALT", "Altitude Hold", false, 0},
    {"BTN_VS", "VS Mode", false, 0},
    {"BTN_GEAR", "Gear Toggle", false, 0},
    {"BTN_FLAPS_UP", "Flaps Up", false, 0},
    {"BTN_FLAPS_DN", "Flaps Down", false, 0},
    {"BTN_MASTER_WARN", "Master Warning Ack", false, 0},
};
const int numButtons = sizeof(buttons) / sizeof(buttons[0]);

struct VirtualEncoder {
    const char* name;
    const char* description;
    int position;
    int lastPosition;
};

VirtualEncoder encoders[] = {
    {"ENC_HDG", "Heading Bug", 0, 0},
    {"ENC_ALT", "Altitude Select", 0, 0},
    {"ENC_VS", "Vertical Speed", 0, 0},
    {"ENC_CRS", "Course Select", 0, 0},
    {"ENC_BARO", "Barometer", 0, 0},
    {"ENC_SPD", "Speed Select", 0, 0},
};
const int numEncoders = sizeof(encoders) / sizeof(encoders[0]);

// ============================================================
// Variables
// ============================================================

String inputBuffer = "";
unsigned long lastHeartbeat = 0;
int messageCount = 0;
int setCount = 0;
bool verboseMode = true;

// ============================================================
// Setup
// ============================================================

void setup() {
    USB.begin();
    Serial.begin(115200);
    
    delay(1000);
    unsigned long start = millis();
    while (!Serial && (millis() - start) < 5000) delay(100);
    delay(1000);
    
    pinMode(LED_BUILTIN, OUTPUT);
    
    // Startup blink
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_BUILTIN, HIGH); delay(100);
        digitalWrite(LED_BUILTIN, LOW); delay(100);
    }
    
    Serial.println("");
    Serial.println("========================================");
    Serial.println("  ESP32-S2 Bridge with Input Support");
    Serial.println("========================================");
    Serial.print("Firmware: "); Serial.println(FIRMWARE_VERSION);
    Serial.print("Buttons: "); Serial.println(numButtons);
    Serial.print("Encoders: "); Serial.println(numEncoders);
    Serial.print("LEDs: "); Serial.println(numLeds);
    Serial.println("");
    Serial.println("Commands: HELLO, STATUS, LIST, INPUTS");
    Serial.println("          PRESS <btn>, RELEASE <btn>");
    Serial.println("          ROTATE <enc> <dir>");
    Serial.println("          SET <led> <value>");
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
            if (inputBuffer.length() > 128) inputBuffer = "";
        }
    }
}

void processCommand(String cmd) {
    cmd.trim();
    messageCount++;
    
    // ---- HELLO ----
    if (cmd == "HELLO") {
        Serial.print("XPDR;fw=");
        Serial.print(FIRMWARE_VERSION);
        Serial.print(";board=");
        Serial.print(BOARD_TYPE);
        Serial.print(";name=");
        Serial.print(DEVICE_NAME);
        Serial.print(";buttons=");
        Serial.print(numButtons);
        Serial.print(";encoders=");
        Serial.print(numEncoders);
        Serial.print(";leds=");
        Serial.println(numLeds);
        return;
    }
    
    // ---- SET ----
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
    
    // ---- PRESS <button> ---- (simulate button press)
    if (cmd.startsWith("PRESS ")) {
        String btnName = cmd.substring(6);
        simulateButtonPress(btnName);
        return;
    }
    
    // ---- RELEASE <button> ---- (simulate button release)
    if (cmd.startsWith("RELEASE ")) {
        String btnName = cmd.substring(8);
        simulateButtonRelease(btnName);
        return;
    }
    
    // ---- ROTATE <encoder> <direction> ---- (simulate encoder rotation)
    // direction: CW, CCW, or a number like +5 or -3
    if (cmd.startsWith("ROTATE ")) {
        int spaceIdx = cmd.indexOf(' ', 7);
        if (spaceIdx > 0) {
            String encName = cmd.substring(7, spaceIdx);
            String dirStr = cmd.substring(spaceIdx + 1);
            simulateEncoderRotation(encName, dirStr);
        }
        return;
    }
    
    // ---- INPUTS ---- (list all inputs)
    if (cmd == "INPUTS") {
        listInputs();
        return;
    }
    
    // ---- LIST ---- (list all LEDs)
    if (cmd == "LIST") {
        listLEDs();
        return;
    }
    
    // ---- STATUS ----
    if (cmd == "STATUS") {
        Serial.println("");
        Serial.println("=== STATUS ===");
        Serial.print("Uptime: "); Serial.print(millis() / 1000); Serial.println("s");
        Serial.print("Messages: "); Serial.println(messageCount);
        Serial.print("Buttons: "); Serial.println(numButtons);
        Serial.print("Encoders: "); Serial.println(numEncoders);
        Serial.print("LEDs: "); Serial.println(numLeds);
        Serial.println("==============");
        return;
    }
    
    // ---- HELP ----
    if (cmd == "HELP") {
        printHelp();
        return;
    }
    
    // ---- PING ----
    if (cmd == "PING") {
        Serial.println("PONG");
        return;
    }
    
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
}

// ============================================================
// Input Simulation
// ============================================================

void simulateButtonPress(String btnName) {
    for (int i = 0; i < numButtons; i++) {
        if (btnName.equalsIgnoreCase(buttons[i].name)) {
            buttons[i].lastState = true;
            buttons[i].lastChange = millis();
            
            // Send INPUT message to Python
            Serial.print("INPUT ");
            Serial.print(buttons[i].name);
            Serial.println(" 1");
            
            if (verboseMode) {
                Serial.print(">>> Button PRESSED: ");
                Serial.print(buttons[i].name);
                Serial.print(" (");
                Serial.print(buttons[i].description);
                Serial.println(") <<<");
            }
            return;
        }
    }
    Serial.print("ERROR: Unknown button '");
    Serial.print(btnName);
    Serial.println("'");
}

void simulateButtonRelease(String btnName) {
    for (int i = 0; i < numButtons; i++) {
        if (btnName.equalsIgnoreCase(buttons[i].name)) {
            buttons[i].lastState = false;
            buttons[i].lastChange = millis();
            
            // Send INPUT message to Python
            Serial.print("INPUT ");
            Serial.print(buttons[i].name);
            Serial.println(" 0");
            
            if (verboseMode) {
                Serial.print(">>> Button RELEASED: ");
                Serial.print(buttons[i].name);
                Serial.println(" <<<");
            }
            return;
        }
    }
    Serial.print("ERROR: Unknown button '");
    Serial.print(btnName);
    Serial.println("'");
}

void simulateEncoderRotation(String encName, String dirStr) {
    int delta = 0;
    
    if (dirStr.equalsIgnoreCase("CW") || dirStr == "1" || dirStr == "+1") {
        delta = 1;
    } else if (dirStr.equalsIgnoreCase("CCW") || dirStr == "-1") {
        delta = -1;
    } else {
        delta = dirStr.toInt();
    }
    
    for (int i = 0; i < numEncoders; i++) {
        if (encName.equalsIgnoreCase(encoders[i].name)) {
            encoders[i].position += delta;
            
            // Send INPUT message to Python
            Serial.print("INPUT ");
            Serial.print(encoders[i].name);
            Serial.print(" ");
            Serial.println(delta);
            
            if (verboseMode) {
                Serial.print(">>> Encoder ROTATED: ");
                Serial.print(encoders[i].name);
                Serial.print(" ");
                Serial.print(delta > 0 ? "+" : "");
                Serial.print(delta);
                Serial.print(" (new pos: ");
                Serial.print(encoders[i].position);
                Serial.println(") <<<");
            }
            return;
        }
    }
    Serial.print("ERROR: Unknown encoder '");
    Serial.print(encName);
    Serial.println("'");
}

void listInputs() {
    Serial.println("");
    Serial.println("=== AVAILABLE INPUTS ===");
    
    Serial.println("");
    Serial.println("Buttons:");
    for (int i = 0; i < numButtons; i++) {
        Serial.print("  ");
        Serial.print(buttons[i].name);
        for (int p = strlen(buttons[i].name); p < 16; p++) Serial.print(" ");
        Serial.print("- ");
        Serial.print(buttons[i].description);
        Serial.print(" [");
        Serial.print(buttons[i].lastState ? "PRESSED" : "released");
        Serial.println("]");
    }
    
    Serial.println("");
    Serial.println("Encoders:");
    for (int i = 0; i < numEncoders; i++) {
        Serial.print("  ");
        Serial.print(encoders[i].name);
        for (int p = strlen(encoders[i].name); p < 16; p++) Serial.print(" ");
        Serial.print("- ");
        Serial.print(encoders[i].description);
        Serial.print(" [pos: ");
        Serial.print(encoders[i].position);
        Serial.println("]");
    }
    
    Serial.println("");
    Serial.println("To simulate: PRESS BTN_AP, RELEASE BTN_AP");
    Serial.println("             ROTATE ENC_HDG CW, ROTATE ENC_ALT -5");
    Serial.println("========================");
    Serial.println("");
}

void listLEDs() {
    Serial.println("");
    Serial.println("=== VIRTUAL LED STATUS ===");
    for (int i = 0; i < numLeds; i++) {
        Serial.print("  ");
        Serial.print(leds[i].name);
        for (int p = strlen(leds[i].name); p < 10; p++) Serial.print(" ");
        Serial.print(": ");
        Serial.print(leds[i].state ? "ON " : "OFF");
        Serial.print("  (value: ");
        Serial.print(leds[i].lastValue, 2);
        Serial.println(")");
    }
    Serial.println("===========================");
    Serial.println("");
}

void handleSet(String key, float value) {
    for (int i = 0; i < numLeds; i++) {
        if (key.equalsIgnoreCase(leds[i].name)) {
            bool newState = (value > 0.5);
            leds[i].state = newState;
            leds[i].lastValue = value;
            
            if (i == 0) digitalWrite(LED_BUILTIN, newState ? HIGH : LOW);
            
            Serial.print(">>> ");
            Serial.print(leds[i].name);
            Serial.print(" = ");
            Serial.print(newState ? "ON" : "OFF");
            Serial.println(" <<<");
            
            Serial.print("ACK ");
            Serial.print(key);
            Serial.print(" ");
            Serial.println(value, 2);
            return;
        }
    }
    Serial.print("ERROR: Unknown LED '");
    Serial.print(key);
    Serial.println("'");
}

void printHelp() {
    Serial.println("");
    Serial.println("=== COMMANDS ===");
    Serial.println("HELLO              - Handshake");
    Serial.println("STATUS             - Device status");
    Serial.println("INPUTS             - List all inputs");
    Serial.println("LIST               - List all LEDs");
    Serial.println("");
    Serial.println("SET <led> <value>  - Set LED state");
    Serial.println("PRESS <button>     - Simulate button press");
    Serial.println("RELEASE <button>   - Simulate button release");
    Serial.println("ROTATE <enc> <dir> - Simulate encoder (CW/CCW/+N/-N)");
    Serial.println("");
    Serial.println("PING               - Connection test");
    Serial.println("HELP               - This message");
    Serial.println("================");
    Serial.println("");
}