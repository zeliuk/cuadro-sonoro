idf_component_register(
    SRCS "src/sonoro_view.cpp" "src/diagnostic_assets.cpp" "third_party/qrcodegen.cpp"
    INCLUDE_DIRS "include"
    REQUIRES lvgl__lvgl
)
