#include "network_manager.hpp"

#include "bsp/esp-bsp.h"
#include "bsp/esp32_s3_touch_lcd_4b.h"
#include "sdkconfig.h"
#include "sonoro_view.hpp"

#include "cJSON.h"
#include "esp_crt_bundle.h"
#include "esp_event.h"
#include "esp_heap_caps.h"
#include "esp_http_client.h"
#include "esp_http_server.h"
#include "esp_io_expander.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_random.h"
#include "esp_wifi.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "lwip/inet.h"
#include "lwip/sockets.h"
#include "mbedtls/sha256.h"
#include "jpeg_decoder.h"
#include "nvs.h"
#include "nvs_flash.h"

#include <array>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <sys/time.h>
#include <unistd.h>
#include <string>
#include <vector>

namespace {
constexpr char TAG[] = "sonoro_network";
constexpr char NVS_NAMESPACE[] = "sonoro";
constexpr char NVS_WIFI_SSID[] = "wifi_ssid";
constexpr char NVS_WIFI_PASS[] = "wifi_pass";
constexpr char NVS_AP_PASS[] = "setup_pass";
constexpr EventBits_t WIFI_READY = BIT0;
constexpr EventBits_t PORTAL_STOP = BIT1;
constexpr EventBits_t SLOT_CHANGED = BIT2;
constexpr uint32_t PWR_BUTTON_PIN = IO_EXPANDER_PIN_NUM_4;
constexpr size_t HTTP_BODY_LIMIT = 2048;
constexpr size_t RTDB_BODY_LIMIT = 24576;
constexpr size_t COVER_BODY_LIMIT = 512 * 1024;
constexpr char PORTAL_HTML[] = R"html(<!doctype html>
<html lang="es"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta charset="utf-8"><title>Configurar Sonoro</title>
<style>body{font:17px system-ui;max-width:34rem;margin:2rem auto;padding:0 1rem;background:#f5efe7;color:#272824}h1{font-size:1.6rem}label{display:block;margin:1rem 0 .35rem}select,input,button{box-sizing:border-box;width:100%;padding:.8rem;border:1px solid #aaa;border-radius:.5rem;font:inherit}button{margin-top:1rem;background:#3c4938;color:white;border:0}p{line-height:1.5}</style>
<h1>Conecta tu cuadro</h1><p>Elige una red doméstica de 2,4 GHz y escribe su contraseña. Se enviará directamente al cuadro y no se compartirá con Firebase.</p>
<button id="refresh" type="button">Buscar redes</button><form id="form"><label for="ssid">Red Wi-Fi</label><select id="ssid" required></select><label for="password">Contraseña de la red</label><input id="password" type="password" autocomplete="current-password"><button>Conectar cuadro</button></form><p id="message" role="status"></p>
<script>const s=document.querySelector('#ssid'),m=document.querySelector('#message');async function scan(){m.textContent='Buscando redes…';try{const r=await fetch('/networks');if(!r.ok)throw 0;const a=await r.json();s.replaceChildren(...a.map(n=>{const o=document.createElement('option');o.value=n.ssid;o.textContent=n.ssid+(n.rssi?' ('+n.rssi+' dBm)':'');return o}));m.textContent=a.length?'Elige tu red.':'No se encontraron redes.'}catch{m.textContent='No se pudo buscar redes. Inténtalo otra vez.'}}document.querySelector('#refresh').onclick=scan;document.querySelector('#form').onsubmit=async e=>{e.preventDefault();m.textContent='Conectando…';try{const r=await fetch('/connect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ssid:s.value,password:document.querySelector('#password').value})});m.textContent=r.ok?'El cuadro está intentando conectarse. Mira su pantalla.':'No se pudo iniciar la conexión.'}catch{m.textContent='Se perdió la conexión con el portal. Mira la pantalla del cuadro.'}};scan();</script></html>)html";

struct CoverSelection {
    std::string image_key;
    std::string title;
    std::string artist;
};

sonoro::View* g_view = nullptr;
esp_netif_t* g_ap_netif = nullptr;
httpd_handle_t g_http_server = nullptr;
EventGroupHandle_t g_events = nullptr;
TaskHandle_t g_dns_task = nullptr;
bool g_provisioning = false;
bool g_has_saved_wifi = false;
std::atomic<bool> g_cover_screen_visible{false};
int g_disconnect_count = 0;
std::array<char, 33> g_ssid{};
std::array<char, 65> g_password{};
std::array<char, 33> g_candidate_ssid{};
std::array<char, 65> g_candidate_password{};
std::array<char, 33> g_ap_ssid{};
std::array<char, 17> g_ap_password{};
std::string g_loaded_cover_key;
std::string g_rtdb_status;
uint8_t* g_cover_pixels = nullptr;
lv_image_dsc_t g_cover_image{};
std::array<CoverSelection, 3> g_slots{};
std::atomic<int> g_selected_slot{-1};
int g_displayed_slot = -1;

void show_wifi_setup(const std::string& status = {}) {
    if (!g_view || !bsp_display_lock(pdMS_TO_TICKS(500))) return;
    g_view->showWifiSetup(g_ap_ssid.data(), g_ap_password.data(), status);
    bsp_display_unlock();
}

void show_wifi_connecting(const char* ssid) {
    if (!g_view || !bsp_display_lock(pdMS_TO_TICKS(500))) return;
    g_view->showWifiConnecting(ssid);
    bsp_display_unlock();
}

void show_firebase(const std::string& status, bool connected) {
    if (!g_view || !bsp_display_lock(pdMS_TO_TICKS(500))) return;
    g_view->showFirebaseStatus(CONFIG_SONORO_FRAME_TOKEN, status, connected);
    g_cover_screen_visible = false;
    g_displayed_slot = -1;
    bsp_display_unlock();
}

void show_firebase_cover(int slot, const std::string& title, const std::string& artist) {
    if (!g_view || !g_cover_pixels || !bsp_display_lock(pdMS_TO_TICKS(500))) return;
    g_view->showFirebaseCover(CONFIG_SONORO_FRAME_TOKEN, slot + 1, title, artist, &g_cover_image);
    g_cover_screen_visible = true;
    g_displayed_slot = slot;
    bsp_display_unlock();
}

void show_firebase_loading(int slot) {
    if (!g_view || !bsp_display_lock(pdMS_TO_TICKS(500))) return;
    g_view->showFirebaseLoading(slot + 1);
    g_cover_screen_visible = false;
    g_displayed_slot = -1;
    bsp_display_unlock();
}

bool load_credentials() {
    nvs_handle_t handle;
    if (nvs_open(NVS_NAMESPACE, NVS_READONLY, &handle) != ESP_OK) return false;
    size_t ssid_size = g_ssid.size();
    size_t password_size = g_password.size();
    const esp_err_t ssid_result = nvs_get_str(handle, NVS_WIFI_SSID, g_ssid.data(), &ssid_size);
    const esp_err_t password_result = nvs_get_str(handle, NVS_WIFI_PASS, g_password.data(), &password_size);
    nvs_close(handle);
    g_has_saved_wifi = ssid_result == ESP_OK && password_result == ESP_OK && g_ssid[0] != '\0';
    if (!g_has_saved_wifi) {
        g_ssid.fill('\0');
        g_password.fill('\0');
    }
    return g_has_saved_wifi;
}

void make_ap_identity() {
    uint8_t mac[6]{};
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    std::snprintf(g_ap_ssid.data(), g_ap_ssid.size(), "Sonoro-Config-%02X%02X", mac[4], mac[5]);

    nvs_handle_t handle;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle) == ESP_OK) {
        size_t length = g_ap_password.size();
        if (nvs_get_str(handle, NVS_AP_PASS, g_ap_password.data(), &length) != ESP_OK ||
            std::strlen(g_ap_password.data()) < 12) {
            static constexpr char alphabet[] = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
            for (size_t i = 0; i < 12; ++i) g_ap_password[i] = alphabet[esp_random() % (sizeof(alphabet) - 1)];
            g_ap_password[12] = '\0';
            nvs_set_str(handle, NVS_AP_PASS, g_ap_password.data());
            nvs_commit(handle);
        }
        nvs_close(handle);
    }
}

esp_err_t portal_root(httpd_req_t* request) {
    httpd_resp_set_type(request, "text/html; charset=utf-8");
    httpd_resp_set_hdr(request, "Cache-Control", "no-store");
    return httpd_resp_send(request, PORTAL_HTML, HTTPD_RESP_USE_STRLEN);
}

esp_err_t portal_networks(httpd_req_t* request) {
    const esp_err_t scan_result = esp_wifi_scan_start(nullptr, true);
    if (scan_result != ESP_OK) {
        httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "No se pudo escanear Wi-Fi");
        return ESP_OK;
    }
    uint16_t count = 0;
    if (esp_wifi_scan_get_ap_num(&count) != ESP_OK) count = 0;
    std::vector<wifi_ap_record_t> records(count);
    if (count && esp_wifi_scan_get_ap_records(&count, records.data()) != ESP_OK) count = 0;
    cJSON* array = cJSON_CreateArray();
    if (!array) return httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "Memoria agotada");
    for (uint16_t i = 0; i < count; ++i) {
        const std::string ssid(reinterpret_cast<const char*>(records[i].ssid),
                               strnlen(reinterpret_cast<const char*>(records[i].ssid), sizeof(records[i].ssid)));
        if (ssid.empty()) continue;
        cJSON* item = cJSON_CreateObject();
        cJSON_AddStringToObject(item, "ssid", ssid.c_str());
        cJSON_AddNumberToObject(item, "rssi", records[i].rssi);
        cJSON_AddItemToArray(array, item);
    }
    char* body = cJSON_PrintUnformatted(array);
    cJSON_Delete(array);
    if (!body) return httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "Memoria agotada");
    httpd_resp_set_type(request, "application/json");
    const esp_err_t result = httpd_resp_sendstr(request, body);
    cJSON_free(body);
    return result;
}

