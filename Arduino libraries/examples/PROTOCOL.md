# Arduino Communication Protocol

## Overview

This document explains how your Arduino/ESP32 talks to XPlane Dataref Bridge.

Communication happens over **Serial USB** at **115200 baud**.

---

## Message Format

All messages are **text-based** and end with a **newline** (`\n`).

This makes debugging easy - you can read messages in Serial Monitor!

---

## Messages: PC → Arduino (Receiving)

### `SET <KEY> <VALUE>`

The PC sends this when an X-Plane dataref changes.

```
SET GEAR 1.0
SET THROTTLE 0.75
SET FLAPS 0.5
SET MASTER_WARN 1.0
```

**Your Arduino should:**
1. Parse the KEY and VALUE
2. Do something with it (light LED, move servo, etc.)
3. Optionally send back an ACK

### `HELLO`

The PC sends this to check if device is ready.

```
HELLO
```

**Your Arduino should respond with:**
```
XPDR;fw=1.0;board=ESP32S2;name=MyPanel
```

---

## Messages: Arduino → PC (Sending)

### `XPDR;fw=<version>;board=<type>;name=<name>`

Handshake response. Tells PC about your device.

```
XPDR;fw=1.0;board=ESP32S2;name=FlightPanel
```

| Field | Description | Examples |
|-------|-------------|----------|
| `fw` | Firmware version | `1.0`, `2.3.1` |
| `board` | Board type | `ESP32S2`, `Arduino Nano`, `Leonardo` |
| `name` | Device name | `FGCP`, `Throttle Quadrant` |

### `INPUT <KEY> <VALUE>`

Send input events to the PC.

```
INPUT BTN_GEAR 1.0      // Button pressed
INPUT BTN_GEAR 0.0      // Button released
INPUT ENC_HDG 1.0       // Encoder turned clockwise
INPUT ENC_HDG -1.0      // Encoder turned counter-clockwise
INPUT POT_THROTTLE 0.5  // Potentiometer at 50%
```

### `CMD <COMMAND>`

Directly trigger an X-Plane command.

```
CMD sim/flight_controls/landing_gear_toggle
CMD sim/autopilot/heading_up
CMD sim/lights/beacon_lights_toggle
```

### `DREF <DATAREF> <VALUE>`

Directly write to an X-Plane dataref.

```
DREF sim/cockpit2/controls/gear_handle_down 1.0
DREF sim/cockpit2/engine/actuators/throttle_ratio_all 0.75
```

### `ACK <KEY> <VALUE>`

Acknowledge a SET command (optional, for debugging).

```
ACK GEAR 1.0
```

---

## Complete Communication Example

```
Timeline:
=========

[Device boots up]
Arduino: (waits for PC)

[PC connects]
PC → Arduino: HELLO

[Arduino responds with device info]
Arduino → PC: XPDR;fw=1.0;board=ESP32S2;name=GearPanel

[X-Plane gear changes, PC notifies Arduino]
PC → Arduino: SET GEAR 1.0

[Arduino turns on gear LED and acknowledges]
Arduino → PC: ACK GEAR 1.0

[User presses button on Arduino]
Arduino → PC: INPUT BTN_AP 1.0

[User releases button]
Arduino → PC: INPUT BTN_AP 0.0

[User turns encoder clockwise]
Arduino → PC: INPUT ENC_HDG 1.0
Arduino → PC: INPUT ENC_HDG 1.0
Arduino → PC: INPUT ENC_HDG 1.0
```

---

## Minimal Arduino Template

