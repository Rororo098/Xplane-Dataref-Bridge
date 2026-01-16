# General Encoder with Command Support

A rotary encoder sketch that can execute X-Plane commands directly.

## Features

- Send encoder rotations as INPUT events to PC
- Execute X-Plane commands via serial (no HID required)
- Separate commands for CW and CCW rotation
- Optional push button with separate command
- Support for multiple encoders (expandable)
- Works on all Arduino boards (Uno, Nano, Leonardo, ESP32)

## Wiring (for KY-040 encoder)

- Encoder CLK → Pin 2 (or your configured ENCODER0_CLK_PIN)
- Encoder DT  → Pin 3 (or your configured ENCODER0_DT_PIN)
- Encoder SW  → Pin 4 (or your configured ENCODER0_BTN_PIN)
- Encoder +   → 5V
- Encoder GND → GND

## Configuration

### Single Encoder (Default)

The sketch is pre-configured with one encoder:

| Setting | Value | Description |
|---------|--------|-------------|
| CLK Pin | 2 | Clock signal pin |
| DT Pin  | 3 | Data signal pin |
| Button Pin | 4 | Push switch (optional) |
| CW Command | sim/autopilot/heading_up | Command for clockwise rotation |
| CCW Command | sim/autopilot/heading_down | Command for counter-clockwise rotation |
| Button Command | sim/autopilot/heading_sync | Command when button is pressed |

### Adding More Encoders

To add additional encoders:

1. Increase `NUM_ENCODERS` at the top of the sketch
2. Add pin definitions:

   ```cpp
   #define ENCODER1_CLK_PIN 5
   #define ENCODER1_DT_PIN 6
   #define ENCODER1_BTN_PIN 7
   ```

3. Update the `ENCODER_PINS` array:

   ```cpp
   const int ENCODER_PINS[NUM_ENCODERS][3] = {
     {ENCODER0_CLK_PIN, ENCODER0_DT_PIN, ENCODER0_BTN_PIN},
     {ENCODER1_CLK_PIN, ENCODER1_DT_PIN, ENCODER1_BTN_PIN}
   };
   ```

4. Add names for input tracking:

   ```cpp
   const char* ENCODER_NAMES[NUM_ENCODERS] = {
     "ENC_CMD_0",
     "ENC_CMD_1"
   };

   const char* ENCODER_BUTTON_NAMES[NUM_ENCODERS] = {
     "BTN_CMD_0",
     "BTN_CMD_1"
   };
   ```

5. Configure commands for the new encoder:

   ```cpp
   const char* ENCODER_COMMANDS_CW[NUM_ENCODERS] = {
     "sim/autopilot/heading_up",
     "sim/autopilot/altitude_up"    // Encoder 1 CW
   };

   const char* ENCODER_COMMANDS_CCW[NUM_ENCODERS] = {
     "sim/autopilot/heading_down",
     "sim/autopilot/altitude_down"   // Encoder 1 CCW
   };

   const char* ENCODER_BUTTON_COMMANDS[NUM_ENCODERS] = {
     "sim/autopilot/heading_sync",
     "sim/autopilot/altitude_hold"   // Encoder 1 button
   };
   ```

## Usage in X-Plane Dataref Bridge

### Step 1: Connect Arduino

1. Upload the sketch to your Arduino
2. Connect via USB
3. Open X-Plane Dataref Bridge application
4. Go to the "Hardware" tab
5. Verify the device appears as "GeneralEncoderCommands"

### Step 2: Map Encoder (Optional)

The encoder sends INPUT events, so you can optionally create mappings:

1. Go to "Mappings" tab
2. Click "Add Mapping"
3. Select input key: `ENC_CMD_0`
4. This is optional since the encoder already executes commands directly
5. You can use this for logging, monitoring, or backup control

### Step 3: Speed Multiplier (Optional)

To execute commands faster:

1. Go to "Mappings" tab
2. Add or edit mapping for the encoder input key
3. Set "Speed Multiplier" to > 1.0
4. Set "Command Delay" to desired interval (e.g., 20ms)
5. Each encoder tick will execute the command multiple times with delays

Example: Multiplier 3.0 = Command executes 3 times, 20ms apart

