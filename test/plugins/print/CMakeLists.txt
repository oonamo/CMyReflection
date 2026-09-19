add_plugin_test_suite(print
  TYPES_HEADER "test_print_types.h"
  PY_TEST      "test_print_plugin.py"
  C_SOURCES    "test_print.c" "test_print_runner.c" "print_refl_impl.c"
  PLUGINS      ${PRINT_EXT}
)
