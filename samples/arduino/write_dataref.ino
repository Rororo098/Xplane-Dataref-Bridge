// write_dataref.ino
// Send/write datarefs to the host (dataref writer).
// Copy to a new file named write_dataref.ino

const int LED_PIN = LED_BUILTIN;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  Serial.begin(115200);
}

void loop() {
  // Example: act on a simple trigger (porting to a real button would be easy)
  // Here we just respond to serial commands for demonstration.

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("WRITE ")) {
      // Expected format: WRITE <name> <type> <value>
      String rest = line.substring(6);
      rest.trim();
      int sp1 = rest.indexOf(' ');
      if (sp1 > 0) {
        String name = rest.substring(0, sp1);
        String rest2 = rest.substring(sp1 + 1);
        rest2.trim();
        int sp2 = rest2.indexOf(' ');
        if (sp2 > 0) {
          String type = rest2.substring(0, sp2);
          String valueStr = rest2.substring(sp2 + 1);
          valueStr.trim();

          // Demonstrative internal state
          Serial.print("OKWriting ");
          Serial.print(name);
          Serial.print(" ");
          Serial.print(type);
          Serial.print(" ");
          Serial.println(valueStr);
        }
      }
    }
  }
}
