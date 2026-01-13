// ============================================================
// XPlane Dataref Bridge - 7-Segment Display Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Shows numeric values on 7-segment LED displays.
// These are the classic red/green numeric displays!
//
// Perfect for:
// - Altitude display
// - Airspeed display
// - Heading display
// - Radio frequencies
// - Transponder code
// - Timer/clock
// - Engine RPM
//
// HARDWARE NEEDED:
// ----------------
// - Arduino or ESP32
// - 7-segment displays (common cathode or common anode)
// - TM1637 or MAX7219 driver module (recommended!)
//
// This example uses the TM1637 4-digit module (easiest!)
// Very cheap on Amazon/eBay, only 2 wires needed.
//
// WIRING (TM1637):
// ----------------
// Module VCC → 5V
// Module GND → GND
// Module CLK → Arduino Digital Pin (e.g., 2)
// Module DIO → Arduino Digital Pin (e.g., 3)
//
// ============================================================

// ============================================================
// INCLUDE LIBRARY
// ============================================================
// 
// Install via: Sketch → Include Library → Manage Libraries
// Search for: TM1637 by Avishay Orpaz

#include <TM1637Display.h>

// ============================================================
// CONFIGURATION
// ============================================================

// How many displays do you have?
#define NUM_DISPLAYS 4

// Pin configuration for each display: {CLK, DIO}
const int DISPLAY_PINS[NUM_DISPLAYS][2] = {
    {2, 3},     // Display 0: Altitude
    {4, 5},     // Display 1: Airspeed
    {6, 7},     // Display 2: Heading
    {8, 9}      // Display 3: VS
};

// Key names for each display
const char* DISPLAY_KEYS[NUM_DISPLAYS] = {
    "ALTITUDE",     // Display 0
    "AIRSPEED",     // Display 1
    "HEADING",      // Display 2
    "VS"            // Display 3
};

// Display modes
#define MODE_INTEGER      0   // Show as integer (1234)
#define MODE_DECIMAL      1   // Show with decimal (12.34)
#define MODE_LEADING_ZERO 2   // Show with leading zeros (0123)
#define MODE_TIME         3   // Show as time (12:34)

const int DISPLAY_MODES[NUM_DISPLAYS] = {
    MODE_INTEGER,       // Altitude: 5000
    MODE_INTEGER,       // Airspeed: 120
    MODE_LEADING_ZERO,  // Heading: 045
    MODE_INTEGER        // VS: +500 or -500
};

// Brightness (0-7)
#define DEFAULT_BRIGHTNESS 5

// ============================================================
// INTERNAL VARIABLES
// ============================================================

// Display objects
TM1637Display displays[NUM_DISPLAYS] = {
    TM1637Display(DISPLAY_PINS[0][0], DISPLAY_PINS[0][1]),
    TM1637Display(DISPLAY_PINS[1][0], DISPLAY_PINS[1][1]),
    TM1637Display(DISPLAY_PINS[2][0], DISPLAY_PINS[2][1]),
    TM1637Display(DISPLAY_PINS[3][0], DISPLAY_PINS[3][1])
};

// Current values
float currentValues[NUM_DISPLAYS];

// Segment definitions for special characters
const uint8_t SEG_DONE[] = {
    SEG_B | SEG_C | SEG_D | SEG_E | SEG_G,          // d
    SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F,  // O
    SEG_C | SEG_E | SEG_G,                          // n
    SEG_A | SEG_D | SEG_E | SEG_F | SEG_G           // E
};

const uint8_t SEG_DASH[] = {
    SEG_G,  // -
    SEG_G,  // -
    SEG_G,  // -
    SEG_G   // -
};

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Initialize all displays
    for (int i = 0; i < NUM_DISPLAYS; i++) {
        displays[i].setBrightness(DEFAULT_BRIGHTNESS);
        displays[i].clear();
        currentValues[i] = 0;
    }
    
    Serial.println("// 7-Segment Controller Ready!");
    Serial.print("// Controlling ");
    Serial.print(NUM_DISPLAYS);
    Serial.println(" displays");
    
    // Test all displays
    testDisplays();
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
    
    delay(50);
}

// ============================================================
// HANDLE MESSAGE FROM PC
// ============================================================

void handleMessage(String message) {
    // --------------------------------------------------------
    // HELLO - Handshake
    // --------------------------------------------------------
    if (message == "HELLO") {
        Serial.println("XPDR;fw=1.0;board=7Segment;name=NumericDisplay");
    }
    
    // --------------------------------------------------------
    // SET <KEY> <VALUE> - Update display value
    // --------------------------------------------------------
    else if (message.startsWith("SET ")) {
        int firstSpace = message.indexOf(' ');
        int secondSpace = message.indexOf(' ', firstSpace + 1);
        
        if (secondSpace == -1) return;
        
        String key = message.substring(firstSpace + 1, secondSpace);
        float value = message.substring(secondSpace + 1).toFloat();
        
        // Find matching display
        for (int i = 0; i < NUM_DISPLAYS; i++) {
            if (key == DISPLAY_KEYS[i]) {
                updateDisplay(i, value);
                currentValues[i] = value;
                
                // Acknowledge
                Serial.print("ACK ");
                Serial.print(key);
                Serial.print(" ");
                Serial.println(value);
                
                break;
            }
        }
    }
    
    // --------------------------------------------------------
    // BRIGHTNESS <KEY> <LEVEL> - Set brightness
    // --------------------------------------------------------
    else if (message.startsWith("BRIGHTNESS ")) {
        // Parse: BRIGHTNESS ALTITUDE 7
        String params = message.substring(11);
        int spacePos = params.indexOf(' ');
        
        if (spacePos > 0) {
            String key = params.substring(0, spacePos);
            int level = params.substring(spacePos + 1).toInt();
            level = constrain(level, 0, 7);
            
            for (int i = 0; i < NUM_DISPLAYS; i++) {
                if (key == DISPLAY_KEYS[i]) {
                    displays[i].setBrightness(level);
                    Serial.print("ACK BRIGHTNESS ");
                    Serial.print(key);
                    Serial.print(" ");
                    Serial.println(level);
                    break;
                }
            }
        }
    }
}

