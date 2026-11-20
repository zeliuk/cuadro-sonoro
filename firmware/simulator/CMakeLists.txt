cmake_minimum_required(VERSION 3.20)
project(cuadro_sonoro_simulator LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)
find_package(SDL2 CONFIG REQUIRED)

set(LV_CONF_PATH "")
set(LV_CONF_INCLUDE_SIMPLE ON CACHE BOOL "Find lv_conf.h from include path")
set(LV_CONF_BUILD_DISABLE_THORVG_INTERNAL ON CACHE BOOL "Do not build unused LVGL vector graphics integration")
set(LV_CONF_BUILD_DISABLE_EXAMPLES ON CACHE BOOL "Do not build LVGL examples")
set(LV_CONF_BUILD_DISABLE_DEMOS ON CACHE BOOL "Do not build LVGL demos")
FetchContent_Declare(lvgl
  GIT_REPOSITORY https://github.com/lvgl/lvgl.git
  GIT_TAG v9.2.2
  GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(lvgl)
target_link_libraries(lvgl PUBLIC SDL2::SDL2)
target_include_directories(lvgl PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")

add_executable(cuadro-sonoro
  src/main.cpp
  src/sonoro_view.cpp
  src/key_input.cpp
  src/stb_image_impl.cpp
  third_party/qrcodegen.cpp
)
target_include_directories(cuadro-sonoro PRIVATE include third_party)
target_link_libraries(cuadro-sonoro PRIVATE lvgl SDL2::SDL2)
target_compile_definitions(cuadro-sonoro PRIVATE
  SONORO_ASSET_DIR="${CMAKE_CURRENT_SOURCE_DIR}/assets"
  SDL_MAIN_HANDLED
)
if(APPLE)
  target_link_libraries(cuadro-sonoro PRIVATE "-framework Cocoa" "-framework IOKit" "-framework CoreVideo")
endif()
