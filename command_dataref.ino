// command_dataref.ino
// Execute command-type datarefs (e.g., toggle LED, reset, etc.)
// Copy to a new file named command_dataref.ino
//
// Protocol:
// 1. Host sends: "CMD <command_name>"
// 2. Arduino responds: "CMD_EXECUTED <command_name>"
//
// This sketch demonstrates how to handle various commands and trigger actions.
// Commands are simple text strings that can be mapped to hardware actions.
//
// Example commands:
// CMD toggleLED -> CMD_EXECUTED toggleLED
// CMD pulseLED -> CMD_EXECUTED pulseLED  
// CMD reset -> CMD_EXECUTED reset
//
// Hardware: Uses built-in LED for visual feedback of command execution

const int LED_PIN = LED_BUILTIN;            // LED for command feedback
unsigned long lastBlink = 0;                // Timer for blink animation
bool ledState = false;                    // Track current LED state

void setup() {
  pinMode(LED_PIN, OUTPUT);                     // Configure LED pin
  digitalWrite(LED_PIN, LOW);                    // Start with LED off
  Serial.begin(115200);                           // Serial communication at 115200 baud
}

void loop() {
  // Check for incoming commands from host
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    
    // Parse CMD command: CMD <command_name>
    if (line.startsWith("CMD ")) {
      String cmd = line.substring(4).trim();       // Extract command name
      executeCommand(cmd);                          // Execute the command
      Serial.println("CMD_EXECUTED " + cmd);    // Acknowledge execution
    }
  }
  
  // Optional: blink LED when it's supposed to be "on" (visual feedback)
  if (ledState && (millis() - lastBlink) > 500) {
    lastBlink = millis();                     // Update blink timer
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));     // Toggle LED state
  }
}

// Execute specific commands based on their name
void executeCommand(const String &cmd) {
  if (cmd == "toggleLED") {
    // Toggle the LED state
    ledState = !ledState;                           // Invert current state
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);        // Apply new state
    
  } else if (cmd == "pulseLED") {
    // Quick blink sequence (3 rapid blinks)
    bool currentState = ledState;                       // Remember current state
    ledState = false;                              // Turn off blinking
    digitalWrite(LED_PIN, LOW);                       // LED off during pulse
    
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);                     // LED on
      delay(100);                                    // 100ms on time
      digitalWrite(LED_PIN, LOW);                      // LED off
      delay(100);                                    // 100ms off time
    }
    
    // Restore previous state after pulse
    ledState = currentState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
    
  } else if (cmd == "reset") {
    // Graceful "soft reset" command
    // In a real implementation, you might:
    // - Reset all variables to default values
    // - Reset hardware to initial state
    // - Clear any pending operations
    Serial.println("RESET_CMD_RECEIVED");              // Acknowledge reset
    
  } else if (cmd == "status") {
    // Report current system status
    Serial.print("STATUS LED:");
    Serial.print(ledState ? "ON" : "OFF");
    Serial.println(" READY");
    
  } else if (cmd == "version") {
    // Report version/firmware information
    Serial.println("CMD_EXECUTED version 1.0");
    
  } else {
    // Unknown command
    Serial.println("UNKNOWN_CMD: " + cmd);
  }
}