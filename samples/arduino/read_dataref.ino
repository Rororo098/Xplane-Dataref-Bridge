// read_dataref.ino
// Read a dataref description over Serial and save the value to a local variable.
// Copy to a new file named read_dataref.ino

float lastFloat = 0.0f;
int lastInt = 0;
bool lastBool = false;
byte lastByte = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  static String line;
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      if (line.startsWith("READ ")) {
        String rest = line.substring(5);
        rest.trim();
        int sp = rest.indexOf(' ');
        if (sp > 0) {
          String name = rest.substring(0, sp);
          String type = rest.substring(sp + 1);
          type.trim();

          if (name == "sensorA" && type == "float") {
            lastFloat = 12.3456;
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastFloat, 6);
          } else if (name == "sensorB" && type == "int") {
            lastInt = 42;
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastInt);
          } else if (name == "flag" && type == "bool") {
            lastBool = true;
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastBool ? 1 : 0);
          } else if (name == "byteA" && type == "byte") {
            lastByte = 0x5A;
            Serial.print("VALUE ");
            Serial.print(name);
            Serial.print(" ");
            Serial.print(type);
            Serial.print(" ");
            Serial.println(lastByte);
          } else {
            Serial.print("UNKNOWN ");
            Serial.println(name);
          }
        }
      }
      line = "";
    } else {
      line += c;
    }
  }
}
