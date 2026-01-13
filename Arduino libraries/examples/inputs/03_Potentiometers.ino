// ============================================================
// XPlane Dataref Bridge - Potentiometer/Analog Input Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Reads analog inputs (potentiometers, sliders, hall sensors)
// and sends smoothed, calibrated values to the PC.
//
// Perfect for:
// - Throttle quadrant
// - Mixture control
// - Prop pitch lever
// - Flap lever
// - Trim wheels
// - Fuel selector
//
// HARDWARE NEEDED:
// ----------------
// - Arduino (any) or ESP32
// - Potentiometers (10K linear recommended)
// - Optional: Slide potentiometers for throttle
//
// WIRING:
// -------
// Potentiometer has 3 pins:
//   Pin 1 (left)   → GND
//   Pin 2 (middle) → Analog Input (A0, A1, A2, etc.)
//   Pin 3 (right)  → 5V (or 3.3V on ESP32)
//
// ============================================================

// ============================================================
// CONFIGURATION - CHANGE THESE FOR YOUR SETUP
// ============================================================

// How many analog inputs do you have?
#define NUM_ANALOG 4

// Which analog pins are they connected to?
// On Arduino: A0, A1, A2, etc. (just use the number)
// On ESP32: Use GPIO numbers (32, 33, 34, 35 are ADC pins)
const int ANALOG_PINS[NUM_ANALOG] = {
    A0,  // Throttle 1
    A1,  // Throttle 2
    A2,  // Mixture
    A3   // Prop
};

// Names for each analog input
const char* ANALOG_NAMES[NUM_ANALOG] = {
    "POT_THR1",    // Throttle 1
    "POT_THR2",    // Throttle 2
    "POT_MIX",     // Mixture
    "POT_PROP"     // Prop
};

// ============================================================
// CALIBRATION VALUES
// ============================================================
// 
// Arduino analog reads 0-1023 (10-bit ADC)
// ESP32 reads 0-4095 (12-bit ADC)
//
// You might find your pot doesn't use the full range.
// Adjust these values to match your hardware.
// 
// HOW TO CALIBRATE:
// 1. Upload sketch with DEBUG true
// 2. Move pot to minimum position, note the raw value
// 3. Move pot to maximum position, note the raw value
// 4. Enter those values below
// ============================================================

// Set to true to print raw values for calibration
#define DEBUG_RAW_VALUES false

// Default calibration (for Arduino 0-1023)
// Format: {min_raw, max_raw}
// Set min > max if you need to invert the axis
int ANALOG_CALIBRATION[NUM_ANALOG][2] = {
    {0, 1023},      // Throttle 1: normal direction
    {0, 1023},      // Throttle 2: normal direction
    {1023, 0},      // Mixture: INVERTED (high value = lean)
    {0, 1023}       // Prop: normal direction
};

// Deadzone - ignore small changes (0.0 to 0.1 recommended)
// Prevents jitter in output
float DEADZONE[NUM_ANALOG] = {
    0.02,   // Throttle 1: 2% deadzone
    0.02,   // Throttle 2: 2% deadzone
    0.02,   // Mixture: 2% deadzone
    0.02    // Prop: 2% deadzone
};

// Change threshold - only send if value changed by this much
// Higher = less messages, but less precise
// Lower = more messages, but smoother
#define CHANGE_THRESHOLD 0.005  // 0.5% change

// Smoothing - average multiple readings to reduce noise
// Higher = smoother but slower response
// Range: 1 (no smoothing) to 20 (very smooth)
#define SMOOTHING_SAMPLES 5

// ============================================================
// INTERNAL VARIABLES
// ============================================================

// Current and previous values for change detection
float currentValue[NUM_ANALOG];
float lastSentValue[NUM_ANALOG];

// Smoothing buffer
int smoothingBuffer[NUM_ANALOG][SMOOTHING_SAMPLES];
int smoothingIndex[NUM_ANALOG];

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Initialize analog pins as inputs
    for (int i = 0; i < NUM_ANALOG; i++) {
        pinMode(ANALOG_PINS[i], INPUT);
        
        // Initialize smoothing buffer with current value
        int initialValue = analogRead(ANALOG_PINS[i]);
        for (int j = 0; j < SMOOTHING_SAMPLES; j++) {
            smoothingBuffer[i][j] = initialValue;
        }
        smoothingIndex[i] = 0;
        
        // Initialize sent values to force first send
        lastSentValue[i] = -999;
    }
    
    Serial.println("// Potentiometer Controller Ready!");
    Serial.print("// Monitoring ");
    Serial.print(NUM_ANALOG);
    Serial.println(" analog inputs");
    
    #ifdef ESP32
    // ESP32 has 12-bit ADC (0-4095) by default
    // Uncomment to change resolution:
    // analogReadResolution(10);  // Set to 10-bit (0-1023) like Arduino
    #endif
}

// ============================================================
// MAIN LOOP
// ============================================================

void loop() {
    // Handle incoming messages
    if (Serial.available()) {
        String message = Serial.readStringUntil('\n');
        message.trim();
        handleMessage(message);
    }
    
    // Read all analog inputs
    readAnalogInputs();
    
    // Delay between reads
    // Too fast = too many messages
    // Too slow = sluggish response
    delay(10);  // 100Hz update rate
}

// ============================================================
// READ ANALOG INPUTS
// ============================================================

