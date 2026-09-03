cmake_minimum_required(VERSION 3.23)
project(cmyreflection C)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_library(${PROJECT_NAME} INTERFACE)

target_include_directories(${PROJECT_NAME} INTERFACE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

target_compile_features(${PROJECT_NAME} INTERFACE c_std_99)

if (PROJECT_IS_TOP_LEVEL)
  set(CMAKE_C_STANDARD_EXTENSIONS OFF)
  set(CMAKE_C_EXTENSIONS OFF)
  set(CMAKE_C_STANDARD 99)
  list(APPEND CMAKE_CTEST_ARGUMENTS "--output-on-failure")
  enable_testing()
  add_subdirectory(test)
endif()
