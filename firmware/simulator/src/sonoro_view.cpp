#include "sonoro_view.hpp"

#include "qrcodegen.hpp"
#include "src/misc/lv_timer.h"

#include <algorithm>
#include <string>

namespace sonoro {

namespace {
lv_obj_t* make_label(lv_obj_t* parent, const char* text, const lv_font_t* font,
                     lv_color_t color, int x, int y, int width, int height) {
    auto* label = lv_label_create(parent);
    lv_label_set_text(label, text);
    lv_label_set_long_mode(label, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(label, width);
    lv_obj_set_height(label, height);
    lv_obj_set_style_text_font(label, font, 0);
    lv_obj_set_style_text_color(label, color, 0);
    lv_obj_set_style_text_line_space(label, 2, 0);
    lv_obj_set_pos(label, x, y);
    return label;
}
}

View::View(const lv_image_dsc_t* decorative_image, const lv_image_dsc_t* album_cover,
           const lv_font_t* title_font, const lv_font_t* artist_font)
    : screen_(lv_screen_active()), decorative_image_(decorative_image), current_cover_(album_cover),
      title_font_(title_font), artist_font_(artist_font) {
    lv_obj_set_style_bg_color(screen_, lv_color_hex(0xeee5da), 0);
    lv_obj_set_style_bg_opa(screen_, LV_OPA_COVER, 0);
    showIdle();
}

void View::clearScreen() {
    if (qr_timer_) {
        lv_timer_delete(qr_timer_);
        qr_timer_ = nullptr;
    }
    lv_obj_clean(screen_);
    qr_layer_ = nullptr;
    song_overlay_ = nullptr;
}

void View::showIdle() {
    playing_ = false;
    mode_ = Mode::Idle;
    clearScreen();
    auto* image = lv_image_create(screen_);
    lv_image_set_src(image, decorative_image_);
    lv_obj_set_size(image, 480, 480);
    lv_image_set_scale(image, 256);
    lv_obj_center(image);
}

void View::showSong(const lv_image_dsc_t* cover, const std::string& title, const std::string& artist) {
    playing_ = true;
    mode_ = Mode::Song;
    current_cover_ = cover;
    title_ = title;
    artist_ = artist;
    clearScreen();
    auto* image = lv_image_create(screen_);
    lv_image_set_src(image, cover);
    lv_image_set_scale(image, 384);
    lv_obj_center(image);

    song_overlay_ = lv_obj_create(screen_);
    lv_obj_remove_style_all(song_overlay_);
    lv_obj_set_size(song_overlay_, 480, 144);
    lv_obj_align(song_overlay_, LV_ALIGN_BOTTOM_MID, 0, 0);
    lv_obj_set_style_bg_color(song_overlay_, lv_color_hex(0x151613), 0);
    lv_obj_set_style_bg_opa(song_overlay_, LV_OPA_90, 0);
    lv_obj_set_style_pad_all(song_overlay_, 0, 0);

    auto* title_label = make_label(song_overlay_, title.c_str(), title_font_,
                                   lv_color_hex(0xfff8ed), 24, 16, 432, 66);
    lv_obj_set_style_text_letter_space(title_label, 0, 0);
    make_label(song_overlay_, artist.c_str(), artist_font_,
               lv_color_hex(0xe9b980), 24, 92, 432, 30);
}

void View::showQr(bool return_after_timeout) {
    clearScreen();
    mode_ = Mode::Qr;
    qr_layer_ = lv_obj_create(screen_);
    lv_obj_remove_style_all(qr_layer_);
    lv_obj_set_size(qr_layer_, 480, 480);
    lv_obj_set_style_bg_color(qr_layer_, lv_color_hex(0xeee5da), 0);
    lv_obj_set_style_bg_opa(qr_layer_, LV_OPA_COVER, 0);

    const auto qr = qrcodegen::QrCode::encodeText(qr_url_.c_str(), qrcodegen::QrCode::Ecc::MEDIUM);
    const int modules = qr.getSize();
    const int quiet_zone = 4;
    const int cell_size = std::min(8, 360 / (modules + quiet_zone * 2));
    const int actual_size = cell_size * (modules + quiet_zone * 2);
    const int start_x = (480 - actual_size) / 2;
    const int start_y = 20;
    qr_pixels_.assign(actual_size * actual_size * 3, 255);
    for (int y = 0; y < modules; ++y) {
        for (int x = 0; x < modules; ++x) {
            if (!qr.getModule(x, y)) continue;
            const int left = (x + quiet_zone) * cell_size;
            const int top = (y + quiet_zone) * cell_size;
            for (int py = top; py < top + cell_size; ++py) {
                for (int px = left; px < left + cell_size; ++px) {
                    const size_t index = (static_cast<size_t>(py) * actual_size + px) * 3;
                    qr_pixels_[index] = qr_pixels_[index + 1] = qr_pixels_[index + 2] = 23;
                }
            }
        }
    }
    qr_image_.header.magic = LV_IMAGE_HEADER_MAGIC;
    qr_image_.header.cf = LV_COLOR_FORMAT_RGB888;
    qr_image_.header.w = actual_size;
    qr_image_.header.h = actual_size;
    qr_image_.header.stride = actual_size * 3;
    qr_image_.data_size = qr_pixels_.size();
    qr_image_.data = qr_pixels_.data();
    auto* qr_image = lv_image_create(qr_layer_);
    lv_image_set_src(qr_image, &qr_image_);
    lv_obj_set_pos(qr_image, start_x, start_y);
    make_label(qr_layer_, "Escanea para elegir tu música", title_font_,
               lv_color_hex(0x272824), 24, start_y + actual_size + 16, 432, 32);
    make_label(qr_layer_, "QR del cuadro", artist_font_,
               lv_color_hex(0x777164), 24, start_y + actual_size + 52, 432, 24);
    if (return_after_timeout) {
        qr_timer_ = lv_timer_create([](lv_timer_t* timer) {
            auto* self = static_cast<View*>(lv_timer_get_user_data(timer));
            self->qr_timer_ = nullptr;
            self->refresh();
            lv_timer_delete(timer);
        }, 20000, this);
    }
}

void View::refresh() {
    if (playing_) showSong(current_cover_, title_, artist_);
    else showIdle();
}

}
