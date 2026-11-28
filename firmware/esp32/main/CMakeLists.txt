idf_component_register(
    SRCS "main.cpp" "network_manager.cpp"
    INCLUDE_DIRS "." "../../common/include"
    REQUIRES lvgl__lvgl waveshare__esp32_s3_touch_lcd_4b espressif__esp_io_expander
            esp_driver_gpio esp_timer esp_wifi esp_event esp_netif nvs_flash
            esp_http_server esp_http_client mbedtls json espressif__esp_jpeg common
)
