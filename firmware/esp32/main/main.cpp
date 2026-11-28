#include "bsp/esp-bsp.h"
#include "diagnostic_assets.hpp"
#include "network_manager.hpp"
#include "sdkconfig.h"
#include "sonoro_view.hpp"

#include "esp_err.h"
#include "esp_heap_caps.h"
#include "esp_log.h"

namespace {
constexpr char TAG[] = "sonoro_diag";
constexpr char VERSION[] = "0.4.6-staged-screens";

sonoro::View* view = nullptr;

void report_memory(const char* stage) {
    ESP_LOGI(TAG, "%s: heap libre=%u B, mayor bloque=%u B, PSRAM libre=%u B",
             stage,
             static_cast<unsigned>(heap_caps_get_free_size(MALLOC_CAP_8BIT)),
             static_cast<unsigned>(heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)),
             static_cast<unsigned>(heap_caps_get_free_size(MALLOC_CAP_SPIRAM)));
}

}

extern "C" void app_main(void) {
    ESP_LOGI(TAG, "Inicio Sonoro firmware %s (prueba Wi-Fi, RTDB, portada y selección)", VERSION);
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
                                    &sonoro_noto_sans_20, &sonoro_noto_sans_16);
    view = &shared_view;
    view->setQrUrl(std::string("https://sonoro.zeliuk.xyz/#token=") + CONFIG_SONORO_FRAME_TOKEN);
    const esp_err_t brightness_error = bsp_display_brightness_set(100);
    if (brightness_error != ESP_OK) {
        ESP_LOGE(TAG, "No se pudo ajustar el brillo: %s", esp_err_to_name(brightness_error));
    }
    bsp_display_unlock();
    report_memory("pantalla lista");
    ESP_LOGI(TAG, "Iniciando Wi-Fi y lecturas Firebase de solo lectura");
    sonoro_network_start(view);
    ESP_LOGI(TAG, "Firmware %s listo; permite cambiar huecos, no reproduce audio ni escribe en Firebase", VERSION);
}