```cpp
// ============================================================
// XPlane Dataref Bridge - Minimal Template
// ============================================================
// This is the simplest possible firmware that works with
// the XPlane Dataref Bridge application.
// ============================================================

void setup() {
    // Start serial communication at 115200 baud
    // This MUST match the PC application's baud rate
    Serial.begin(115200);
    
    // Wait for serial port to be ready
    while (!Serial) {
        delay(10);
    }
}

void loop() {
    // Check if PC sent us any data
    if (Serial.available()) {
        // Read the incoming line
        String line = Serial.readStringUntil('\n');
        line.trim();  // Remove whitespace
        
        // Handle the message
        handleMessage(line);
    }
    
    // Your input reading code here
    // (buttons, encoders, potentiometers)
}

void handleMessage(String message) {
    // --------------------------------------------------------
    // HELLO - Handshake request from PC
    // --------------------------------------------------------
    if (message == "HELLO") {
        // Respond with device info
        Serial.println("XPDR;fw=1.0;board=Arduino;name=MyDevice");
    }
    
    // --------------------------------------------------------
    // SET <KEY> <VALUE> - PC wants us to update something
    // --------------------------------------------------------
    else if (message.startsWith("SET ")) {
        // Extract key and value
        int firstSpace = message.indexOf(' ');
        int secondSpace = message.indexOf(' ', firstSpace + 1);
        
        String key = message.substring(firstSpace + 1, secondSpace);
        float value = message.substring(secondSpace + 1).toFloat();
        
        // Handle the key
        handleSet(key, value);
    }
}

void handleSet(String key, float value) {
    // --------------------------------------------------------
    // Add your output handling here!
    // --------------------------------------------------------
    
    // Example: Gear LED
    if (key == "GEAR") {
        // Turn LED on if gear is down (value > 0.5)
        // digitalWrite(GEAR_LED_PIN, value > 0.5 ? HIGH : LOW);
    }
    
    // Example: Throttle servo
    else if (key == "THROTTLE") {
        // Map 0.0-1.0 to servo position 0-180
        // int angle = (int)(value * 180);
        // servo.write(angle);
    }
    
    // Send acknowledgment (optional)
    Serial.print("ACK ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(value);
}

// ============================================================
// Helper function to send input events
// ============================================================
void sendInput(String key, float value) {
    Serial.print("INPUT ");
    Serial.print(key);
    Serial.print(" ");
    Serial.println(value, 4);  // 4 decimal places
}

// ============================================================
// Helper function to send X-Plane commands directly
// ============================================================
void sendCommand(String command) {
    Serial.print("CMD ");
    Serial.println(command);
}

// ============================================================
// Helper function to write X-Plane datarefs directly
// ============================================================
void sendDataref(String dataref, float value) {
    Serial.print("DREF ");
    Serial.print(dataref);
    Serial.print(" ");
    Serial.println(value, 4);
}
```

---

## ESP32-S2/S3 Hybrid Mode

ESP32-S2 and S3 can act as **both**:
1. **USB HID Device** (Joystick) - for inputs
2. **USB CDC Serial** - for outputs

This means you can:
- Use native joystick buttons (faster, no mapping needed)
- Receive serial data for LEDs/servos

See the [Hybrid Sketches](hybrid/) for examples.

---

## Troubleshooting

### Nothing happens when I send from Arduino

1. Check baud rate is 115200
2. Make sure messages end with `\n` (println, not print)
3. Check Serial Monitor shows your messages

### PC doesn't see my device

1. Install USB drivers (CH340, CP2102, etc.)
2. Check Device Manager for COM port
3. Try a different USB cable (some are charge-only!)

### Values are wrong/garbled

1. Don't mix `print` and `println` mid-message
2. Use `Serial.println()` for complete messages
3. Add small delay if sending many messages quickly

---

## Best Practices

### 1. Use Meaningful Key Names

```cpp
// ✅ Good - clear what it is
sendInput("BTN_GEAR", 1.0);
sendInput("ENC_HEADING", 1.0);
sendInput("POT_THROTTLE", 0.5);

// ❌ Bad - confusing
sendInput("B1", 1.0);
sendInput("E1", 1.0);
sendInput("A0", 0.5);
```

### 2. Debounce Buttons

```cpp
// ✅ Good - debounced
if (buttonPressed && millis() - lastPress > 50) {
    sendInput("BTN_GEAR", 1.0);
    lastPress = millis();
}

// ❌ Bad - will send many times
if (digitalRead(BUTTON_PIN) == LOW) {
    sendInput("BTN_GEAR", 1.0);
}
```

### 3. Only Send Changes

```cpp
// ✅ Good - only send when value changes
int newValue = analogRead(POT_PIN);
if (abs(newValue - lastValue) > 10) {
    sendInput("POT_THROTTLE", newValue / 1023.0);
    lastValue = newValue;
}

// ❌ Bad - floods serial with same values
sendInput("POT_THROTTLE", analogRead(POT_PIN) / 1023.0);
```

### 4. Handle Unknown Keys Gracefully

```cpp
void handleSet(String key, float value) {
    if (key == "GEAR") {
        // handle gear
    }
    else if (key == "FLAPS") {
        // handle flaps
    }
    else {
        // Unknown key - ignore or log
        Serial.print("UNKNOWN KEY: ");
        Serial.println(key);
    }
}
```
