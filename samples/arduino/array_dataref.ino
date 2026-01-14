// array_dataref.ino
// Read/write array datarefs for int, float, bool, and byte.
// Copy to a new file named array_dataref.ino

int arrInt[4]   = {0, 0, 0, 0};
float arrFloat[4] = {0.0f, 0.0f, 0.0f, 0.0f};
bool arrBool[4]  = {false, false, false, false};
byte arrByte[4]  = {0, 0, 0, 0};

void setup() {
  Serial.begin(115200);
}

void loop() {
  static String line = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      processLine(line);
      line = "";
    } else {
      line += c;
    }
  }
}

void printAllInt() {
  Serial.print("ARR_INT: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrInt[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllFloat() {
  Serial.print("ARR_FLOAT: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrFloat[i], 4);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllBool() {
  Serial.print("ARR_BOOL: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print(arrBool[i] ? 1 : 0);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void printAllByte() {
  Serial.print("ARR_BYTE: ");
  for (int i = 0; i < 4; ++i) {
    Serial.print((int)arrByte[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();
}

void processLine(const String &line) {
  if (line.startsWith("READ ")) {
    String rest = line.substring(5);
    rest.trim();
    int sp1 = rest.indexOf(' ');
    if (sp1 > 0) {
      String name = rest.substring(0, sp1);
      String rest2 = rest.substring(sp1 + 1);
      rest2.trim();
      int sp2 = rest2.indexOf(' ');
      String type;
      String idxStr;
      if (sp2 > 0) {
        type = rest2.substring(0, sp2);
        idxStr = rest2.substring(sp2 + 1);
      } else {
        type = rest2;
        idxStr = "";
      }

      if (name == "arrInt" && type == "int") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllInt();
        } else {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrInt ");
          Serial.println(idx >= 0 && idx < 4 ? arrInt[idx] : 0);
        }
      } else if (name == "arrFloat" && type == "float") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllFloat();
        } else {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrFloat ");
          Serial.println(idx >= 0 && idx < 4 ? arrFloat[idx] : 0.0f, 4);
        }
      } else if (name == "arrBool" && type == "bool") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllBool();
        } else {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrBool ");
          Serial.println((idx >= 0 && idx < 4) ? (arrBool[idx] ? 1 : 0) : 0);
        }
      } else if (name == "arrByte" && type == "byte") {
        if (idxStr == "ALL" || idxStr.length() == 0) {
          printAllByte();
        } else {
          int idx = idxStr.toInt();
          Serial.print("VALUE arrByte ");
          Serial.println((idx >= 0 && idx < 4) ? (int)arrByte[idx] : 0);
        }
      }
    }
  } else if (line.startsWith("WRITE ")) {
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
        String rest3 = rest2.substring(sp2 + 1);
        rest3.trim();
        int sp3 = rest3.indexOf(' ');
        String idxStr, valStr;
        if (sp3 > 0) {
          idxStr = rest3.substring(0, sp3);
          valStr = rest3.substring(sp3 + 1);
        } else {
          idxStr = "";
          valStr = rest3;
        }

        if (name == "arrInt" && type == "int" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          arrInt[idx] = valStr.toInt();
        } else if (name == "arrFloat" && type == "float" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          arrFloat[idx] = valStr.toFloat();
        } else if (name == "arrBool" && type == "bool" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          arrBool[idx] = (valStr == "1" || valStr.equalsIgnoreCase("true"));
        } else if (name == "arrByte" && type == "byte" && idxStr.length() > 0) {
          int idx = idxStr.toInt();
          arrByte[idx] = (byte)valStr.toInt();
        }
        Serial.println("OK");
      }
    }
  }
}