esp_err_t portal_connect(httpd_req_t* request) {
    if (request->content_len <= 0 || request->content_len > HTTP_BODY_LIMIT) {
        httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Solicitud no válida");
        return ESP_OK;
    }
    std::string body(static_cast<size_t>(request->content_len), '\0');
    size_t received = 0;
    while (received < body.size()) {
        const int bytes = httpd_req_recv(request, body.data() + received, body.size() - received);
        if (bytes <= 0) return httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Solicitud incompleta");
        received += static_cast<size_t>(bytes);
    }
    cJSON* json = cJSON_ParseWithLength(body.c_str(), body.size());
    const cJSON* ssid = json ? cJSON_GetObjectItemCaseSensitive(json, "ssid") : nullptr;
    const cJSON* password = json ? cJSON_GetObjectItemCaseSensitive(json, "password") : nullptr;
    if (!cJSON_IsString(ssid) || !ssid->valuestring || !cJSON_IsString(password) || !password->valuestring ||
        std::strlen(ssid->valuestring) == 0 || std::strlen(ssid->valuestring) >= g_candidate_ssid.size() ||
        std::strlen(password->valuestring) > 63) {
        cJSON_Delete(json);
        httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Red o contraseña no válida");
        return ESP_OK;
    }
    std::strncpy(g_candidate_ssid.data(), ssid->valuestring, g_candidate_ssid.size() - 1);
    std::strncpy(g_candidate_password.data(), password->valuestring, g_candidate_password.size() - 1);
    cJSON_Delete(json);

    wifi_config_t station{};
    std::memcpy(station.sta.ssid, g_candidate_ssid.data(), std::strlen(g_candidate_ssid.data()));
    std::memcpy(station.sta.password, g_candidate_password.data(), std::strlen(g_candidate_password.data()));
    station.sta.threshold.authmode = WIFI_AUTH_OPEN;
    g_disconnect_count = 0;
    g_provisioning = true;
    esp_err_t result = esp_wifi_set_mode(WIFI_MODE_APSTA);
    if (result == ESP_OK) result = esp_wifi_set_config(WIFI_IF_STA, &station);
    if (result == ESP_OK) result = esp_wifi_connect();
    if (result != ESP_OK) {
        g_provisioning = false;
        g_candidate_ssid.fill('\0');
        g_candidate_password.fill('\0');
        httpd_resp_send_err(request, HTTPD_500_INTERNAL_SERVER_ERROR, "No se pudo iniciar la conexión");
        return ESP_OK;
    }
    httpd_resp_set_type(request, "application/json");
    return httpd_resp_sendstr(request, "{\"accepted\":true}");
}

