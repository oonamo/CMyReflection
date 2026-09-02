cmake_minimum_required(VERSION 3.23)
project(cmyreflection C)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_library(${PROJECT_NAME} INTERFACE)

enable_testing()

target_include_directories(${PROJECT_NAME} INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})
add_subdirectory(test)
