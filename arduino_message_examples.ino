/*
 * Arduino Message Examples for X-Plane Dataref Bridge
 * 
 * This sketch demonstrates how to send different message types from Arduino to PC
 * using the X-Plane Dataref Bridge protocol.
 */

// Pin definitions
const int BUTTON_PIN = 2;
const int POTENTIOMETER_PIN = A0;
const int LED_PIN = 13;

// Variables to track state
int lastButtonState = HIGH;  // Using pullup resistor, so default is HIGH
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;
int lastReading = HIGH;

// Array example
float sensorArray[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
int arrayIndex = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(POTENTIOMETER_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Send initialization acknowledgment
  sendAck("INIT", "SUCCESS");
  
  // Send configuration acknowledgment
  sendAck("CONFIG", "COMPLETE");
  
  Serial.println("Arduino ready - sending messages to PC");
}

void loop() {
  // Check for button presses (INPUT message example)
  checkButtonPress();
  
  // Periodically send sensor values (VALUE message example)
  sendSensorValues();
  
  // Send array values periodically (ARRAYVALUE message example)
  sendArrayValues();
  
  // Simulate periodic command execution notifications
  simulatePeriodicNotifications();
  
  // Handle incoming messages from PC
  handleSerialInput();
  
  delay(100); // Small delay to prevent overwhelming the serial port
}

void checkButtonPress() {
  int reading = digitalRead(BUTTON_PIN);

  // Debounce the button
  if (reading != lastReading) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != lastButtonState) {
      lastButtonState = reading;
      
      if (reading == LOW) {
        // Button pressed - send INPUT message
        sendInputNotification("BUTTON_1", "PRESSED");
        digitalWrite(LED_PIN, HIGH);
      } else {
        // Button released - send INPUT message
        sendInputNotification("BUTTON_1", "RELEASED");
        digitalWrite(LED_PIN, LOW);
      }
    }
  }
  lastReading = reading;
}

void sendSensorValues() {
  // Read potentiometer value
  int potValue = analogRead(POTENTIOMETER_PIN);
  
  // Convert to a normalized value (0.0 to 1.0)
  float normalizedValue = (float)potValue / 1023.0;
  
  // Send VALUE message for a simulated dataref
  sendValueResponse("sim/cockpit2/switches/landing_lights_on", String(normalizedValue, 3));
  
  // Update array with new sensor value
  sensorArray[arrayIndex] = normalizedValue;
  arrayIndex = (arrayIndex + 1) % 5; // Cycle through array positions
}

void sendArrayValues() {
  static unsigned long lastArraySend = 0;
  
  if (millis() - lastArraySend > 2000) { // Send every 2 seconds
    // Create CSV string of array values
    String csvValues = "";
    for (int i = 0; i < 5; i++) {
      csvValues += String(sensorArray[i], 3);
      if (i < 4) {
        csvValues += ",";
      }
    }
    
    // Send ARRAYVALUE message
    sendArrayValue("sensor_array", "float", csvValues);
    lastArraySend = millis();
  }
}

void simulatePeriodicNotifications() {
  static unsigned long lastNotificationTime = 0;
  static int notificationCounter = 0;
  
  if (millis() - lastNotificationTime > 3000) { // Every 3 seconds
    notificationCounter++;
    
    switch (notificationCounter % 4) {
      case 0:
        sendCommand("PING");
        break;
      case 1:
        sendValueResponse("sim/time/zulu_time_sec", String(millis()/1000));
        break;
      case 2:
        sendAck("HEARTBEAT", String(millis()));
        break;
      case 3:
        // Send a specific array element value
        sendElementValue("sensor_array", 0, "float", String(sensorArray[0], 3));
        break;
    }
    
    lastNotificationTime = millis();
  }
}

// Function to send INPUT <KEY> <VALUE> message
void sendInputNotification(String key, String value) {
  String message = "INPUT " + key + " " + value;
  Serial.println(message);
}

// Function to send CMD <COMMAND> message
void sendCommand(String command) {
  String message = "CMD " + command;
  Serial.println(message);
}

// Function to send DREF <DATAREF> <VALUE> message
void sendDatarefWrite(String dataref, String value) {
  String message = "DREF " + dataref + " " + value;
  Serial.println(message);
}

// Function to send ACK <KEY> <VALUE> message
void sendAck(String key, String value) {
  String message = "ACK " + key + " " + value;
  Serial.println(message);
}

// Function to send VALUE <DATAREF> <VALUE> message
void sendValueResponse(String dataref, String value) {
  String message = "VALUE " + dataref + " " + value;
  Serial.println(message);
}

// Function to send ARRAYVALUE <ARRAY_NAME> <TYPE> <CSV_VALUES> message
void sendArrayValue(String arrayName, String dataType, String csvValues) {
  String message = "ARRAYVALUE " + arrayName + " " + dataType + " " + csvValues;
  Serial.println(message);
}

// Function to send ELEMVALUE <ARRAY_NAME[INDEX]> <TYPE> <VALUE> message
void sendElementValue(String arrayName, int index, String dataType, String value) {
  String message = "ELEMVALUE " + arrayName + "[" + index + "] " + dataType + " " + value;
  Serial.println(message);
}

// Example of handling serial input from PC
void handleSerialInput() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim(); // Remove any trailing whitespace
    
    // Echo the received command back as an acknowledgment
    sendAck("RECEIVED", input);
    
    // Parse and handle different commands from PC
    if (input.startsWith("SET_LED ")) {
      int ledState = input.substring(8).toInt(); // Get value after "SET_LED "
      digitalWrite(LED_PIN, ledState ? HIGH : LOW);
      sendAck("LED", ledState ? "ON" : "OFF");
    }
    else if (input.startsWith("GET_SENSOR")) {
      int potValue = analogRead(POTENTIOMETER_PIN);
      sendValueResponse("sim/flightmodel/position/altitude", String(potValue));
    }
    else if (input.startsWith("UPDATE_ARRAY ")) {
      // Parse array update command: UPDATE_ARRAY index value
      int space1 = input.indexOf(' ', 13); // Find space after "UPDATE_ARRAY "
      
      if (space1 > 0) {
        String params = input.substring(space1 + 1);
        int space2 = params.indexOf(' ');
        
        if (space2 > 0) {
          int index = params.substring(0, space2).toInt();
          float value = params.substring(space2 + 1).toFloat();
          
          if (index >= 0 && index < 5) {
            sensorArray[index] = value;
            sendAck("ARRAY_UPDATE", "SUCCESS");
            // Send updated element value back to PC
            sendElementValue("sensor_array", index, "float", String(value, 3));
          } else {
            sendAck("ARRAY_UPDATE", "ERROR_INVALID_INDEX");
          }
        }
      }
    }
  }
}