set(GENERATED_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/generated.h")
set(REFLECTION_SOURCE_FILES "${CMAKE_CURRENT_SOURCE_DIR}/types.h")

add_executable(json_serializer)
target_sources(json_serializer PRIVATE main.c)

cmy_add_reflection(json_serializer
  INPUTS "${REFLECTION_SOURCE_FILES}"
  OUTPUT "${GENERATED_HEADER}"
  STD_PLUGINS json format
)

set_target_properties(json_serializer PROPERTIES
  C_STANDARD 99
  C_STANDARD_REQUIRED ON
  C_EXTENSIONS OFF
)

target_include_directories(json_serializer PUBLIC ${PROJECT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(json_serializer PRIVATE
  "EXAMPLE_OUT_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}\""
)

target_compile_options(json_serializer PRIVATE ${STRICT_WARNINGS})
