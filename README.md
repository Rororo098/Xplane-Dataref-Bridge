X-Plane Dataref Bridge

X-Plane Dataref Bridge is a powerful, open-source middleware application that enables seamless bidirectional communication between X-Plane flight simulator and Arduino-based hardware. It acts as a universal translator, allowing you to build professional-grade cockpit hardware, instrument panels, and control systems without writing complex networking code.

Python Version 3.8+
License MIT
Platform Windows


Overview
X-Plane Dataref Bridge is a sophisticated cross-platform application that serves as a middleware solution connecting X-Plane flight simulator with hardware devices and custom controllers. Built with Python and PyQt6, it enables real-time bidirectional communication between X-Plane’s datarefs and various hardware interfaces including Arduino microcontrollers and HID devices.

Key Features
🛫 Flight Simulator Integration
Real-time Data Exchange: Seamless communication with X-Plane 11/12 via UDP networking
Dataref Management: Comprehensive database of 6,992+ X-Plane datarefs with custom dataref support
Bi-directional Control: Send datarefs to X-Plane and receive live updates from the simulator

🧩 Hardware Support
Arduino Integration: Full support for Arduino-based hardware panels and controllers
HID Device Support: Compatible with joysticks, throttles, switches, and custom HID controllers
ESP32 Support: Includes sample configurations for ESP32-based wireless controllers
Plug-and-Play: Automatic device detection and connection management

⚡ Advanced Features
Logic Engine: Complex conditional logic system for creating automated behaviors
Input Mapping: Flexible mapping system for custom controller configurations
Profile System: Save and load different hardware configurations
Multi-Condition Rules: Advanced conditional logic with multiple criteria
Real-time Monitoring: Live data monitoring and debugging tools

🎨 User Interface
Modern PyQt6 GUI: Professional, responsive user interface
Tabbed Navigation: Organized into Output Config, Input Config, Hardware, and Settings panels
Visual Feedback: Real-time connection status and device monitoring
Custom Icons: Professional branding and visual identity

Technical Architecture

Core Components
X-Plane Connection Manager: Handles UDP communication with X-Plane
Dataref Manager: Manages subscriptions and data exchange
Arduino Manager: Controls serial communication with Arduino devices
HID Manager: Interfaces with joystick and custom HID devices
Logic Engine: Processes conditional rules and automated behaviors
Variable Store: Centralized storage for application variables
Supported Protocols
UDP Networking: Standard X-Plane dataref protocol
Serial Communication: For Arduino and microcontroller interfaces
HID Protocol: Native Windows HID support for joysticks and controllers

Use Cases

🎮 Home Cockpit Builders
Create realistic home cockpit panels with authentic switches and indicators
Integrate custom hardware with X-Plane for immersive flight simulation
Build radio stacks, autopilot panels, and engine controls

🛠️ Flight Training
Develop custom training aids and procedures trainers
Create specialized control panels for specific aircraft types
Build educational tools for flight instruction

🎯 Hardware Development
Prototype new flight simulator hardware concepts
Test custom controller designs
Validate hardware-software integration


Getting Started

Prerequisites
Python 3.8+
X-Plane 11 or 12 with network data output enabled
Compatible Microcontroller or Arduino board or HID device (optional)

Installation
Clone or download the repository
Install dependencies: pip install -r requirements.txt
Run the application: python main.py

Basic Setup
Configure X-Plane network settings (Data Input/Output)
Connect your hardware devices
Map datarefs to your hardware inputs/outputs
Save your configuration profile

Development

Contributing
We welcome contributions to enhance the X-Plane Dataref Bridge! Please fork the repository and submit pull requests for:

Bug fixes
New hardware support
UI improvements
Additional datarefs
Documentation updates

Architecture Notes
Modular design with clear separation of concerns
Extensible plugin architecture for new device types
Comprehensive logging and debugging capabilities
Cross-platform compatibility (Windows, macOS, Linux)

Support & Community

Documentation
Comprehensive user manual included
Sample configurations for common hardware setups
Troubleshooting guides and FAQs

Donations
This project is maintained by enthusiasts for the flight simulation community. If you find this tool valuable, consider supporting its continued development through our donation links.

License
This project is released under the MIT License - see the LICENSE file for details.
