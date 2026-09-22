cmake_minimum_required(VERSION 3.17)
project(my_app C)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)

FetchContent_Declare(
    cmyreflection
    # GIT_REPOSITORY https://github.com/oonamo/CMyReflection.git
    # GIT_TAG        main
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../
)
FetchContent_MakeAvailable(cmyreflection)

# Add Sources
add_executable(${PROJECT_NAME})
target_sources(${PROJECT_NAME} PRIVATE src/main.c)

set(REFL_OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/refl.generated.h")

# Link cmyreflection
target_link_libraries(${PROJECT_NAME} PRIVATE cmyreflection)

cmy_add_reflection(my_app
    INPUTS      "${CMAKE_CURRENT_SOURCE_DIR}/src/types.h"
    OUTPUT      "${REFL_OUTPUT}"
    STD_PLUGINS json print
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_BINARY_DIR}
)
