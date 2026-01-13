// ============================================================
// XPlane Dataref Bridge - LCD Display Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Displays X-Plane data on LCD screens!
// Shows text and numbers in a readable format.
//
// Perfect for:
// - Radio frequencies (COM1, NAV1, etc.)
// - Autopilot settings (ALT, HDG, VS, SPD)
// - Flight data (altitude, speed, heading)
// - Fuel quantities
// - Timer/clock display
// - Custom MFD panels
//
// HARDWARE NEEDED:
// ----------------
// - Arduino or ESP32
// - LCD display (16x2 or 20x4 character LCD)
// - I2C backpack (recommended) OR direct wiring
//
// LCD TYPES SUPPORTED:
// --------------------
// 1. 16x2 Character LCD (16 chars, 2 rows)
// 2. 20x4 Character LCD (20 chars, 4 rows)
// 3. I2C versions (2 wires only!)
//
// WIRING (I2C Version - Recommended!):
// ------------------------------------
// LCD VCC → 5V
// LCD GND → GND
// LCD SDA → Arduino A4 (or ESP32 GPIO21)
// LCD SCL → Arduino A5 (or ESP32 GPIO22)
//
// ============================================================

// ============================================================
// INCLUDE LIBRARIES
// ============================================================
// 
// Install via: Sketch → Include Library → Manage Libraries
// Search for: LiquidCrystal I2C

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ============================================================
// CONFIGURATION
// ============================================================

// LCD Configuration
// Common I2C addresses: 0x27 or 0x3F
// If display doesn't work, try the other address!
#define LCD_ADDRESS 0x27

// LCD Size: columns x rows
#define LCD_COLS 20
#define LCD_ROWS 4

// For 16x2 LCD, use:
// #define LCD_COLS 16
// #define LCD_ROWS 2

// ============================================================
// DATA KEYS - What data we're displaying
// ============================================================
// 
// These are the keys that the PC app will send us.
// Each key has a display position and format.

// How many values are we displaying?
#define NUM_VALUES 8

// Key names - must match Output Keys in PC app!
const char* VALUE_KEYS[NUM_VALUES] = {
    "COM1_ACT",     // Active COM1 frequency
    "COM1_STB",     // Standby COM1 frequency
    "NAV1_ACT",     // Active NAV1 frequency
    "NAV1_STB",     // Standby NAV1 frequency
    "AP_ALT",       // Autopilot altitude
    "AP_HDG",       // Autopilot heading
    "AP_VS",        // Autopilot vertical speed
    "AP_SPD"        // Autopilot speed
};

// Display position for each value: {row, column}
const int VALUE_POS[NUM_VALUES][2] = {
    {0, 0},     // COM1_ACT: Row 0, Column 0
    {0, 10},    // COM1_STB: Row 0, Column 10
    {1, 0},     // NAV1_ACT: Row 1, Column 0
    {1, 10},    // NAV1_STB: Row 1, Column 10
    {2, 0},     // AP_ALT: Row 2, Column 0
    {2, 10},    // AP_HDG: Row 2, Column 10
    {3, 0},     // AP_VS: Row 3, Column 0
    {3, 10}     // AP_SPD: Row 3, Column 10
};

// Format strings - how to display each value
// %s = label, %d = integer, %.1f = 1 decimal, %.2f = 2 decimals
const char* VALUE_FORMAT[NUM_VALUES] = {
    "C1:%.3f",    // COM1_ACT: frequency with 3 decimals
    "%.3f",       // COM1_STB
    "N1:%.2f",    // NAV1_ACT
    "%.2f",       // NAV1_STB
    "ALT:%5d",    // AP_ALT: integer, 5 chars wide
    "HDG:%03d",   // AP_HDG: integer, 3 digits with leading zeros
    "VS:%+5d",    // AP_VS: signed integer (+ or -)
    "SPD:%3d"     // AP_SPD: integer, 3 chars
};

// ============================================================
// INTERNAL VARIABLES
// ============================================================

// Create LCD object
LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLS, LCD_ROWS);

// Store current values
float values[NUM_VALUES];

// Flag for display update
bool needsUpdate = false;

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Initialize LCD
    lcd.init();
    lcd.backlight();
    lcd.clear();
    
    // Initialize values
    for (int i = 0; i < NUM_VALUES; i++) {
        values[i] = 0;
    }
    
    // Show startup message
    lcd.setCursor(0, 0);
    lcd.print("XPlane Dataref");
    lcd.setCursor(0, 1);
    lcd.print("Bridge Ready!");
    
    Serial.println("// LCD Controller Ready!");
    
    delay(2000);
    lcd.clear();
    
    // Draw static labels/layout
    drawLayout();
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
    
    // Update display if values changed
    if (needsUpdate) {
        updateDisplay();
        needsUpdate = false;
    }
    
    delay(50);  // 20Hz update rate
}

// ============================================================
// DRAW STATIC LAYOUT
// ============================================================

void drawLayout() {
    // Draw any static labels or dividers
    // These don't change during operation
    
    // For a radio stack display:
    // lcd.setCursor(0, 0);
    // lcd.print("COM1:");
    // lcd.setCursor(0, 1);
    // lcd.print("NAV1:");
    
    // For this example, we'll draw when values update
}

