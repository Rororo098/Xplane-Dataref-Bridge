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

// Global variables for debouncing
int lastButtonState = HIGH;
int currentButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;
int lastReading = HIGH;
unsigned long lastDebounceTime_var = 0;
const unsigned long debounceDelay_var = 50;
int lastButtonState_var = HIGH;
int currentButtonState_var = HIGH;
int lastReading_var = HIGH;
unsigned long lastSensorSend = 0;
unsigned long lastArraySend = 0;
unsigned long lastNotificationTime = 0;

// Array example
float sensorArray[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
int arrayIndex = 0;
int sensorArray_index = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(POTENTIOMETER_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  Serial.println("Arduino ready - sending messages to PC");
}

void loop() {
  // Check for button presses (INPUT message example)
  checkButtonPress();
  
  // Periodically send sensor values (VALUE message example)
  if (millis() - lastSensorSend > 1000) { // Send every second
    sendSensorValues();
    lastSensorSend = millis();
  }
  
  // Send array values periodically (ARRAYVALUE message example)
  if (millis() - lastArraySend > 2000) { // Send every 2 seconds
    sendArrayValues();
    lastArraySend = millis();
  }
  
  // Simulate periodic notifications
  if (millis() - lastNotificationTime > 3000) { // Every 3 seconds
    simulatePeriodicMessages();
    lastNotificationTime = millis();
  }
  
  // Handle incoming messages from PC
  handleSerialInput();
  
  delay(10); // Small delay to prevent overwhelming the serial port
}

void checkButtonPress() {
  int reading = digitalRead(BUTTON_PIN);

  // Debounce the button
  if (reading != lastReading_var) {
    lastDebounceTime_var = millis();
  }
  
  if ((millis() - lastDebounceTime_var) > debounceDelay_var) {
    if (reading != lastButtonState_var) {
      lastButtonState_var = reading;
      
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
  lastReading_var = reading;
}

void sendSensorValues() {
  // Read potentiometer value
  int potValue = analogRead(POTENTIOMETER_PIN);
  
  // Convert to a normalized value (0.0 to 1.0)
  float normalizedValue = (float)potValue / 1023.0;
  
  // Send VALUE message for a simulated dataref
  sendValueResponse("sim/cockpit2/switches/landing_lights_on", String(normalizedValue, 3));
  
  // Update our array with the new value
  sensorArray[sensorArray_index] = normalizedValue;
  sensorArray_index = (sensorArray_index + 1) % 5; // Cycle through array positions
}

void sendArrayValues() {
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
}

void simulatePeriodicMessages() {
  // Send different types of messages periodically to demonstrate the protocol
  
  // Send a command notification
  sendCommand("HEARTBEAT_" + String(millis()));
  
  // Send a value response
  sendValueResponse("sim/time/zulu_time_sec", String(millis()/1000));
  
  // Send an acknowledgment
  sendAck("PERIODIC", String(millis()));
  
  // Send an element value
  sendElementValue("sensor_array", 0, "float", String(random(100)/100.0, 3));
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

// Function to handle serial input from PC
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