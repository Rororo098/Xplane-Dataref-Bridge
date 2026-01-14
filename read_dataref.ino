// read_dataref.ino
// Read a dataref description over Serial and save value to a local variable.
// Copy to a new file named read_dataref.ino
//
// Protocol:
// 1. Host sends: "READ <name> <type>"
// 2. Arduino responds: "VALUE <name> <type> <value>"
// 3. Arduino responds: "UNKNOWN <name>" for unrecognized datarefs
//
// Supported types: float, int, bool, byte
// Examples:
// READ sensorA float -> VALUE sensorA float 12.345600
// READ sensorB int   -> VALUE sensorB int 42
// READ flag bool     -> VALUE flag bool 1
// READ byteA byte   -> VALUE byteA byte 90

float lastFloat = 0.0f;        // Storage for float datarefs
int lastInt = 0;                // Storage for int datarefs
bool lastBool = false;             // Storage for bool datarefs
byte lastByte = 0;               // Storage for byte datarefs

void setup() {
  Serial.begin(115200);                           // Start serial communication at 115200 baud
}

void loop() {
  static String line = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      
      // Parse READ command: READ <name> <type>
      if (line.startsWith("READ ")) {
        String rest = line.substring(5).trim();           // Remove "READ " prefix
        int sp = rest.indexOf(' ');
        if (sp > 0) {
          String name = rest.substring(0, sp);           // Extract dataref name
          String type = rest.substring(sp + 1).trim();    // Extract dataref type

          // Handle different dataref types with simulated values
          if (name == "sensorA" && type == "float") {
            lastFloat = 12.3456f;                      // Simulate float value
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastFloat, 6);                 // 6 decimal places
              
          } else if (name == "sensorB" && type == "int") {
            lastInt = 42;                                    // Simulate int value
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastInt);
              
          } else if (name == "flag" && type == "bool") {
            lastBool = true;                                   // Simulate bool value
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastBool ? 1 : 0);                 // Bool as 1 or 0
              
          } else if (name == "byteA" && type == "byte") {
            lastByte = 0x5A;                                    // Simulate byte value (90 decimal)
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastByte);
              
          } else {
            // Unknown dataref name
            Serial.print("UNKNOWN ");
            Serial.println(name);
          }
        }
      }
      line = "";                                     // Clear line buffer
    } else {
      line += c;                                       // Accumulate characters
    }
  }
}