// ============================================================
// XPlane Dataref Bridge - Servo Motor Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Moves servo motors to positions based on X-Plane data.
// Perfect for analog gauges and physical indicators!
//
// Perfect for:
// - Airspeed indicator
// - Altimeter
// - Attitude indicator (artificial horizon)
// - Fuel gauge
// - Flap position indicator
// - Trim indicator
// - VSI (Vertical Speed Indicator)
// - Engine gauges (RPM, manifold pressure, etc.)
//
// HARDWARE NEEDED:
// ----------------
// - Arduino or ESP32
// - Servo motors (SG90 micro servos are great for gauges)
// - External power supply for servos (recommended for 3+ servos)
//
// WIRING:
// -------
// Servo has 3 wires:
//   Brown/Black → GND
//   Red → 5V (or external 5-6V supply)
//   Orange/Yellow/White → Arduino PWM pin
//
// IMPORTANT: If using more than 1-2 servos, power them
// from an external supply, not the Arduino 5V pin!
// Share GND between Arduino and external supply.
//
// ============================================================

// ============================================================
// INCLUDE SERVO LIBRARY
// ============================================================
// 
// Arduino has a built-in Servo library.
// For ESP32, we'll use the ESP32Servo library.
// Install it via: Sketch → Include Library → Manage Libraries
// Search for: ESP32Servo

#ifdef ESP32
    #include <ESP32Servo.h>
#else
    #include <Servo.h>
#endif

// ============================================================
// CONFIGURATION
// ============================================================

// How many servos do you have?
#define NUM_SERVOS 4

// What pins are the servos connected to?
// Arduino: Use any digital pin
// ESP32: Use GPIO pins 2, 4, 12-19, 21-23, 25-27, 32-33
const int SERVO_PINS[NUM_SERVOS] = {
    9,    // Servo 0: Airspeed
    10,   // Servo 1: Altitude
    11,   // Servo 2: Fuel
    12    // Servo 3: Flaps
};

// What key should control each servo?
// These must match the Output Keys in the PC app!
const char* SERVO_KEYS[NUM_SERVOS] = {
    "AIRSPEED",   // Servo 0
    "ALTITUDE",   // Servo 1
    "FUEL",       // Servo 2
    "FLAPS"       // Servo 3
};

// ============================================================
// SERVO CALIBRATION
// ============================================================
// 
// Servos typically move from 0 to 180 degrees.
// But your gauge might not use the full range!
// 
// Set the minimum and maximum angle for each servo:
//   - min_angle: Position when input value = 0.0
//   - max_angle: Position when input value = 1.0

// Format: {min_angle, max_angle}
const int SERVO_ANGLES[NUM_SERVOS][2] = {
    {20, 160},    // Airspeed: 20° to 160° (140° range)
    {0, 180},     // Altitude: Full range
    {30, 150},    // Fuel: 30° to 150°
    {0, 90}       // Flaps: 0° to 90°
};

// ============================================================
// INPUT VALUE SCALING
// ============================================================
//
// X-Plane sends different ranges for different datarefs:
//   - Airspeed: 0 to ~250+ knots
//   - Altitude: 0 to ~50000 feet
//   - Fuel: 0.0 to 1.0 (ratio)
//   - Flaps: 0.0 to 1.0 (ratio)
//
// We need to map these to 0.0-1.0 for the servo.
// Set the expected input range for each:

// Format: {min_input, max_input}
const float SERVO_INPUT_RANGE[NUM_SERVOS][2] = {
    {0, 200},     // Airspeed: 0-200 knots → 0-1
    {0, 20000},   // Altitude: 0-20000 feet → 0-1
    {0, 1},       // Fuel: already 0-1
    {0, 1}        // Flaps: already 0-1
};

// Smoothing factor (0.0 to 1.0)
// Higher = slower, smoother movement
// Lower = faster, more responsive
// 0.9 is a good starting point
const float SERVO_SMOOTHING = 0.9;

// ============================================================
// INTERNAL VARIABLES
// ============================================================

// Servo objects
Servo servos[NUM_SERVOS];

// Current and target positions
float currentPosition[NUM_SERVOS];
float targetPosition[NUM_SERVOS];

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Attach servos to pins
    for (int i = 0; i < NUM_SERVOS; i++) {
        servos[i].attach(SERVO_PINS[i]);
        
        // Start at minimum position
        int minAngle = SERVO_ANGLES[i][0];
        servos[i].write(minAngle);
        
        currentPosition[i] = 0;
        targetPosition[i] = 0;
    }
    
    Serial.println("// Servo Controller Ready!");
    Serial.print("// Controlling ");
    Serial.print(NUM_SERVOS);
    Serial.println(" servos");
    
    // Sweep all servos to show they're working
    testAllServos();
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
    
    // Smoothly move servos to target positions
    updateServos();
    
    // Small delay for smooth movement
    delay(20);  // 50Hz update rate
}

