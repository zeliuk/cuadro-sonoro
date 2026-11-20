#include "key_input.hpp"

namespace sonoro {

KeyInput::KeyInput(Callback short_press, Callback long_press)
    : short_press_(std::move(short_press)), long_press_(std::move(long_press)) {}

void KeyInput::update(uint32_t now_ms, bool pressed) {
    if (pressed && !is_down_) {
        is_down_ = true;
        long_fired_ = false;
        pressed_at_ = now_ms;
    }
    else if (!pressed && is_down_) {
        is_down_ = false;
        if (!long_fired_) short_press_();
    }
    if (is_down_ && !long_fired_ && SDL_TICKS_PASSED(now_ms, pressed_at_ + 2000)) {
        long_fired_ = true;
        long_press_();
    }
}

}
