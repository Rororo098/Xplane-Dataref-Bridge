/*
===============================================================================
X-Plane Dataref Bridge - Comprehensive Test Controller for ESP32-S2
===============================================================================

PURPOSE:
This sketch creates a comprehensive test controller that repeatedly changes values for
various X-Plane datarefs with different behaviors:
1. Toggles sim/lights/beacon_lights_toggle on/off every 500ms
2. Gradually changes sim/flightmodel/controls/parkbrake from 0 to 1 and back
3. Gradually changes sim/cockpit2/radios/actuators/com1_frequency_Mhz from 118 to 136
4. Changes sim/aircraft/view/acf_ICAO from C152 to C1522 repeatedly every 1 sec
5. Reads and prints the current value of sim/aircraft/view/acf_ICAO

REQUIRED HARDWARE:
- ESP32-S2 development board
- USB cable for programming and communication

COMMANDS USED:
- DREF for writing numeric/string datarefs
- INPUT for requesting dataref values from X-Plane (requires OUTPUT_ID mapping in bridge)
- SET for receiving dataref values from bridge

FEATURES:
- Multiple simultaneous dataref changes
- Reading dataref values from X-Plane
- Proper handshake protocol with X-Plane Dataref Bridge
- Configurable timing for different dataref types
- Error handling and bounds checking

TROUBLESHOOTING:
- No communication? Verify 115200 baud rate in Serial Monitor
- Wrong values? Check if datarefs are writable in X-Plane
- ESP32-S2 not detected? Verify correct board selected in Arduino IDE
===============================================================================
*/

/* ==========================================================================
   DEVICE IDENTIFICATION SECTION
   These constants identify your device to bridge application
   ========================================================================== */

const char* DEVICE_NAME = "ComprehensiveTestController";     // Human-readable name for your device
const char* FIRMWARE_VERSION = "1.0";                // Version number for updates/tracking
const char* BOARD_TYPE = "ESP32-S2";                 // ESP32-S2 board type

/* ==========================================================================
   DATAREF DEFINITIONS SECTION
   These define the datarefs we'll write to directly in X-Plane
   ========================================================================== */

const char* DATAREF_BEACON = "sim/lights/beacon_lights_toggle";
const char* DATAREF_PARKBRAKE = "sim/flightmodel/controls/parkbrake";
const char* DATAREF_COM_FREQ = "sim/cockpit2/radios/actuators/com1_frequency_Mhz";
const char* DATAREF_AIRCRAFT_ICAO = "sim/aircraft/view/acf_ICAO";

/* ==========================================================================
   OUTPUT_ID DEFINITIONS SECTION
   These are friendly names we'll use for receiving data from X-Plane
   NOTE: These must be mapped in the Bridge application
   ========================================================================== */

const char* OUTPUT_ID_CURRENT_ICAO = "CURRENT_ICAO";  // For receiving current ICAO code

/* ==========================================================================
   TIMING VARIABLES SECTION
   Variables to control timing for different dataref updates
   ========================================================================== */

unsigned long lastBeaconUpdate = 0;           // Timestamp of last beacon update
const unsigned long BEACON_INTERVAL = 500;    // Update beacon every 500ms
bool beaconState = false;                     // Current beacon state (true=on, false=off)

unsigned long lastParkBrakeUpdate = 0;        // Timestamp of last park brake update
const unsigned long PARKBRAKE_INTERVAL = 100; // Update park brake every 100ms for gradual change
float parkBrakeValue = 0.0;                   // Current park brake value (0.0 to 1.0)
float parkBrakeDirection = 0.01;              // Direction and increment for gradual change

unsigned long lastComFreqUpdate = 0;          // Timestamp of last COM frequency update
const unsigned long COM_FREQ_INTERVAL = 500;  // Update COM frequency every 500ms
float comFrequency = 118.0;                   // Current COM frequency (118.0 to 136.0)
float comFreqDirection = 0.1;                 // Direction and increment for gradual change

unsigned long lastIcaoUpdate = 0;             // Timestamp of last ICAO update
const unsigned long ICAO_INTERVAL = 1000;     // Update ICAO every 1000ms (1 second)
bool icaoState = false;                       // Current ICAO state (false=C152, true=C1522)

unsigned long lastIcaoRead = 0;               // Timestamp of last ICAO read request
const unsigned long ICAO_READ_INTERVAL = 2000; // Read ICAO every 2000ms (2 seconds)

String currentIcaoValue = "UNKNOWN";          // Current ICAO value received from X-Plane

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
  Serial.println("// Comprehensive Test Controller Started");  // Startup confirmation
  Serial.print("// Device: ");
  Serial.println(DEVICE_NAME);                        // Send device name
  Serial.println("// Testing: beacon, parkbrake, com_freq, aircraft_icao, read_icao");  // Function guide
  
  // Initialize timing
  lastBeaconUpdate = millis();
  lastParkBrakeUpdate = millis();
  lastComFreqUpdate = millis();
  lastIcaoUpdate = millis();
  lastIcaoRead = millis();
}

/* ==========================================================================
   MAIN LOOP FUNCTION
   This runs continuously after setup() - handles communication and value updates
   ========================================================================== */

void loop() {
  checkSerial();        // Listen for commands from bridge application
  updateBeacon();       // Update beacon light toggle
  updateParkBrake();    // Update park brake gradually
  updateComFrequency(); // Update COM frequency gradually
  updateIcaoCode();     // Update aircraft ICAO code
  readCurrentIcao();    // Read current ICAO value from X-Plane
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
  // --- Handle SET Commands (values from X-Plane) ---
  // Bridge sends "SET <KEY> <VALUE>" when X-Plane dataref changes
  else if (line.startsWith("SET ")) {
    // Parse format: "SET CURRENT_ICAO C172"
    int firstSpace = line.indexOf(' ');      // Find first space
    int secondSpace = line.lastIndexOf(' '); // Find last space

    if (firstSpace > 0 && secondSpace > firstSpace) {
      String key = line.substring(firstSpace + 1, secondSpace);  // Extract the OUTPUT_ID
      String valueStr = line.substring(secondSpace + 1);         // Extract the value

      // Handle the SET command based on the key
      handleSetCommand(key, valueStr);
    }
  }
}

