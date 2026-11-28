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
    : decorative_image_(decorative_image), current_cover_(album_cover),
      title_font_(title_font), artist_font_(artist_font) {
    showIdle();
}

void View::beginScreen() {
    if (qr_timer_) {
        lv_timer_delete(qr_timer_);
        qr_timer_ = nullptr;
    }

    pending_screen_ = lv_obj_create(nullptr);
    lv_obj_set_style_bg_color(pending_screen_, lv_color_hex(0xeee5da), 0);
    lv_obj_set_style_bg_opa(pending_screen_, LV_OPA_COVER, 0);
    content_ = lv_obj_create(pending_screen_);
    lv_obj_remove_style_all(content_);
    lv_obj_set_size(content_, LV_PCT(100), LV_PCT(100));
    lv_obj_clear_flag(content_, LV_OBJ_FLAG_SCROLLABLE);
    qr_layer_ = nullptr;
    song_overlay_ = nullptr;
}

void View::loadScreen() {
    if (!pending_screen_) return;
    lv_screen_load_anim(pending_screen_, LV_SCREEN_LOAD_ANIM_NONE, 0, 0, true);
    pending_screen_ = nullptr;
    content_ = nullptr;
}

int View::addQr(lv_obj_t* parent, const std::string& payload, int max_size, int x, int y) {
    const auto qr = qrcodegen::QrCode::encodeText(payload.c_str(), qrcodegen::QrCode::Ecc::MEDIUM);
    const int modules = qr.getSize();
    constexpr int quiet_zone = 4;
    const int cell_size = std::max(1, std::min(8, max_size / (modules + quiet_zone * 2)));
    const int actual_size = cell_size * (modules + quiet_zone * 2);
    qr_pixels_.assign(static_cast<size_t>(actual_size) * actual_size * 3, 255);
    for (int row = 0; row < modules; ++row) {
        for (int col = 0; col < modules; ++col) {
            if (!qr.getModule(col, row)) continue;
            const int left = (col + quiet_zone) * cell_size;
            const int top = (row + quiet_zone) * cell_size;
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
    auto* image = lv_image_create(parent);
    lv_image_set_src(image, &qr_image_);
    lv_obj_set_pos(image, x, y);
    return actual_size;
}

void View::showIdle() {
    playing_ = false;
    mode_ = Mode::Idle;
    beginScreen();
    auto* image = lv_image_create(content_);
    lv_image_set_src(image, decorative_image_);
    lv_obj_set_size(image, 480, 480);
    lv_image_set_scale(image, 256);
    lv_obj_center(image);
    loadScreen();
}

void View::showDiagnostic(const std::string& version) {
    playing_ = false;
    mode_ = Mode::Diagnostic;
    beginScreen();
    auto* name = make_label(content_, "Sonoro", title_font_, lv_color_hex(0x272824),
                            32, 176, 416, 56);
    lv_obj_set_style_text_align(name, LV_TEXT_ALIGN_CENTER, 0);
    auto* label = make_label(content_, "DIAGNÓSTICO DE FIRMWARE", artist_font_,
                             lv_color_hex(0x777164), 32, 238, 416, 36);
    lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
    auto* version_label = make_label(content_, version.c_str(), artist_font_,
                                     lv_color_hex(0x777164), 32, 282, 416, 32);
    lv_obj_set_style_text_align(version_label, LV_TEXT_ALIGN_CENTER, 0);
    auto* controls = make_label(content_, "BOOT: hueco 1 (mantén 2 s para QR)\nPWR: hueco 2",
                                artist_font_, lv_color_hex(0x777164), 24, 334, 432, 56);
    lv_obj_set_style_text_align(controls, LV_TEXT_ALIGN_CENTER, 0);
    loadScreen();
}

void View::showSong(const lv_image_dsc_t* cover, const std::string& title, const std::string& artist) {
    playing_ = true;
    mode_ = Mode::Song;
    current_cover_ = cover;
    title_ = title;
    artist_ = artist;
    beginScreen();
    auto* image = lv_image_create(content_);
    lv_image_set_src(image, cover);
    lv_image_set_scale(image, 384);
    lv_obj_center(image);

    song_overlay_ = lv_obj_create(content_);
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
    loadScreen();
}

void View::showQr(bool return_after_timeout) {
    beginScreen();
    mode_ = Mode::Qr;
    qr_layer_ = lv_obj_create(content_);
    lv_obj_remove_style_all(qr_layer_);
    lv_obj_set_size(qr_layer_, 480, 480);
    lv_obj_set_style_bg_color(qr_layer_, lv_color_hex(0xeee5da), 0);
    lv_obj_set_style_bg_opa(qr_layer_, LV_OPA_COVER, 0);

    const int actual_size = addQr(qr_layer_, qr_url_, 360, 60, 20);
    const int start_y = 20;
    make_label(qr_layer_, "Escanea para elegir tu música", title_font_,
               lv_color_hex(0x272824), 24, start_y + actual_size + 16, 432, 32);
    make_label(qr_layer_, "QR del cuadro", artist_font_,
               lv_color_hex(0x777164), 24, start_y + actual_size + 52, 432, 24);
    loadScreen();
    if (return_after_timeout) {
        qr_timer_ = lv_timer_create([](lv_timer_t* timer) {
            auto* self = static_cast<View*>(lv_timer_get_user_data(timer));
            self->qr_timer_ = nullptr;
            self->refresh();
            lv_timer_delete(timer);
        }, 20000, this);
    }
}

void View::showWifiSetup(const std::string& ssid, const std::string& password,
                         const std::string& status) {
    mode_ = Mode::Diagnostic;
    beginScreen();
    auto* title = make_label(content_, "Conecta tu cuadro a Wi-Fi", title_font_,
                             lv_color_hex(0x272824), 24, 28, 432, 40);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, 0);
    const std::string wifi_qr = "WIFI:T:WPA;S:" + ssid + ";P:" + password + ";;";
    addQr(content_, wifi_qr, 214, 28, 102);
    make_label(content_, "Escanea para unirte a esta red", artist_font_,
               lv_color_hex(0x777164), 20, 326, 226, 44);

    const std::string network = "Red temporal:\n" + ssid;
    make_label(content_, network.c_str(), artist_font_, lv_color_hex(0x272824),
               258, 118, 202, 58);
    make_label(content_, "Después abre en el móvil:\nhttp://192.168.4.1",
               artist_font_, lv_color_hex(0x272824), 258, 194, 202, 56);
    const std::string key = "Clave temporal:\n" + password;
    make_label(content_, key.c_str(), artist_font_, lv_color_hex(0x777164),
               258, 266, 202, 56);
    if (!status.empty()) {
        make_label(content_, status.c_str(), artist_font_, lv_color_hex(0x9b4d32),
                   24, 392, 432, 48);
    }
    loadScreen();
}

void View::showWifiConnecting(const std::string& ssid) {
    mode_ = Mode::Diagnostic;
    beginScreen();
    auto* title = make_label(content_, "Conectando a Wi-Fi", title_font_,
                             lv_color_hex(0x272824), 24, 170, 432, 44);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, 0);
    auto* detail = make_label(content_, ssid.c_str(), artist_font_,
                              lv_color_hex(0x777164), 24, 224, 432, 40);
    lv_obj_set_style_text_align(detail, LV_TEXT_ALIGN_CENTER, 0);
    loadScreen();
}

