#include "key_input.hpp"
#include "sonoro_view.hpp"

#include "lvgl.h"
#include "src/drivers/sdl/lv_sdl_window.h"
#include "stb_image.h"

#include <SDL.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#ifndef SONORO_ASSET_DIR
#define SONORO_ASSET_DIR "assets"
#endif

namespace {
struct Image {
    lv_image_dsc_t descriptor{};
    std::vector<uint8_t> pixels;
};

struct Song {
    bool available = false;
    bool station = false;
    Image cover;
    std::string title;
    std::string artist;
};

void set_lvgl_rgb888_descriptor(Image& image, int width, int height) {
    /* LVGL RGB888 consumes bytes as B, G, R; stb_image and our artwork use R, G, B. */
    for (size_t index = 0; index < image.pixels.size(); index += 3) {
        std::swap(image.pixels[index], image.pixels[index + 2]);
    }
    image.descriptor.header.magic = LV_IMAGE_HEADER_MAGIC;
    image.descriptor.header.cf = LV_COLOR_FORMAT_RGB888;
    image.descriptor.header.w = width;
    image.descriptor.header.h = height;
    image.descriptor.header.stride = width * 3;
    image.descriptor.data_size = image.pixels.size();
    image.descriptor.data = image.pixels.data();
}

Image make_station_fallback() {
    constexpr int size = 320;
    Image image;
    image.pixels.resize(size * size * 3);
    const uint8_t background[] = {235, 233, 222};
    const uint8_t body[] = {49, 61, 50};
    const uint8_t speaker[] = {207, 200, 181};
    for (int y = 0; y < size; ++y) {
        for (int x = 0; x < size; ++x) {
            const bool radio_body = x >= 74 && x <= 246 && y >= 103 && y <= 222;
            const int dx = x - 160;
            const int dy = y - 163;
            const int radius = dx * dx + dy * dy;
            const bool ring = radio_body && radius >= 24 * 24 && radius <= 43 * 43;
            const bool center = radio_body && radius < 24 * 24;
            const uint8_t* color = (ring || center) ? speaker : (radio_body ? body : background);
            const size_t index = (static_cast<size_t>(y) * size + x) * 3;
            image.pixels[index] = color[0];
            image.pixels[index + 1] = color[1];
            image.pixels[index + 2] = color[2];
        }
    }
    set_lvgl_rgb888_descriptor(image, size, size);
    return image;
}

Image load_station_art(const std::string& path) {
    if (path.empty()) return make_station_fallback();

    int width = 0, height = 0, channels = 0;
    if (!stbi_info(path.c_str(), &width, &height, &channels) || width <= 0 || height <= 0 ||
        width > 1024 || height > 1024 || static_cast<uint64_t>(width) * height > 1024 * 1024) {
        return make_station_fallback();
    }
    stbi_uc* raw = stbi_load(path.c_str(), &width, &height, &channels, 4);
    if (!raw) return make_station_fallback();

    constexpr int size = 320;
    constexpr int max_logo = 220;
    const float scale = std::min(static_cast<float>(max_logo) / width,
                                 static_cast<float>(max_logo) / height);
    const int logo_width = std::max(1, static_cast<int>(width * scale));
    const int logo_height = std::max(1, static_cast<int>(height * scale));
    const int left = (size - logo_width) / 2;
    const int top = (size - logo_height) / 2;
    Image image;
    image.pixels.resize(size * size * 3);
    for (size_t i = 0; i < image.pixels.size(); i += 3) {
        image.pixels[i] = 235;
        image.pixels[i + 1] = 233;
        image.pixels[i + 2] = 222;
    }
    for (int y = 0; y < logo_height; ++y) {
        const int source_y = std::min(height - 1, y * height / logo_height);
        for (int x = 0; x < logo_width; ++x) {
            const int source_x = std::min(width - 1, x * width / logo_width);
            const size_t source = (static_cast<size_t>(source_y) * width + source_x) * 4;
            const size_t target = (static_cast<size_t>(top + y) * size + left + x) * 3;
            const unsigned alpha = raw[source + 3];
            for (int channel = 0; channel < 3; ++channel) {
                const unsigned background = image.pixels[target + channel];
                image.pixels[target + channel] = static_cast<uint8_t>(
                    (raw[source + channel] * alpha + background * (255 - alpha)) / 255);
            }
        }
    }
    stbi_image_free(raw);
    set_lvgl_rgb888_descriptor(image, size, size);
    return image;
}

Image load_jpeg(const std::string& path, int expected_width, int expected_height,
                bool allow_480_cover = false) {
    int info_width = 0, info_height = 0, info_channels = 0;
    if (!stbi_info(path.c_str(), &info_width, &info_height, &info_channels)) {
        throw std::runtime_error("No se pudo leer la cabecera JPEG: " + path);
    }
    const bool expected_size = info_width == expected_width && info_height == expected_height;
    const bool high_resolution_cover = allow_480_cover && info_width == 480 && info_height == 480;
    if (!expected_size && !high_resolution_cover) {
        throw std::runtime_error("Dimensiones no esperadas en: " + path);
    }

    int width = 0, height = 0, channels = 0;
    stbi_uc* raw = stbi_load(path.c_str(), &width, &height, &channels, 3);
    if (!raw) throw std::runtime_error("No se pudo abrir la imagen: " + path);
    if (width != info_width || height != info_height) {
        stbi_image_free(raw);
        throw std::runtime_error("Las dimensiones cambiaron al decodificar: " + path);
    }

    Image image;
    image.pixels.assign(raw, raw + width * height * 3);
    stbi_image_free(raw);
    set_lvgl_rgb888_descriptor(image, width, height);
    return image;
}

std::string load_text(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) throw std::runtime_error("No se pudo leer la configuración temporal del QR.");
    return std::string(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
}

void save_capture(lv_display_t* display, const std::string& path) {
    auto* renderer = static_cast<SDL_Renderer*>(lv_sdl_window_get_renderer(display));
    auto* surface = SDL_CreateRGBSurfaceWithFormat(0, 480, 480, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surface || SDL_RenderReadPixels(renderer, nullptr, SDL_PIXELFORMAT_RGBA32,
                                          surface->pixels, surface->pitch) != 0 ||
        SDL_SaveBMP(surface, path.c_str()) != 0) {
        const std::string error = SDL_GetError();
        if (surface) SDL_FreeSurface(surface);
        throw std::runtime_error("No se pudo guardar la captura: " + error);
    }
    SDL_FreeSurface(surface);
}

int SDLCALL watch_close_events(void* state, SDL_Event* event) {
    auto* running = static_cast<bool*>(state);
    if (event->type == SDL_QUIT || (event->type == SDL_WINDOWEVENT && event->window.event == SDL_WINDOWEVENT_CLOSE)) {
        *running = false;
    }
    return 1;
}
}

