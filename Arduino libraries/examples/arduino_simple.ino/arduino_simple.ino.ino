/*
 * Arduino Simple Bridge Test
 * Works with: Arduino Nano, Pro Micro, Leonardo, Uno, Mega
 */

#define FIRMWARE_VERSION "1.0"
#define DEVICE_NAME "ArduinoTest"
#define BOARD_TYPE "Arduino"

#ifndef LED_BUILTIN
  #define LED_BUILTIN 13
#endif

String inputBuffer = "";
unsigned long lastBlink = 0;
unsigned long lastHeartbeat = 0;
bool ledState = false;

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(115200);
    
    // Wait for serial (needed for Leonardo/Pro Micro)
    while (!Serial && millis() < 3000) {
        delay(100);
    }
    
    // Startup blink
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_BUILTIN, HIGH);
        delay(100);
        digitalWrite(LED_BUILTIN, LOW);
        delay(100);
    }
    
    Serial.println("READY");
}

void loop() {
    // Handle serial
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
    
    // Blink
    if (millis() - lastBlink > 500) {
        ledState = !ledState;
        digitalWrite(LED_BUILTIN, ledState);
        lastBlink = millis();
    }
    
    // Heartbeat
    if (millis() - lastHeartbeat > 5000) {
        Serial.print("HEARTBEAT ");
        Serial.println(millis() / 1000);
        lastHeartbeat = millis();
    }
}

void processCommand(String cmd) {
    cmd.trim();
    
    Serial.print("RECV: ");
    Serial.println(cmd);
    
    if (cmd == "HELLO") {
        Serial.print("XPDR;fw=");
        Serial.print(FIRMWARE_VERSION);
        Serial.print(";board=");
        Serial.print(BOARD_TYPE);
        Serial.print(";name=");
        Serial.println(DEVICE_NAME);
    }
    else if (cmd.startsWith("SET ")) {
        int firstSpace = cmd.indexOf(' ', 4);
        if (firstSpace > 0) {
            String key = cmd.substring(4, firstSpace);
            float value = cmd.substring(firstSpace + 1).toFloat();
            
            if (key == "LED") {
                digitalWrite(LED_BUILTIN, value > 0.5 ? HIGH : LOW);
            }
            
            Serial.print("ACK ");
            Serial.print(key);
            Serial.print(" ");
            Serial.println(value);
        }
    }
    else if (cmd == "PING") {
        Serial.println("PONG");
    }
    else if (cmd == "STATUS") {
        Serial.print("STATUS;uptime=");
        Serial.println(millis() / 1000);
    }
}