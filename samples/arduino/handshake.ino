// handshake.ino
// Simple two-way handshake over Serial with heartbeat.

const unsigned long HANDSHAKE_TIMEOUT = 5000;      // 5 seconds
const unsigned long HEARTBEAT_INTERVAL = 1000;     // 1 second
bool handshakeComplete = false;
unsigned long handshakeStart = 0;
unsigned long lastHeartbeat = 0;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
  while (!Serial) { ; } // wait for serial to be ready on boards like Leonardo/Micro
  Serial.println("XP_HANDSHAKE_REQ");
  handshakeStart = millis();
  digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
  if (!handshakeComplete) {
    // Listen for handshake response
    if (Serial.available()) {
      String line = Serial.readStringUntil('\n');
      line.trim();
      if (line == "XP_HANDSHAKE_RES" || line == "XP_HANDSHAKE_OK" || line == "XP_READY") {
        handshakeComplete = true;
        Serial.println("XP_HANDSHAKE_OK");
        digitalWrite(LED_BUILTIN, HIGH);
      }
    }

    // Timeout fallback: resend request
    if (millis() - handshakeStart > HANDSHAKE_TIMEOUT) {
      Serial.println("XP_HANDSHAKE_REQ");
      handshakeStart = millis();
    }
  } else {
    // Heartbeat after handshake
    if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
      lastHeartbeat = millis();
      Serial.println("HEARTBEAT");
    }
  }
}
