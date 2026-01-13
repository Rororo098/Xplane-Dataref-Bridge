// ============================================================
// XPlane Dataref Bridge - Buzzer & Speaker Example
// ============================================================
// 
// WHAT THIS DOES:
// ---------------
// Plays sounds based on X-Plane events!
// From simple beeps to voice warnings.
//
// Perfect for:
// - Master warning/caution alerts
// - Gear warning horn
// - Stall warning
// - Altitude alerts
// - Marker beacon tones
// - Autopilot disconnect warning
// - Landing gear horn
// - GPWS-style callouts (with DFPlayer)
//
// HARDWARE OPTIONS:
// -----------------
// 1. Passive Buzzer - Simple beeps, needs tone()
// 2. Active Buzzer - Just on/off, makes its own sound
// 3. Speaker with DFPlayer - Full audio files (MP3)
//
// WIRING (Passive Buzzer):
// ------------------------
// Buzzer + → Arduino PWM Pin (through 100Ω resistor)
// Buzzer - → GND
//
// WIRING (Active Buzzer):
// -----------------------
// Buzzer + → Arduino Digital Pin
// Buzzer - → GND
//
// ============================================================

// ============================================================
// CONFIGURATION
// ============================================================

// Choose your hardware:
#define USE_PASSIVE_BUZZER true    // Set false for active buzzer
#define USE_DFPLAYER false          // Set true if using DFPlayer for MP3

// Buzzer pin
#define BUZZER_PIN 9  // Use PWM pin for passive buzzer

// ============================================================
// SOUND DEFINITIONS
// ============================================================

// How many different sound triggers do we have?
#define NUM_SOUNDS 6

// Sound types
#define SOUND_BEEP      0   // Single beep
#define SOUND_WARN      1   // Warning (repeating fast beeps)
#define SOUND_ALARM     2   // Alarm (continuous tone)
#define SOUND_CLICK     3   // Short click
#define SOUND_MELODY    4   // Play a melody
#define SOUND_SILENCE   5   // Stop all sounds

// Define our sounds
struct SoundDef {
    const char* key;        // Key from PC app
    int soundType;          // What type of sound to play
    int frequency;          // Tone frequency (Hz) for passive buzzer
    int duration;           // Duration (ms) for single sounds
};

SoundDef sounds[NUM_SOUNDS] = {
    {"MASTER_WARN",   SOUND_WARN,   2000, 200},    // High pitched warning
    {"MASTER_CAUT",   SOUND_BEEP,   1500, 300},    // Caution beep
    {"GEAR_WARN",     SOUND_ALARM,  800,  0},      // Continuous gear horn
    {"STALL_WARN",    SOUND_WARN,   2500, 100},    // Very fast stall warning
    {"ALT_ALERT",     SOUND_BEEP,   1000, 500},    // Single altitude beep
    {"AP_DISC",       SOUND_MELODY, 0,    0}       // AP disconnect melody
};

// ============================================================
// MARKER BEACON TONES (Optional)
// ============================================================
// Outer marker: 400 Hz dashes
// Middle marker: 1300 Hz alternating
// Inner marker: 3000 Hz rapid dots

#define OUTER_MARKER_FREQ 400
#define MIDDLE_MARKER_FREQ 1300
#define INNER_MARKER_FREQ 3000

// ============================================================
// INTERNAL VARIABLES
// ============================================================

// Current sound state
bool soundActive[NUM_SOUNDS];

// For repeating sounds
unsigned long lastBeepTime = 0;
bool beepState = false;

// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    while (!Serial) delay(10);
    
    // Initialize buzzer pin
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);
    
    // Initialize sound states
    for (int i = 0; i < NUM_SOUNDS; i++) {
        soundActive[i] = false;
    }
    
    Serial.println("// Buzzer Controller Ready!");
    
    // Test beep
    testBuzzer();
}

// ============================================================
// MAIN LOOP
// ============================================================

void loop() {
    // Check for messages from PC
    if (Serial.available()) {
        String message = Serial.readStringUntil('\n');
        message.trim();
        handleMessage(message);
    }
    
    // Update sounds
    updateSounds();
    
    delay(10);
}

