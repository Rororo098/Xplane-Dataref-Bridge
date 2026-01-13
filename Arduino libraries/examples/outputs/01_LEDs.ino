// ============================================================
// XPlane Dataref Bridge - LED Output Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Receives data from X-Plane and controls LEDs accordingly.
// LEDs can show binary states (on/off) or brightness levels.
//
// Perfect for:
// - Gear status indicators (green = down, red = up)
// - Warning lights (master warning, master caution)
// - Annunciator panel
// - Switch position indicators
// - Engine status lights
//
// HARDWARE NEEDED:
// ----------------
// - Arduino or ESP32
// - LEDs (any color)
// - Resistors (220-470 ohm depending on LED)
//
// WIRING:
// -------
//   Arduino Pin → Resistor (220Ω) → LED (+) 
//   LED (-) → GND
//
// For brighter LEDs or multiple in series, use transistors!
//
// ============================================================

// ============================================================
// CONFIGURATION
// ============================================================

// How many LEDs do you have?
#define NUM_LEDS 8

// What pins are the LEDs connected to?
// Use PWM-capable pins (marked with ~) for brightness control
// Arduino Uno/Nano PWM pins: 3, 5, 6, 9, 10, 11
// ESP32: All pins support PWM (LEDC)
const int LED_PINS[NUM_LEDS] = {
    3,    // LED 0: Gear Nose (PWM)
    4,    // LED 1: Gear Left
    5,    // LED 2: Gear Right (PWM)
    6,    // LED 3: Autopilot (PWM)
    7,    // LED 4: Master Warning
    8,    // LED 5: Master Caution
    9,    // LED 6: Beacon indicator (PWM)
    10    // LED 7: Low Fuel (PWM)
};

// What key should control each LED?
// These must match the Output Keys configured in the PC app!
const char* LED_KEYS[NUM_LEDS] = {
    "GEAR_NOSE",      // LED 0
    "GEAR_LEFT",      // LED 1
    "GEAR_RIGHT",     // LED 2
    "AP_ENGAGED",     // LED 3
    "MASTER_WARN",    // LED 4
    "MASTER_CAUT",    // LED 5
    "BEACON_ON",      // LED 6
    "LOW_FUEL"        // LED 7
};

// LED modes - how should each LED behave?
#define MODE_BINARY   0   // On/off only (value > 0.5 = on)
#define MODE_PWM      1   // Brightness control (0.0 to 1.0)
#define MODE_BLINK    2   // Blink when value > 0.5
#define MODE_INVERTED 3   // On when value < 0.5

const int LED_MODES[NUM_LEDS] = {
    MODE_BINARY,    // Gear Nose: on/off
    MODE_BINARY,    // Gear Left: on/off
    MODE_BINARY,    // Gear Right: on/off
    MODE_PWM,       // Autopilot: can dim
    MODE_BLINK,     // Master Warning: blinks
    MODE_BLINK,     // Master Caution: blinks
    MODE_BINARY,    // Beacon: on/off
    MODE_BLINK      // Low Fuel: blinks
};

// Blink interval (milliseconds) for MODE_BLINK
#define BLINK_INTERVAL 500

// ============================================================
// INTERNAL VARIABLES
// ============================================================

// Store current LED values
float ledValues[NUM_LEDS];

// Track blink state
bool blinkState = false;
unsigned long lastBlinkTime = 0;

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Initialize LED pins as outputs
    for (int i = 0; i < NUM_LEDS; i++) {
        pinMode(LED_PINS[i], OUTPUT);
        digitalWrite(LED_PINS[i], LOW);  // Start with all LEDs off
        ledValues[i] = 0.0;
    }
    
    Serial.println("// LED Controller Ready!");
    Serial.print("// Controlling ");
    Serial.print(NUM_LEDS);
    Serial.println(" LEDs");
    
    // Flash all LEDs briefly to show we're ready
    testAllLEDs();
}

// ============================================================
// MAIN LOOP
// ============================================================

void loop() {
    // Check for messages from PC
    if (Serial.available()) {
        String message = Serial.readStringUntil('\n');
        message.trim();
        handleMessage(message);
    }
    
    // Update blink state
    updateBlink();
    
    // Update all LEDs
    updateLEDs();
    
    delay(10);  // Small delay
}

// ============================================================
// UPDATE BLINK STATE
// ============================================================

void updateBlink() {
    unsigned long currentTime = millis();
    
    if (currentTime - lastBlinkTime >= BLINK_INTERVAL) {
        blinkState = !blinkState;
        lastBlinkTime = currentTime;
    }
}

// ============================================================
// UPDATE LEDs
// ============================================================

