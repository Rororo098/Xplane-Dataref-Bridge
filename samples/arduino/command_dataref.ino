// command_dataref.ino
// Execute command-type datarefs (e.g., toggle LED, reset, etc.)
// Copy to a new file named command_dataref.ino

const int LED_PIN = LED_BUILTIN;
unsigned long lastBlink = 0;
bool ledState = false;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("CMD ")) {
      String cmd = line.substring(4);
      cmd.trim();
      executeCommand(cmd);
      Serial.println("CMD_EXECUTED " + cmd);
    }
  }
  // Optional: keep LED in a visible state
  if (ledState && (millis() - lastBlink) > 500) {
    lastBlink = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
}

void executeCommand(const String &cmd) {
  if (cmd == "toggleLED") {
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
  } else if (cmd == "pulseLED") {
    // quick blink
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
  } else if (cmd == "reset") {
    // A graceful "soft reset" placeholder
    Serial.println("RESET_CMD_RECEIVED");
  }
  // Add more commands as needed
}
