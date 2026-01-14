/*
 * X-Plane Dataref Bridge - General Encoder with Data Output Support
 * =========================================================================
 * DESCRIPTION:
 * This sketch demonstrates a general-purpose rotary encoder with both input
 * and output capabilities using Serial communication only (no HID/joystick).
 * It can:
 * 1. Send encoder rotations to the PC as INPUT events
 * 2. Receive and handle SET commands for data outputs (LEDs, displays, etc.)
 *
 * This is perfect for rotary knobs that control datarefs and also need
 * visual feedback (e.g., a radio frequency knob with a display).
 *
 * FEATURES:
 * - Quadrature encoder reading (CW/CCW detection)
 * - Optional encoder push button
 * - Support for multiple encoders (expandable)
 * - Data output support (SET commands) for feedback
 * - Debouncing for reliable operation
 * - Works on ALL Arduino boards (Uno, Nano, Leonardo, ESP32, etc.)
 * - Serial-only communication (no HID/joystick libraries)
 * =========================================================================
 */

// ================================================================
// 1. DEVICE IDENTIFICATION
// ================================================================

// Device name sent to PC during handshake
const char* DEVICE_NAME = "GeneralEncoder";

// ================================================================
// 2. CONFIGURATION
// ================================================================

// Number of encoders connected to this Arduino
#define NUM_ENCODERS 1

// Encoder pin definitions
// Format: {CLK_PIN, DT_PIN, BUTTON_PIN}
// Use -1 for BUTTON_PIN if encoder doesn't have a button
const int ENCODER_PINS[NUM_ENCODERS][3] = {
    {2, 3, 4}     // Encoder 0: CLK=2, DT=3, Button=4
};

// Encoder input names (keys to send to PC)
// These are the INPUT keys you'll map in the X-Plane Dataref Bridge app
const char* ENCODER_NAMES[NUM_ENCODERS] = {
    "KNOB_0"       // Encoder 0 (sends +1.0 for CW, -1.0 for CCW)
};

// Encoder button input names
// Use empty string "" if encoder has no button
const char* ENCODER_BUTTON_NAMES[NUM_ENCODERS] = {
    "BTN_KNOB_0"   // Encoder 0 button
};

// ================================================================
// 3. DATA OUTPUT CONFIGURATION
// ================================================================

// Data output pins - for LEDs, displays, etc.
// These are controlled by SET commands from the PC
// Format: {OUTPUT_KEY, PIN_NUMBER}
// When PC sends "SET LED_STATUS 1.0", this turns the LED on

// Example: Simple LED indicators
#define NUM_OUTPUTS 1
const struct OutputPin {
    const char* key;  // Data output key (matches what you set in the app)
    int pin;         // Arduino pin number
    bool isPwm;      // True for PWM/analog, False for digital
} OUTPUT_PINS[NUM_OUTPUTS] = {
    {"LED_STATUS", 5, false}    // Digital LED (on/off)
    // Add more outputs as needed:
    // {"DISPLAY_BRIGHTNESS", 6, true},  // PWM output for display brightness
    // {"LED_WARNING", 7, false}        // Another LED
};

// ================================================================
// 4. INTERNAL VARIABLES
// ================================================================

// Encoder state tracking
int lastClkState[NUM_ENCODERS];
bool lastButtonState[NUM_ENCODERS];
unsigned long lastEncoderTime[NUM_ENCODERS];
unsigned long lastButtonTime[NUM_ENCODERS];

// Timing constants
#define ENCODER_DEBOUNCE_MS 5
#define BUTTON_DEBOUNCE_MS 50

// Serial input buffer
String inputBuffer = "";

// ================================================================
// 5. SETUP
// ================================================================