esp_err_t register_portal_uri(const char* path, httpd_method_t method,
                              esp_err_t (*handler)(httpd_req_t*)) {
    httpd_uri_t uri{};
    uri.uri = path;
    uri.method = method;
    uri.handler = handler;
    return httpd_register_uri_handler(g_http_server, &uri);
}

bool start_http_portal() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    config.max_uri_handlers = 12;
    config.uri_match_fn = httpd_uri_match_wildcard;
    if (httpd_start(&g_http_server, &config) != ESP_OK) return false;
    if (register_portal_uri("/networks", HTTP_GET, portal_networks) != ESP_OK ||
        register_portal_uri("/connect", HTTP_POST, portal_connect) != ESP_OK ||
        register_portal_uri("/", HTTP_GET, portal_root) != ESP_OK ||
        register_portal_uri("/*", HTTP_GET, portal_root) != ESP_OK) {
        httpd_stop(g_http_server);
        g_http_server = nullptr;
        return false;
    }
    return true;
}

bool make_dns_answer(const uint8_t* query, size_t query_len, uint8_t* response, size_t& response_len) {
    if (query_len < 17) return false;
    const uint16_t questions = (static_cast<uint16_t>(query[4]) << 8) | query[5];
    if (questions != 1) return false;
    size_t end = 12;
    while (end < query_len && query[end] != 0) {
        const uint8_t label_size = query[end];
        if (label_size > 63 || end + label_size + 1 >= query_len) return false;
        end += label_size + 1;
    }
    if (end + 5 > query_len) return false;
    const uint16_t type = (static_cast<uint16_t>(query[end + 1]) << 8) | query[end + 2];
    const uint16_t klass = (static_cast<uint16_t>(query[end + 3]) << 8) | query[end + 4];
    if (klass != 1) return false;
    const size_t question_size = end + 5 - 12;
    std::memcpy(response, query, 12 + question_size);
    response[2] = 0x81;
    response[3] = 0x80;
    response[6] = 0;
    response[7] = type == 1 ? 1 : 0;
    response[8] = response[9] = response[10] = response[11] = 0;
    response_len = 12 + question_size;
    if (type == 1) {
        const uint8_t record[] = {0xc0, 0x0c, 0, 1, 0, 1, 0, 0, 0, 30, 0, 4, 192, 168, 4, 1};
        std::memcpy(response + response_len, record, sizeof(record));
        response_len += sizeof(record);
    }
    return true;
}

