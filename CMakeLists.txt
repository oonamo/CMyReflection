cmake_minimum_required(VERSION 3.23)
project(cmyreflection C)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_library(${PROJECT_NAME} INTERFACE)

target_include_directories(${PROJECT_NAME} INTERFACE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

target_compile_features(${PROJECT_NAME} INTERFACE c_std_99)

function(cmy_add_reflection TARGET_NAME)
  cmake_parse_arguments(ARG "" "OUTPUT" "INPUTS;PLUGINS;STD_PLUGINS" ${ARGN})

  find_package(Python3 REQUIRED COMPONENTS Interpreter)

  set(CMY_SCRIPT "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/cmy_reflector.py")
  set(RESOLVED_PLUGINS "")

  foreach(std_plugin IN LISTS ARG_STD_PLUGINS)
    list(APPEND RESOLVED_PLUGINS "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/plugins/${std_plugin}.py")
  endforeach()
  list(APPEND RESOLVED_PLUGINS ${ARG_PLUGINS})

  set(PLUGIN_ARGS)
  if(RESOLVED_PLUGINS)
    list(APPEND PLUGIN_ARGS "--plugin" ${RESOLVED_PLUGINS})
  endif()

  add_custom_command(
    OUTPUT  ${ARG_OUTPUT}
    COMMAND Python3::Interpreter "${CMY_SCRIPT}"
            --input ${ARG_INPUTS}
            --output ${ARG_OUTPUT}
            ${PLUGIN_ARGS}
    DEPENDS "${CMY_SCRIPT}" ${ARG_INPUTS} ${RESOLVED_PLUGINS}
    COMMENT "Generating C reflection metadata for ${TARGET_NAME}..."
  )

  target_sources(${TARGET_NAME} PRIVATE ${ARG_OUTPUT})
endfunction()

if (PROJECT_IS_TOP_LEVEL)
  set(CMAKE_C_STANDARD_EXTENSIONS OFF)
  set(CMAKE_C_EXTENSIONS OFF)
  set(CMAKE_C_STANDARD 99)
  list(APPEND CMAKE_CTEST_ARGUMENTS "--output-on-failure")
  enable_testing()
  add_subdirectory(test)
  add_subdirectory(examples)
endif()
