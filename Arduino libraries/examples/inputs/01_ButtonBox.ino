// ============================================================
// XPlane Dataref Bridge - Button Box Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Reads multiple buttons and sends their state to the PC.
// Each button press/release is sent as an INPUT message.
//
// HARDWARE NEEDED:
// ----------------
// - Arduino (Nano, Uno, Leonardo) or ESP32
// - Push buttons (momentary, normally open)
// - Optional: 10K pull-up resistors (or use internal pull-ups)
//
// WIRING:
// -------
// Button 1: Pin 2 → Button → GND
// Button 2: Pin 3 → Button → GND
// Button 3: Pin 4 → Button → GND
// (Add more as needed)
//
// We use INPUT_PULLUP so buttons connect pin to GND when pressed.
// No external resistors needed!
//
// ============================================================

// ============================================================
// CONFIGURATION - CHANGE THESE FOR YOUR SETUP
// ============================================================

// How many buttons do you have?
#define NUM_BUTTONS 8

// What pins are the buttons connected to?
// Change these to match your wiring!
const int BUTTON_PINS[NUM_BUTTONS] = {
    2,   // Button 0: Gear Toggle
    3,   // Button 1: Flaps Up
    4,   // Button 2: Flaps Down
    5,   // Button 3: Autopilot Master
    6,   // Button 4: Heading Hold
    7,   // Button 5: Nav Hold
    8,   // Button 6: Approach Mode
    9    // Button 7: Landing Lights
};

// What should each button be called?
// These names are sent to the PC application.
// Use descriptive names so you know what each button does!
const char* BUTTON_NAMES[NUM_BUTTONS] = {
    "BTN_GEAR",      // Button 0
    "BTN_FLAP_UP",   // Button 1
    "BTN_FLAP_DN",   // Button 2
    "BTN_AP",        // Button 3
    "BTN_HDG",       // Button 4
    "BTN_NAV",       // Button 5
    "BTN_APR",       // Button 6
    "BTN_LAND_LT"    // Button 7
};

// Debounce time in milliseconds
// Prevents multiple triggers from button bounce
// Increase if buttons trigger multiple times per press
#define DEBOUNCE_MS 50

// ============================================================
// INTERNAL VARIABLES - DON'T CHANGE THESE
// ============================================================

// Store the last state of each button
// true = pressed, false = released
bool buttonStates[NUM_BUTTONS];

// Store the last time each button changed state
// Used for debouncing
unsigned long lastDebounceTime[NUM_BUTTONS];

// ============================================================
// SETUP - RUNS ONCE WHEN ARDUINO POWERS ON
// ============================================================

void setup() {
    // --------------------------------------------------------
    // Initialize Serial Communication
    // --------------------------------------------------------
    // 115200 is the baud rate - must match the PC application!
    // This is how fast data is sent (115200 bits per second)
    Serial.begin(115200);
    
    // Wait for serial port to be ready
    // This is important for boards with native USB (Leonardo, ESP32)
    while (!Serial) {
        delay(10);  // Wait 10 milliseconds
    }
    
    // --------------------------------------------------------
    // Initialize Button Pins
    // --------------------------------------------------------
    for (int i = 0; i < NUM_BUTTONS; i++) {
        // Set each pin as INPUT_PULLUP
        // INPUT_PULLUP means:
        //   - The pin reads HIGH (1) when button is NOT pressed
        //   - The pin reads LOW (0) when button IS pressed
        //   - Uses internal pull-up resistor (no external resistor needed!)
        pinMode(BUTTON_PINS[i], INPUT_PULLUP);
        
        // Initialize state as "not pressed"
        // We invert because INPUT_PULLUP reads LOW when pressed
        buttonStates[i] = false;
        
        // Initialize debounce timer
        lastDebounceTime[i] = 0;
    }
    
    // --------------------------------------------------------
    // Print startup message (for debugging in Serial Monitor)
    // --------------------------------------------------------
    Serial.println("// Button Box Ready!");
    Serial.print("// Monitoring ");
    Serial.print(NUM_BUTTONS);
    Serial.println(" buttons");
}

// ============================================================
// MAIN LOOP - RUNS FOREVER
// ============================================================

void loop() {
    // --------------------------------------------------------
    // Check for messages from PC
    // --------------------------------------------------------
    // The PC might send us a "HELLO" to check if we're ready
    if (Serial.available()) {
        String message = Serial.readStringUntil('\n');
        message.trim();  // Remove whitespace and newline
        handleMessage(message);
    }
    
    // --------------------------------------------------------
    // Read all buttons and detect changes
    // --------------------------------------------------------
    readButtons();
    
    // Small delay to prevent overwhelming the CPU
    // 1ms is enough - we check buttons 1000 times per second
    delay(1);
}

// ============================================================
// READ BUTTONS - CHECK ALL BUTTONS FOR STATE CHANGES
// ============================================================

