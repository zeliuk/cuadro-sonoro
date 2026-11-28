idf_component_register(
    SRCS "src/sonoro_view.cpp" "src/diagnostic_assets.cpp"
         "src/font_noto_sans_16.c" "src/font_noto_sans_20.c"
         "third_party/qrcodegen.cpp"
    INCLUDE_DIRS "include"
    REQUIRES lvgl__lvgl
)