void setup() {
    Serial.begin(115200);
    
    // Wait for serial port (important for USB boards like Leonardo, ESP32)
    #if defined(__AVR_ATmega32U4__) || defined(ARDUINO_ARCH_ESP32) || defined(ARDUINO_ARCH_ESP32S2) || defined(ARDUINO_ARCH_ESP32S3)
    while (!Serial) {
        delay(10);
    }
    #endif

    // Initialize encoder pins
    for (int i = 0; i < NUM_ENCODERS; i++) {
        pinMode(ENCODER_PINS[i][0], INPUT_PULLUP);  // CLK
        pinMode(ENCODER_PINS[i][1], INPUT_PULLUP);  // DT
        
        if (ENCODER_PINS[i][2] != -1) {
            pinMode(ENCODER_PINS[i][2], INPUT_PULLUP);  // Button
            lastButtonState[i] = digitalRead(ENCODER_PINS[i][2]) == LOW;
        }
        
        lastClkState[i] = digitalRead(ENCODER_PINS[i][0]);
        lastEncoderTime[i] = 0;
        lastButtonTime[i] = 0;
    }

    // Initialize output pins
    for (int i = 0; i < NUM_OUTPUTS; i++) {
        if (OUTPUT_PINS[i].isPwm) {
            pinMode(OUTPUT_PINS[i].pin, OUTPUT);
            analogWrite(OUTPUT_PINS[i].pin, 0);
        } else {
            pinMode(OUTPUT_PINS[i].pin, OUTPUT);
            digitalWrite(OUTPUT_PINS[i].pin, LOW);
        }
    }

    Serial.println("// General Encoder Ready!");
    Serial.print("// Monitoring ");
    Serial.print(NUM_ENCODERS);
    Serial.println(" encoder(s)");
}

// ================================================================
// 6. MAIN LOOP
// ================================================================

void loop() {
    // Check for messages from PC
    checkSerial();
    
    // Read all encoders
    readEncoders();
    
    // Read all encoder buttons
    readEncoderButtons();
    
    // Small delay for stability
    delay(1);
}

// ================================================================
// 7. ENCODER READING
// ================================================================

void readEncoders() {
    unsigned long currentTime = millis();
    
    for (int i = 0; i < NUM_ENCODERS; i++) {
        int clkState = digitalRead(ENCODER_PINS[i][0]);
        
        // Detect CLK state change (encoder rotation)
        if (clkState != lastClkState[i] && clkState == LOW) {
            
            // Debounce check
            if ((currentTime - lastEncoderTime[i]) > ENCODER_DEBOUNCE_MS) {
                lastEncoderTime[i] = currentTime;
                
                // Determine direction using DT pin
                int dtState = digitalRead(ENCODER_PINS[i][1]);
                
                // Send INPUT to PC
                if (dtState != clkState) {
                    // Clockwise: Send +1.0
                    sendInput(ENCODER_NAMES[i], 1.0);
                } else {
                    // Counter-clockwise: Send -1.0
                    sendInput(ENCODER_NAMES[i], -1.0);
                }
            }
        }
        
        lastClkState[i] = clkState;
    }
}

// ================================================================
// 8. ENCODER BUTTON READING
// ================================================================

void readEncoderButtons() {
    unsigned long currentTime = millis();
    
    for (int i = 0; i < NUM_ENCODERS; i++) {
        if (ENCODER_PINS[i][2] == -1) continue;
        
        bool buttonState = (digitalRead(ENCODER_PINS[i][2]) == LOW);
        
        if (buttonState != lastButtonState[i]) {
            if ((currentTime - lastButtonTime[i]) > BUTTON_DEBOUNCE_MS) {
                lastButtonTime[i] = currentTime;
                lastButtonState[i] = buttonState;
                
                // Send INPUT to PC (1.0 for pressed, 0.0 for released)
                sendInput(ENCODER_BUTTON_NAMES[i], buttonState ? 1.0 : 0.0);
            }
        }
    }
}

// ================================================================
// 9. PROTOCOL HANDLING
// ================================================================

void checkSerial() {
    while (Serial.available()) {
        char c = Serial.read();
        
        if (c == '\n') {
            processLine(inputBuffer);
            inputBuffer = "";
        } else if (c != '\r') {
            inputBuffer += c;
        }
    }
}

