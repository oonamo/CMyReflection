cmake_minimum_required(VERSION 3.23)
project(cmyreflection C)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_library(${PROJECT_NAME} INTERFACE)

target_include_directories(${PROJECT_NAME} INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

if (PROJECT_IS_TOP_LEVEL)
  list(APPEND CMAKE_CTEST_ARGUMENTS "--output-on-failure")
  enable_testing()
  add_subdirectory(test)
endif()