void readButtons() {
    // Current time in milliseconds since Arduino started
    unsigned long currentTime = millis();
    
    // Check each button
    for (int i = 0; i < NUM_BUTTONS; i++) {
        // --------------------------------------------------------
        // Read the current physical state of the button
        // --------------------------------------------------------
        // digitalRead() returns HIGH (1) or LOW (0)
        // With INPUT_PULLUP: LOW = pressed, HIGH = not pressed
        // We invert it so: true = pressed, false = not pressed
        bool currentState = (digitalRead(BUTTON_PINS[i]) == LOW);
        
        // --------------------------------------------------------
        // Check if the state has changed
        // --------------------------------------------------------
        if (currentState != buttonStates[i]) {
            // --------------------------------------------------------
            // Debounce: Has enough time passed since last change?
            // --------------------------------------------------------
            // When a button is pressed/released, it "bounces" - 
            // rapidly switching between on and off for a few milliseconds.
            // We ignore changes that happen too quickly.
            if ((currentTime - lastDebounceTime[i]) > DEBOUNCE_MS) {
                // Enough time has passed, this is a real press/release
                
                // Update the stored state
                buttonStates[i] = currentState;
                
                // Update the debounce timer
                lastDebounceTime[i] = currentTime;
                
                // --------------------------------------------------------
                // Send the state change to the PC!
                // --------------------------------------------------------
                // Value: 1.0 = pressed, 0.0 = released
                float value = currentState ? 1.0 : 0.0;
                sendInput(BUTTON_NAMES[i], value);
            }
        }
    }
}

// ============================================================
// SEND INPUT - SEND A BUTTON STATE TO THE PC
// ============================================================

void sendInput(const char* key, float value) {
    // Format: INPUT <KEY> <VALUE>
    // Example: INPUT BTN_GEAR 1.0
    
    Serial.print("INPUT ");     // The command type
    Serial.print(key);          // The button name
    Serial.print(" ");          // Space separator
    Serial.println(value, 1);   // The value (1 decimal place)
    
    // Note: println() adds a newline at the end
    // This is important - the PC looks for newlines to know
    // when a message is complete!
}

// ============================================================
// HANDLE MESSAGE - PROCESS MESSAGES FROM PC
// ============================================================

void handleMessage(String message) {
    // --------------------------------------------------------
    // HELLO - Handshake from PC
    // --------------------------------------------------------
    if (message == "HELLO") {
        // Respond with device information
        // Format: XPDR;fw=<version>;board=<type>;name=<name>
        Serial.println("XPDR;fw=1.0;board=ButtonBox;name=MyButtonBox");
    }
    
    // --------------------------------------------------------
    // SET commands - PC wants us to do something
    // --------------------------------------------------------
    // For a button box (input only), we don't usually need SET commands
    // But we handle them anyway for completeness
    else if (message.startsWith("SET ")) {
        // Button boxes typically don't have outputs
        // But you could add status LEDs here!
        
        // Parse the message
        int firstSpace = message.indexOf(' ');
        int secondSpace = message.indexOf(' ', firstSpace + 1);
        String key = message.substring(firstSpace + 1, secondSpace);
        float value = message.substring(secondSpace + 1).toFloat();
        
        // Acknowledge the message
        Serial.print("ACK ");
        Serial.print(key);
        Serial.print(" ");
        Serial.println(value);
    }
}

// ============================================================
// ADVANCED: HELPER FUNCTIONS FOR DIFFERENT BUTTON TYPES
// ============================================================

// --------------------------------------------------------
// Send an X-Plane command directly
// Use this instead of INPUT if you know exactly what
// command you want to trigger
// --------------------------------------------------------
void sendCommand(const char* command) {
    Serial.print("CMD ");
    Serial.println(command);
}

// --------------------------------------------------------
// Example: Trigger gear toggle command directly
// Call this from readButtons() if you want a button
// to directly send a command without PC-side mapping
// --------------------------------------------------------
void onGearButtonPressed() {
    sendCommand("sim/flight_controls/landing_gear_toggle");
}

// ============================================================
// MODIFICATION IDEAS:
// ============================================================
//
// 1. ADD MORE BUTTONS:
//    - Increase NUM_BUTTONS
//    - Add pins to BUTTON_PINS array
//    - Add names to BUTTON_NAMES array
//
// 2. USE A BUTTON MATRIX:
//    For lots of buttons (16+), use a matrix to save pins.
//    See: 02_ButtonMatrix.ino
//
// 3. ADD TOGGLE SWITCHES:
//    Toggle switches work differently - they stay on/off.
//    The code above works for both, but you might want
//    to send the state on startup too.
//
// 4. ADD STATUS LEDS:
//    Add LEDs that light up when a button is pressed.
//    Use the SET message to control them.
//
// 5. DIRECT COMMANDS:
//    Instead of sending INPUT messages, you could have
//    buttons directly send X-Plane commands using:
//    sendCommand("sim/some/command");
//
// ============================================================