// ============================================================
// HANDLE MESSAGE FROM PC
// ============================================================

void handleMessage(String message) {
    // --------------------------------------------------------
    // HELLO - Handshake
    // --------------------------------------------------------
    if (message == "HELLO") {
        Serial.println("XPDR;fw=1.0;board=Buzzer;name=AudioAlerts");
    }
    
    // --------------------------------------------------------
    // SET <KEY> <VALUE> - Trigger/stop sounds
    // --------------------------------------------------------
    else if (message.startsWith("SET ")) {
        int firstSpace = message.indexOf(' ');
        int secondSpace = message.indexOf(' ', firstSpace + 1);
        
        if (secondSpace == -1) return;
        
        String key = message.substring(firstSpace + 1, secondSpace);
        float value = message.substring(secondSpace + 1).toFloat();
        
        // Find matching sound
        for (int i = 0; i < NUM_SOUNDS; i++) {
            if (key == sounds[i].key) {
                // value > 0.5 = turn on, value <= 0.5 = turn off
                bool shouldPlay = (value > 0.5);
                
                if (shouldPlay && !soundActive[i]) {
                    // Start sound
                    startSound(i);
                }
                else if (!shouldPlay && soundActive[i]) {
                    // Stop sound
                    stopSound(i);
                }
                
                // Acknowledge
                Serial.print("ACK ");
                Serial.print(key);
                Serial.print(" ");
                Serial.println(value);
                
                break;
            }
        }
    }
}

// ============================================================
// START SOUND
// ============================================================

void startSound(int soundIndex) {
    SoundDef& snd = sounds[soundIndex];
    soundActive[soundIndex] = true;
    
    switch (snd.soundType) {
        case SOUND_BEEP:
            // Play single beep
            playTone(snd.frequency, snd.duration);
            soundActive[soundIndex] = false;  // Auto-stop after beep
            break;
            
        case SOUND_CLICK:
            // Very short click
            playTone(snd.frequency, 20);
            soundActive[soundIndex] = false;
            break;
            
        case SOUND_WARN:
        case SOUND_ALARM:
            // These continue until stopped
            // Handled in updateSounds()
            break;
            
        case SOUND_MELODY:
            // Play melody (async would be better, but for now blocking)
            playAPDisconnect();
            soundActive[soundIndex] = false;
            break;
    }
}

// ============================================================
// STOP SOUND
// ============================================================

void stopSound(int soundIndex) {
    soundActive[soundIndex] = false;
    
    // If no sounds active, silence buzzer
    bool anyActive = false;
    for (int i = 0; i < NUM_SOUNDS; i++) {
        if (soundActive[i]) anyActive = true;
    }
    
    if (!anyActive) {
        noTone(BUZZER_PIN);
        #if !USE_PASSIVE_BUZZER
        digitalWrite(BUZZER_PIN, LOW);
        #endif
    }
}

// ============================================================
// UPDATE SOUNDS - Handle repeating sounds
// ============================================================

void updateSounds() {
    unsigned long currentTime = millis();
    
    // Find highest priority active sound
    for (int i = 0; i < NUM_SOUNDS; i++) {
        if (!soundActive[i]) continue;
        
        SoundDef& snd = sounds[i];
        
        if (snd.soundType == SOUND_WARN) {
            // Warning: beep on/off at interval
            if (currentTime - lastBeepTime >= snd.duration) {
                lastBeepTime = currentTime;
                beepState = !beepState;
                
                if (beepState) {
                    #if USE_PASSIVE_BUZZER
                    tone(BUZZER_PIN, snd.frequency);
                    #else
                    digitalWrite(BUZZER_PIN, HIGH);
                    #endif
                } else {
                    #if USE_PASSIVE_BUZZER
                    noTone(BUZZER_PIN);
                    #else
                    digitalWrite(BUZZER_PIN, LOW);
                    #endif
                }
            }
            return;  // Only play highest priority
        }
        else if (snd.soundType == SOUND_ALARM) {
            // Alarm: continuous tone
            #if USE_PASSIVE_BUZZER
            tone(BUZZER_PIN, snd.frequency);
            #else
            digitalWrite(BUZZER_PIN, HIGH);
            #endif
            return;
        }
    }
    
    // No active sounds - ensure silence
    #if USE_PASSIVE_BUZZER
    noTone(BUZZER_PIN);
    #else
    digitalWrite(BUZZER_PIN, LOW);
    #endif
}

