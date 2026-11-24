idf_component_register(
    SRCS "main.cpp"
    INCLUDE_DIRS "." "../../common/include"
    REQUIRES lvgl__lvgl waveshare__esp32_s3_touch_lcd_4b common
)
