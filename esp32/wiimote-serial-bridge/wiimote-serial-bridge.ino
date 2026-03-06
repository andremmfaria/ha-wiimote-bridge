#include <Arduino.h>
#include "ESP32Wiimote.h"

ESP32Wiimote wiimote;

struct ButtonMap {
  uint32_t mask;
  const char *name;
};

static const ButtonMap BUTTONS[] = {
    {BUTTON_A, "A"},
    {BUTTON_B, "B"},
    {BUTTON_ONE, "ONE"},
    {BUTTON_TWO, "TWO"},
    {BUTTON_PLUS, "PLUS"},
    {BUTTON_MINUS, "MINUS"},
    {BUTTON_HOME, "HOME"},
    {BUTTON_UP, "UP"},
    {BUTTON_DOWN, "DOWN"},
    {BUTTON_LEFT, "LEFT"},
    {BUTTON_RIGHT, "RIGHT"},
};

static ButtonState lastButtons = NO_BUTTON;
static bool connected = false;
static bool baselineCaptured = false;

static unsigned long lastWaitingMsgMs = 0;
static unsigned long lastHeartbeatMs = 0;

static const unsigned long WAITING_INTERVAL_MS = 5000;
static const unsigned long HEARTBEAT_INTERVAL_MS = 10000;

void emitReady() {
  Serial.println("{\"type\":\"status\",\"device\":\"esp32\",\"ready\":true}");
}

void emitConnected(bool isConnected) {
  Serial.print("{\"type\":\"status\",\"wiimote\":1,\"connected\":");
  Serial.print(isConnected ? "true" : "false");
  Serial.println("}");
}

void emitWaiting() {
  Serial.println("{\"type\":\"status\",\"wiimote\":1,\"connected\":false,\"waiting\":true}");
}

void emitPrompt() {
  Serial.println("{\"type\":\"status\",\"wiimote\":1,\"connected\":false,\"note\":\"press_1_and_2\"}");
}

void emitHeartbeat() {
  Serial.print("{\"type\":\"heartbeat\",\"device\":\"esp32\",\"wiimote\":1,\"connected\":");
  Serial.print(connected ? "true" : "false");
  Serial.println("}");
}

void emitButton(const char *name, bool down) {
  Serial.print("{\"type\":\"btn\",\"wiimote\":1,\"btn\":\"");
  Serial.print(name);
  Serial.print("\",\"down\":");
  Serial.print(down ? "true" : "false");
  Serial.println("}");
}

void emitButtonsChanged(ButtonState currentButtons) {
  uint32_t changed = ((uint32_t)currentButtons) ^ ((uint32_t)lastButtons);
  if (changed == 0) {
    return;
  }

  for (const auto &b : BUTTONS) {
    if (changed & b.mask) {
      bool isDown = (((uint32_t)currentButtons) & b.mask) != 0;
      emitButton(b.name, isDown);
    }
  }

  lastButtons = currentButtons;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  emitReady();
  emitPrompt();

  // Keep the stream button-focused for now.
  wiimote.addFilter(ACTION_IGNORE, FILTER_ACCEL | FILTER_NUNCHUK_STICK);
  wiimote.init();

  unsigned long now = millis();
  lastWaitingMsgMs = now;
  lastHeartbeatMs = now;
}

void loop() {
  wiimote.task();
  unsigned long now = millis();

  int avail = wiimote.available();
  if (avail > 0) {
    ButtonState buttons = wiimote.getButtonState();

    if (!connected) {
      connected = true;
      baselineCaptured = false;
      emitConnected(true);
    }

    // On the first packet after connection, capture the current state
    // without emitting button events. This avoids bogus startup transitions.
    if (!baselineCaptured) {
      lastButtons = buttons;
      baselineCaptured = true;
    } else {
      emitButtonsChanged(buttons);
    }
  }

  if (!connected && (now - lastWaitingMsgMs >= WAITING_INTERVAL_MS)) {
    emitWaiting();
    lastWaitingMsgMs = now;
  }

  if (now - lastHeartbeatMs >= HEARTBEAT_INTERVAL_MS) {
    emitHeartbeat();
    lastHeartbeatMs = now;
  }

  delay(10);
}
