/*
 * X-Plane Dataref Bridge - General Encoder with Command Support
 * This sketch demonstrates rotary encoders that can execute X-Plane commands.
 * It can:
 * - Send encoder rotations as INPUT events to PC
 * - Execute X-Plane commands directly (no HID, serial-only)
 * - Support for multiple encoders with different commands for CW/CCW
 * - Optional push button on each encoder
 * - Debouncing for reliable operation
 * - Works on all Arduino boards (Uno, Nano, Leonardo, ESP32, etc.)
 */

// ================================================================
// 1. CONFIGURATION
// ================================================================

// Number of encoders connected to this Arduino
#define NUM_ENCODERS 1

// Encoder pin definitions: {CLK_PIN, DT_PIN, BUTTON_PIN}
#define ENCODER0_CLK_PIN 2
#define ENCODER0_DT_PIN 3
#define ENCODER0_BTN_PIN 4

const int ENCODER_PINS[NUM_ENCODERS][3] = {
  {ENCODER0_CLK_PIN, ENCODER0_DT_PIN, ENCODER0_BTN_PIN}
};

// Encoder input names (keys to send to PC for input tracking)
const char* ENCODER_NAMES[NUM_ENCODERS] = {
  "ENC_CMD_0"
};

// Encoder button input names (if no button, keep empty "")
const char* ENCODER_BUTTON_NAMES[NUM_ENCODERS] = {
  "BTN_CMD_0"
};

// ================================================================
// COMMAND CONFIGURATION
// ================================================================

// Commands to execute when encoder rotates
// These are X-Plane command paths
// Format: "sim/path/to/command"
// Set to empty string "" to skip command execution for that encoder
const char* ENCODER_COMMANDS_CW[NUM_ENCODERS] = {
  "sim/autopilot/heading_up"    // Command when encoder 0 turns clockwise
};

const char* ENCODER_COMMANDS_CCW[NUM_ENCODERS] = {
  "sim/autopilot/heading_down"  // Command when encoder 0 turns counter-clockwise
};

// Button commands (executed when button is pressed)
const char* ENCODER_BUTTON_COMMANDS[NUM_ENCODERS] = {
  "sim/autopilot/heading_sync"  // Command when encoder 0 button is pressed
};

// ================================================================
// INTERNAL VARIABLES
// ================================================================

int lastClkState[NUM_ENCODERS];
bool lastBtnState[NUM_ENCODERS];
unsigned long lastEncoderTime[NUM_ENCODERS];
unsigned long lastButtonTime[NUM_ENCODERS];

#define ENCODER_DEBOUNCE_MS 5
#define BUTTON_DEBOUNCE_MS 50

const char* DEVICE_NAME = "GeneralEncoderCommands";

// ================================================================
// 2. SETUP
// ================================================================

void setup() {
  Serial.begin(115200);

  // Wait for serial port (important for USB boards)
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
      lastBtnState[i] = digitalRead(ENCODER_PINS[i][2]) == LOW;
    }

    lastClkState[i] = digitalRead(ENCODER_PINS[i][0]);
    lastEncoderTime[i] = 0;
    lastButtonTime[i] = 0;
  }

  Serial.println("// General Encoder (Commands) Ready!");
  Serial.print("// Monitoring ");
  Serial.print(NUM_ENCODERS);
  Serial.println(" encoder(s) with command support");
}

// ================================================================
// 3. MAIN LOOP
// ================================================================

void loop() {
  checkSerial();
  readEncoders();
  readEncoderButtons();
  delay(1);
}

// ================================================================
// 4. SERIAL HANDLING
// ================================================================

void checkSerial() {
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    // Handshake: PC asking "Who are you?"
    if (line == "HELLO") {
      Serial.print("XPDR;fw=1.0;name=");
      Serial.println(DEVICE_NAME);
    }
    // Acknowledge SET commands from PC
    else if (line.startsWith("SET ")) {
      int firstSpace = line.indexOf(' ');
      int secondSpace = line.lastIndexOf(' ');

      if (firstSpace > 0 && secondSpace > firstSpace) {
        String key = line.substring(firstSpace + 1, secondSpace);
        String valStr = line.substring(secondSpace + 1);
        float value = valStr.toFloat();

        Serial.print("ACK ");
        Serial.print(key);
        Serial.print(" ");
        Serial.println(value, 6);
      }
    }
  }
}

// ================================================================
// 5. ENCODER READING WITH COMMAND EXECUTION
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

        // Send INPUT event to PC (for tracking/logging)
        Serial.print("INPUT ");
        Serial.print(ENCODER_NAMES[i]);
        Serial.print(" ");
        Serial.println((dtState != clkState) ? 1.0 : -1.0, 1);

        // Execute X-Plane command
        if (dtState != clkState) {
          // Clockwise
          executeCommand(i, ENCODER_COMMANDS_CW[i], "CW");
        } else {
          // Counter-clockwise
          executeCommand(i, ENCODER_COMMANDS_CCW[i], "CCW");
        }
      }
    }

    lastClkState[i] = clkState;
  }
}

// ================================================================
// 6. ENCODER BUTTON READING WITH COMMAND EXECUTION
// ================================================================

