/*
 * X-Plane Dataref Bridge - General Encoder (No HID, Serial-only)
 * This sketch demonstrates a general-purpose rotary encoder with both input
 * and output capabilities using Serial communication only (no HID).
 * It can:
 * - Send encoder rotations to the PC as INPUT events
 * - Optionally write datarefs on the PC by sending SETDREF commands (no HID)
 * - Debounce inputs for reliability
 * - Support for multiple encoders (expandable)
 * - Works on AVR and ESP32 boards (no HID libraries)
 */

// ================================================================
// 1. CONFIGURATION
// ================================================================

// Number of encoders connected to this Arduino
#define NUM_ENCODERS 1

// Encoder pin definitions: {CLK, DT, BUTTON}
#define ENCODER0_CLK_PIN 2
#define ENCODER0_DT_PIN 3
#define ENCODER0_BTN_PIN 4

const int ENCODER_PINS[NUM_ENCODERS][3] = {
  {ENCODER0_CLK_PIN, ENCODER0_DT_PIN, ENCODER0_BTN_PIN}
};

// Names for the encoder inputs (keys to send to PC)
const char* ENCODER_NAMES[NUM_ENCODERS] = {
  "ENC_KNOB_0"
};

// Button names (if no buttons, keep empty string "")
const char* ENCODER_BUTTON_NAMES[NUM_ENCODERS] = {
  "BTN_KNOB_0"
};

// Datarefs to set from encoder (empty string means do not emit SETDREF)
// Example: {"sim/cockpit2/radios/actuators/frequency_hz"}
const char* ENCODER_DREF_SET[NUM_ENCODERS] = {
  "" // Set per encoder if you want to write datarefs from encoder
};

// Internal state
float encoderValue[NUM_ENCODERS] = {0.0f};
int lastClkState[NUM_ENCODERS];
bool lastBtnState[NUM_ENCODERS];
unsigned long lastEncoderTime[NUM_ENCODERS];
unsigned long lastButtonTime[NUM_ENCODERS];

#define ENCODER_DEBOUNCE_MS 5
#define BUTTON_DEBOUNCE_MS 50

const char* DEVICE_NAME = "GeneralEncoderNoHID";

// ================================================================
// 2. SETUP
// ================================================================
void setup() {
  Serial.begin(115200);
  // For boards that require wait for serial, this is safe on most AVR boards
  #if defined(__AVR_ATmega32U4__) || defined(ARDUINO_ARCH_ESP32)
  while (!Serial) { delay(10); }
  #endif

  // Initialize encoder pins
  for (int i = 0; i < NUM_ENCODERS; i++) {
    pinMode(ENCODER_PINS[i][0], INPUT_PULLUP); // CLK
    pinMode(ENCODER_PINS[i][1], INPUT_PULLUP); // DT
    if (ENCODER_PINS[i][2] != -1) {
      pinMode(ENCODER_PINS[i][2], INPUT_PULLUP); // Button
      lastBtnState[i] = digitalRead(ENCODER_PINS[i][2]) == LOW;
    }
    lastClkState[i] = digitalRead(ENCODER_PINS[i][0]);
    lastEncoderTime[i] = 0;
    lastButtonTime[i] = 0;
  }

  Serial.println("// General Encoder (No HID) Ready!");
  Serial.print("// Encoding "); Serial.print(NUM_ENCODERS); Serial.println(" encoder(s)");
}

// ================================================================
// 3. MAIN LOOP
// ================================================================
void loop() {
  checkSerial();
  readEncoders();
  readButtons();
  delay(1);
}

// ================================================================
// 4. SERIAL HANDLING
// ================================================================
void checkSerial() {
  // Simple handshake and potential SET commands from host
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line == "HELLO") {
      Serial.print("XPDR;fw=1.0;board=General_NoHID;name=");
      Serial.println(DEVICE_NAME);
    } else if (line.startsWith("SET ")) {
      int firstSpace = line.indexOf(' ');
      int secondSpace = line.indexOf(' ', firstSpace + 1);
      if (firstSpace > 0 && secondSpace > firstSpace) {
        String key = line.substring(firstSpace + 1, secondSpace);
        String valStr = line.substring(secondSpace + 1);
        float value = valStr.toFloat();
        // Acknowledge reception
        Serial.print("ACK "); Serial.print(key); Serial.print(" "); Serial.println(value, 6);
        // Optional: apply to a local state or forward to X-Plane via a separate path
        (void)value; // no-op placeholder
      }
    }
  }
}

// ================================================================
// 5. ENCODER READERS
// ================================================================
void readEncoders() {
  unsigned long now = millis();
  for (int i = 0; i < NUM_ENCODERS; i++) {
    int clk = digitalRead(ENCODER_PINS[i][0]);
    if (clk != lastClkState[i] && clk == LOW) {
      if ((now - lastEncoderTime[i]) > ENCODER_DEBOUNCE_MS) {
        lastEncoderTime[i] = now;
        int dt = digitalRead(ENCODER_PINS[i][1]);
        bool cw = (dt != clk);
        // Send INPUT (no HID)
        Serial.print("INPUT "); Serial.print(ENCODER_NAMES[i]); Serial.print(" "); Serial.println(cw ? 1.0 : -1.0, 1);

        // Optional: emit dataref write to PC
        const char* dref = ENCODER_DREF_SET[i];
        if (dref && dref[0] != '\0') {
          encoderValue[i] += (cw ? 1.0f : -1.0f);
          Serial.print("SETDREF "); Serial.print(dref); Serial.print(" "); Serial.println(encoderValue[i], 6);
        }
      }
    }
    lastClkState[i] = clk;
  }
}

// ================================================================
// 6. ENCODER BUTTONS
// ================================================================
void readButtons() {
  unsigned long now = millis();
  for (int i = 0; i < NUM_ENCODERS; i++) {
    if (ENCODER_PINS[i][2] == -1) continue;
    bool pressed = (digitalRead(ENCODER_PINS[i][2]) == LOW);
    if (pressed != lastBtnState[i]) {
      if ((now - lastButtonTime[i]) > BUTTON_DEBOUNCE_MS) {
        lastButtonTime[i] = now;
        lastBtnState[i] = pressed;
        Serial.print("INPUT "); Serial.print(ENCODER_BUTTON_NAMES[i]); Serial.print(" "); Serial.println(pressed ? 1.0 : 0.0, 1);
      }
    }
  }
}

// ================================================================
// End
// ================================================================