void readAnalogInputs() {
    for (int i = 0; i < NUM_ANALOG; i++) {
        // --------------------------------------------------------
        // Step 1: Read raw value and add to smoothing buffer
        // --------------------------------------------------------
        int rawValue = analogRead(ANALOG_PINS[i]);
        
        // Add to circular buffer
        smoothingBuffer[i][smoothingIndex[i]] = rawValue;
        smoothingIndex[i] = (smoothingIndex[i] + 1) % SMOOTHING_SAMPLES;
        
        // --------------------------------------------------------
        // Step 2: Calculate smoothed (averaged) value
        // --------------------------------------------------------
        long sum = 0;
        for (int j = 0; j < SMOOTHING_SAMPLES; j++) {
            sum += smoothingBuffer[i][j];
        }
        int smoothedValue = sum / SMOOTHING_SAMPLES;
        
        // --------------------------------------------------------
        // Step 3: Debug output (if enabled)
        // --------------------------------------------------------
        #if DEBUG_RAW_VALUES
        Serial.print("// RAW ");
        Serial.print(ANALOG_NAMES[i]);
        Serial.print(": ");
        Serial.println(smoothedValue);
        #endif
        
        // --------------------------------------------------------
        // Step 4: Apply calibration
        // --------------------------------------------------------
        int minCal = ANALOG_CALIBRATION[i][0];
        int maxCal = ANALOG_CALIBRATION[i][1];
        
        // Constrain to calibration range
        // Note: constrain works even if min > max (inverted)
        if (minCal < maxCal) {
            smoothedValue = constrain(smoothedValue, minCal, maxCal);
        } else {
            smoothedValue = constrain(smoothedValue, maxCal, minCal);
        }
        
        // Map to 0.0 - 1.0
        // map() returns integer, so we do float math manually
        float normalized;
        if (maxCal != minCal) {
            normalized = (float)(smoothedValue - minCal) / (float)(maxCal - minCal);
        } else {
            normalized = 0.0;
        }
        
        // Clamp to 0.0 - 1.0 (floating point errors can exceed)
        normalized = constrain(normalized, 0.0, 1.0);
        
        // --------------------------------------------------------
        // Step 5: Apply deadzone
        // --------------------------------------------------------
        // Deadzone at both ends - if value is very close to 0 or 1,
        // snap it to exactly 0 or 1
        float dz = DEADZONE[i];
        if (normalized < dz) {
            normalized = 0.0;
        } else if (normalized > (1.0 - dz)) {
            normalized = 1.0;
        } else {
            // Rescale the middle range to use full 0-1
            normalized = (normalized - dz) / (1.0 - 2.0 * dz);
        }
        
        // Store current value
        currentValue[i] = normalized;
        
        // --------------------------------------------------------
        // Step 6: Check if value changed enough to send
        // --------------------------------------------------------
        float change = abs(normalized - lastSentValue[i]);
        
        if (change >= CHANGE_THRESHOLD) {
            // Value changed significantly - send it!
            sendInput(ANALOG_NAMES[i], normalized);
            lastSentValue[i] = normalized;
        }
    }
}

// ============================================================
// SEND INPUT
// ============================================================

void sendInput(const char* key, float value) {
    Serial.print("INPUT ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(value, 4);  // 4 decimal places for precision
}

// ============================================================
// HANDLE MESSAGE
// ============================================================

void handleMessage(String message) {
    if (message == "HELLO") {
        Serial.println("XPDR;fw=1.0;board=ThrottleQuadrant;name=AnalogInputs");
    }
    else if (message.startsWith("SET ")) {
        // Acknowledge SET commands
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
// CALIBRATION HELPER
// ============================================================
// 
// Uncomment this function and call it from loop() to help
// find your calibration values.
// 
// void printCalibrationHelper() {
//     static unsigned long lastPrint = 0;
//     if (millis() - lastPrint > 500) {  // Print every 500ms
//         lastPrint = millis();
//         
//         Serial.print("// CALIBRATION: ");
//         for (int i = 0; i < NUM_ANALOG; i++) {
//             Serial.print(ANALOG_NAMES[i]);
//             Serial.print("=");
//             Serial.print(analogRead(ANALOG_PINS[i]));
//             Serial.print(" ");
//         }
//         Serial.println();
//     }
// }
//
// ============================================================

// ============================================================
// MODIFICATION IDEAS:
// ============================================================
//
// 1. CUSTOM CURVES:
//    Apply exponential or logarithmic curves for non-linear
//    response. Good for throttle detents.
//
//    float applyCurve(float value, float curve) {
//        return pow(value, curve);  // curve > 1 = soft start
//    }
//
// 2. DETENTS:
//    Snap to specific positions (idle, MCT, TOGA).
//
//    float applyDetent(float value, float detent, float range) {
//        if (abs(value - detent) < range) return detent;
//        return value;
//    }
//
// 3. SPLIT AXIS:
//    One pot controls two things (like reverser/throttle).
//    Below 25% = reverse thrust
//    Above 25% = forward thrust
//
// 4. COMBINED AXES:
//    Two pots control one axis (like yoke).
//    Use max() or average of both.
//
// 5. HALL EFFECT SENSORS:
//    Same code works! Just wire the analog output to Arduino.
//
// 6. LINEAR vs LOGARITHMIC:
//    Audio taper pots are logarithmic - apply inverse curve.
//
// ============================================================
