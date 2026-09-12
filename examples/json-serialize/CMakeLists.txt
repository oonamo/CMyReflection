find_package(Python3 REQUIRED COMPONENTS Interpreter)

# file(GLOB_RECURSE REFLECTION_SOURCE_FILES CONFIGURE_DEPENDS "*.h" "*.c")
set(REFLECTION_SOURCE_FILES "types.h")

set(GENERATED_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/generated.h")

add_custom_command(
  OUTPUT ${GENERATED_HEADER}
  COMMAND Python3::Interpreter "${PROJECT_SOURCE_DIR}/cmy_reflector.py" "${CMAKE_CURRENT_SOURCE_DIR}" -o "${GENERATED_HEADER}"
  DEPENDS "${PROJECT_SOURCE_DIR}/cmy_reflector.py" ${REFLECTION_SOURCE_FILES}
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