void View::showFirebaseStatus(const std::string& identifier, const std::string& status,
                              bool connected) {
    mode_ = Mode::Diagnostic;
    beginScreen();
    auto* title = make_label(content_, connected ? "Conectado a Firebase" : "Firebase no disponible",
                             title_font_, connected ? lv_color_hex(0x466a47) : lv_color_hex(0x9b4d32),
                             24, 138, 432, 44);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, 0);
    const std::string id = "Identificador de prueba: " + identifier;
    auto* id_label = make_label(content_, id.c_str(), artist_font_, lv_color_hex(0x777164),
                                24, 196, 432, 32);
    lv_obj_set_style_text_align(id_label, LV_TEXT_ALIGN_CENTER, 0);
    auto* detail = make_label(content_, status.c_str(), artist_font_, lv_color_hex(0x272824),
                              36, 250, 408, 100);
    lv_obj_set_style_text_align(detail, LV_TEXT_ALIGN_CENTER, 0);
    loadScreen();
}

void View::showFirebaseLoading(int slot_number) {
    mode_ = Mode::FirebaseLoading;
    beginScreen();
    auto* title = make_label(content_, "Cargando selección", title_font_,
                             lv_color_hex(0x272824), 24, 150, 432, 48);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, 0);
    auto* spinner = lv_spinner_create(content_);
    lv_spinner_set_anim_params(spinner, 900, 270);
    lv_obj_set_size(spinner, 76, 76);
    lv_obj_set_style_arc_width(spinner, 8, LV_PART_MAIN);
    lv_obj_set_style_arc_color(spinner, lv_color_hex(0xd8cbbb), LV_PART_MAIN);
    lv_obj_set_style_arc_width(spinner, 8, LV_PART_INDICATOR);
    lv_obj_set_style_arc_color(spinner, lv_color_hex(0xc77c42), LV_PART_INDICATOR);
    lv_obj_align(spinner, LV_ALIGN_CENTER, 0, 8);
    const std::string detail = "Hueco " + std::to_string(slot_number);
    auto* label = make_label(content_, detail.c_str(), artist_font_,
                              lv_color_hex(0x777164), 24, 284, 432, 32);
    lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
    loadScreen();
}

