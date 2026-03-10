#ifndef MESSAGES_H
#define MESSAGES_H

#include <stdint.h>

void emitReady();
void emitConnected(bool isConnected);
void emitWaiting();
void emitPrompt();
void emitHeartbeat();
void emitBattery(uint8_t level);
void emitButton(const char *name, bool down);

#endif