void dns_server_task(void*) {
    const int socket_fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (socket_fd < 0) { g_dns_task = nullptr; vTaskDelete(nullptr); }
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(53);
    address.sin_addr.s_addr = htonl(INADDR_ANY);
    timeval timeout{1, 0};
    setsockopt(socket_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    if (bind(socket_fd, reinterpret_cast<sockaddr*>(&address), sizeof(address)) != 0) {
        close(socket_fd); g_dns_task = nullptr; vTaskDelete(nullptr);
    }
    std::array<uint8_t, 512> query{};
    std::array<uint8_t, 512> response{};
    while (!(xEventGroupGetBits(g_events) & PORTAL_STOP)) {
        sockaddr_in client{};
        socklen_t client_size = sizeof(client);
        const int length = recvfrom(socket_fd, query.data(), query.size(), 0,
                                    reinterpret_cast<sockaddr*>(&client), &client_size);
        if (length <= 0) continue;
        size_t response_size = 0;
        if (make_dns_answer(query.data(), static_cast<size_t>(length), response.data(), response_size)) {
            sendto(socket_fd, response.data(), response_size, 0,
                   reinterpret_cast<sockaddr*>(&client), client_size);
        }
    }
    close(socket_fd);
    g_dns_task = nullptr;
    vTaskDelete(nullptr);
}

void start_dns_server() {
    if (g_events) xEventGroupClearBits(g_events, PORTAL_STOP);
    if (xTaskCreate(dns_server_task, "sonoro_dns", 3072, nullptr, 4, &g_dns_task) != pdPASS) {
        g_dns_task = nullptr;
    }
}

void stop_portal() {
    if (g_events) xEventGroupSetBits(g_events, PORTAL_STOP);
    for (int i = 0; g_dns_task && i < 15; ++i) vTaskDelay(pdMS_TO_TICKS(100));
    if (g_http_server) { httpd_stop(g_http_server); g_http_server = nullptr; }
}

void start_setup_ap() {
    if (!g_ap_netif) g_ap_netif = esp_netif_create_default_wifi_ap();
    make_ap_identity();
    wifi_config_t access_point{};
    std::strncpy(reinterpret_cast<char*>(access_point.ap.ssid), g_ap_ssid.data(), sizeof(access_point.ap.ssid) - 1);
    std::strncpy(reinterpret_cast<char*>(access_point.ap.password), g_ap_password.data(), sizeof(access_point.ap.password) - 1);
    access_point.ap.ssid_len = std::strlen(g_ap_ssid.data());
    access_point.ap.channel = 1;
    access_point.ap.max_connection = 4;
    access_point.ap.authmode = WIFI_AUTH_WPA2_PSK;
    if (esp_wifi_set_mode(WIFI_MODE_APSTA) != ESP_OK ||
        esp_wifi_set_config(WIFI_IF_AP, &access_point) != ESP_OK ||
        esp_wifi_start() != ESP_OK) {
        ESP_LOGE(TAG, "No se pudo iniciar el punto de acceso de configuración");
        show_wifi_setup("No se pudo iniciar la red temporal.");
        return;
    }
    esp_netif_ip_info_t ip{};
    if (esp_netif_get_ip_info(g_ap_netif, &ip) == ESP_OK) {
        esp_netif_dns_info_t dns{};
        dns.ip.type = ESP_IPADDR_TYPE_V4;
        dns.ip.u_addr.ip4 = ip.ip;
        esp_netif_set_dns_info(g_ap_netif, ESP_NETIF_DNS_MAIN, &dns);
    }
    if (!start_http_portal()) ESP_LOGE(TAG, "No se pudo iniciar el portal HTTP local");
    start_dns_server();
    show_wifi_setup();
    ESP_LOGI(TAG, "Portal local iniciado en la red temporal; la clave solo se muestra en pantalla");
}

struct HttpBody {
    std::string data;
    size_t limit = RTDB_BODY_LIMIT;
    bool too_large = false;
};

esp_err_t collect_http_body(esp_http_client_event_t* event) {
    if (event->event_id == HTTP_EVENT_ON_DATA && event->data && event->data_len > 0) {
        auto* body = static_cast<HttpBody*>(event->user_data);
        if (body->data.size() + static_cast<size_t>(event->data_len) > body->limit) {
            body->too_large = true;
            return ESP_FAIL;
        }
        body->data.append(static_cast<const char*>(event->data), static_cast<size_t>(event->data_len));
    }
    return ESP_OK;
}

std::string frame_hash(const char* identifier) {
    uint8_t digest[32]{};
    if (mbedtls_sha256(reinterpret_cast<const unsigned char*>(identifier),
                       std::strlen(identifier), digest, 0) != 0) return {};
    char output[65];
    for (size_t i = 0; i < sizeof(digest); ++i) std::snprintf(output + i * 2, 3, "%02x", digest[i]);
    output[64] = '\0';
    return output;
}

std::string url_encode(const std::string& value) {
    static constexpr char HEX[] = "0123456789ABCDEF";
    std::string encoded;
    encoded.reserve(value.size() * 3);
    for (const unsigned char byte : value) {
        if ((byte >= 'a' && byte <= 'z') || (byte >= 'A' && byte <= 'Z') ||
            (byte >= '0' && byte <= '9') || byte == '-' || byte == '_' || byte == '.' || byte == '~') {
            encoded.push_back(static_cast<char>(byte));
        } else {
            encoded.push_back('%');
            encoded.push_back(HEX[byte >> 4]);
            encoded.push_back(HEX[byte & 0x0f]);
        }
    }
    return encoded;
}

bool read_cover(const std::string& image_key, const std::string& hash,
                uint8_t*& pixels, lv_image_dsc_t& image) {
    const std::string expected_prefix = "private/frames/" + hash + "/";
    if (image_key.rfind(expected_prefix, 0) != 0 ||
        !(image_key.size() >= 4 && image_key.compare(image_key.size() - 4, 4, ".jpg") == 0) ||
        std::strlen(CONFIG_SONORO_FIREBASE_STORAGE_BUCKET) == 0) {
        return false;
    }

    const std::string url = "https://firebasestorage.googleapis.com/v0/b/" +
        url_encode(CONFIG_SONORO_FIREBASE_STORAGE_BUCKET) + "/o/" + url_encode(image_key) + "?alt=media";
    HttpBody body{{}, COVER_BODY_LIMIT};
    esp_http_client_config_t config{};
    config.url = url.c_str();
    config.event_handler = collect_http_body;
    config.user_data = &body;
    config.timeout_ms = 20000;
    config.crt_bundle_attach = esp_crt_bundle_attach;
    config.buffer_size = 4096;
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) return false;
    const esp_err_t request_result = esp_http_client_perform(client);
    const int http_status = esp_http_client_get_status_code(client);
    esp_http_client_cleanup(client);
    if (request_result != ESP_OK || body.too_large || http_status != 200 || body.data.empty()) return false;

    esp_jpeg_image_cfg_t jpeg_config{};
    jpeg_config.indata = reinterpret_cast<uint8_t*>(body.data.data());
    jpeg_config.indata_size = body.data.size();
    jpeg_config.out_format = JPEG_IMAGE_FORMAT_RGB565;
    jpeg_config.out_scale = JPEG_IMAGE_SCALE_0;
    // LVGL's RGB565 image data uses little-endian pixel bytes on this target.
    jpeg_config.flags.swap_color_bytes = 0;
    esp_jpeg_image_output_t output{};
    if (esp_jpeg_get_image_info(&jpeg_config, &output) != ESP_OK ||
        output.width == 0 || output.height == 0 || output.width > 512 || output.height > 512 ||
        output.output_len == 0 || output.output_len > 512U * 512U * 2U) {
        return false;
    }

    pixels = static_cast<uint8_t*>(heap_caps_malloc(output.output_len, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
    if (!pixels) return false;
    jpeg_config.outbuf = pixels;
    jpeg_config.outbuf_size = output.output_len;
    if (esp_jpeg_decode(&jpeg_config, &output) != ESP_OK) {
        heap_caps_free(pixels);
        pixels = nullptr;
        return false;
    }

    image = {};
    image.header.magic = LV_IMAGE_HEADER_MAGIC;
    image.header.cf = LV_COLOR_FORMAT_RGB565;
    image.header.w = output.width;
    image.header.h = output.height;
    image.header.stride = output.width * 2;
    image.data_size = output.output_len;
    image.data = pixels;
    return true;
}

bool read_rtdb(std::array<CoverSelection, 3>& covers, std::string& status) {
    const std::string database_url = CONFIG_SONORO_FIREBASE_DATABASE_URL;
    const std::string identifier = CONFIG_SONORO_FRAME_TOKEN;
    if (database_url.rfind("https://", 0) != 0 || identifier.empty()) {
        status = "Wi-Fi está conectado. Falta configurar la URL pública de RTDB en menuconfig.";
        return false;
    }
    const std::string hash = frame_hash(identifier.c_str());
    if (hash.empty()) {
        status = "No se pudo preparar la consulta de Firebase.";
        return false;
    }
    std::string url = database_url;
    while (!url.empty() && url.back() == '/') url.pop_back();
    url += "/frames/" + hash + "/slots.json";

    HttpBody body{{}, RTDB_BODY_LIMIT};
    esp_http_client_config_t config{};
    config.url = url.c_str();
    config.event_handler = collect_http_body;
    config.user_data = &body;
    config.timeout_ms = 15000;
    config.crt_bundle_attach = esp_crt_bundle_attach;
    config.buffer_size = 4096;
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) {
        status = "No se pudo iniciar la conexión segura.";
        return false;
    }
    const esp_err_t request_result = esp_http_client_perform(client);
    const int http_status = esp_http_client_get_status_code(client);
    esp_http_client_cleanup(client);
    if (request_result != ESP_OK || body.too_large || http_status != 200) {
        status = "No se pudo leer RTDB. Se volverá a intentar.";
        return false;
    }

    cJSON* slots = cJSON_ParseWithLength(body.data.c_str(), body.data.size());
    const std::string empty_status = "Firebase responde; " + identifier + " todavía no tiene selecciones.";
    if ((!slots && body.data == "null") || cJSON_IsNull(slots)) {
        cJSON_Delete(slots);
        status = empty_status;
        return true;
    }
    if (!cJSON_IsObject(slots)) {
        cJSON_Delete(slots);
        status = "Firebase respondió con un formato no esperado.";
        return false;
    }
    int count = 0;
    std::string titles;
    for (int i = 0; i < 3; ++i) {
        char key[8];
        std::snprintf(key, sizeof(key), "slot-%d", i);
        const cJSON* slot = cJSON_GetObjectItemCaseSensitive(slots, key);
        if (!cJSON_IsObject(slot)) continue;
        const cJSON* title = cJSON_GetObjectItemCaseSensitive(slot, "title");
        const cJSON* kind = cJSON_GetObjectItemCaseSensitive(slot, "kind");
        const cJSON* image_key = cJSON_GetObjectItemCaseSensitive(slot, "image_key");
        if (!cJSON_IsString(title) || !title->valuestring) continue;
        ++count;
        if (!titles.empty()) titles += "\n";
        titles += std::to_string(i + 1) + ". " + title->valuestring;
        covers[i].title = title->valuestring;
        const cJSON* artist = cJSON_GetObjectItemCaseSensitive(slot, "artist");
        if (cJSON_IsString(artist) && artist->valuestring) covers[i].artist = artist->valuestring;
        const bool song_kind = !kind ||
            (cJSON_IsString(kind) && kind->valuestring && std::strcmp(kind->valuestring, "song") == 0);
        if (song_kind && cJSON_IsString(image_key) && image_key->valuestring) {
            covers[i].image_key = image_key->valuestring;
        }
    }
    cJSON_Delete(slots);
    if (count == 0) status = empty_status;
    else status = std::to_string(count) + " selección(es) publicada(s):\n" + titles;
    return true;
}

void show_selected_slot() {
    const int slot = g_selected_slot.load();
    if (slot < 0 || slot >= static_cast<int>(g_slots.size())) {
        show_firebase(g_rtdb_status, true);
        return;
    }
    const CoverSelection& selection = g_slots[static_cast<size_t>(slot)];
    if (selection.image_key.empty()) {
        const std::string detail = selection.title.empty()
            ? "El hueco " + std::to_string(slot + 1) + " está vacío."
            : "El hueco " + std::to_string(slot + 1) + " no tiene portada descargable.";
        show_firebase(detail, true);
        return;
    }
    if (selection.image_key == g_loaded_cover_key && g_cover_pixels) {
        if (!g_cover_screen_visible || g_displayed_slot != slot) {
            show_firebase_cover(slot, selection.title, selection.artist);
        }
        return;
    }

    uint8_t* pixels = nullptr;
    lv_image_dsc_t image{};
    const std::string hash = frame_hash(CONFIG_SONORO_FRAME_TOKEN);
    if (!read_cover(selection.image_key, hash, pixels, image)) {
        if (g_selected_slot.load() != slot) return;
        show_firebase("No se pudo cargar la portada del hueco " + std::to_string(slot + 1) + ".", true);
        return;
    }
    if (g_selected_slot.load() != slot) {
        heap_caps_free(pixels);
        return;
    }
    if (!g_view || !bsp_display_lock(pdMS_TO_TICKS(500))) {
        heap_caps_free(pixels);
        return;
    }
    uint8_t* previous_pixels = g_cover_pixels;
    g_cover_pixels = pixels;
    g_cover_image = image;
    g_view->showFirebaseCover(CONFIG_SONORO_FRAME_TOKEN, slot + 1,
                              selection.title, selection.artist, &g_cover_image);
    g_cover_screen_visible = true;
    g_displayed_slot = slot;
    bsp_display_unlock();
    g_loaded_cover_key = selection.image_key;
    if (previous_pixels) heap_caps_free(previous_pixels);
}

void firebase_task(void*) {
    while (true) {
        xEventGroupWaitBits(g_events, WIFI_READY, pdFALSE, pdTRUE, portMAX_DELAY);
        std::string status;
        std::array<CoverSelection, 3> slots{};
        const bool connected = read_rtdb(slots, status);
        if (!connected) {
            show_firebase(status, false);
        } else {
            g_slots = std::move(slots);
            g_rtdb_status = status;
            int selected = g_selected_slot.load();
            if (selected < 0 || selected >= static_cast<int>(g_slots.size()) ||
                g_slots[static_cast<size_t>(selected)].title.empty()) {
                selected = -1;
                for (size_t i = 0; i < g_slots.size(); ++i) {
                    if (!g_slots[i].title.empty()) {
                        selected = static_cast<int>(i);
                        break;
                    }
                }
                g_selected_slot.store(selected);
            }
            if (g_slots[0].title.empty() && g_slots[1].title.empty() && g_slots[2].title.empty()) {
                show_firebase(status, true);
            } else {
                show_selected_slot();
            }
        }

        const EventBits_t changed = xEventGroupWaitBits(
            g_events, SLOT_CHANGED, pdTRUE, pdFALSE, pdMS_TO_TICKS(30000));
        if ((changed & SLOT_CHANGED) && (xEventGroupGetBits(g_events) & WIFI_READY)) {
            show_selected_slot();
        }
    }
}

struct ButtonDebouncer {
    bool candidate = false;
    bool stable = false;
    TickType_t changed_at = 0;
};

bool pressed_edge(bool raw_pressed, ButtonDebouncer& button, TickType_t now) {
    if (raw_pressed != button.candidate) {
        button.candidate = raw_pressed;
        button.changed_at = now;
    }
    if (button.candidate != button.stable &&
        now - button.changed_at >= pdMS_TO_TICKS(40)) {
        button.stable = button.candidate;
        return button.stable;
    }
    return false;
}

void button_task(void* expander_arg) {
    const auto expander = static_cast<esp_io_expander_handle_t>(expander_arg);
    gpio_config_t boot_config{};
    boot_config.pin_bit_mask = 1ULL << GPIO_NUM_0;
    boot_config.mode = GPIO_MODE_INPUT;
    boot_config.pull_up_en = GPIO_PULLUP_ENABLE;
    boot_config.pull_down_en = GPIO_PULLDOWN_DISABLE;
    boot_config.intr_type = GPIO_INTR_DISABLE;
    const bool boot_ready = gpio_config(&boot_config) == ESP_OK;
    const bool pwr_ready = expander &&
        esp_io_expander_set_dir(expander, PWR_BUTTON_PIN, IO_EXPANDER_INPUT) == ESP_OK;
    if (!boot_ready) ESP_LOGW(TAG, "No se pudo preparar BOOT para selección de hueco");
    if (!pwr_ready) ESP_LOGW(TAG, "No se pudo preparar PWR para selección de hueco");
    ESP_LOGI(TAG, "Botones provisionales: BOOT=hueco 1; PWR=hueco 2; pulsación corta");

    ButtonDebouncer boot{};
    ButtonDebouncer pwr{};
    while (true) {
        if (xEventGroupGetBits(g_events) & WIFI_READY) {
            const TickType_t now = xTaskGetTickCount();
            const bool boot_pressed = boot_ready && gpio_get_level(GPIO_NUM_0) == 0;
            uint32_t pwr_levels = 0;
            const bool pwr_pressed = pwr_ready &&
                esp_io_expander_get_level(expander, PWR_BUTTON_PIN, &pwr_levels) == ESP_OK &&
                (pwr_levels & PWR_BUTTON_PIN) != 0;
            if (pressed_edge(boot_pressed, boot, now)) {
                g_selected_slot.store(0);
                show_firebase_loading(0);
                xEventGroupSetBits(g_events, SLOT_CHANGED);
            }
            if (pressed_edge(pwr_pressed, pwr, now)) {
                g_selected_slot.store(1);
                show_firebase_loading(1);
                xEventGroupSetBits(g_events, SLOT_CHANGED);
            }
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

bool persist_candidate() {
    nvs_handle_t handle;
    if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle) != ESP_OK) return false;
    esp_err_t result = nvs_set_str(handle, NVS_WIFI_SSID, g_candidate_ssid.data());
    if (result == ESP_OK) result = nvs_set_str(handle, NVS_WIFI_PASS, g_candidate_password.data());
    if (result == ESP_OK) result = nvs_commit(handle);
    nvs_close(handle);
    if (result != ESP_OK) return false;
    g_ssid = g_candidate_ssid;
    g_password = g_candidate_password;
    g_has_saved_wifi = true;
    g_candidate_ssid.fill('\0');
    g_candidate_password.fill('\0');
    g_provisioning = false;
    return true;
}

void wifi_event(void*, esp_event_base_t base, int32_t id, void*) {
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(g_events, WIFI_READY);
        if (g_provisioning && ++g_disconnect_count >= 5) {
            g_provisioning = false;
            g_candidate_ssid.fill('\0');
            g_candidate_password.fill('\0');
            show_wifi_setup("No se conectó. Comprueba la contraseña y vuelve a intentarlo.");
        } else if (g_has_saved_wifi) {
            esp_wifi_connect();
            if (!(xEventGroupGetBits(g_events) & WIFI_READY)) {
                show_wifi_connecting(g_ssid.data());
            }
        }
        return;
    }
    if (base != IP_EVENT || id != IP_EVENT_STA_GOT_IP) return;
    g_disconnect_count = 0;
    if (g_provisioning) {
        if (persist_candidate()) {
            stop_portal();
            esp_wifi_set_mode(WIFI_MODE_STA);
        } else {
            g_provisioning = false;
            g_candidate_ssid.fill('\0');
            g_candidate_password.fill('\0');
            show_firebase("Wi-Fi conectado; no se pudieron guardar las credenciales en el dispositivo.", false);
        }
    }
    xEventGroupSetBits(g_events, WIFI_READY);
    ESP_LOGI(TAG, "Wi-Fi listo; consultando RTDB por HTTPS");
}

bool initialize_wifi() {
    const esp_err_t nvs_result = nvs_flash_init();
    if (nvs_result != ESP_OK && nvs_result != ESP_ERR_INVALID_STATE) return false;
    const esp_err_t netif_result = esp_netif_init();
    if (netif_result != ESP_OK && netif_result != ESP_ERR_INVALID_STATE) return false;
    const esp_err_t loop_result = esp_event_loop_create_default();
    if (loop_result != ESP_OK && loop_result != ESP_ERR_INVALID_STATE) return false;
    wifi_init_config_t wifi_config = WIFI_INIT_CONFIG_DEFAULT();
    if (esp_wifi_init(&wifi_config) != ESP_OK) return false;
    esp_wifi_set_storage(WIFI_STORAGE_RAM);
    esp_netif_create_default_wifi_sta();
    if (esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event, nullptr) != ESP_OK ||
        esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event, nullptr) != ESP_OK) return false;
    return true;
}
}

