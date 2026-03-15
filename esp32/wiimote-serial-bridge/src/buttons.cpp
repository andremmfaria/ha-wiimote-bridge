#include "../include/buttons.h"
#include "../include/state.h"
#include "../include/messages.h"

const ButtonMap BUTTONS[] = {
  {static_cast<uint32_t>(kButtonA), "A"},
  {static_cast<uint32_t>(kButtonB), "B"},
  {static_cast<uint32_t>(kButtonOne), "ONE"},
  {static_cast<uint32_t>(kButtonTwo), "TWO"},
  {static_cast<uint32_t>(kButtonPlus), "PLUS"},
  {static_cast<uint32_t>(kButtonMinus), "MINUS"},
  {static_cast<uint32_t>(kButtonHome), "HOME"},
  {static_cast<uint32_t>(kButtonUp), "UP"},
  {static_cast<uint32_t>(kButtonDown), "DOWN"},
  {static_cast<uint32_t>(kButtonLeft), "LEFT"},
  {static_cast<uint32_t>(kButtonRight), "RIGHT"},
};

const int BUTTONS_COUNT = sizeof(BUTTONS) / sizeof(BUTTONS[0]);

void emitButtonsChanged(ButtonState currentButtons) {
  uint32_t changed = ((uint32_t)currentButtons) ^ ((uint32_t)lastButtons);
  if (changed == 0) {
    return;
  }

  for (int i = 0; i < BUTTONS_COUNT; i++) {
    if (changed & BUTTONS[i].mask) {
      bool isDown = (((uint32_t)currentButtons) & BUTTONS[i].mask) != 0;
      emitButton(BUTTONS[i].name, isDown);
    }
  }

  lastButtons = currentButtons;
}