## Common X-Plane Commands

### Autopilot

- `sim/autopilot/heading_up` - Increase heading bug
- `sim/autopilot/heading_down` - Decrease heading bug
- `sim/autopilot/heading_sync` - Sync heading bug to current heading
- `sim/autopilot/altitude_up` - Increase selected altitude
- `sim/autopilot/altitude_down` - Decrease selected altitude
- `sim/autopilot/altitude_hold` - Engage altitude hold
- `sim/autopilot/airspeed_up` - Increase selected airspeed
- `sim/autopilot/airspeed_down` - Decrease selected airspeed

### Radio

- `sim/radios/stby_com1_fine_up` - Fine tune COM1 frequency up
- `sim/radios/stby_com1_fine_down` - Fine tune COM1 frequency down
- `sim/radios/com1_stby_flip` - Toggle COM1 standby/active
- `sim/radios/stby_com1_coarse_up` - Coarse tune COM1 frequency up
- `sim/radios/stby_com1_coarse_down` - Coarse tune COM1 frequency down

### Instruments

- `sim/instruments/heading_bug_up` - Heading bug up
- `sim/instruments/heading_bug_down` - Heading bug down
- `sim/instruments/altimeter_up` - Altimeter up
- `sim/instruments/altimeter_down` - Altimeter down

### Finding Commands

1. Open X-Plane
2. Go to **Developer** menu
3. Select **Dataref Editor**
4. Browse commands starting with `sim/`

## Protocol

### Handshake

```
PC → Arduino: HELLO
Arduino → PC:   XPDR;fw=1.0;name=GeneralEncoderCommands
```

### Encoder Rotation (Clockwise)

```
Arduino → PC: INPUT ENC_CMD_0 1.0
Arduino → PC: CMD sim/autopilot/heading_up
```

### Encoder Rotation (Counter-Clockwise)

```
Arduino → PC: INPUT ENC_CMD_0 -1.0
Arduino → PC: CMD sim/autopilot/heading_down
```

### Encoder Button Press

```
Arduino → PC: INPUT BTN_CMD_0 1.0
Arduino → PC: CMD sim/autopilot/heading_sync
```

### PC → Arduino (Optional)

```
PC → Arduino: SET SOME_KEY 1.0
Arduino → PC:   ACK SOME_KEY 1.000000
```

## Example Configurations

### Radio Frequency Knob

```cpp
const char* ENCODER_COMMANDS_CW[NUM_ENCODERS] = {
  "sim/radios/stby_com1_fine_up"
};

const char* ENCODER_COMMANDS_CCW[NUM_ENCODERS] = {
  "sim/radios/stby_com1_fine_down"
};

const char* ENCODER_BUTTON_COMMANDS[NUM_ENCODERS] = {
  "sim/radios/com1_stby_flip"
};
```

### Autopilot Heading Bug

```cpp
const char* ENCODER_COMMANDS_CW[NUM_ENCODERS] = {
  "sim/autopilot/heading_up"
};

const char* ENCODER_COMMANDS_CCW[NUM_ENCODERS] = {
  "sim/autopilot/heading_down"
};

const char* ENCODER_BUTTON_COMMANDS[NUM_ENCODERS] = {
  "sim/autopilot/heading_sync"
};
```

### Altimeter Knob

```cpp
const char* ENCODER_COMMANDS_CW[NUM_ENCODERS] = {
  "sim/instruments/altimeter_up"
};

const char* ENCODER_COMMANDS_CCW[NUM_ENCODERS] = {
  "sim/instruments/altimeter_down"
};

const char* ENCODER_BUTTON_COMMANDS[NUM_ENCODERS] = {
  "" // No button or leave empty
};
```

## Troubleshooting

### Encoder Not Responding

- Check wiring (CLK and DT pins)
- Verify pin numbers match configuration
- Test with serial monitor to see if INPUT events are sent

### Commands Not Executing

- Verify command paths are correct (use X-Plane Dataref Editor)
- Check that PC bridge is running and connected
- Look at PC logs for CMD lines being received

### Wrong Direction

- Swap CLK and DT pin assignments
- Or invert logic by swapping CW/CCW command assignments

## License

This example is part of the X-Plane Dataref Bridge project.
