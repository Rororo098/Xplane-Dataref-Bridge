#include "Adafruit_TinyUSB.h"

// --- Config ---
#define PRODUCT_NAME "Ruzu Pro Controller"
#define VENDOR_ID    0x303A
#define PRODUCT_ID   0x80CB // New PID

// --- HID Report ---
uint8_t const desc_hid_report[] = { TUD_HID_REPORT_DESC_GAMEPAD() };
Adafruit_USBD_HID usb_hid;

// --- State ---
unsigned long lastUpdate = 0;
bool btnState = false;

void setup() {
  // 1. Setup Identity
  // Try TinyUSBDevice first. If this errors, use USBDevice.
  TinyUSBDevice.setID(VENDOR_ID, PRODUCT_ID);
  TinyUSBDevice.setManufacturerDescriptor("Ruzu FSD");
  TinyUSBDevice.setProductDescriptor(PRODUCT_NAME);

  // 2. Setup HID
  usb_hid.setPollInterval(2);
  usb_hid.setReportDescriptor(desc_hid_report, sizeof(desc_hid_report));
  usb_hid.begin();

  // 3. Setup Serial
  Serial.begin(115200);

  // 4. Wait for Mount (with timeout)
  unsigned long start = millis();
  while (!TinyUSBDevice.mounted() && (millis() - start < 5000)) {
    delay(10);
  }
}

void loop() {
  // 1. Handle Serial
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "HELLO") {
      Serial.println("XPDR;fw=TinyUSB 2.1;board=ESP32S2;name=" PRODUCT_NAME);
    }
  }

  // 2. Simulate Button
  if (millis() - lastUpdate > 1000) {
    lastUpdate = millis();
    btnState = !btnState;
    
    if (usb_hid.ready()) {
      hid_gamepad_report_t report;
      memset(&report, 0, sizeof(report));
      if (btnState) report.buttons = (1 << 0);
      usb_hid.sendReport(0, &report, sizeof(report));
    }
  }
}