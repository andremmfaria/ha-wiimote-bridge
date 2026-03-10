#include <Arduino.h>
#include "../include/messages.h"
#include "../include/state.h"

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
  if (connected) {
    Serial.print(",\"battery\":");
    Serial.print(lastBatteryLevel);
  }
  Serial.println("}");
}

void emitBattery(uint8_t level) {
  Serial.print("{\"type\":\"battery\",\"wiimote\":1,\"level\":");
  Serial.print(level);
  Serial.println("}");
}

void emitButton(const char *name, bool down) {
  Serial.print("{\"type\":\"btn\",\"wiimote\":1,\"btn\":\"");
  Serial.print(name);
  Serial.print("\",\"down\":");
  Serial.print(down ? "true" : "false");
  Serial.println("}");
}
