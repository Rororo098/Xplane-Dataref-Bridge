// handshake.ino
// Simple two-way handshake over Serial with heartbeat.
// Copy to a new file named handshake.ino
//
// Protocol:
// 1. Arduino sends "XP_HANDSHAKE_REQ" to initiate handshake
// 2. Host responds with "XP_HANDSHAKE_RES" or "XP_HANDSHAKE_OK"
// 3. Arduino sends "XP_HANDSHAKE_OK" to confirm and starts heartbeat
// 4. Arduino sends "HEARTBEAT" every second to maintain connection
//
// Hardware: Uses built-in LED to indicate handshake status
// - LED OFF: Handshake in progress or failed
// - LED ON: Handshake complete and connection active
//
// Timeouts: Retries handshake every 5 seconds if no response

const unsigned long HANDSHAKE_TIMEOUT = 5000;      // 5 seconds before retry
const unsigned long HEARTBEAT_INTERVAL = 1000;     // 1 second heartbeat
bool handshakeComplete = false;
unsigned long handshakeStart = 0;
unsigned long lastHeartbeat = 0;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);                    // LED for handshake status
  Serial.begin(115200);                           // Serial communication at 115200 baud
  while (!Serial) { ; }                            // Wait for serial to be ready (Leonardo/Micro)
  
  // Send initial handshake request
  Serial.println("XP_HANDSHAKE_REQ");
  handshakeStart = millis();                         // Record when we sent request
  digitalWrite(LED_BUILTIN, LOW);                    // LED off = handshake in progress
}

void loop() {
  if (!handshakeComplete) {
    // STEP 1: Wait for handshake response from host
    if (Serial.available()) {
      String line = Serial.readStringUntil('\n');
      line.trim();
      
      // Accept any of these valid handshake responses
      if (line == "XP_HANDSHAKE_RES" || line == "XP_HANDSHAKE_OK" || line == "XP_READY") {
        handshakeComplete = true;                       // Mark connection as established
        Serial.println("XP_HANDSHAKE_OK");             // Confirm handshake to host
        digitalWrite(LED_BUILTIN, HIGH);                 // LED on = connection active
      }
    }

    // STEP 2: If no response within timeout, retry handshake
    if (millis() - handshakeStart > HANDSHAKE_TIMEOUT) {
      Serial.println("XP_HANDSHAKE_REQ");              // Resend handshake request
      handshakeStart = millis();                         // Reset timeout timer
    }
  } else {
    // STEP 3: After successful handshake, send periodic heartbeat
    if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
      lastHeartbeat = millis();                     // Update heartbeat timer
      Serial.println("HEARTBEAT");                    // Send heartbeat to host
    }
  }
}