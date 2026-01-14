#!/usr/bin/env python3
"""
Quick ESP32-S2 Handshake Debug Tool
Use this to diagnose connection issues
"""

import serial
import serial.tools.list_ports
import time

def main():
    print("=" * 60)
    print("  ESP32-S2 Handshake Debug Tool")
    print("=" * 60)
    
    # List ports
    print("\n[1] Available Serial Ports:")
    ports = serial.tools.list_ports.comports()
    
    for i, p in enumerate(ports):
        print(f"    [{i}] {p.device}")
        print(f"        {p.description}")
        if "USB" in p.description or "ESP" in p.description.upper():
            print(f"        ^^^ This is likely your ESP32-S2 ^^^")
    
    if not ports:
        print("\n[!] No serial ports found!")
        print("    Make sure:")
        print("    - ESP32-S2 is connected via USB cable")
        print("    - Drivers are installed")
        print("    - Arduino IDE can see the device")
        return
    
    # Get port
    try:
        choice = input("\n[2] Enter port number (or full path): ").strip()
        if choice.isdigit():
            port = ports[int(choice)].device
        else:
            port = choice
    except (ValueError, IndexError):
        print("[!] Invalid selection")
        return
    
    print(f"\n[3] Opening {port} at 115200 baud...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=3)
        print("    [OK] Port opened")
    except Exception as e:
        print(f"    [!] Error: {e}")
        return
    
    # Wait for reset
    print("\n[4] Waiting for ESP32-S2 to reset (3s)...")
    time.sleep(3)
    
    # Clear buffer
    ser.reset_input_buffer()
    
    # Send HELLO
    print("\n[5] Sending HELLO command...")
    ser.write(b"HELLO\n")
    
    # Read response
    start = time.time()
    response = ""
    
    while time.time() - start < 2:
        if ser.in_waiting:
            line = ser.readline().decode(errors="ignore")
            response += line
            print(f"    Received: {line.strip()}")
    
    # Check response
    print("\n[6] Analysis:")
    if "XPDR" in response:
        print("    [OK] Handshake successful!")
        
        # Parse handshake
        for line in response.strip().split('\n'):
            if line.startswith("XPDR"):
                parts = line.split(';')
                print(f"\n    Handshake details:")
                for part in parts:
                    print(f"        {part}")
                
                # Check board type
                board = None
                for part in parts:
                    if part.startswith("board="):
                        board = part.split('=')[1]
                
                if board:
                    print(f"\n    [INFO] Board type detected: {board}")
                    if "ESP32S2" in board.upper() or "ESP32-S2" in board.upper():
                        print("    [OK] Correct ESP32-S2 identification")
                    else:
                        print("    [!] Board type may not match expected format")
        
        print("\n[7] Your device should work with the Bridge App!")
    else:
        print("    [!] No XPDR response received")
        print(f"    Raw response: {repr(response)}")
        print("\n    Possible issues:")
        print("    - Firmware not uploaded correctly")
        print("    - Wrong baud rate (should be 115200)")
        print("    - USB CDC On Boot not enabled")
        print("    - Arduino code not responding to HELLO")
    
    ser.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
