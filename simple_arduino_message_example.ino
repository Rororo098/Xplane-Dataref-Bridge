/*
 * Arduino Message Examples for X-Plane Dataref Bridge
 * 
 * This sketch demonstrates how to send different message types from Arduino to PC
 * using the X-Plane Dataref Bridge protocol.
 */

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Arduino ready - sending messages to PC");
}

void loop() {
  // Send different message types to demonstrate the protocol
  
  // INPUT <KEY> <VALUE>: Input notification (e.g., button press)
  sendInputNotification("BUTTON_1", "PRESSED");
  delay(100);
  
  // CMD <COMMAND>: Command execution
  sendCommand("RESET_SYSTEM");
  delay(100);
  
  // DREF <DATAREF> <VALUE>: Dataref write
  sendDatarefWrite("sim/cockpit/electrical/avionics_on", "1");
  delay(100);
  
  // ACK <KEY> <VALUE>: Acknowledgment
  sendAck("CONFIG", "COMPLETE");
  delay(100);
  
  // VALUE <DATAREF> <VALUE>: Dataref value response
  sendValueResponse("sim/flightmodel/position/altitude", "1500.5");
  delay(100);
  
  // ARRAYVALUE <ARRAY_NAME> <TYPE> <CSV_VALUES>: Array value response
  sendArrayValue("gauge_values", "float", "1.0,2.5,3.7,4.2,5.1");
  delay(100);
  
  // ELEMVALUE <ARRAY_NAME[INDEX]> <TYPE> <VALUE>: Array element value response
  sendElementValue("servo_positions", 2, "int", "1500");
  delay(100);
  
  delay(2000); // Wait 2 seconds before repeating
}

// Function to send INPUT <KEY> <VALUE> message
void sendInputNotification(String key, String value) {
  String message = "INPUT " + key + " " + value;
  Serial.println(message);
  Serial.flush();
}

// Function to send CMD <COMMAND> message
void sendCommand(String command) {
  String message = "CMD " + command;
  Serial.println(message);
  Serial.flush();
}

// Function to send DREF <DATAREF> <VALUE> message (for writing to datarefs)
void sendDatarefWrite(String dataref, String value) {
  String message = "DREF " + dataref + " " + value;
  Serial.println(message);
  Serial.flush();
}

// Function to send ACK <KEY> <VALUE> message
void sendAck(String key, String value) {
  String message = "ACK " + key + " " + value;
  Serial.println(message);
  Serial.flush();
}

// Function to send VALUE <DATAREF> <VALUE> message (for reporting dataref values)
void sendValueResponse(String dataref, String value) {
  String message = "VALUE " + dataref + " " + value;
  Serial.println(message);
  Serial.flush();
}

// Function to send ARRAYVALUE <ARRAY_NAME> <TYPE> <CSV_VALUES> message
void sendArrayValue(String arrayName, String dataType, String csvValues) {
  String message = "ARRAYVALUE " + arrayName + " " + dataType + " " + csvValues;
  Serial.println(message);
  Serial.flush();
}

// Function to send ELEMVALUE <ARRAY_NAME[INDEX]> <TYPE> <VALUE> message
void sendElementValue(String arrayName, int index, String dataType, String value) {
  String message = "ELEMVALUE " + arrayName + "[" + index + "] " + dataType + " " + value;
  Serial.println(message);
  Serial.flush();
}

// Function to handle incoming messages from PC
void handleIncomingMessages() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    // Process different types of incoming messages
    if (input.startsWith("INPUT ")) {
      // Handle input command from PC
      processInputCommand(input);
    }
    else if (input.startsWith("CMD ")) {
      // Handle command from PC
      processCommand(input);
    }
    else if (input.startsWith("DREF ")) {
      // Handle dataref write from PC
      processDatarefWrite(input);
    }
    else if (input.startsWith("ACK ")) {
      // Handle acknowledgment from PC
      processAck(input);
    }
    else if (input.startsWith("VALUE ")) {
      // Handle value response from PC
      processValueResponse(input);
    }
    else if (input.startsWith("ARRAYVALUE ")) {
      // Handle array value from PC
      processArrayValue(input);
    }
    else if (input.startsWith("ELEMVALUE ")) {
      // Handle element value from PC
      processElementValue(input);
    }
  }
}