int main(int argc, char** argv) {
    try {
        const bool firebase_data = argc >= 3 && std::string(argv[1]) == "--firebase-data" &&
            (argc == 3 || (argc >= 8 && (argc - 3) % 5 == 0));
        if (argc > 1 && !firebase_data &&
            !(argc == 3 && (std::string(argv[1]) == "--capture-song" || std::string(argv[1]) == "--verify-flow"))) {
            throw std::runtime_error("Argumentos internos de ejecución no válidos.");
        }

        SDL_SetMainReady();
        lv_init();
        lv_display_t* display = lv_sdl_window_create(480, 480);
        if (!display) throw std::runtime_error("No se pudo crear la ventana SDL.");
        if (!lv_sdl_window_get_renderer(display)) {
            throw std::runtime_error(std::string("SDL no creó su ventana/renderer: ") + SDL_GetError());
        }
        lv_sdl_window_set_title(display, "Cuadro sonoro — prueba de pantalla");
        lv_sdl_window_set_resizeable(display, false);
        lv_sdl_window_set_zoom(display, 1);

        const std::string assets = SONORO_ASSET_DIR;
        Image decorative = load_jpeg(assets + "/imagen-decorativa.jpg", 480, 480);
        std::array<Song, 3> songs;
        std::string qr_url;
        if (firebase_data) {
            qr_url = load_text(argv[2]);
            if (qr_url.empty()) throw std::runtime_error("La URL temporal del QR está vacía.");
            for (int arg = 3; arg < argc; arg += 5) {
                const std::string slot_text = argv[arg];
                const std::string kind = argv[arg + 1];
                size_t parsed = 0;
                const int slot = std::stoi(slot_text, &parsed);
                if (parsed != slot_text.size() || slot < 0 || slot > 2 || songs[slot].available) {
                    throw std::runtime_error("Los huecos de canción recibidos no son válidos.");
                }
                if (kind != "song" && kind != "station") {
                    throw std::runtime_error("El tipo de selección recibida no es válido.");
                }
                songs[slot].available = true;
                songs[slot].station = kind == "station";
                const std::string image_path = argv[arg + 2];
                if (songs[slot].station) {
                    songs[slot].cover = load_station_art(image_path == "-" ? "" : image_path);
                } else {
                    if (image_path == "-") throw std::runtime_error("La canción no tiene carátula local.");
                    songs[slot].cover = load_jpeg(image_path, 320, 320, true);
                }
                songs[slot].title = argv[arg + 3];
                songs[slot].artist = argv[arg + 4];
            }
        } else {
            songs[0].available = true;
            songs[0].cover = load_jpeg(assets + "/caratula-demo.jpg", 320, 320);
            songs[0].title = "La canción que todavía recuerda el jardín después de la lluvia";
            songs[0].artist = "Artista de prueba · Edición de otoño";
        }
        const bool all_slots_empty = std::none_of(songs.begin(), songs.end(),
            [](const Song& song) { return song.available; });
        sonoro::View view(&decorative.descriptor, &songs[0].cover.descriptor,
                          &sonoro_noto_sans_20, &sonoro_noto_sans_16);
        if (firebase_data) view.setQrUrl(qr_url);
        int active_slot = -1;
        int short_press_count = 0;
        int long_press_count = 0;
        std::array<std::unique_ptr<sonoro::KeyInput>, 3> inputs;
        for (int slot = 0; slot < 3; ++slot) {
            inputs[slot] = std::make_unique<sonoro::KeyInput>(
                [&view, &songs, &active_slot, &short_press_count, &all_slots_empty, slot]() {
                    ++short_press_count;
                    if (!songs[slot].available) {
                        view.showQr(!all_slots_empty);
                        return;
                    }
                    if (active_slot == slot) {
                        active_slot = -1;
                        view.showIdle();
                        return;
                    }
                    active_slot = slot;
                    view.showSong(&songs[slot].cover.descriptor, songs[slot].title, songs[slot].artist);
                },
                [&view, &long_press_count, &all_slots_empty, slot]() {
                    if (slot == 0) {
                        ++long_press_count;
                        view.showQr(!all_slots_empty);
                    }
                }
            );
        }
        if (all_slots_empty) view.showQr(false);

        bool running = true;
        SDL_AddEventWatch(watch_close_events, &running);

        if (argc == 3 && std::string(argv[1]) == "--capture-song") {
            view.showSong(&songs[0].cover.descriptor, songs[0].title, songs[0].artist);
            lv_refr_now(display);
            save_capture(display, argv[2]);
            std::cout << "Captura guardada en " << argv[2] << '\n';
            return 0;
        }

        if (argc == 3 && std::string(argv[1]) == "--verify-flow") {
            const std::string prefix = argv[2];
            if (view.mode() != sonoro::View::Mode::Idle) throw std::runtime_error("No inició en reposo.");
            lv_refr_now(display);
            save_capture(display, prefix + "-reposo.bmp");
            const uint32_t t = SDL_GetTicks();
            inputs[0]->update(t, true);
            inputs[0]->update(t + 300, false);
            if (short_press_count != 1 || view.mode() != sonoro::View::Mode::Song) throw std::runtime_error("Falló la pulsación corta de inicio.");
            lv_refr_now(display);
            save_capture(display, prefix + "-cancion.bmp");
            inputs[0]->update(t + 400, true);
            inputs[0]->update(t + 700, false);
            if (short_press_count != 2 || view.mode() != sonoro::View::Mode::Idle) throw std::runtime_error("Falló el retorno a reposo.");
            inputs[0]->update(t + 800, true);
            inputs[0]->update(t + 1100, false);
            if (short_press_count != 3 || view.mode() != sonoro::View::Mode::Song) throw std::runtime_error("Falló la segunda activación de canción.");
            const uint32_t hold = t + 1200;
            inputs[0]->update(hold, true);
            inputs[0]->update(hold + 2000, true);
            inputs[0]->update(hold + 2100, false);
            if (long_press_count != 1 || short_press_count != 3 || view.mode() != sonoro::View::Mode::Qr) throw std::runtime_error("El gesto largo ejecutó una acción corta o no mostró el QR.");
            lv_refr_now(display);
            save_capture(display, prefix + "-qr.bmp");
            const uint32_t qr_started = SDL_GetTicks();
            while (SDL_GetTicks() - qr_started < 19500) {
                lv_timer_handler();
                SDL_Delay(5);
            }
            if (view.mode() != sonoro::View::Mode::Qr) throw std::runtime_error("El QR expiró antes de 20 s.");
            while (SDL_GetTicks() - qr_started < 20500) {
                lv_timer_handler();
                SDL_Delay(5);
            }
            if (view.mode() != sonoro::View::Mode::Song || short_press_count != 3) throw std::runtime_error("El QR no volvió a la canción al expirar.");
            lv_refr_now(display);
            save_capture(display, prefix + "-tras-qr.bmp");
            std::cout << "OK: reposo -> canción -> reposo; gesto largo sin acción corta; QR visible a 19,5 s y retirado a 20,5 s; retorno a canción. Capturas: " << prefix << "-*.bmp\n";
            return 0;
        }

        while (running) {
            lv_timer_handler();
            if (!running) break;
            int key_count = 0;
            const Uint8* keys = SDL_GetKeyboardState(&key_count);
            for (int slot = 0; slot < 3; ++slot) {
                const auto scancode = static_cast<SDL_Scancode>(SDL_SCANCODE_1 + slot);
                inputs[slot]->update(SDL_GetTicks(), key_count > scancode && keys[scancode]);
            }
            SDL_Delay(5);
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}