void processLine(String line) {
    line.trim();

    // Handshake: PC asking "Who are you?"
    if (line == "HELLO") {
        Serial.print("XPDR;fw=1.0;name=");
        Serial.println(DEVICE_NAME);
    }

    // Data output: PC sending SET command
    else if (line.startsWith("SET ")) {
        int firstSpace = line.indexOf(' ');
        int secondSpace = line.lastIndexOf(' ');

        if (firstSpace > 0 && secondSpace > firstSpace) {
            String key = line.substring(firstSpace + 1, secondSpace);
            String valStr = line.substring(secondSpace + 1);
            float value = valStr.toFloat();

            handleOutput(key, value);
        }
    }
}

// ================================================================
// 10. DATA OUTPUT HANDLING
// ================================================================

void handleOutput(String key, float value) {
    for (int i = 0; i < NUM_OUTPUTS; i++) {
        if (key == OUTPUT_PINS[i].key) {
            if (OUTPUT_PINS[i].isPwm) {
                // PWM output (0-255)
                int pwmValue = (int)(value * 255);
                analogWrite(OUTPUT_PINS[i].pin, pwmValue);
            } else {
                // Digital output (on/off)
                digitalWrite(OUTPUT_PINS[i].pin, value > 0.5 ? HIGH : LOW);
            }
            break;
        }
    }
}

// ================================================================
// 11. INPUT SENDING
// ================================================================

void sendInput(const char* key, float value) {
    Serial.print("INPUT ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(value, 1);
}

// ================================================================
// 12. HOW TO USE
// ================================================================

/*
 * SETUP IN X-PLANE DATAREF BRIDGE APP:
 * -----------------------------------
 * 1. Connect your Arduino (check correct COM port)
 * 2. Go to "Hardware" tab, verify device appears
 * 3. Go to "Mappings" tab
 * 
 * FOR ENCODER INPUTS:
 * 4. Click "Add Mapping"
 * 5. Select input key: "KNOB_0" (from ENCODER_NAMES)
 * 6. Select action type: "Increase Value (Encoder CW)" or "Decrease Value"
 * 7. Set target dataref (e.g., "sim/cockpit2/radios/actuators/com1_frequency_hz")
 * 8. Configure increment, limits, and speed multiplier
 * 9. Click "Save"
 * 
 * FOR ENCODER BUTTON:
 * 10. Click "Add Mapping"
 * 11. Select input key: "BTN_KNOB_0" (from ENCODER_BUTTON_NAMES)
 * 12. Select action type: "Set Value" or "Command"
 * 13. Set target as needed
 * 14. Click "Save"
 * 
 * FOR DATA OUTPUTS:
 * 15. Go to "Outputs" tab
 * 16. Click "Add Output"
 * 17. Set output key: "LED_STATUS" (from OUTPUT_PINS)
 * 18. Set dataref: e.g., "sim/cockpit2/annunciators/master_caution"
 * 19. Set value on and value off
 * 20. Click "Save"
 * 
 * 
 * USAGE EXAMPLES:
 * --------------
 * 
 * Example 1: Radio Frequency Knob with Status LED
 * - Encoder: Controls COM1 frequency
 * - Button: Toggles COM standby/active
 * - LED: Shows if radio is transmitting
 * 
 * Example 2: Heading Bug with Indication
 * - Encoder: Adjusts heading bug
 * - LED: Lights when autopilot is engaged
 * 
 * Example 3: Altitude Selector with Display
 * - Encoder: Adjusts selected altitude
 * - PWM Output: Controls display brightness based on cabin lights
 * 
 * 
 * CUSTOMIZATION:
 * --------------
 * 
 * To add more encoders:
 * 1. Increase NUM_ENCODERS
 * 2. Add pin definitions to ENCODER_PINS array
 * 3. Add names to ENCODER_NAMES and ENCODER_BUTTON_NAMES
 * 
 * To add more outputs:
 * 1. Increase NUM_OUTPUTS
 * 2. Add entries to OUTPUT_PINS array
 * 3. Create mappings in the app
 * 
 * To use interrupts (faster response):
 * - Requires pins 2 and 3 on Arduino Uno/Nano
 * - Any pin on ESP32
 * - See code comments in library examples for details
 */
