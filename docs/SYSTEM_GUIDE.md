# X-Plane Dataref Bridge - System Guide

## Introduction
Welcome to the X-Plane Dataref Bridge! This documentation explains how the system works "under the hood" so you can build your own custom hardware cockpits using Arduino, ESP32, or any other serial-capable microcontroller.

**ELI5 (Explain Like I'm 5):**
Imagine X-Plane is a pilot flying a plane.
*   **The Bridge (This App)** is the radio operator sitting next to the pilot.
*   **Your Arduino** is the ground crew.
*   The Radio Operator (Bridge) watches the Pilot (X-Plane). When the pilot lowers the landing gear, the Radio Operator shouts "GEAR_DOWN" to the Ground Crew (Arduino).
*   The Ground Crew (Arduino) hears "GEAR_DOWN" and turns on a green light.
*   If the Ground Crew flips a switch, they shout "FLAPS_DOWN" to the Radio Operator, who tells the Pilot to lower the flaps.

---

## System Architecture

1.  **X-Plane 11/12**: The flight simulator. It has "Datarefs" (Data References) which are variables like `sim/cockpit/switches/gear_handle_status`.
2.  **UDP Connection**: X-Plane sends data out via UDP packets. This app listens to those packets.
3.  **The Bridge App (Python)**:
    *   Receives UDP data from X-Plane.
    *   Translates complex Datarefs (e.g., `sim/cockpit/switches/gear_handle_status` = 1) into simple Keys (e.g., `GEAR_LED` = 1).
    *   Sends these Keys to your Arduino via **USB Serial**.
4.  **Arduino/ESP32**:
    *   Listens to Serial for commands like `SET GEAR_LED 1`.
    *   Turns on LEDs, moves Servos, etc.
    *   Reads Buttons/Potentiometers and sends commands back like `INPUT GEAR_SWITCH 1` or `CMD sim/operation/quit`.

---

## The Serial Protocol
To talk to the Bridge, your Arduino must speak "The Protocol". It's a simple text-based language.

### 1. The Handshake (Start-up)
When you plug in your Arduino, the Bridge doesn't know what it is.
1.  **Bridge says:** `HELLO`
2.  **Arduino must reply:** `XPDR;fw=1.0;board=ESP32;name=MyDevice`
    *   `fw`: Firmware version (for your reference).
    *   `board`: Your board type (e.g., Uno, Mega, ESP32).
    *   `name`: A unique name for this device (e.g., "RadioPanel", "Overhead").

### 2. PC -> Arduino (Outputs)
The Bridge tells the Arduino to do something.
**Format:** `SET <key> <value>`
*   `SET`: The command word.
*   `<key>`: The name of the thing to change (defined in the App).
*   `<value>`: The number value (float).

**Examples:**
*   `SET GEAR_LED 1.0000` (Turn Gear LED On)
*   `SET FLAPS_POS 0.5000` (Move Flaps Servo to 50%)
*   `SET ALTITUDE 10000.0` (Show 10,000 on LCD)

### 3. Arduino -> PC (Inputs)
The Arduino tells the Bridge that a human touched something. There are 3 ways to do this:

#### A. Basic Input (Mapped in App)
You send a key, and the App decides what that key does.
**Format:** `INPUT <key> <value>`
*   **Example:** `INPUT GEAR_SWITCH 1` (You flipped the switch up)
*   **Why use this?** You can change what "GEAR_SWITCH" does inside the App without reprogramming the Arduino.

#### B. Direct Dataref Write (Advanced)
You tell X-Plane directly to change a variable.
**Format:** `DREF <dataref_path> <value>`
*   **Example:** `DREF sim/cockpit/switches/gear_handle_status 1`
*   **Why use this?** Faster for simple things, but requires recompiling Arduino to change the target.

#### C. Command Execution
You tell X-Plane to run a command (like pressing a button in the virtual cockpit).
**Format:** `CMD <command_path>`
*   **Example:** `CMD sim/flight_controls/flaps_down`
*   **Why use this?** Best for momentary buttons or toggle actions.

---

## How to use the Example Sketches
We have provided a folder `examples/arduino` with templates.

1.  **Basic_Template**: Start here. It handles the connection and reading `SET` commands for you.
2.  **Input_Examples**: Shows how to add Buttons, Encoders, Potentiometers.
3.  **Output_Examples**: Shows how to control LEDs, Servos, LCDs.

### Compatibility
The sketches are designed to work on:
*   **AVR Boards**: Arduino Uno, Mega 2560, Nano, Leonardo, Pro Micro.
*   **ESP Boards**: ESP32, ESP32-S2, ESP32-S3, ESP8266.

**Note for ESP32 Users:**
The sketches use standard `Serial`. On some ESP32 boards (like S2/S3 native USB), you might need to use `Serial0` or ensure `USB CDC On Boot` is enabled in Arduino IDE Tools if you are using the native USB port.

## Debugging
If it's not working:
1.  **Open the App Log**: Help -> Open Log File.
2.  **Check Handshake**: Does the log say "Device ready"? If not, your Arduino isn't replying to "HELLO".
3.  **Check Baud Rate**: Ensure your Arduino code has `Serial.begin(115200)`.
