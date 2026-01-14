// read_write_basic_types.ino
// Read/write int, float, bool, and byte datarefs.
// Copy to a new file named read_write_basic_types.ino

int dataInt = 0;
float dataFloat = 0.0f;
bool dataBool = false;
byte dataByte = 0;

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

void processLine(const String &line) {
  if (line.startsWith("READ ")) {
    String rest = line.substring(5);
    rest.trim();
    int sp = rest.indexOf(' ');
    if (sp > 0) {
      String name = rest.substring(0, sp);
      String type = rest.substring(sp + 1);
      type.trim();

      if (name == "counter" && type == "int") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataInt);
      } else if (name == "rate" && type == "float") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataFloat, 6);
      } else if (name == "armed" && type == "bool") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println(dataBool ? 1 : 0);
      } else if (name == "mode" && type == "byte") {
        Serial.print("VALUE ");
        Serial.print(name);
        Serial.print(" ");
        Serial.println((int)dataByte);
      } else {
        Serial.println("UNKNOWN");
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
        String valueStr = rest2.substring(sp2 + 1);
        valueStr.trim();

        if (name == "counter" && type == "int") {
          dataInt = valueStr.toInt();
          Serial.println("OK");
        } else if (name == "rate" && type == "float") {
          dataFloat = valueStr.toFloat();
          Serial.println("OK");
        } else if (name == "armed" && type == "bool") {
          dataBool = (valueStr == "1" || valueStr.equalsIgnoreCase("true"));
          Serial.println("OK");
        } else if (name == "mode" && type == "byte") {
          dataByte = (byte)valueStr.toInt();
          Serial.println("OK");
        } else {
          Serial.println("ERR");
        }
      }
    }
  }
}
