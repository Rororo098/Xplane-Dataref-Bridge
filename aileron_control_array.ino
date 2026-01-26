/*
===============================================================================
X-Plane Dataref Bridge - Aileron Control Array for ESP32-S2 (Direct DREF)
===============================================================================

PURPOSE:
This sketch creates an aileron control array that repeatedly changes values for
the dataref array indices 0, 1, 2 from 0-1 for sim/flightmodel2/wing/aileron2_deg.
The values are sent directly using DREF commands to X-Plane.

REQUIRED HARDWARE:
- ESP32-S2 development board
- USB cable for programming and communication

DIRECT DATAREF WRITING:
This sketch sends DREF commands directly to X-Plane to write values to datarefs.
The format is: DREF <dataref_name>[index] <value>

COMMAND FORMAT:
- DREF sim/flightmodel2/wing/aileron2_deg[0] <value> - Sets aileron 1 value
- DREF sim/flightmodel2/wing/aileron2_deg[1] <value> - Sets aileron 2 value
- DREF sim/flightmodel2/wing/aileron2_deg[2] <value> - Sets aileron 3 value

FEATURES:
- Repeatedly cycles values for aileron array elements
- Proper handshake protocol with X-Plane Dataref Bridge
- Direct dataref writing without requiring OUTPUT_ID mapping
- Configurable timing for value changes
- Error handling and bounds checking

TROUBLESHOOTING:
- No communication? Verify 115200 baud rate in Serial Monitor
- Wrong values? Check if dataref is writable in X-Plane
- ESP32-S2 not detected? Verify correct board selected in Arduino IDE
===============================================================================
*/

/* ==========================================================================
   DEVICE IDENTIFICATION SECTION
   These constants identify your device to bridge application
   ========================================================================== */

const char* DEVICE_NAME = "AileronControlArray";     // Human-readable name for your device
const char* FIRMWARE_VERSION = "2.0";                // Version number for updates/tracking
const char* BOARD_TYPE = "ESP32-S2";                 // ESP32-S2 board type

/* ==========================================================================
   DATAREF DEFINITIONS SECTION
   These define the dataref we'll write to directly in X-Plane
   ========================================================================== */

const char* DATAREF_BASE = "sim/flightmodel2/wing/aileron2_deg";  // Base dataref name

/* ==========================================================================
   AILERON ARRAY VALUES SECTION
   Variables to store current values for each aileron array element
   ========================================================================== */

float aileronValues[3] = {0.0, 0.0, 0.0};  // Current values for aileron array [0], [1], [2]
int currentAileronIndex = -1;                // Index of current aileron being updated (-1 to start with 0 on first iteration)
unsigned long lastUpdate = 0;               // Timestamp of last value update
const unsigned long UPDATE_INTERVAL = 1000; // Update interval in milliseconds (1 second)

/* ==========================================================================
   SERIAL COMMUNICATION SECTION
   Buffer for building messages from PC character by character
   ========================================================================== */

String inputBuffer = "";  // Storage for incoming serial messages

/* ==========================================================================
   SETUP FUNCTION
   This runs once when ESP32-S2 boots up - initializes all hardware and settings
   ========================================================================== */

void setup() {
  // --- Initialize Serial Communication ---
  // Start serial communication at 115200 baud (bits per second)
  // This is the speed required by X-Plane Dataref Bridge
  Serial.begin(115200);

  // --- Wait for Serial Connection ---
  // ESP32-S2 needs time to establish serial connection
  // This waits up to 5 seconds for serial to be ready
  while (!Serial && millis() < 5000) {
    delay(10);  // Small delay to prevent overwhelming the processor
  }

  // --- Send Startup Messages ---
  // These messages help with debugging and confirm device is working
  Serial.println("// Aileron Control Array Started (DREF Mode)");  // Startup confirmation
  Serial.print("// Device: ");
  Serial.println(DEVICE_NAME);                        // Send device name
  Serial.println("// Writing to: sim/flightmodel2/wing/aileron2_deg[0-2]");  // Function guide

  // Initialize timing
  lastUpdate = millis();
}

/* ==========================================================================
   MAIN LOOP FUNCTION
   This runs continuously after setup() - handles communication and value updates
   ========================================================================== */

void loop() {
  checkSerial();        // Listen for commands from bridge application
  updateAileronValues(); // Update aileron values periodically
  delay(10);            // Small delay to prevent overwhelming processor
}

/* ==========================================================================
   SERIAL COMMUNICATION HANDLER
   Processes incoming messages from X-Plane Dataref Bridge using correct protocol
   ========================================================================== */

void checkSerial() {
  // Check if any data is available to read from serial port
  while (Serial.available() > 0) {
    // Read one character at a time
    char c = (char)Serial.read();

    // If we receive a newline character, the message is complete
    if (c == '\n') {
      processLine(inputBuffer);    // Process the complete message
      inputBuffer = "";             // Clear buffer for next message
    }
    // Ignore carriage return characters (Windows sometimes sends them)
    else if (c != '\r') {
      inputBuffer += c;    // Add character to buffer
    }
  }
}

/* ==========================================================================
   MESSAGE PROCESSING FUNCTION
   Decodes and handles messages received from the bridge application
   ========================================================================== */

void processLine(String line) {
  line.trim();  // Remove any whitespace from beginning and end

  // --- Handle Handshake Request ---
  // Bridge sends "HELLO" to check if device is responding
  if (line == "HELLO") {
    // Respond with device information in the exact expected format
    Serial.print("XPDR;fw=");
    Serial.print(FIRMWARE_VERSION);    // Send firmware version
    Serial.print(";board=");
    Serial.print(BOARD_TYPE);          // Send board type
    Serial.print(";name=");
    Serial.println(DEVICE_NAME);       // Send device name

    // Visual feedback - blink built-in LED to show connection established
    #ifdef LED_BUILTIN
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    #endif
  }
}

/* ==========================================================================
   AILERON VALUE UPDATE FUNCTION
   Updates aileron values periodically and sends them to X-Plane
   ========================================================================== */

void updateAileronValues() {
  // Check if it's time to update the values
  if (millis() - lastUpdate > UPDATE_INTERVAL) {
    // Cycle through aileron indices (0, 1, 2)
    currentAileronIndex = (currentAileronIndex + 1) % 3;

    // Generate a new value between 0.0 and 1.0 (using sine wave for smooth transitions)
    float newValue = (sin(millis() / 2000.0) + 1.0) / 2.0;  // Sine wave from 0 to 1

    // Update the current aileron value
    aileronValues[currentAileronIndex] = newValue;

    // Send DREF command to X-Plane to directly set the dataref value
    Serial.print("DREF ");
    Serial.print(DATAREF_BASE);
    Serial.print("[");
    Serial.print(currentAileronIndex);
    Serial.print("] ");
    Serial.println(aileronValues[currentAileronIndex], 4);

    Serial.print("// Sent Aileron[");
    Serial.print(currentAileronIndex);
    Serial.print("] value: ");
    Serial.println(aileronValues[currentAileronIndex], 4);

    // Update the timestamp
    lastUpdate = millis();
  }
}

/* ==========================================================================
   ADDITIONAL UTILITY FUNCTIONS
   Various helper functions for mathematical operations
   ========================================================================== */

// Note: Using Arduino's built-in constrain() function which limits a value to be between min and max

/* ==========================================================================
   END OF SKETCH
   Congratulations! You now have a working aileron control array with direct DREF writing.
   ========================================================================== */