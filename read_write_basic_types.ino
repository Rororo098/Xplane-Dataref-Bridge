// read_write_basic_types.ino
// Read/write int, float, bool, and byte datarefs.
// Copy to a new file named read_write_basic_types.ino
//
// Protocol:
// READ commands: "READ <name> <type>" -> "VALUE <name> <type> <value>"
// WRITE commands: "WRITE <name> <type> <value>" -> "OK"
// Error responses: "ERR" for invalid commands or values
//
// This sketch demonstrates bidirectional communication for basic data types.
// Values are stored locally and can be read back or overwritten.
//
// Example interactions:
// READ counter int -> VALUE counter int 42
// WRITE counter int 100 -> OK
// READ counter int -> VALUE counter int 100
// READ rate float -> VALUE rate float 2.500000
// WRITE rate float 3.14 -> OK

int dataInt = 0;                // Storage for integer datarefs
float dataFloat = 0.0f;           // Storage for floating point datarefs
bool dataBool = false;             // Storage for boolean datarefs
byte dataByte = 0;               // Storage for byte datarefs

void setup() {
  Serial.begin(115200);                           // Start serial communication at 115200 baud
}

void loop() {
  static String line = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      processLine(line);                              // Handle complete command
      line = "";                                     // Clear line buffer
    } else {
      line += c;                                       // Accumulate characters
    }
  }
}

void processLine(const String &line) {
  if (line.startsWith("READ ")) {
    // Handle READ commands: READ <name> <type>
    String rest = line.substring(5).trim();           // Remove "READ " prefix
    int sp = rest.indexOf(' ');
    if (sp > 0) {
      String name = rest.substring(0, sp);           // Extract dataref name
      String type = rest.substring(sp + 1).trim();    // Extract dataref type

      // Return current values based on name and type
      if (name == "counter" && type == "int") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataInt);                     // Return integer value
          
      } else if (name == "rate" && type == "float") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataFloat, 6);                 // Return float with 6 decimals
          
      } else if (name == "armed" && type == "bool") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataBool ? 1 : 0);                 // Return boolean as 1 or 0
          
      } else if (name == "mode" && type == "byte") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println((int)dataByte);                 // Return byte as integer
          
      } else {
        Serial.println("UNKNOWN");                           // Unknown dataref
      }
    }
    
  } else if (line.startsWith("WRITE ")) {
    // Handle WRITE commands: WRITE <name> <type> <value>
    String rest = line.substring(6).trim();           // Remove "WRITE " prefix
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);           // Extract dataref name
      String rest2 = rest.substring(sp1 + 1).trim();   // Extract remaining part
      int sp2 = rest2.indexOf(' ');
      if (sp2 > 0) {
        String type = rest2.substring(0, sp2);         // Extract dataref type
        String valueStr = rest2.substring(sp2 + 1).trim(); // Extract the value

        // Update local variables based on name and type
        if (name == "counter" && type == "int") {
          dataInt = valueStr.toInt();               // Convert string to integer
          Serial.println("OK");                         // Acknowledge success
          
        } else if (name == "rate" && type == "float") {
          dataFloat = valueStr.toFloat();             // Convert string to float
          Serial.println("OK");                         // Acknowledge success
          
        } else if (name == "armed" && type == "bool") {
          // Convert various boolean representations
          dataBool = (valueStr == "1" || valueStr.equalsIgnoreCase("true") || valueStr.equalsIgnoreCase("on"));
          Serial.println("OK");                         // Acknowledge success
          
        } else if (name == "mode" && type == "byte") {
          dataByte = (byte)valueStr.toInt();           // Convert and cast to byte
          Serial.println("OK");                         // Acknowledge success
          
        } else {
          Serial.println("ERR");                             // Error: invalid name/type combo
        }
      }
    }
  }
}