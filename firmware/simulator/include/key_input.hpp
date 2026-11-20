#pragma once

#include <SDL.h>

#include <cstdint>
#include <functional>

namespace sonoro {

class KeyInput {
public:
    using Callback = std::function<void()>;
    KeyInput(Callback short_press, Callback long_press);
    void update(uint32_t now_ms, bool is_pressed);

private:
    Callback short_press_;
    Callback long_press_;
    bool is_down_ = false;
    bool long_fired_ = false;
    uint32_t pressed_at_ = 0;
};

}
