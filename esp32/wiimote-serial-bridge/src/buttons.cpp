#include "../include/buttons.h"
#include "../include/state.h"
#include "../include/messages.h"

const ButtonMap BUTTONS[] = {
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