/* ==========================================================================
   SET COMMAND HANDLER
   Processes SET commands and sends ACK responses for debugging
   ========================================================================== */

void handleSetCommand(String key, String value) {
  if (key == OUTPUT_ID_CURRENT_ICAO) {
    currentIcaoValue = value;  // Store current ICAO value
    Serial.print("// Received current ICAO: ");
    Serial.println(currentIcaoValue);
  }

  // Send acknowledgment for debugging (optional but helpful)
  Serial.print("ACK ");
  Serial.print(key);
  Serial.print(" ");
  Serial.println(value);
}

/* ==========================================================================
   BEACON LIGHT UPDATE FUNCTION
   Updates beacon light state every 500ms, toggling between on and off
   ========================================================================== */

void updateBeacon() {
  if (millis() - lastBeaconUpdate > BEACON_INTERVAL) {
    // Toggle beacon state
    beaconState = !beaconState;

    // Send CMD command to X-Plane to toggle beacon light
    // This is a command dataref, not a value dataref
    Serial.print("CMD ");
    Serial.println(DATAREF_BEACON);

    Serial.print("// Beacon command sent: ");
    Serial.println(beaconState ? "ON" : "OFF");

    // Update the timestamp
    lastBeaconUpdate = millis();
  }
}

/* ==========================================================================
   PARK BRAKE UPDATE FUNCTION
   Gradually changes park brake value from 0 to 1 and back
   ========================================================================== */

void updateParkBrake() {
  if (millis() - lastParkBrakeUpdate > PARKBRAKE_INTERVAL) {
    // Update park brake value gradually
    parkBrakeValue += parkBrakeDirection;
    
    // Reverse direction if we hit the limits
    if (parkBrakeValue >= 1.0) {
      parkBrakeValue = 1.0;
      parkBrakeDirection = -0.01;  // Start decreasing
    } else if (parkBrakeValue <= 0.0) {
      parkBrakeValue = 0.0;
      parkBrakeDirection = 0.01;   // Start increasing
    }
    
    // Send DREF command to X-Plane to set park brake value
    Serial.print("DREF ");
    Serial.print(DATAREF_PARKBRAKE);
    Serial.print(" ");
    Serial.println(parkBrakeValue, 4);  // Send value with 4 decimal places
    
    Serial.print("// Park brake value: ");
    Serial.println(parkBrakeValue, 4);

    // Update the timestamp
    lastParkBrakeUpdate = millis();
  }
}

/* ==========================================================================
   COM FREQUENCY UPDATE FUNCTION
   Gradually changes COM frequency from 118 to 136 MHz
   ========================================================================== */

void updateComFrequency() {
  if (millis() - lastComFreqUpdate > COM_FREQ_INTERVAL) {
    // Update COM frequency gradually
    comFrequency += comFreqDirection;
    
    // Reverse direction if we hit the limits
    if (comFrequency >= 136.0) {
      comFrequency = 136.0;
      comFreqDirection = -0.1;  // Start decreasing
    } else if (comFrequency <= 118.0) {
      comFrequency = 118.0;
      comFreqDirection = 0.1;   // Start increasing
    }
    
    // Send DREF command to X-Plane to set COM frequency
    Serial.print("DREF ");
    Serial.print(DATAREF_COM_FREQ);
    Serial.print(" ");
    Serial.println(comFrequency, 2);  // Send value with 2 decimal places
    
    Serial.print("// COM frequency: ");
    Serial.print(comFrequency, 2);
    Serial.println(" MHz");

    // Update the timestamp
    lastComFreqUpdate = millis();
  }
}

/* ==========================================================================
   AIRCRAFT ICAO CODE UPDATE FUNCTION
   Changes aircraft ICAO code from C152 to C1522 every second
   ========================================================================== */

void updateIcaoCode() {
  if (millis() - lastIcaoUpdate > ICAO_INTERVAL) {
    // Toggle ICAO code
    icaoState = !icaoState;

    // Send STRING command to X-Plane to set aircraft ICAO code
    Serial.print("STRING ");
    Serial.print(DATAREF_AIRCRAFT_ICAO);
    Serial.print(" ");
    if (icaoState) {
      Serial.println("C1522");  // Send C1522 when state is true
    } else {
      Serial.println("C152");   // Send C152 when state is false
    }

    Serial.print("// Aircraft ICAO: ");
    Serial.println(icaoState ? "C1522" : "C152");

    // Update the timestamp
    lastIcaoUpdate = millis();
  }
}

/* ==========================================================================
   READ CURRENT ICAO FUNCTION
   This function doesn't actively read the ICAO value from X-Plane.
   Instead, it just displays the last received value.
   To receive values from X-Plane, you must configure the bridge to
   subscribe to the dataref and map it to the OUTPUT_ID.
   ========================================================================== */

void readCurrentIcao() {
  if (millis() - lastIcaoRead > ICAO_READ_INTERVAL) {
    // Just display the last received ICAO value
    Serial.print("// Current ICAO value: ");
    Serial.println(currentIcaoValue);

    // Update the timestamp
    lastIcaoRead = millis();
  }
}

/* ==========================================================================
   END OF SKETCH
   Congratulations! You now have a comprehensive test controller with multiple dataref types.
   ========================================================================== */