// ============================================================
// XPlane Dataref Bridge - Toggle Switch Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Reads toggle switches (on/off, 2-position, 3-position) and
// sends their physical position to the PC.
//
// TOGGLE vs MOMENTARY:
// --------------------
// Momentary Button: Only ON while pressed, returns to OFF
// Toggle Switch: Stays ON or OFF until you flip it again
//
// This sketch is designed for TOGGLE switches that stay in position.
// It sends the switch position on startup AND when it changes.
//
// Perfect for:
// - Master Battery
// - Avionics Master
// - Fuel Pump
// - Beacon/Nav/Strobe lights
// - Magneto switch
// - Landing gear lever (if using a physical lever)
//
// HARDWARE NEEDED:
// ----------------
// - Arduino or ESP32
// - Toggle switches (SPST, SPDT, or 3-position)
//
// WIRING:
// -------
// 2-Position Switch (SPST - Single Pole Single Throw):
//   One terminal → GND
//   Other terminal → Arduino Pin (with INPUT_PULLUP)
//
// 2-Position Switch (SPDT - Single Pole Double Throw):
//   Center terminal → Arduino Pin (with INPUT_PULLUP)
//   Top terminal → GND (for "ON")
//   Bottom terminal → Floating or another GPIO
//
// 3-Position Switch:
//   Center terminal → GND
//   Top terminal → Arduino Pin 1 (with INPUT_PULLUP)
//   Bottom terminal → Arduino Pin 2 (with INPUT_PULLUP)
//
// ============================================================

// ============================================================
// CONFIGURATION
// ============================================================

// Define your switch types
#define SWITCH_2POS   2    // Simple ON/OFF
#define SWITCH_3POS   3    // ON/OFF/ON (like magneto: L-OFF-R)

// How many switches do you have of each type?
#define NUM_2POS_SWITCHES 6
#define NUM_3POS_SWITCHES 2

// ============================================================
// 2-POSITION SWITCH CONFIGURATION
// ============================================================

// Pins for 2-position switches
const int SWITCH_2POS_PINS[NUM_2POS_SWITCHES] = {
    2,    // Master Battery
    3,    // Avionics Master
    4,    // Fuel Pump
    5,    // Beacon Light
    6,    // Nav Lights
    7     // Strobe Lights
};

// Output ID Names for 2-position switches
const char* SWITCH_2POS_NAMES[NUM_2POS_SWITCHES] = {
    "SW_BATT",
    "SW_AVIONICS", 
    "SW_FUEL_PUMP",
    "SW_BEACON",
    "SW_NAV",
    "SW_STROBE"
};

// Should the logic be inverted? 
// Set to true if switch ON should send 0 instead of 1
const bool SWITCH_2POS_INVERT[NUM_2POS_SWITCHES] = {
    false,  // Master Battery: normal
    false,  // Avionics: normal
    false,  // Fuel Pump: normal
    false,  // Beacon: normal
    false,  // Nav: normal
    false   // Strobe: normal
};

// ============================================================
// 3-POSITION SWITCH CONFIGURATION
// ============================================================

// Pins for 3-position switches
// Each switch needs 2 pins: {TOP_PIN, BOTTOM_PIN}
// Center position = both pins HIGH (pulled up)
const int SWITCH_3POS_PINS[NUM_3POS_SWITCHES][2] = {
    {8, 9},     // Magneto switch (L-OFF-R)
    {10, 11}    // Landing light (OFF-TAXI-LAND)
};

// Names for 3-position switches
const char* SWITCH_3POS_NAMES[NUM_3POS_SWITCHES] = {
    "SW_MAGNETO",
    "SW_LANDING_LT"
};

// Values for each position: {TOP, CENTER, BOTTOM}
// Customize based on what X-Plane expects
const float SWITCH_3POS_VALUES[NUM_3POS_SWITCHES][3] = {
    {0.0, 1.0, 2.0},    // Magneto: L=0, OFF=1, R=2 (or your mapping)
    {0.0, 0.5, 1.0}     // Landing light: OFF=0, TAXI=0.5, LAND=1
};

// ============================================================
// INTERNAL VARIABLES
// ============================================================

// Previous states for change detection
bool prev2PosState[NUM_2POS_SWITCHES];
int prev3PosState[NUM_3POS_SWITCHES];  // 0=TOP, 1=CENTER, 2=BOTTOM

// Flag to send all states on startup
bool needInitialSend = true;

// Debounce
unsigned long lastSwitchTime[NUM_2POS_SWITCHES + NUM_3POS_SWITCHES];
#define SWITCH_DEBOUNCE_MS 50

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Initialize 2-position switch pins
    for (int i = 0; i < NUM_2POS_SWITCHES; i++) {
        pinMode(SWITCH_2POS_PINS[i], INPUT_PULLUP);
        prev2PosState[i] = false;
        lastSwitchTime[i] = 0;
    }
    
    // Initialize 3-position switch pins
    for (int i = 0; i < NUM_3POS_SWITCHES; i++) {
        pinMode(SWITCH_3POS_PINS[i][0], INPUT_PULLUP);  // TOP
        pinMode(SWITCH_3POS_PINS[i][1], INPUT_PULLUP);  // BOTTOM
        prev3PosState[i] = 1;  // Assume CENTER
        lastSwitchTime[NUM_2POS_SWITCHES + i] = 0;
    }
    
    Serial.println("// Toggle Switch Panel Ready!");
    
    // Small delay then send initial states
    delay(100);
}

