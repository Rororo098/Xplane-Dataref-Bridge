"""
Sample code snippets for handling Arduino-to-PC message types

This file demonstrates how to parse and handle the different message types
in the Arduino-to-PC communication protocol:
- INPUT <KEY> <VALUE>: Input notification
- CMD <COMMAND>: Command execution
- DREF <DATAREF> <VALUE>: Dataref write
- ACK <KEY> <VALUE>: Acknowledgment
- VALUE <DATAREF> <VALUE>: Dataref value response
- ARRAYVALUE <ARRAY_NAME> <TYPE> <CSV_VALUES>: Array value response
- ELEMVALUE <ARRAY_NAME[INDEX]> <TYPE> <VALUE>: Array element value response
"""

import re
import json
from typing import Dict, Any, List, Tuple, Optional


class MessageParser:
    """
    A parser for handling different types of messages from Arduino to PC
    """
    
    def __init__(self):
        # Regex patterns for different message types
        self.patterns = {
            'INPUT': r'^INPUT\s+(\w+)\s+(.+)$',
            'CMD': r'^CMD\s+(.+)$',
            'DREF': r'^DREF\s+([^\s]+)\s+(.+)$',
            'ACK': r'^ACK\s+(\w+)\s+(.+)$',
            'VALUE': r'^VALUE\s+([^\s]+)\s+(.+)$',
            'ARRAYVALUE': r'^ARRAYVALUE\s+(\w+)\s+(\w+)\s+(.+)$',
            'ELEMVALUE': r'^ELEMVALUE\s+(\w+\[\d+\])\s+(\w+)\s+(.+)$'
        }
    
    def parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse an incoming message and return its type and components
        """
        message = message.strip()
        
        for msg_type, pattern in self.patterns.items():
            match = re.match(pattern, message)
            if match:
                groups = match.groups()
                
                if msg_type == 'INPUT':
                    return {
                        'type': 'INPUT',
                        'key': groups[0],
                        'value': groups[1]
                    }
                elif msg_type == 'CMD':
                    return {
                        'type': 'CMD',
                        'command': groups[0]
                    }
                elif msg_type == 'DREF':
                    return {
                        'type': 'DREF',
                        'dataref': groups[0],
                        'value': groups[1]
                    }
                elif msg_type == 'ACK':
                    return {
                        'type': 'ACK',
                        'key': groups[0],
                        'value': groups[1]
                    }
                elif msg_type == 'VALUE':
                    return {
                        'type': 'VALUE',
                        'dataref': groups[0],
                        'value': groups[1]
                    }
                elif msg_type == 'ARRAYVALUE':
                    return {
                        'type': 'ARRAYVALUE',
                        'array_name': groups[0],
                        'data_type': groups[1],
                        'values': [val.strip() for val in groups[2].split(',')]
                    }
                elif msg_type == 'ELEMVALUE':
                    # Extract array name and index from format like "arrayname[0]"
                    array_match = re.match(r'(\w+)\[(\d+)\]', groups[0])
                    if array_match:
                        array_name, index = array_match.groups()
                        return {
                            'type': 'ELEMVALUE',
                            'array_name': array_name,
                            'index': int(index),
                            'data_type': groups[1],
                            'value': groups[2]
                        }
        
        # If no pattern matches, return None
        return None


class ArduinoMessageHandler:
    """
    Handler for processing different types of messages from Arduino
    """
    
    def __init__(self):
        self.parser = MessageParser()
        self.variables = {}
        self.datarefs = {}
        self.arrays = {}
    
    def handle_message(self, message: str) -> bool:
        """
        Process an incoming message from Arduino
        """
        parsed_msg = self.parser.parse_message(message)
        
        if not parsed_msg:
            print(f"Unknown message format: {message}")
            return False
        
        msg_type = parsed_msg['type']
        
        if msg_type == 'INPUT':
            return self.handle_input(parsed_msg)
        elif msg_type == 'CMD':
            return self.handle_cmd(parsed_msg)
        elif msg_type == 'DREF':
            return self.handle_dref(parsed_msg)
        elif msg_type == 'ACK':
            return self.handle_ack(parsed_msg)
        elif msg_type == 'VALUE':
            return self.handle_value(parsed_msg)
        elif msg_type == 'ARRAYVALUE':
            return self.handle_arrayvalue(parsed_msg)
        elif msg_type == 'ELEMVALUE':
            return self.handle_elemvalue(parsed_msg)
        
        return False
    
    def handle_input(self, msg: Dict[str, Any]) -> bool:
        """
        Handle INPUT <KEY> <VALUE> messages
        Used for input notifications from Arduino (buttons, switches, etc.)
        """
        key = msg['key']
        value = msg['value']
        
        print(f"Input received: {key} = {value}")
        
        # Store the input value in variables
        self.variables[key] = value
        
        # You could trigger specific actions based on the input
        if key.startswith('button'):
            self.process_button(key, value)
        elif key.startswith('switch'):
            self.process_switch(key, value)
        elif key.startswith('pot'):
            self.process_potentiometer(key, value)
        
        return True
    
    def handle_cmd(self, msg: Dict[str, Any]) -> bool:
        """
        Handle CMD <COMMAND> messages
        Used for command execution requests from Arduino
        """
        command = msg['command']
        
        print(f"Command received: {command}")
        
        # Execute the command
        if command == 'RESET':
            self.reset_system()
        elif command == 'REBOOT':
            self.reboot_system()
        elif command.startswith('SET_MODE'):
            self.set_mode(command.split(' ', 1)[1])
        else:
            print(f"Unknown command: {command}")
            return False
        
        return True
    
    def handle_dref(self, msg: Dict[str, Any]) -> bool:
        """
        Handle DREF <DATAREF> <VALUE> messages
        Used for writing values to datarefs
        """
        dataref = msg['dataref']
        value = msg['value']
        
        print(f"Dataref write: {dataref} = {value}")
        
        # Send the dataref value to X-Plane
        self.send_to_xplane(dataref, value)
        
        # Store locally for reference
        self.datarefs[dataref] = value
        
        return True
    
    def handle_ack(self, msg: Dict[str, Any]) -> bool:
        """
        Handle ACK <KEY> <VALUE> messages
        Used for acknowledgments from Arduino
        """
        key = msg['key']
        value = msg['value']
        
        print(f"Acknowledgment: {key} = {value}")
        
        # Process acknowledgment based on the key
        if key == 'INIT':
            print("Arduino initialization acknowledged")
        elif key == 'CONFIG':
            print(f"Configuration acknowledged: {value}")
        elif key.startswith('WRITE'):
            print(f"Write operation acknowledged: {value}")
        
        return True
    
    def handle_value(self, msg: Dict[str, Any]) -> bool:
        """
        Handle VALUE <DATAREF> <VALUE> messages
        Used for reporting dataref values from Arduino sensors
        """
        dataref = msg['dataref']
        value = msg['value']
        
        print(f"Dataref value reported: {dataref} = {value}")
        
        # Store the reported value
        self.datarefs[dataref] = value
        
        # Could trigger updates in the UI or other systems
        self.update_dataref_display(dataref, value)
        
        return True
    
    def handle_arrayvalue(self, msg: Dict[str, Any]) -> bool:
        """
        Handle ARRAYVALUE <ARRAY_NAME> <TYPE> <CSV_VALUES> messages
        Used for reporting array values from Arduino
        """
        array_name = msg['array_name']
        data_type = msg['data_type']
        values = msg['values']
        
        print(f"Array value reported: {array_name} ({data_type}) = {values}")
        
        # Convert values based on type
        converted_values = self.convert_values(values, data_type)
        
        # Store the array
        self.arrays[array_name] = {
            'type': data_type,
            'values': converted_values
        }
        
        # Could trigger updates for array data
        self.update_array_display(array_name, converted_values)
        
        return True
    
    def handle_elemvalue(self, msg: Dict[str, Any]) -> bool:
        """
        Handle ELEMVALUE <ARRAY_NAME[INDEX]> <TYPE> <VALUE> messages
        Used for reporting individual array element values from Arduino
        """
        array_name = msg['array_name']
        index = msg['index']
        data_type = msg['data_type']
        value = msg['value']
        
        print(f"Array element value: {array_name}[{index}] ({data_type}) = {value}")
        
        # Convert value based on type
        converted_value = self.convert_single_value(value, data_type)
        
        # Initialize array if it doesn't exist
        if array_name not in self.arrays:
            self.arrays[array_name] = {'type': data_type, 'values': []}
        
        # Ensure the array is large enough
        while len(self.arrays[array_name]['values']) <= index:
            self.arrays[array_name]['values'].append(None)
        
        # Set the value at the specified index
        self.arrays[array_name]['values'][index] = converted_value
        
        # Could trigger updates for specific array elements
        self.update_array_element_display(array_name, index, converted_value)
        
        return True
    
    def convert_values(self, values: List[str], data_type: str) -> List[Any]:
        """
        Convert string values to appropriate types based on data_type
        """
        if data_type.lower() == 'float':
            return [float(v) for v in values]
        elif data_type.lower() == 'int':
            return [int(v) for v in values]
        elif data_type.lower() == 'bool':
            return [v.lower() == 'true' for v in values]
        else:  # Default to string
            return values
    
    def convert_single_value(self, value: str, data_type: str) -> Any:
        """
        Convert a single string value to appropriate type
        """
        if data_type.lower() == 'float':
            return float(value)
        elif data_type.lower() == 'int':
            return int(value)
        elif data_type.lower() == 'bool':
            return value.lower() == 'true'
        else:  # Default to string
            return value
    
    # Placeholder methods for actual implementations
    def process_button(self, key: str, value: str):
        """Process button input"""
        print(f"Processing button {key} with value {value}")
    
    def process_switch(self, key: str, value: str):
        """Process switch input"""
        print(f"Processing switch {key} with value {value}")
    
    def process_potentiometer(self, key: str, value: str):
        """Process potentiometer input"""
        print(f"Processing potentiometer {key} with value {value}")
    
    def reset_system(self):
        """Reset the system"""
        print("Resetting system...")
    
    def reboot_system(self):
        """Reboot the system"""
        print("Rebooting system...")
    
    def set_mode(self, mode: str):
        """Set system mode"""
        print(f"Setting mode to {mode}")
    
    def send_to_xplane(self, dataref: str, value: str):
        """Send dataref value to X-Plane"""
        print(f"Sending {dataref} = {value} to X-Plane")
    
    def update_dataref_display(self, dataref: str, value: str):
        """Update dataref display in UI"""
        print(f"Updating display for {dataref} = {value}")
    
    def update_array_display(self, array_name: str, values: List[Any]):
        """Update array display in UI"""
        print(f"Updating array display for {array_name}: {values}")
    
    def update_array_element_display(self, array_name: str, index: int, value: Any):
        """Update specific array element display in UI"""
        print(f"Updating array element display for {array_name}[{index}] = {value}")


# Arduino-side C++ code examples (as comments)
ARDUINO_CODE_EXAMPLES = """
// Arduino code examples for sending different message types