void readEncoderButtons() {
  unsigned long currentTime = millis();

  for (int i = 0; i < NUM_ENCODERS; i++) {
    if (ENCODER_PINS[i][2] == -1) continue;

    bool buttonState = (digitalRead(ENCODER_PINS[i][2]) == LOW);

    if (buttonState != lastBtnState[i]) {
      if ((currentTime - lastButtonTime[i]) > BUTTON_DEBOUNCE_MS) {
        lastButtonTime[i] = currentTime;
        lastBtnState[i] = buttonState;

        // Send INPUT event to PC (for tracking/logging)
        Serial.print("INPUT ");
        Serial.print(ENCODER_BUTTON_NAMES[i]);
        Serial.print(" ");
        Serial.println(buttonState ? 1.0 : 0.0, 1);

        // Execute X-Plane command on button press
        if (buttonState) {
          executeCommand(i, ENCODER_BUTTON_COMMANDS[i], "BUTTON_PRESS");
        }
      }
    }
  }
}

// ================================================================
// 7. COMMAND EXECUTION
// ================================================================

void executeCommand(int encoderIndex, const char* command, const char* direction) {
  // Check if command is configured (not empty string)
  if (command == nullptr || command[0] == '\0') {
    return;
  }

  // Send command to X-Plane via PC bridge
  // Format: CMD sim/path/to/command
  Serial.print("CMD ");
  Serial.println(command);
}

// ================================================================
// 8. USAGE EXAMPLES
// ================================================================

/*
 * EXAMPLE 1: Heading Bug Control
 * ============================
 * CW Command: sim/autopilot/heading_up
 * CCW Command: sim/autopilot/heading_down
 * Button Command: sim/autopilot/heading_sync
 *
 * Use: Turn encoder to adjust heading bug, press button to sync with aircraft
 *
 *
 * EXAMPLE 2: Autopilot Altitude Selector
 * ======================================
 * CW Command: sim/autopilot/altitude_up
 * CCW Command: sim/autopilot/altitude_down
 * Button Command: sim/autopilot/altitude_hold
 *
 * Use: Turn encoder to select altitude, press button to engage altitude hold
 *
 *
 * EXAMPLE 3: Radio Frequency Tuning
 * ==================================
 * CW Command: sim/radios/stby_com1_fine_up
 * CCW Command: sim/radios/stby_com1_fine_down
 * Button Command: sim/radios/com1_stby_flip
 *
 * Use: Turn encoder to fine-tune frequency, press button to toggle standby
 *
 *
 * ADDING MORE ENCODERS:
 * =====================
 * 1. Increase NUM_ENCODERS
 * 2. Add pin definitions:
 *    #define ENCODER1_CLK_PIN 5
 *    #define ENCODER1_DT_PIN 6
 *    #define ENCODER1_BTN_PIN 7
 * 3. Update ENCODER_PINS array
 * 4. Add names to ENCODER_NAMES and ENCODER_BUTTON_NAMES
 * 5. Add commands to ENCODER_COMMANDS_CW and ENCODER_COMMANDS_CCW
 * 6. Add button commands to ENCODER_BUTTON_COMMANDS
 *
 *
 * SPEED MULTIPLIER (PC SIDE):
 * =========================
 * The encoder sends a single event per "click". To speed up command execution,
 * configure the speed multiplier on the PC side:
 *
 * - In X-Plane Dataref Bridge app, go to Mappings tab
 * - Map the encoder INPUT key to a COMMAND action type
 * - Set Speed Multiplier to > 1.0 (e.g., 3.0)
 * - Set Command Delay (e.g., 20ms)
 *
 * Result: Each encoder tick will execute the command multiple times with short delays
 * Example: Multiplier 3.0 = Command executes 3 times, 20ms apart
 *
 *
 * FINDING X-PLANE COMMANDS:
 * ===========================
 * - Open X-Plane Dataref Browser (developer menu)
 * - Search for commands starting with "sim/"
 * - Common command categories:
 *   - sim/autopilot/* - Autopilot controls
 *   - sim/radios/* - Radio controls
 *   - sim/instruments/* - Instrument controls
 *   - sim/cockpit/* - Cockpit switches and controls
 *
 *
 * PROTOCOL:
 * ==========
 * Handshake:
 *   PC -> Arduino: HELLO
 *   Arduino -> PC: XPDR;fw=1.0;name=GeneralEncoderCommands
 *
 * Encoder Rotation:
 *   Arduino -> PC: INPUT ENC_CMD_0 1.0  (CW)
 *   Arduino -> PC: CMD sim/autopilot/heading_up
 *
 * Encoder Button:
 *   Arduino -> PC: INPUT BTN_CMD_0 1.0  (Press)
 *   Arduino -> PC: CMD sim/autopilot/heading_sync
 *
 * PC handles CMD lines and forwards them to X-Plane as commands
 *
 * COMBINED APPROACH:
 * =================
 * You can use both:
 * 1. INPUT events for tracking/mapping in the PC app
 * 2. CMD events for direct command execution
 *
 * This gives you flexibility to map encoders however you want!
 */

// ================================================================
// End
// ================================================================