void sonoro_network_start(sonoro::View* view) {
    g_view = view;
    g_events = xEventGroupCreate();
    if (!g_events || !initialize_wifi()) {
        show_firebase("No se pudo iniciar el gestor Wi-Fi.", false);
        return;
    }
    if (xTaskCreate(firebase_task, "sonoro_firebase", 8192, nullptr, 4, nullptr) != pdPASS) {
        show_firebase("No se pudo iniciar la consulta de RTDB.", false);
        return;
    }
    esp_io_expander_handle_t expander = bsp_io_expander_init();
    if (xTaskCreate(button_task, "sonoro_buttons", 3072, expander, 3, nullptr) != pdPASS) {
        ESP_LOGW(TAG, "No se pudo iniciar la selección provisional con botones integrados");
    }
    if (!load_credentials()) {
        start_setup_ap();
        return;
    }
    wifi_config_t station{};
    std::memcpy(station.sta.ssid, g_ssid.data(), std::strlen(g_ssid.data()));
    std::memcpy(station.sta.password, g_password.data(), std::strlen(g_password.data()));
    station.sta.threshold.authmode = WIFI_AUTH_OPEN;
    esp_err_t result = esp_wifi_set_mode(WIFI_MODE_STA);
    if (result == ESP_OK) result = esp_wifi_set_config(WIFI_IF_STA, &station);
    if (result == ESP_OK) result = esp_wifi_start();
    if (result != ESP_OK) {
        show_firebase("No se pudo iniciar Wi-Fi.", false);
        return;
    }
    esp_wifi_connect();
    show_wifi_connecting(g_ssid.data());
}