// ============================================================
// UPDATE SERVOS - SMOOTH MOVEMENT
// ============================================================

void updateServos() {
    for (int i = 0; i < NUM_SERVOS; i++) {
        // Apply smoothing
        // New position = (old * smoothing) + (target * (1 - smoothing))
        currentPosition[i] = (currentPosition[i] * SERVO_SMOOTHING) + 
                             (targetPosition[i] * (1.0 - SERVO_SMOOTHING));
        
        // Map position (0.0-1.0) to angle
        int minAngle = SERVO_ANGLES[i][0];
        int maxAngle = SERVO_ANGLES[i][1];
        
        int angle = minAngle + (int)(currentPosition[i] * (maxAngle - minAngle));
        angle = constrain(angle, min(minAngle, maxAngle), max(minAngle, maxAngle));
        
        // Move servo
        servos[i].write(angle);
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
        Serial.println("XPDR;fw=1.0;board=ServoController;name=Gauges");
    }
    
    // --------------------------------------------------------
    // SET <KEY> <VALUE> - Update servo target
    // --------------------------------------------------------
    else if (message.startsWith("SET ")) {
        // Parse the message
        int firstSpace = message.indexOf(' ');
        int secondSpace = message.indexOf(' ', firstSpace + 1);
        
        if (secondSpace == -1) return;
        
        String key = message.substring(firstSpace + 1, secondSpace);
        float value = message.substring(secondSpace + 1).toFloat();
        
        // Find matching servo
        for (int i = 0; i < NUM_SERVOS; i++) {
            if (key == SERVO_KEYS[i]) {
                // Map input value to 0.0-1.0 range
                float minInput = SERVO_INPUT_RANGE[i][0];
                float maxInput = SERVO_INPUT_RANGE[i][1];
                
                float normalized;
                if (maxInput != minInput) {
                    normalized = (value - minInput) / (maxInput - minInput);
                } else {
                    normalized = 0;
                }
                
                // Clamp to 0-1
                normalized = constrain(normalized, 0.0, 1.0);
                
                // Set target position
                targetPosition[i] = normalized;
                
                // Acknowledge
                Serial.print("ACK ");
                Serial.print(key);
                Serial.print(" ");
                Serial.println(value);
                
                break;
            }
        }
    }
}

// ============================================================
// TEST ALL SERVOS
// ============================================================

void testAllServos() {
    Serial.println("// Testing servos...");
    
    // Move to minimum
    for (int i = 0; i < NUM_SERVOS; i++) {
        servos[i].write(SERVO_ANGLES[i][0]);
    }
    delay(500);
    
    // Move to maximum
    for (int i = 0; i < NUM_SERVOS; i++) {
        servos[i].write(SERVO_ANGLES[i][1]);
    }
    delay(500);
    
    // Return to minimum
    for (int i = 0; i < NUM_SERVOS; i++) {
        servos[i].write(SERVO_ANGLES[i][0]);
    }
    
    Serial.println("// Servo test complete!");
}

// ============================================================
// HELPER: DIRECT ANGLE CONTROL
// ============================================================

void setServoAngle(int servoIndex, int angle) {
    if (servoIndex >= 0 && servoIndex < NUM_SERVOS) {
        angle = constrain(angle, 0, 180);
        servos[servoIndex].write(angle);
    }
}

// ============================================================
// ADVANCED: NON-LINEAR GAUGE SCALES
// ============================================================
//
// Real gauges often have non-linear scales.
// For example, airspeed indicators are compressed at high speeds.
//
// float applyAirspeedScale(float linearValue) {
//     // Example: logarithmic-ish scale
//     // Adjust these values for your gauge dial
//     return pow(linearValue, 0.7);
// }
//
// ============================================================

// ============================================================
// ADVANCED: STEPPER MOTORS
// ============================================================
//
// For gauges needing more than 180° rotation or higher precision,
// use stepper motors with drivers like A4988 or TMC2209.
//
// See: 03_StepperMotors.ino
//
// ============================================================

// ============================================================
// MODIFICATION IDEAS:
// ============================================================
//
// 1. MULTIPLE NEEDLE GAUGES:
//    Altimeter has 3 needles - use 3 servos on one gauge!
//
// 2. EASING FUNCTIONS:
//    Add acceleration/deceleration for more realistic movement.
//
// 3. LIMITS WITH WARNINGS:
//    Move to red zone position and vibrate at limits.
//
// 4. NEEDLE CALIBRATION:
//    Add commands to manually calibrate needle positions.
//
// 5. POWER SAVING:
//    Detach servos when at rest position to reduce power/noise.
//
// 6. DIRECT ANGLE MODE:
//    Some datarefs give degrees directly - skip scaling.
//
// ============================================================
