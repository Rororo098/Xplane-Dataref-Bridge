// ============================================================
// XPlane Dataref Bridge - Rotary Encoder Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Reads rotary encoders (the spinny knobs with clicks) and sends
// rotation direction to the PC.
//
// Rotary encoders are perfect for:
// - Heading bug adjustment
// - Altitude selector
// - Radio frequency tuning
// - Trim wheels
// - Barometer setting
//
// HARDWARE NEEDED:
// ----------------
// - Arduino (Nano, Uno, Leonardo) or ESP32
// - Rotary encoders (KY-040 or similar)
// - Optional: encoders with push button
//
// WIRING (for KY-040 encoder):
// ----------------------------
// Encoder CLK → Arduino Pin (e.g., 2)
// Encoder DT  → Arduino Pin (e.g., 3)
// Encoder SW  → Arduino Pin (e.g., 4) [optional, for button]
// Encoder +   → 5V
// Encoder GND → GND
//
// HOW ENCODERS WORK:
// ------------------
// When you turn an encoder, it generates a pattern of HIGH/LOW
// signals on two pins (CLK and DT). By reading the pattern,
// we can tell which direction you're turning.
//
// ============================================================

// ============================================================
// CONFIGURATION - CHANGE THESE FOR YOUR SETUP
// ============================================================

// How many encoders do you have?
#define NUM_ENCODERS 3

// Encoder pin definitions
// Each encoder needs 2 pins (CLK and DT) and optionally a button pin
// Format: {CLK_PIN, DT_PIN, BUTTON_PIN}
// Use -1 for BUTTON_PIN if the encoder doesn't have a button
const int ENCODER_PINS[NUM_ENCODERS][3] = {
    {2, 3, 4},     // Encoder 0: Heading (CLK=2, DT=3, Button=4)
    {5, 6, 7},     // Encoder 1: Altitude (CLK=5, DT=6, Button=7)
    {8, 9, 10}     // Encoder 2: Baro (CLK=8, DT=9, Button=10)
};

// Encoder names - what each encoder is called
// CW = Clockwise, CCW = Counter-Clockwise
const char* ENCODER_NAMES_CW[NUM_ENCODERS] = {
    "ENC_HDG_CW",   // Encoder 0 clockwise
    "ENC_ALT_CW",   // Encoder 1 clockwise
    "ENC_BARO_CW"   // Encoder 2 clockwise
};

const char* ENCODER_NAMES_CCW[NUM_ENCODERS] = {
    "ENC_HDG_CCW",   // Encoder 0 counter-clockwise
    "ENC_ALT_CCW",   // Encoder 1 counter-clockwise
    "ENC_BARO_CCW"   // Encoder 2 counter-clockwise
};

const char* ENCODER_BUTTON_NAMES[NUM_ENCODERS] = {
    "BTN_HDG_SEL",   // Encoder 0 button
    "BTN_ALT_SEL",   // Encoder 1 button
    "BTN_BARO_STD"   // Encoder 2 button
};

// ============================================================
// INTERNAL VARIABLES - DON'T CHANGE THESE
// ============================================================

// Store the last state of the CLK pin for each encoder
// This is used to detect rotation direction
int lastClkState[NUM_ENCODERS];

// Store the last button state
bool lastButtonState[NUM_ENCODERS];

// Debounce timing
unsigned long lastEncoderTime[NUM_ENCODERS];
unsigned long lastButtonTime[NUM_ENCODERS];

#define ENCODER_DEBOUNCE_MS 5    // For encoder rotation
#define BUTTON_DEBOUNCE_MS 50    // For encoder button

// ============================================================
// SETUP - RUNS ONCE WHEN ARDUINO POWERS ON
// ============================================================

void setup() {
    // --------------------------------------------------------
    // Initialize Serial Communication
    // --------------------------------------------------------
    Serial.begin(115200);
    
    // Wait for serial port (important for USB boards)
    while (!Serial) {
        delay(10);
    }
    
    // --------------------------------------------------------
    // Initialize Encoder Pins
    // --------------------------------------------------------
    for (int i = 0; i < NUM_ENCODERS; i++) {
        // CLK and DT pins as INPUT_PULLUP
        pinMode(ENCODER_PINS[i][0], INPUT_PULLUP);  // CLK
        pinMode(ENCODER_PINS[i][1], INPUT_PULLUP);  // DT
        
        // Button pin (if present, pin != -1)
        if (ENCODER_PINS[i][2] != -1) {
            pinMode(ENCODER_PINS[i][2], INPUT_PULLUP);  // Button
            lastButtonState[i] = false;
        }
        
        // Read initial CLK state
        lastClkState[i] = digitalRead(ENCODER_PINS[i][0]);
        
        // Initialize timing
        lastEncoderTime[i] = 0;
        lastButtonTime[i] = 0;
    }
    
    Serial.println("// Rotary Encoders Ready!");
    Serial.print("// Monitoring ");
    Serial.print(NUM_ENCODERS);
    Serial.println(" encoders");
}

// ============================================================
// MAIN LOOP - RUNS FOREVER
// ============================================================

void loop() {
    // Check for messages from PC
    if (Serial.available()) {
        String message = Serial.readStringUntil('\n');
        message.trim();
        handleMessage(message);
    }
    
    // Read all encoders
    readEncoders();
    
    // Read all encoder buttons
    readEncoderButtons();
    
    // Small delay - encoders need fast polling!
    delay(1);
}

// ============================================================
// READ ENCODERS - DETECT ROTATION
// ============================================================

