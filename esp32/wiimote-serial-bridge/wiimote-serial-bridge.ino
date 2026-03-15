#include <Arduino.h>
#include "ESP32Wiimote.h"
#include "include/state.h"
#include "include/messages.h"
#include "include/buttons.h"

// Global variable definitions
ESP32Wiimote wiimote;
ButtonState lastButtons = kNoButton;
bool connected = false;
bool baselineCaptured = false;
uint8_t lastBatteryLevel = 0;

unsigned long lastWaitingMsgMs = 0;
unsigned long lastHeartbeatMs = 0;
unsigned long lastBatteryRequestMs = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Keep library logs to errors and warnings only.
  ESP32Wiimote::setLogLevel(kWiimoteLogWarning);
  if (!wiimote.init()) {
    Serial.println("{\"type\":\"status\",\"device\":\"esp32\",\"ready\":false,\"error\":\"wiimote_init_failed\"}");
    while (true) {
      delay(1000);
    }
  }

  // Keep the stream button-focused for now.
  wiimote.addFilter(FilterAction::Ignore, kFilterAccel | kFilterNunchukStick);

  emitReady();
  emitPrompt();

  unsigned long now = millis();
  lastWaitingMsgMs = now;
  lastHeartbeatMs = now;
  lastBatteryRequestMs = now;
}

void loop() {
  wiimote.task();
  unsigned long now = millis();

  // Check connection status using library method
  bool isConnected = ESP32Wiimote::isConnected();
  
  // Detect connection state changes
  if (isConnected && !connected) {
    // Just connected
    connected = true;
    baselineCaptured = false;
    emitConnected(true);
    // Request initial battery level
    ESP32Wiimote::requestBatteryUpdate();
    lastBatteryRequestMs = now;
  } else if (!isConnected && connected) {
    // Just disconnected
    connected = false;
    baselineCaptured = false;
    lastBatteryLevel = 0;
    emitConnected(false);
  }

  // Process every pending update so state does not lag behind.
  while (wiimote.available() > 0) {
    ButtonState buttons = wiimote.getButtonState();

    // On the first packet after connection, capture the current state
    // without emitting button events. This avoids bogus startup transitions.
    if (!baselineCaptured) {
      lastButtons = buttons;
      baselineCaptured = true;
    } else {
      emitButtonsChanged(buttons);
    }
    
    // Check for battery level changes
    uint8_t currentBattery = ESP32Wiimote::getBatteryLevel();
    if (currentBattery != lastBatteryLevel) {
      lastBatteryLevel = currentBattery;
      emitBattery(currentBattery);
    }
  }

  if (!connected && (now - lastWaitingMsgMs >= WAITING_INTERVAL_MS)) {
    emitWaiting();
    lastWaitingMsgMs = now;
  }

  // Request battery update periodically when connected
  if (connected && (now - lastBatteryRequestMs >= BATTERY_REQUEST_INTERVAL_MS)) {
    ESP32Wiimote::requestBatteryUpdate();
    lastBatteryRequestMs = now;
  }

  if (now - lastHeartbeatMs >= HEARTBEAT_INTERVAL_MS) {
    emitHeartbeat();
    lastHeartbeatMs = now;
  }

  delay(10);
}
