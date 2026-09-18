include(FetchContent)
FetchContent_MakeAvailable(unity)

find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(GENERATED_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/json.generated.h")
set(REFLECTION_SOURCE_FILES "${CMAKE_CURRENT_SOURCE_DIR}/test_json_types.h")
file(GLOB_RECURSE PLUGIN_FILES CONFIGURE_DEPENDS "${PROJECT_SOURCE_DIR}/plugins/*.py")

set(PRINT_EXT
  "${PROJECT_SOURCE_DIR}/plugins/print.py"
)
set(JSON_EXT
  "${PROJECT_SOURCE_DIR}/plugins/json.py"
)

add_custom_command(
  OUTPUT ${GENERATED_HEADER}
  COMMAND Python3::Interpreter "${PROJECT_SOURCE_DIR}/cmy_reflector.py" "${REFLECTION_SOURCE_FILES}" -o "${GENERATED_HEADER}" --plugin ${PRINT_EXT} --plugin ${JSON_EXT}
  DEPENDS "${PROJECT_SOURCE_DIR}/cmy_reflector.py" ${REFLECTION_SOURCE_FILES} ${PLUGIN_FILES}
  COMMENT "Generating C reflection data..."
)

set(JSON_TEST_SOURCES
  test_json.c
  test_json_runner.c
  json_refl_impl.c
  ${GENERATED_HEADER}
)

add_executable(test_json)
set_target_properties(test_json PROPERTIES
  C_STANDARD 99
  C_STANDARD_REQUIRED ON
  C_EXTENSIONS OFF
)

target_link_libraries(test_json PRIVATE unity)
target_sources(test_json PRIVATE ${JSON_TEST_SOURCES})
target_include_directories(test_json PUBLIC ${PROJECT_SOURCE_DIR})
target_compile_definitions(test_json PRIVATE
  "TEST_OUT_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}\""
)
add_test(NAME JsonTests COMMAND test_json -v)

add_test(NAME NodeJsonValidation COMMAND node ${CMAKE_CURRENT_SOURCE_DIR}/validate_json.js)
set_tests_properties(NodeJsonValidation PROPERTIES DEPENDS JsonTests)