void View::showFirebaseCover(const std::string& identifier, int slot_number, const std::string& title,
                             const std::string& artist, const lv_image_dsc_t* cover) {
    if (!cover || !cover->data || cover->header.w == 0 || cover->header.h == 0) return;
    mode_ = Mode::FirebaseCover;
    beginScreen();
    auto* image = lv_image_create(content_);
    lv_image_set_src(image, cover);
    const int largest_dimension = std::max(cover->header.w, cover->header.h);
    const uint32_t scale = static_cast<uint32_t>((480U * 256U) / largest_dimension);
    lv_image_set_scale(image, scale);
    lv_obj_center(image);

    auto* badge = lv_obj_create(content_);
    lv_obj_remove_style_all(badge);
    lv_obj_set_size(badge, 480, 44);
    lv_obj_align(badge, LV_ALIGN_TOP_MID, 0, 0);
    lv_obj_set_style_bg_color(badge, lv_color_hex(0x151613), 0);
    lv_obj_set_style_bg_opa(badge, LV_OPA_80, 0);
    const std::string badge_text = "Prueba · hueco " + std::to_string(slot_number) + " · " + identifier;
    make_label(badge, badge_text.c_str(), artist_font_,
               lv_color_hex(0xfff8ed), 18, 10, 444, 26);

    auto* overlay = lv_obj_create(content_);
    lv_obj_remove_style_all(overlay);
    lv_obj_set_size(overlay, 480, 144);
    lv_obj_align(overlay, LV_ALIGN_BOTTOM_MID, 0, 0);
    lv_obj_set_style_bg_color(overlay, lv_color_hex(0x151613), 0);
    lv_obj_set_style_bg_opa(overlay, LV_OPA_90, 0);
    lv_obj_set_style_pad_all(overlay, 0, 0);
    make_label(overlay, title.c_str(), title_font_, lv_color_hex(0xfff8ed),
               24, 16, 432, 66);
    make_label(overlay, artist.c_str(), artist_font_, lv_color_hex(0xe9b980),
               24, 92, 432, 30);
    loadScreen();
}

void View::refresh() {
    if (playing_) showSong(current_cover_, title_, artist_);
    else showIdle();
}

}
