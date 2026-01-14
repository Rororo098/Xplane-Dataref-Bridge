// write_dataref.ino
// Send/write datarefs to the host (dataref writer).
// Copy to a new file named write_dataref.ino
//
// Protocol:
// 1. Host sends: "WRITE <name> <type> <value>"
// 2. Arduino responds: "OKWriting <name> <type> <value>"
//
// This sketch demonstrates how to parse write commands and acknowledge them.
// In a real implementation, you would map these to actual hardware outputs.
//
// Example flow:
// WRITE ledPin bool 1 -> OKWriting ledPin bool 1
// WRITE throttle float 0.75 -> OKWriting throttle float 0.75
//
// Hardware: Uses built-in LED to indicate write operations

const int LED_PIN = LED_BUILTIN;            // LED for visual feedback

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
    
    // Parse WRITE command: WRITE <name> <type> <value>
    if (line.startsWith("WRITE ")) {
      String rest = line.substring(6).trim();           // Remove "WRITE " prefix
      int sp1 = rest.indexOf(' ');
      if (sp1 > 0) {
        String name = rest.substring(0, sp1);           // Extract dataref name
        String rest2 = rest.substring(sp1 + 1).trim();   // Extract remaining part
        int sp2 = rest2.indexOf(' ');
        if (sp2 > 0) {
          String type = rest2.substring(0, sp2);         // Extract dataref type
          String valueStr = rest2.substring(sp2 + 1).trim(); // Extract the value

          // In a real implementation, you would:
          // 1. Validate the value matches the expected type
          // 2. Apply the value to actual hardware (e.g., servo position, LED state)
          // 3. Store the value for local state tracking
          
          // For this demo, we just acknowledge receipt
          Serial.print("OKWriting ");
          Serial.print(name);                          // Echo back the name
          Serial.print(" ");
          Serial.print(type);                          // Echo back the type
          Serial.print(" ");
          Serial.println(valueStr);                      // Echo back the value
          
          // Visual feedback: brief flash on write
          digitalWrite(LED_PIN, HIGH);
          delay(100);
          digitalWrite(LED_PIN, LOW);
        }
      }
    }
  }
}