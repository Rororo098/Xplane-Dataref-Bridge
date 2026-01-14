// array_elements_read_write.ino
// Read/write single elements and multiple elements of dataref arrays.
// Copy to a new file named array_elements_read_write.ino
//
// Protocol:
// READ single element: "READ <name> <type> <index>" -> "VALUE <name> <index> <value>"
// READ entire array: "READ <name> <type> ALL" -> formatted array output
// WRITE single element: "WRITE <name> <type> <index> <value>" -> "OK"
//
// Advanced array handling with "ALL" keyword for full array operations.
// Demonstrates both individual element and bulk array access patterns.
//
// Example interactions:
// READ arrInt int 0 -> VALUE arrInt 0 42
// READ arrInt int ALL -> arrInt: 42, 0, 123, 456
// WRITE arrInt int 2 999 -> OK
// READ arrInt int 2 -> VALUE arrInt 2 999

// Array storage (4 elements each)
int arrInt[4] = {0, 0, 0, 0};          // Integer array with sample data
float arrFloat[4] = {0.0f, 0.0f, 0.0f, 0.0f}; // Float array with sample data
bool arrBool[4] = {false, false, false, false};   // Boolean array with sample data
byte arrByte[4] = {0, 0, 0, 0};              // Byte array with sample data

// Constants
const int ARRAY_SIZE = 4;                // Array size for bounds checking

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

// Helper functions to print entire arrays with different formatting
void printAllInt() {
  Serial.print("arrInt: ");
  for (int i = 0; i < ARRAY_SIZE; ++i) {
    Serial.print(arrInt[i]);
    if (i < ARRAY_SIZE - 1) Serial.print(", ");
  }
  Serial.println();
}

void printAllFloat() {
  Serial.print("arrFloat: ");
  for (int i = 0; i < ARRAY_SIZE; ++i) {
    Serial.print(arrFloat[i], 4);                      // 4 decimal places for floats
    if (i < ARRAY_SIZE - 1) Serial.print(", ");
  }
  Serial.println();
}

void printAllBool() {
  Serial.print("arrBool: ");
  for (int i = 0; i < ARRAY_SIZE; ++i) {
    Serial.print(arrBool[i] ? 1 : 0);              // Booleans as 1 or 0
    if (i < ARRAY_SIZE - 1) Serial.print(", ");
  }
  Serial.println();
}

void printAllByte() {
  Serial.print("arrByte: ");
  for (int i = 0; i < ARRAY_SIZE; ++i) {
    Serial.print((int)arrByte[i]);                       // Bytes as decimal values
    if (i < ARRAY_SIZE - 1) Serial.print(", ");
  }
  Serial.println();
}

void processLine(const String &line) {
  if (line.startsWith("READ ")) {
    // Handle READ commands: READ <name> <type> <index|ALL>
    String rest = line.substring(5).trim();           // Remove "READ " prefix
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);           // Extract dataref name
      String rest2 = rest.substring(sp1 + 1).trim();   // Extract remaining part

      int sp2 = rest2.indexOf(' ');
      String type;
      String idxStr;
      
      if (sp2 > 0) {
        type = rest2.substring(0, sp2);             // Extract dataref type
        idxStr = rest2.substring(sp2 + 1).trim(); // Extract index or ALL
      } else {
        type = rest2;                                 // No index specified
        idxStr = "";
      }

      // Process READ based on name and type
      if (name == "arrInt" && type == "int") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllInt();                                 // Print entire array
        } else {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrInt ");
          Serial.print(idx);                                 // Include index in response
          Serial.print(" ");
          Serial.println(idx >= 0 && idx < ARRAY_SIZE ? arrInt[idx] : 0); // Bounds check
        }
          
      } else if (name == "arrFloat" && type == "float") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllFloat();                                // Print entire array
        } else {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrFloat ");
          Serial.print(idx);                                 // Include index in response
          Serial.print(" ");
          Serial.println(idx >= 0 && idx < ARRAY_SIZE ? arrFloat[idx] : 0.0f, 4); // Bounds check
        }
          
      } else if (name == "arrBool" && type == "bool") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllBool();                                 // Print entire array
        } else {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrBool ");
          Serial.print(idx);                                 // Include index in response
          Serial.print(" ");
          Serial.println((idx >= 0 && idx < ARRAY_SIZE) ? (arrBool[idx] ? 1 : 0) : 0); // Bounds check
        }
          
      } else if (name == "arrByte" && type == "byte") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllByte();                                 // Print entire array
        } else {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrByte ");
          Serial.print(idx);                                 // Include index in response
          Serial.print(" ");
          Serial.println((idx >= 0 && idx < ARRAY_SIZE) ? (int)arrByte[idx] : 0); // Bounds check
        }
      }
    }
    
  } else if (line.startsWith("WRITE ")) {
    // Handle WRITE commands: WRITE <name> <type> <index> <value>
    String rest = line.substring(6).trim();           // Remove "WRITE " prefix
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);           // Extract dataref name
      String rest2 = rest.substring(sp1 + 1).trim();   // Extract remaining part

      int sp2 = rest2.indexOf(' ');
      if (sp2 > 0) {
        String type = rest2.substring(0, sp2);         // Extract dataref type
        String rest3 = rest2.substring(sp2 + 1).trim(); // Extract remaining part

        int sp3 = rest3.indexOf(' ');
        String idxStr, valStr;
        
        if (sp3 > 0) {
          idxStr = rest3.substring(0, sp3).trim();   // Extract index for array writes
          valStr = rest3.substring(sp3 + 1).trim();   // Extract value
        } else {
          idxStr = "";                                   // No index for non-array writes (not used in this sketch)
          valStr = rest3;
        }

        // Process WRITE based on name and type (only array writes supported here)
        if (name == "arrInt" && type == "int" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          if (idx >= 0 && idx < ARRAY_SIZE) {
            arrInt[idx] = valStr.toInt();           // Write to array element
            Serial.println("OK");                         // Acknowledge success
          } else {
            Serial.println("ERR: Index out of bounds");       // Bounds error
          }
          
        } else if (name == "arrFloat" && type == "float" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          if (idx >= 0 && idx < ARRAY_SIZE) {
            arrFloat[idx] = valStr.toFloat();           // Write to array element
            Serial.println("OK");                         // Acknowledge success
          } else {
            Serial.println("ERR: Index out of bounds");       // Bounds error
          }
          
        } else if (name == "arrBool" && type == "bool" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          if (idx >= 0 && idx < ARRAY_SIZE) {
            arrBool[idx] = (valStr == "1" || valStr.equalsIgnoreCase("true") || valStr.equalsIgnoreCase("on"));
            Serial.println("OK");                         // Acknowledge success
          } else {
            Serial.println("ERR: Index out of bounds");       // Bounds error
          }
          
        } else if (name == "arrByte" && type == "byte" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          if (idx >= 0 && idx < ARRAY_SIZE) {
            arrByte[idx] = (byte)valStr.toInt();           // Write to array element
            Serial.println("OK");                         // Acknowledge success
          } else {
            Serial.println("ERR: Index out of bounds");       // Bounds error
          }
          
        } else {
          // Unsupported write operation
          Serial.println("ERR: Unsupported operation");
        }
      }
    }
  }
}