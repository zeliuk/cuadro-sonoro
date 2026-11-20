#pragma once

#include "lvgl.h"

#include <string>
#include <vector>

namespace sonoro {

class View {
public:
    enum class Mode { Idle, Song, Qr };
    View(const lv_image_dsc_t* decorative_image, const lv_image_dsc_t* album_cover,
         const lv_font_t* title_font, const lv_font_t* artist_font);
    void showSong(const lv_image_dsc_t* cover, const std::string& title, const std::string& artist);
    void setQrUrl(const std::string& url) { qr_url_ = url; }
    void showIdle();
    void showQr();
    void refresh();
    Mode mode() const { return mode_; }

private:
    void clearScreen();
    lv_obj_t* screen_;
    lv_obj_t* qr_layer_ = nullptr;
    lv_obj_t* song_overlay_ = nullptr;
    const lv_image_dsc_t* decorative_image_;
    const lv_image_dsc_t* current_cover_;
    const lv_font_t* title_font_;
    const lv_font_t* artist_font_;
    bool playing_ = false;
    Mode mode_ = Mode::Idle;
    std::string title_ = "La canción que todavía recuerda el jardín después de la lluvia";
    std::string artist_ = "Artista de prueba · Edición de otoño";
    std::string qr_url_ = "https://sonoro.zeliuk.xyz/#token=cuadro-demo";
    lv_timer_t* qr_timer_ = nullptr;
    std::vector<uint8_t> qr_pixels_;
    lv_image_dsc_t qr_image_{};
};

}