// ============================================================
// PLAY TONE - Wrapper for buzzer type
// ============================================================

void playTone(int frequency, int duration) {
    #if USE_PASSIVE_BUZZER
    tone(BUZZER_PIN, frequency, duration);
    delay(duration);  // Wait for tone to finish
    #else
    // Active buzzer - just on/off
    digitalWrite(BUZZER_PIN, HIGH);
    delay(duration);
    digitalWrite(BUZZER_PIN, LOW);
    #endif
}

// ============================================================
// SPECIAL SOUNDS
// ============================================================

void playAPDisconnect() {
    // Autopilot disconnect sound: three descending tones
    playTone(1500, 100);
    delay(50);
    playTone(1200, 100);
    delay(50);
    playTone(900, 150);
}

void playGearWarning() {
    // Classic gear warning horn
    playTone(800, 500);
    delay(200);
}

void playMarkerBeacon(int type) {
    // type: 0=outer, 1=middle, 2=inner
    int freq, onTime, offTime;
    
    switch (type) {
        case 0:  // Outer - slow dashes
            freq = OUTER_MARKER_FREQ;
            onTime = 400;
            offTime = 200;
            break;
        case 1:  // Middle - alternating
            freq = MIDDLE_MARKER_FREQ;
            onTime = 150;
            offTime = 150;
            break;
        case 2:  // Inner - rapid
            freq = INNER_MARKER_FREQ;
            onTime = 75;
            offTime = 75;
            break;
        default:
            return;
    }
    
    playTone(freq, onTime);
    delay(offTime);
}

// ============================================================
// TEST BUZZER
// ============================================================

void testBuzzer() {
    Serial.println("// Testing buzzer...");
    
    playTone(1000, 100);
    delay(100);
    playTone(1500, 100);
    delay(100);
    playTone(2000, 100);
    
    Serial.println("// Buzzer test complete!");
}

// ============================================================
// MODIFICATION IDEAS:
// ============================================================
//
// 1. VOLUME CONTROL:
//    Use PWM duty cycle to control volume.
//
// 2. DFPLAYER MINI:
//    Play MP3 files for realistic voice warnings.
//    "TERRAIN", "PULL UP", "MINIMUMS", etc.
//
// 3. MULTIPLE BUZZERS:
//    Different buzzers for different warning types.
//
// 4. HAPTIC FEEDBACK:
//    Use vibration motors for stick shaker simulation!
//
// 5. INTERRUPT-BASED:
//    Use timer interrupts for non-blocking sounds.
//
// 6. PRIORITY SYSTEM:
//    Higher priority sounds interrupt lower ones.
//
// ============================================================

// ============================================================
// DFPLAYER MINI EXAMPLE (Uncomment if using)
// ============================================================
// 
// #include "DFRobotDFPlayerMini.h"
// #include <SoftwareSerial.h>
// 
// SoftwareSerial mySerial(10, 11);  // RX, TX
// DFRobotDFPlayerMini myDFPlayer;
// 
// void setupDFPlayer() {
//     mySerial.begin(9600);
//     if (myDFPlayer.begin(mySerial)) {
//         myDFPlayer.volume(20);  // 0-30
//     }
// }
// 
// void playMP3(int track) {
//     myDFPlayer.play(track);
// }
// 
// // Track numbers on SD card:
// // 0001.mp3 = "TERRAIN TERRAIN"
// // 0002.mp3 = "PULL UP"
// // 0003.mp3 = "MINIMUMS"
// // 0004.mp3 = "AUTOPILOT"
// // etc.
//
// ============================================================