// Processing functions for incoming messages
void processInputCommand(String input) {
  // Extract key and value from INPUT message
  int firstSpace = input.indexOf(' ');
  int secondSpace = input.indexOf(' ', firstSpace + 1);
  
  if (secondSpace > 0) {
    String key = input.substring(firstSpace + 1, secondSpace);
    String value = input.substring(secondSpace + 1);
    
    Serial.println("Received INPUT: " + key + " = " + value);
  }
}

void processCommand(String input) {
  String command = input.substring(4); // Remove "CMD " prefix
  Serial.println("Received CMD: " + command);
  
  // Execute the command
  executeCommand(command);
}

void processDatarefWrite(String input) {
  int firstSpace = input.indexOf(' ');
  int secondSpace = input.indexOf(' ', firstSpace + 1);
  
  if (secondSpace > 0) {
    String dataref = input.substring(firstSpace + 1, secondSpace);
    String value = input.substring(secondSpace + 1);
    
    Serial.println("Received DREF write: " + dataref + " = " + value);
    
    // Write to the dataref
    writeDataref(dataref, value);
  }
}

void processAck(String input) {
  int firstSpace = input.indexOf(' ');
  int secondSpace = input.indexOf(' ', firstSpace + 1);
  
  if (secondSpace > 0) {
    String key = input.substring(firstSpace + 1, secondSpace);
    String value = input.substring(secondSpace + 1);
    
    Serial.println("Received ACK: " + key + " = " + value);
  }
}

void processValueResponse(String input) {
  int firstSpace = input.indexOf(' ');
  int secondSpace = input.indexOf(' ', firstSpace + 1);
  
  if (secondSpace > 0) {
    String dataref = input.substring(firstSpace + 1, secondSpace);
    String value = input.substring(secondSpace + 1);
    
    Serial.println("Received VALUE: " + dataref + " = " + value);
  }
}

void processArrayValue(String input) {
  int firstSpace = input.indexOf(' ');
  int secondSpace = input.indexOf(' ', firstSpace + 1);
  int thirdSpace = input.indexOf(' ', secondSpace + 1);
  
  if (thirdSpace > 0) {
    String arrayName = input.substring(firstSpace + 1, secondSpace);
    String dataType = input.substring(secondSpace + 1, thirdSpace);
    String csvValues = input.substring(thirdSpace + 1);
    
    Serial.println("Received ARRAYVALUE: " + arrayName + " (" + dataType + ") = " + csvValues);
  }
}

void processElementValue(String input) {
  int firstSpace = input.indexOf(' ');
  int bracketOpen = input.indexOf('[', firstSpace + 1);
  int bracketClose = input.indexOf(']', bracketOpen);
  int secondSpace = input.indexOf(' ', bracketClose + 1);
  int thirdSpace = input.indexOf(' ', secondSpace + 1);
  
  if (bracketClose > 0 && thirdSpace > 0) {
    String arrayName = input.substring(firstSpace + 1, bracketOpen);
    String indexStr = input.substring(bracketOpen + 1, bracketClose);
    String dataType = input.substring(secondSpace + 1, thirdSpace);
    String value = input.substring(thirdSpace + 1);
    
    int index = indexStr.toInt();
    
    Serial.println("Received ELEMVALUE: " + arrayName + "[" + index + "] (" + dataType + ") = " + value);
  }
}

// Placeholder functions for actual implementations
void executeCommand(String command) {
  if (command == "RESET") {
    Serial.println("Executing reset command");
  } else if (command == "REBOOT") {
    Serial.println("Executing reboot command");
  } else {
    Serial.println("Unknown command: " + command);
  }
}

void writeDataref(String dataref, String value) {
  Serial.println("Writing " + value + " to " + dataref);
  // In a real implementation, this would write to the actual dataref
}

void processButtonPress(int buttonNum) {
  String key = "BUTTON_" + String(buttonNum);
  String value = "PRESSED";
  sendInputNotification(key, value);
}