// Example 1: Sending input notification (e.g., button press)
void sendInputNotification(String key, String value) {
  Serial.println("INPUT " + key + " " + value);
}

// Example 2: Sending command execution request
void sendCommand(String command) {
  Serial.println("CMD " + command);
}

// Example 3: Sending dataref write request
void sendDatarefWrite(String dataref, String value) {
  Serial.println("DREF " + dataref + " " + value);
}

// Example 4: Sending acknowledgment
void sendAck(String key, String value) {
  Serial.println("ACK " + key + " " + value);
}

// Example 5: Sending dataref value response
void sendValueResponse(String dataref, String value) {
  Serial.println("VALUE " + dataref + " " + value);
}

// Example 6: Sending array value response
void sendArrayValue(String arrayName, String dataType, String csvValues) {
  Serial.println("ARRAYVALUE " + arrayName + " " + dataType + " " + csvValues);
}

// Example 7: Sending array element value response
void sendElementValue(String arrayName, int index, String dataType, String value) {
  String message = "ELEMVALUE ";
  message += arrayName;
  message += "[";
  message += index;
  message += "] ";
  message += dataType;
  message += " ";
  message += value;
  Serial.println(message);
}

// Complete example of Arduino code that handles inputs and sends messages
String lastButtonState = "0";

