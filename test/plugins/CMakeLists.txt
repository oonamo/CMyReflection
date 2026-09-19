set(PRINT_EXT
  "${PROJECT_SOURCE_DIR}/plugins/print.py"
)
set(JSON_EXT
  "${PROJECT_SOURCE_DIR}/plugins/json.py"
)

include(FetchContent)
FetchContent_MakeAvailable(unity)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

function(add_plugin_test_suite PLUGIN_NAME)
  set(options)
  set(oneValueArgs TYPES_HEADER PY_TEST)
  set(multiValueArgs C_SOURCES PLUGINS)
  cmake_parse_arguments(ARGS "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

  if(ARGS_PY_TEST)
    add_test(NAME PyTest_${PLUGIN_NAME}
             COMMAND Python3::Interpreter -m pytest ${CMAKE_CURRENT_SOURCE_DIR}/${ARGS_PY_TEST})
  endif()

  set(GENERATED_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/${PLUGIN_NAME}.generated.h")

  set(CLI_PLUGIN_ARGS "")
  foreach(plugin_path ${ARGS_PLUGINS})
    list(APPEND CLI_PLUGIN_ARGS "--plugin" "${plugin_path}")
  endforeach()

  add_custom_command(
    OUTPUT ${GENERATED_HEADER}
    COMMAND Python3::Interpreter "${PROJECT_SOURCE_DIR}/cmy_reflector.py"
            "${CMAKE_CURRENT_SOURCE_DIR}/${ARGS_TYPES_HEADER}"
            -o "${GENERATED_HEADER}"
            ${CLI_PLUGIN_ARGS}
    DEPENDS "${PROJECT_SOURCE_DIR}/cmy_reflector.py"
            "${CMAKE_CURRENT_SOURCE_DIR}/${ARGS_TYPES_HEADER}"
            ${ARGS_PLUGINS}
    COMMENT "Generating C reflection data for ${PLUGIN_NAME}..."
  )


  set(EXE_NAME test_${PLUGIN_NAME})
  add_executable(${EXE_NAME})
  set_target_properties(${EXE_NAME} PROPERTIES
    C_STANDARD 99
    C_STANDARD_REQUIRED ON
    C_EXTENSIONS OFF
  )

  target_sources(${EXE_NAME} PRIVATE ${ARGS_C_SOURCES} ${GENERATED_HEADER})
  target_link_libraries(${EXE_NAME} PRIVATE unity)
  target_include_directories(${EXE_NAME} PUBLIC ${PROJECT_SOURCE_DIR})
  target_compile_definitions(${EXE_NAME} PRIVATE
        "TEST_OUT_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}\""
  )

  add_test(NAME CTest_${PLUGIN_NAME} COMMAND ${EXE_NAME} -v)

  if(ARGS_PY_TEST)
    set_tests_properties(CTest_${PLUGIN_NAME} PROPERTIES DEPENDS PyTest_${PLUGIN_NAME})
  endif()
endfunction()

add_subdirectory(json)
