add_plugin_test_suite(json
  TYPES_HEADER "test_json_types.h"
  PY_TEST      "test_json_plugin.py"
  C_SOURCES    "test_json.c" "test_json_runner.c" "json_refl_impl.c"
  PLUGINS      ${PRINT_EXT}  ${JSON_EXT}
)
add_test(NAME NodeJsonValidation COMMAND node ${CMAKE_CURRENT_SOURCE_DIR}/validate_json.js)
set_tests_properties(NodeJsonValidation PROPERTIES DEPENDS JsonTests)
