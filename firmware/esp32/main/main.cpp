#include "bsp/esp-bsp.h"
#include "diagnostic_assets.hpp"
#include "sonoro_view.hpp"

#include "esp_err.h"
#include "esp_heap_caps.h"
#include "esp_log.h"

namespace {
constexpr char TAG[] = "sonoro_diag";
constexpr char VERSION[] = "0.1.0-diagnostico";
constexpr char QR_URL[] = "https://sonoro.zeliuk.xyz/#token=cuadro-demo";

sonoro::View* view = nullptr;
unsigned view_index = 1;

void report_memory(const char* stage) {
    ESP_LOGI(TAG, "%s: heap libre=%u B, mayor bloque=%u B, PSRAM libre=%u B",
             stage,
             static_cast<unsigned>(heap_caps_get_free_size(MALLOC_CAP_8BIT)),
             static_cast<unsigned>(heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)),
             static_cast<unsigned>(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)));
}

void next_view(lv_timer_t*) {
    if (!view) return;
    switch (view_index++ % 4) {
        case 0: view->showDiagnostic(VERSION); ESP_LOGI(TAG, "Vista: diagnóstico"); break;
        case 1: view->showIdle(); ESP_LOGI(TAG, "Vista: imagen decorativa"); break;
        case 2: view->showSong(&sonoro_diagnostic_cover,
                              "La canción que todavía recuerda el jardín después de la lluvia",
                              "Artista de prueba · Edición de otoño");
                ESP_LOGI(TAG, "Vista: carátula local"); break;
        default: view->showQr(false); ESP_LOGI(TAG, "Vista: QR local de prueba"); break;
    }
}
}

extern "C" void app_main(void) {
    ESP_LOGI(TAG, "Inicio Sonoro firmware %s (modo diagnóstico; no es el comportamiento de producto)", VERSION);
    report_memory("antes de pantalla");
    lv_display_t* display = bsp_display_start();
    if (!display) {
        ESP_LOGE(TAG, "No se pudo inicializar BSP/pantalla LVGL de Waveshare");
        report_memory("fallo de pantalla");
        return;
    }
    const int width = lv_display_get_horizontal_resolution(display);
    const int height = lv_display_get_vertical_resolution(display);
    ESP_LOGI(TAG, "BSP listo: %d x %d", width, height);
    if (width != 480 || height != 480) {
        ESP_LOGE(TAG, "Resolución inesperada; el diagnóstico requiere 480 x 480");
        report_memory("resolución incorrecta");
        return;
    }
    if (!bsp_display_lock(0)) {
        ESP_LOGE(TAG, "No se pudo adquirir el bloqueo LVGL");
        report_memory("fallo del bloqueo LVGL");
        return;
    }
    static sonoro::View shared_view(&sonoro_diagnostic_decorative,
                                    &sonoro_diagnostic_cover,
                                    &lv_font_montserrat_20, &lv_font_montserrat_16);
    view = &shared_view;
    view->setQrUrl(QR_URL);
    view->showDiagnostic(VERSION);
    if (!lv_timer_create(next_view, 5000, nullptr)) {
        ESP_LOGE(TAG, "No se pudo crear el temporizador del recorrido diagnóstico");
        report_memory("fallo del temporizador");
    }
    const esp_err_t brightness_error = bsp_display_brightness_set(100);
    if (brightness_error != ESP_OK) {
        ESP_LOGE(TAG, "No se pudo ajustar el brillo: %s", esp_err_to_name(brightness_error));
    }
    bsp_display_unlock();
    report_memory("pantalla lista");
    ESP_LOGI(TAG, "Recorrido automático cada 5 s: diagnóstico, reposo, carátula y QR");
}
