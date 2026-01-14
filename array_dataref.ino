// array_dataref.ino
// Read/write array datarefs for int, float, bool, and byte.
// Copy to a new file named array_dataref.ino
//
// Protocol:
// READ single element: "READ <name> <type> <index>" -> "VALUE <name> <index> <value>"
// READ entire array: "READ <name> <type>" -> formatted array output
// WRITE single element: "WRITE <name> <type> <index> <value>" -> "OK"
//
// Demonstrates array handling for different data types with bounds checking.
// Arrays are size 4, indexed 0-3. Out-of-bounds accesses return 0.

// Array storage (4 elements each)
int arrInt[4] = {0, 0, 0, 0};          // Integer array
float arrFloat[4] = {0.0f, 0.0f, 0.0f, 0.0f}; // Float array
bool arrBool[4] = {false, false, false, false};   // Boolean array
byte arrByte[4] = {0, 0, 0, 0};              // Byte array

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

// Helper functions to print entire arrays
void printAllInt() {
  Serial.print("ARR_INT: ");
  for (int i = 0; i < ARRAY_SIZE; ++i) {
    Serial.print(arrInt[i]);
    if (i < ARRAY_SIZE - 1) Serial.print(", ");
  }
  Serial.println();
}

void printAllFloat() {
  Serial.print("ARR_FLOAT: ");
  for (int i = 0; i < ARRAY_SIZE; ++i) {
    Serial.print(arrFloat[i], 4);                      // 4 decimal places
    if (i < ARRAY_SIZE - 1) Serial.print(", ");
  }
  Serial.println();
}

void printAllBool() {
  Serial.print("ARR_BOOL: ");
  for (int i = 0; i < ARRAY_SIZE; ++i) {
    Serial.print(arrBool[i] ? "1" : "0");              // Booleans as 1 or 0
    if (i < ARRAY_SIZE - 1) Serial.print(", ");
  }
  Serial.println();
}

void printAllByte() {
  Serial.print("ARR_BYTE: ");
  for (int i = 0; i < ARRAY_SIZE; ++i) {
    Serial.print((int)arrByte[i]);                       // Bytes as integers
    if (i < ARRAY_SIZE - 1) Serial.print(", ");
  }
  Serial.println();
}

void processLine(const String &line) {
  if (line.startsWith("READ ")) {
    // Handle READ commands: READ <name> <type> [index]
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
        idxStr = rest2.substring(sp2 + 1).trim(); // Extract index if present
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
          idxStr = rest3.substring(0, sp3).trim();   // Extract index
          valStr = rest3.substring(sp3 + 1).trim();   // Extract value
        } else {
          idxStr = "";                                   // No index for non-array writes
          valStr = rest3;
        }

        // Process WRITE based on name and type
        if (name == "arrInt" && type == "int" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          if (idx >= 0 && idx < ARRAY_SIZE) {
            arrInt[idx] = valStr.toInt();           // Write to array element
          }
          Serial.println("OK");                             // Acknowledge success
          
        } else if (name == "arrFloat" && type == "float" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          if (idx >= 0 && idx < ARRAY_SIZE) {
            arrFloat[idx] = valStr.toFloat();           // Write to array element
          }
          Serial.println("OK");                             // Acknowledge success
          
        } else if (name == "arrBool" && type == "bool" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          if (idx >= 0 && idx < ARRAY_SIZE) {
            arrBool[idx] = (valStr == "1" || valStr.equalsIgnoreCase("true") || valStr.equalsIgnoreCase("on"));
          }
          Serial.println("OK");                             // Acknowledge success
          
        } else if (name == "arrByte" && type == "byte" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          if (idx >= 0 && idx < ARRAY_SIZE) {
            arrByte[idx] = (byte)valStr.toInt();           // Write to array element
          }
          Serial.println("OK");                             // Acknowledge success
        }
      }
    }
  }
}