void updateLEDs() {
    for (int i = 0; i < NUM_LEDS; i++) {
        float value = ledValues[i];
        int outputValue = 0;
        
        switch (LED_MODES[i]) {
            case MODE_BINARY:
                // Simple on/off: > 0.5 = on
                outputValue = (value > 0.5) ? 255 : 0;
                break;
                
            case MODE_PWM:
                // Brightness control: 0.0 to 1.0 → 0 to 255
                outputValue = (int)(value * 255);
                outputValue = constrain(outputValue, 0, 255);
                break;
                
            case MODE_BLINK:
                // Blink when value > 0.5
                if (value > 0.5) {
                    outputValue = blinkState ? 255 : 0;
                } else {
                    outputValue = 0;
                }
                break;
                
            case MODE_INVERTED:
                // Inverted: on when value < 0.5
                outputValue = (value < 0.5) ? 255 : 0;
                break;
        }
        
        // Write to LED
        // Use analogWrite for PWM pins, digitalWrite for others
        if (LED_MODES[i] == MODE_PWM) {
            analogWrite(LED_PINS[i], outputValue);
        } else {
            digitalWrite(LED_PINS[i], outputValue > 0 ? HIGH : LOW);
        }
    }
}

// ============================================================
// HANDLE MESSAGE FROM PC
// ============================================================

void handleMessage(String message) {
    // --------------------------------------------------------
    // HELLO - Handshake
    // --------------------------------------------------------
    if (message == "HELLO") {
        Serial.println("XPDR;fw=1.0;board=LEDController;name=Annunciator");
    }
    
    // --------------------------------------------------------
    // SET <KEY> <VALUE> - Update LED value
    // --------------------------------------------------------
    else if (message.startsWith("SET ")) {
        // Parse the message
        int firstSpace = message.indexOf(' ');
        int secondSpace = message.indexOf(' ', firstSpace + 1);
        
        if (secondSpace == -1) return;  // Invalid message
        
        String key = message.substring(firstSpace + 1, secondSpace);
        float value = message.substring(secondSpace + 1).toFloat();
        
        // Find matching LED
        bool found = false;
        for (int i = 0; i < NUM_LEDS; i++) {
            if (key == LED_KEYS[i]) {
                ledValues[i] = value;
                found = true;
                
                // Acknowledge
                Serial.print("ACK ");
                Serial.print(key);
                Serial.print(" ");
                Serial.println(value);
                break;
            }
        }
        
        if (!found) {
            // Unknown key - could log for debugging
            // Serial.print("// Unknown key: ");
            // Serial.println(key);
        }
    }
}

// ============================================================
// TEST ALL LEDs
// ============================================================

void testAllLEDs() {
    Serial.println("// Testing LEDs...");
    
    // Turn each LED on briefly
    for (int i = 0; i < NUM_LEDS; i++) {
        digitalWrite(LED_PINS[i], HIGH);
        delay(100);
    }
    
    delay(500);
    
    // Turn all off
    for (int i = 0; i < NUM_LEDS; i++) {
        digitalWrite(LED_PINS[i], LOW);
    }
    
    Serial.println("// LED test complete!");
}

// ============================================================
// ADDITIONAL LED EFFECTS (Optional)
// ============================================================

// Fade effect for smooth transitions
void fadeToValue(int ledIndex, float targetValue, int duration) {
    float currentValue = ledValues[ledIndex];
    int steps = duration / 10;  // 10ms per step
    float stepSize = (targetValue - currentValue) / steps;
    
    for (int i = 0; i < steps; i++) {
        currentValue += stepSize;
        analogWrite(LED_PINS[ledIndex], (int)(currentValue * 255));
        delay(10);
    }
    
    ledValues[ledIndex] = targetValue;
}

// Pulse effect (fade in and out)
void pulseEffect(int ledIndex) {
    static float pulseValue = 0;
    static bool increasing = true;
    
    if (increasing) {
        pulseValue += 0.02;
        if (pulseValue >= 1.0) increasing = false;
    } else {
        pulseValue -= 0.02;
        if (pulseValue <= 0.0) increasing = true;
    }
    
    analogWrite(LED_PINS[ledIndex], (int)(pulseValue * 255));
}

// ============================================================
// MODIFICATION IDEAS:
// ============================================================
//
// 1. RGB LEDs:
//    Use WS2812B (NeoPixel) for colored indicators.
//    Green = safe, Yellow = caution, Red = warning.
//
// 2. LED STRIPS:
//    Use addressable strips for bar graphs (fuel, flaps).
//
// 3. BRIGHTNESS ADJUSTMENT:
//    Add a master brightness pot for night flying.
//
// 4. NIGHT MODE:
//    Reduce all LED brightness via PWM at night.
//
// 5. TRANSIT ANIMATION:
//    Gear LEDs blink during gear transit, solid when locked.
//
// 6. SEQUENCE INDICATORS:
//    Multiple LEDs show a sequence (startup, shutdown).
//
// ============================================================

// ============================================================
// ADVANCED: TRANSIT STATE FOR GEAR LEDs
// ============================================================
//
// X-Plane gear dataref:
// 0.0 = fully up
// 0.5 = in transit  
// 1.0 = fully down
//
// We can detect transit and show a special indication:
//
// void handleGearLED(int ledIndex, float value) {
//     if (value < 0.1) {
//         // Gear UP - LED off
//         ledValues[ledIndex] = 0;
//     } else if (value > 0.9) {
//         // Gear DOWN - LED on solid
//         ledValues[ledIndex] = 1.0;
//     } else {
//         // Gear in TRANSIT - blink fast!
//         LED_MODES[ledIndex] = MODE_BLINK;
//         ledValues[ledIndex] = 1.0;
//     }
// }
//
// ============================================================
