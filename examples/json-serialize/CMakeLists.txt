find_package(Python3 REQUIRED COMPONENTS Interpreter)

# file(GLOB_RECURSE REFLECTION_SOURCE_FILES CONFIGURE_DEPENDS "*.h" "*.c")
set(REFLECTION_SOURCE_FILES "types.h")

set(GENERATED_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/generated.h")

file(GLOB_RECURSE PLUGIN_FILES CONFIGURE_DEPENDS "${PROJECT_SOURCE_DIR}/plugins/*.py")

set(PRINT_EXT
  "${PROJECT_SOURCE_DIR}/plugins/print.py"
)
set(JSON_EXT
  "${PROJECT_SOURCE_DIR}/plugins/json.py"
)

add_custom_command(
  OUTPUT ${GENERATED_HEADER}
  COMMAND Python3::Interpreter "${PROJECT_SOURCE_DIR}/cmy_reflector.py"
          --input "${CMAKE_CURRENT_SOURCE_DIR}"
          --output "${GENERATED_HEADER}"
          --plugin ${PRINT_EXT} ${JSON_EXT}
  DEPENDS "${PROJECT_SOURCE_DIR}/cmy_reflector.py" ${REFLECTION_SOURCE_FILES} ${PLUGIN_FILES}
  COMMENT "Generating C reflection data for json-serializer..."
)

add_executable(json_serializer)
set_target_properties(json_serializer PROPERTIES
  C_STANDARD 99
  C_STANDARD_REQUIRED ON
  C_EXTENSIONS OFF
)
target_sources(json_serializer PRIVATE main.c ${GENERATED_HEADER})
target_include_directories(json_serializer PUBLIC ${PROJECT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(json_serializer PRIVATE
  "EXAMPLE_OUT_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}\""
)
