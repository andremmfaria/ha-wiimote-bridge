#ifndef BUTTONS_H
#define BUTTONS_H

#include "ESP32Wiimote.h"

struct ButtonMap {
  uint32_t mask;
  const char *name;
};

extern const ButtonMap BUTTONS[];
extern const int BUTTONS_COUNT;

void emitButtonsChanged(ButtonState currentButtons);

#endif
