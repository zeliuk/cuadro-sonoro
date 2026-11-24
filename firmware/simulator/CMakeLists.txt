cmake_minimum_required(VERSION 3.20)
project(cuadro_sonoro_simulator LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)
set(SDL_SHARED ON CACHE BOOL "Build SDL2 as a shared library" FORCE)
set(SDL_STATIC OFF CACHE BOOL "Do not build SDL2 static library" FORCE)
set(SDL_TEST OFF CACHE BOOL "Do not build SDL2 tests" FORCE)
FetchContent_Declare(SDL2
  GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
  GIT_TAG release-2.32.10
  GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(SDL2)

set(LV_CONF_PATH "")
set(LV_CONF_INCLUDE_SIMPLE ON CACHE BOOL "Find lv_conf.h from include path")
set(CONFIG_LV_USE_THORVG_INTERNAL OFF CACHE BOOL "Do not build unused LVGL vector renderer" FORCE)
set(CONFIG_LV_BUILD_EXAMPLES OFF CACHE BOOL "Do not build unused LVGL examples" FORCE)
set(CONFIG_LV_BUILD_DEMOS OFF CACHE BOOL "Do not build unused LVGL demos" FORCE)
FetchContent_Declare(lvgl
  GIT_REPOSITORY https://github.com/lvgl/lvgl.git
  GIT_TAG v9.5.0
  GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(lvgl)
target_link_libraries(lvgl PUBLIC SDL2::SDL2)
target_include_directories(lvgl PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
target_include_directories(lvgl PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/../common/include")

add_executable(cuadro-sonoro
  src/main.cpp
  ../common/src/sonoro_view.cpp
  ../common/third_party/qrcodegen.cpp
  src/key_input.cpp
  src/stb_image_impl.cpp
)
target_include_directories(cuadro-sonoro PRIVATE include ../common/include third_party)
target_link_libraries(cuadro-sonoro PRIVATE lvgl SDL2::SDL2)
target_compile_definitions(cuadro-sonoro PRIVATE
  SONORO_ASSET_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../common/assets"
  SDL_MAIN_HANDLED
)
if(APPLE)
  target_link_libraries(cuadro-sonoro PRIVATE "-framework Cocoa" "-framework IOKit" "-framework CoreVideo")
endif()