void checkInputs() {
  int buttonState = digitalRead(2); // Assume button connected to pin 2
  
  if (buttonState != lastButtonState) {
    if (buttonState == HIGH) {
      sendInputNotification("button1", "pressed");
    } else {
      sendInputNotification("button1", "released");
    }
    lastButtonState = buttonState;
  }
  
  // Send potentiometer value periodically
  int potValue = analogRead(A0);
  sendValueResponse("sim/cockpit2/switches/landing_lights_on", String(potValue));
}

void setup() {
  Serial.begin(115200);
  pinMode(2, INPUT_PULLUP);
}

void loop() {
  checkInputs();
  delay(50);
}
"""


def demo_message_handling():
    """
    Demonstrate the message handling functionality
    """
    handler = ArduinoMessageHandler()
    
    # Sample messages to test
    test_messages = [
        "INPUT button1 pressed",
        "CMD RESET",
        "DREF sim/cockpit2/switches/landing_lights_on 1",
        "ACK INIT success",
        "VALUE sim/flightmodel/position/altitude 1000.5",
        "ARRAYVALUE gauge_values float 1.0,2.5,3.7,4.2",
        "ELEMVALUE servo_positions[2] int 1500"
    ]
    
    print("Testing message parsing and handling:")
    print("=" * 50)
    
    for msg in test_messages:
        print(f"\nProcessing: {msg}")
        success = handler.handle_message(msg)
        print(f"Result: {'Success' if success else 'Failed'}")
    
    print("\nFinal state:")
    print(f"Variables: {handler.variables}")
    print(f"Datarefs: {handler.datarefs}")
    print(f"Arrays: {handler.arrays}")


if __name__ == "__main__":
    demo_message_handling()
    
    print("\n" + "=" * 50)
    print("Arduino code examples:")
    print(ARDUINO_CODE_EXAMPLES)