// ============================================================
// UPDATE DISPLAY
// ============================================================

void updateDisplay() {
    char buffer[21];  // Temporary buffer for formatting
    
    for (int i = 0; i < NUM_VALUES; i++) {
        // Position cursor
        lcd.setCursor(VALUE_POS[i][1], VALUE_POS[i][0]);
        
        // Format the value
        // Note: sprintf on Arduino has limited float support
        // For floats, we use dtostrf() or format manually
        
        float val = values[i];
        String format = VALUE_FORMAT[i];
        
        // Check format type and use appropriate function
        if (format.indexOf(".3f") >= 0) {
            // 3 decimal places (radio frequency)
            char fmtBuf[10];
            dtostrf(val, 7, 3, fmtBuf);
            
            // Extract label if present
            int colonPos = format.indexOf(':');
            if (colonPos >= 0) {
                String label = format.substring(0, colonPos + 1);
                sprintf(buffer, "%s%s", label.c_str(), fmtBuf);
            } else {
                strcpy(buffer, fmtBuf);
            }
        }
        else if (format.indexOf(".2f") >= 0) {
            // 2 decimal places
            char fmtBuf[10];
            dtostrf(val, 6, 2, fmtBuf);
            
            int colonPos = format.indexOf(':');
            if (colonPos >= 0) {
                String label = format.substring(0, colonPos + 1);
                sprintf(buffer, "%s%s", label.c_str(), fmtBuf);
            } else {
                strcpy(buffer, fmtBuf);
            }
        }
        else if (format.indexOf("%+") >= 0) {
            // Signed integer with +/-
            sprintf(buffer, format.c_str(), (int)val);
        }
        else if (format.indexOf("%0") >= 0) {
            // Zero-padded integer
            sprintf(buffer, format.c_str(), (int)val);
        }
        else {
            // Regular integer
            sprintf(buffer, format.c_str(), (int)val);
        }
        
        // Print to LCD
        lcd.print(buffer);
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
        Serial.println("XPDR;fw=1.0;board=LCDDisplay;name=RadioStack");
    }
    
    // --------------------------------------------------------
    // SET <KEY> <VALUE> - Update value
    // --------------------------------------------------------
    else if (message.startsWith("SET ")) {
        // Parse the message
        int firstSpace = message.indexOf(' ');
        int secondSpace = message.indexOf(' ', firstSpace + 1);
        
        if (secondSpace == -1) return;
        
        String key = message.substring(firstSpace + 1, secondSpace);
        float value = message.substring(secondSpace + 1).toFloat();
        
        // Find matching key
        for (int i = 0; i < NUM_VALUES; i++) {
            if (key == VALUE_KEYS[i]) {
                values[i] = value;
                needsUpdate = true;
                
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
    // CLEAR - Clear display
    // --------------------------------------------------------
    else if (message == "CLEAR") {
        lcd.clear();
        for (int i = 0; i < NUM_VALUES; i++) {
            values[i] = 0;
        }
        Serial.println("ACK CLEAR");
    }
    
    // --------------------------------------------------------
    // BACKLIGHT <0/1> - Control backlight
    // --------------------------------------------------------
    else if (message.startsWith("BACKLIGHT ")) {
        int state = message.substring(10).toInt();
        if (state) {
            lcd.backlight();
        } else {
            lcd.noBacklight();
        }
        Serial.print("ACK BACKLIGHT ");
        Serial.println(state);
    }
}

// ============================================================
// HELPER: PRINT TEXT AT POSITION
// ============================================================

void printAt(int col, int row, const char* text) {
    lcd.setCursor(col, row);
    lcd.print(text);
}

// ============================================================
// HELPER: CLEAR A PORTION OF THE DISPLAY
// ============================================================

void clearArea(int col, int row, int length) {
    lcd.setCursor(col, row);
    for (int i = 0; i < length; i++) {
        lcd.print(" ");
    }
}

// ============================================================
// CUSTOM CHARACTERS
// ============================================================
//
// LCD displays can show custom characters (up to 8).
// Great for: arrows, bars, plane icons, etc.
//
// byte arrowUp[8] = {
//     0b00100,
//     0b01110,
//     0b11111,
//     0b00100,
//     0b00100,
//     0b00100,
//     0b00100,
//     0b00000
// };
//
// void setup() {
//     lcd.createChar(0, arrowUp);
// }
//
// void showArrow() {
//     lcd.write(byte(0));  // Display custom char 0
// }
//
// ============================================================

// ============================================================
// MODIFICATION IDEAS:
// ============================================================
//
// 1. SCROLLING TEXT:
//    Scroll long messages across the display.
//
// 2. BLINKING VALUES:
//    Blink values that are out of range or warnings.
//
// 3. MULTIPLE PAGES:
//    Cycle through different info pages with a button.
//
// 4. BAR GRAPHS:
//    Use custom characters to create progress bars.
//
// 5. OLED DISPLAYS:
//    OLED screens offer more flexibility - see separate example.
//
// 6. TFT COLOR DISPLAYS:
//    For full graphical displays, use TFT screens with
//    libraries like TFT_eSPI or Adafruit_GFX.
//
// ============================================================