// ============================================================
// UPDATE DISPLAY
// ============================================================

void updateDisplay(int displayIndex, float value) {
    if (displayIndex < 0 || displayIndex >= NUM_DISPLAYS) return;
    
    TM1637Display& display = displays[displayIndex];
    int mode = DISPLAY_MODES[displayIndex];
    
    switch (mode) {
        case MODE_INTEGER:
            // Show as integer, no leading zeros
            // Handles -999 to 9999
            showInteger(display, (int)value, false);
            break;
            
        case MODE_DECIMAL:
            // Show with 2 decimal places (XX.XX)
            showDecimal(display, value);
            break;
            
        case MODE_LEADING_ZERO:
            // Show with leading zeros
            showInteger(display, (int)value, true);
            break;
            
        case MODE_TIME:
            // Show as MM:SS or HH:MM
            showTime(display, (int)value);
            break;
    }
}

// ============================================================
// DISPLAY HELPER: SHOW INTEGER
// ============================================================

void showInteger(TM1637Display& display, int value, bool leadingZeros) {
    // Handle negative numbers
    if (value < 0 && value > -1000) {
        // For negative, we can only show 3 digits + minus
        // TM1637 doesn't have a minus segment, so we use the middle segment
        value = abs(value);
        // Show minus-XXX format
        uint8_t segments[4];
        segments[0] = SEG_G;  // Minus sign
        segments[1] = display.encodeDigit((value / 100) % 10);
        segments[2] = display.encodeDigit((value / 10) % 10);
        segments[3] = display.encodeDigit(value % 10);
        display.setSegments(segments);
    }
    else {
        // Positive number or zero
        value = constrain(value, 0, 9999);
        display.showNumberDec(value, leadingZeros, 4, 0);
    }
}

// ============================================================
// DISPLAY HELPER: SHOW DECIMAL
// ============================================================

void showDecimal(TM1637Display& display, float value) {
    // Show as XX.XX format
    // Multiply by 100 and show with colon as decimal point
    int displayValue = (int)(value * 100);
    displayValue = constrain(displayValue, 0, 9999);
    
    // Show number with colon (used as decimal point)
    display.showNumberDecEx(displayValue, 0b01000000, true, 4, 0);
}

// ============================================================
// DISPLAY HELPER: SHOW TIME
// ============================================================

void showTime(TM1637Display& display, int seconds) {
    // Convert seconds to MM:SS
    int minutes = (seconds / 60) % 60;
    int secs = seconds % 60;
    
    int displayValue = minutes * 100 + secs;
    
    // Show with colon
    display.showNumberDecEx(displayValue, 0b01000000, true, 4, 0);
}

// ============================================================
// TEST DISPLAYS
// ============================================================

void testDisplays() {
    Serial.println("// Testing displays...");
    
    // Show test pattern on each display
    for (int i = 0; i < NUM_DISPLAYS; i++) {
        displays[i].showNumberDec(i + 1, false, 4, 0);
        delay(300);
    }
    
    delay(500);
    
    // Clear all
    for (int i = 0; i < NUM_DISPLAYS; i++) {
        displays[i].clear();
    }
    
    Serial.println("// Display test complete!");
}

// ============================================================
// CUSTOM SEGMENTS
// ============================================================
//
// You can display custom characters using segments:
//
//       A
//      ---
//   F |   | B
//      -G-
//   E |   | C
//      ---
//       D
//
// SEG_A = 0b00000001
// SEG_B = 0b00000010
// SEG_C = 0b00000100
// SEG_D = 0b00001000
// SEG_E = 0b00010000
// SEG_F = 0b00100000
// SEG_G = 0b01000000
// SEG_DP = 0b10000000 (decimal point, if available)
//
// Example: Letter 'H' = B + C + E + F + G
// uint8_t H = SEG_B | SEG_C | SEG_E | SEG_F | SEG_G;
//
// ============================================================

// ============================================================
// MODIFICATION IDEAS:
// ============================================================
//
// 1. COLON BLINKING:
//    Blink the colon every second for clock displays.
//
// 2. SCROLLING:
//    For numbers > 9999, scroll the digits across.
//
// 3. BRIGHTNESS DIMMING:
//    Auto-dim based on ambient light sensor.
//
// 4. ERROR DISPLAY:
//    Show "Err" when receiving invalid data.
//
// 5. FLASHING VALUES:
//    Flash warning values (like low fuel, overspeed).
//
// 6. MAX7219 CASCADING:
//    For more digits, use MAX7219 modules chained together.
//
// ============================================================
