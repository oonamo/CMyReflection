add_plugin_test_suite(format
  TYPES_HEADER "test_format_types.h"
  PY_TEST      "test_format_plugin.py"
  C_SOURCES    "test_format.c" "test_format_runner.c" "format_refl_impl.c"
  PLUGINS      ${FORMAT_EXT}
)