void readEncoders() {
    unsigned long currentTime = millis();
    
    for (int i = 0; i < NUM_ENCODERS; i++) {
        // --------------------------------------------------------
        // Read current state of CLK pin
        // --------------------------------------------------------
        int clkState = digitalRead(ENCODER_PINS[i][0]);
        
        // --------------------------------------------------------
        // Did CLK state change? (Encoder moved)
        // --------------------------------------------------------
        // We trigger on CLK going from HIGH to LOW
        // (falling edge detection)
        if (clkState != lastClkState[i] && clkState == LOW) {
            
            // Debounce check
            if ((currentTime - lastEncoderTime[i]) > ENCODER_DEBOUNCE_MS) {
                lastEncoderTime[i] = currentTime;
                
                // --------------------------------------------------------
                // Determine rotation direction
                // --------------------------------------------------------
                // Read the DT pin state
                // If DT is different from CLK, we're going clockwise
                // If DT is same as CLK, we're going counter-clockwise
                int dtState = digitalRead(ENCODER_PINS[i][1]);
                
                if (dtState != clkState) {
                    // Clockwise rotation
                    sendInput(ENCODER_NAMES_CW[i], 1.0);
                } else {
                    // Counter-clockwise rotation
                    sendInput(ENCODER_NAMES_CCW[i], 1.0);
                }
            }
        }
        
        // Remember CLK state for next iteration
        lastClkState[i] = clkState;
    }
}

// ============================================================
// READ ENCODER BUTTONS
// ============================================================

void readEncoderButtons() {
    unsigned long currentTime = millis();
    
    for (int i = 0; i < NUM_ENCODERS; i++) {
        // Skip if this encoder has no button
        if (ENCODER_PINS[i][2] == -1) continue;
        
        // Read current button state
        bool buttonState = (digitalRead(ENCODER_PINS[i][2]) == LOW);
        
        // Check for state change
        if (buttonState != lastButtonState[i]) {
            // Debounce check
            if ((currentTime - lastButtonTime[i]) > BUTTON_DEBOUNCE_MS) {
                lastButtonTime[i] = currentTime;
                lastButtonState[i] = buttonState;
                
                // Send button state
                sendInput(ENCODER_BUTTON_NAMES[i], buttonState ? 1.0 : 0.0);
            }
        }
    }
}

// ============================================================
// SEND INPUT - SEND AN INPUT EVENT TO THE PC
// ============================================================

void sendInput(const char* key, float value) {
    Serial.print("INPUT ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(value, 1);
}

// ============================================================
// HANDLE MESSAGE - PROCESS MESSAGES FROM PC
// ============================================================

void handleMessage(String message) {
    if (message == "HELLO") {
        Serial.println("XPDR;fw=1.0;board=Encoders;name=EncoderPanel");
    }
    else if (message.startsWith("SET ")) {
        // Encoders don't usually have outputs, but acknowledge anyway
        int firstSpace = message.indexOf(' ');
        int secondSpace = message.indexOf(' ', firstSpace + 1);
        String key = message.substring(firstSpace + 1, secondSpace);
        float value = message.substring(secondSpace + 1).toFloat();
        
        Serial.print("ACK ");
        Serial.print(key);
        Serial.print(" ");
        Serial.println(value);
    }
}

// ============================================================
// ALTERNATIVE: USING INTERRUPTS FOR FASTER RESPONSE
// ============================================================
// 
// The polling method above works well, but for very fast
// turning or multiple encoders, interrupts are better.
//
// Here's how to use interrupts (for one encoder):
//
// volatile int encoderCount = 0;
// 
// void setup() {
//     attachInterrupt(digitalPinToInterrupt(2), encoderISR, CHANGE);
// }
// 
// void encoderISR() {
//     int clk = digitalRead(2);
//     int dt = digitalRead(3);
//     if (clk != dt) encoderCount++;
//     else encoderCount--;
// }
//
// void loop() {
//     if (encoderCount != 0) {
//         sendInput("ENC_HDG", encoderCount);
//         encoderCount = 0;
//     }
// }
//
// Note: Only pins 2 and 3 support interrupts on Arduino Uno/Nano
// ESP32 can use interrupts on any GPIO pin
//
// ============================================================

// ============================================================
// ALTERNATIVE: SEND SINGLE ENCODER VALUE WITH DIRECTION
// ============================================================
//
// Instead of separate CW/CCW events, you could send:
//   ENC_HDG 1.0   (for clockwise)
//   ENC_HDG -1.0  (for counter-clockwise)
//
// This requires only one input name per encoder:
//
// void onEncoderRotate(int encoderIndex, bool clockwise) {
//     float value = clockwise ? 1.0 : -1.0;
//     sendInput(ENCODER_NAMES[encoderIndex], value);
// }
//
// ============================================================

// ============================================================
// MODIFICATION IDEAS:
// ============================================================
//
// 1. ACCELERATION:
//    Turn faster = bigger value changes.
//    Track time between clicks and multiply value accordingly.
//
// 2. VELOCITY BASED:
//    Instead of sending each click, send rotation speed.
//    Great for smooth analog-like control.
//
// 3. DUAL CONCENTRIC ENCODERS:
//    Some radios have two encoders on one shaft.
//    Wire inner and outer as separate encoders.
//
// 4. PUSH-TO-MULTIPLY:
//    When encoder button is held, multiply value by 10.
//    Great for fast altitude changes.
//
// 5. DIRECT COMMANDS:
//    Instead of INPUT messages, send X-Plane commands:
//    sendCommand("sim/autopilot/heading_up");
//
// ============================================================
