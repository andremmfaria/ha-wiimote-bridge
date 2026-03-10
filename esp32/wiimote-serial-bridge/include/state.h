#ifndef STATE_H
#define STATE_H

#include "ESP32Wiimote.h"

// Global state variables
extern ButtonState lastButtons;
extern bool connected;
extern bool baselineCaptured;
extern uint8_t lastBatteryLevel;

// Timing variables
extern unsigned long lastWaitingMsgMs;
extern unsigned long lastHeartbeatMs;
extern unsigned long lastBatteryRequestMs;

// Timing constants
static const unsigned long WAITING_INTERVAL_MS = 5000;
static const unsigned long HEARTBEAT_INTERVAL_MS = 10000;
static const unsigned long BATTERY_REQUEST_INTERVAL_MS = 60000;

// Wiimote instance
extern ESP32Wiimote wiimote;

#endif