// ============================================================
// MAIN LOOP
// ============================================================

void loop() {
    // Handle messages
    if (Serial.available()) {
        String message = Serial.readStringUntil('\n');
        message.trim();
        handleMessage(message);
    }
    
    // Send initial switch positions (once, after startup)
    if (needInitialSend) {
        sendAllSwitchStates();
        needInitialSend = false;
    }
    
    // Read switches and detect changes
    read2PosSwitches();
    read3PosSwitches();
    
    delay(5);
}

// ============================================================
// SEND ALL SWITCH STATES
// ============================================================
// Called on startup to sync physical switch positions with X-Plane

void sendAllSwitchStates() {
    Serial.println("// Sending initial switch states...");
    
    // Send all 2-position switches
    for (int i = 0; i < NUM_2POS_SWITCHES; i++) {
        bool state = (digitalRead(SWITCH_2POS_PINS[i]) == LOW);
        if (SWITCH_2POS_INVERT[i]) state = !state;
        
        prev2PosState[i] = state;
        sendInput(SWITCH_2POS_NAMES[i], state ? 1.0 : 0.0);
        delay(10);  // Small delay between sends
    }
    
    // Send all 3-position switches
    for (int i = 0; i < NUM_3POS_SWITCHES; i++) {
        int position = read3PosPosition(i);
        prev3PosState[i] = position;
        
        float value = SWITCH_3POS_VALUES[i][position];
        sendInput(SWITCH_3POS_NAMES[i], value);
        delay(10);
    }
    
    Serial.println("// Initial states sent!");
}

// ============================================================
// READ 2-POSITION SWITCHES
// ============================================================

void read2PosSwitches() {
    unsigned long currentTime = millis();
    
    for (int i = 0; i < NUM_2POS_SWITCHES; i++) {
        // Read current state
        // LOW = switch connected to GND = ON
        bool state = (digitalRead(SWITCH_2POS_PINS[i]) == LOW);
        
        // Apply inversion if configured
        if (SWITCH_2POS_INVERT[i]) {
            state = !state;
        }
        
        // Check for change
        if (state != prev2PosState[i]) {
            // Debounce
            if ((currentTime - lastSwitchTime[i]) > SWITCH_DEBOUNCE_MS) {
                lastSwitchTime[i] = currentTime;
                prev2PosState[i] = state;
                
                // Send new state
                sendInput(SWITCH_2POS_NAMES[i], state ? 1.0 : 0.0);
            }
        }
    }
}

// ============================================================
// READ 3-POSITION SWITCHES
// ============================================================

int read3PosPosition(int switchIndex) {
    // Read both pins
    bool topActive = (digitalRead(SWITCH_3POS_PINS[switchIndex][0]) == LOW);
    bool bottomActive = (digitalRead(SWITCH_3POS_PINS[switchIndex][1]) == LOW);
    
    // Determine position
    // TOP: top pin LOW, bottom HIGH
    // BOTTOM: top pin HIGH, bottom LOW
    // CENTER: both pins HIGH
    if (topActive && !bottomActive) {
        return 0;  // TOP position
    } else if (!topActive && bottomActive) {
        return 2;  // BOTTOM position
    } else {
        return 1;  // CENTER position
    }
}

void read3PosSwitches() {
    unsigned long currentTime = millis();
    
    for (int i = 0; i < NUM_3POS_SWITCHES; i++) {
        int position = read3PosPosition(i);
        
        // Check for change
        if (position != prev3PosState[i]) {
            int debounceIndex = NUM_2POS_SWITCHES + i;
            
            // Debounce
            if ((currentTime - lastSwitchTime[debounceIndex]) > SWITCH_DEBOUNCE_MS) {
                lastSwitchTime[debounceIndex] = currentTime;
                prev3PosState[i] = position;
                
                // Get value for this position
                float value = SWITCH_3POS_VALUES[i][position];
                sendInput(SWITCH_3POS_NAMES[i], value);
            }
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
    Serial.println(value, 2);
}

// ============================================================
// HANDLE MESSAGE
// ============================================================

void handleMessage(String message) {
    if (message == "HELLO") {
        Serial.println("XPDR;fw=1.0;board=SwitchPanel;name=ToggleSwitches");
        
        // Resend all switch states when PC reconnects
        needInitialSend = true;
    }
    else if (message.startsWith("SET ")) {
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
// MODIFICATION IDEAS:
// ============================================================
//
// 1. ROTARY SELECTOR SWITCH:
//    For 5+ position rotary switches, use a voltage divider
//    and read with analogRead(), or use multiple pins.
//
// 2. KEY SWITCH:
//    Same as 2-position toggle, just has a key!
//
// 3. COVERED SWITCHES:
//    Guard cover is just another switch - add it!
//    Example: Starter cover opens, then starter switch pressed.
//
// 4. SPRING-LOADED SWITCHES:
//    Some switches return to center when released.
//    Treat these like momentary buttons.
//
// 5. LOCKING TOGGLES:
//    Pull-to-unlock type. Wire normally, mechanical lock.
//
// 6. LED INDICATOR INTEGRATION:
//    Add LEDs that show actual X-Plane state (not switch position).
//    This shows when sync is off.
//
// ============================================================
