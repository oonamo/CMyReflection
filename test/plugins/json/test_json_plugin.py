import sys
from pathlib import Path

import pytest

# test_json_plugin.py -> json/ -> plugins/ -> test/ -> ROOT
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import plugins.json as json
import plugins.print as printer
from cmy_reflector import _PLUGINS, Reflector, generate_reflection


@pytest.fixture(autouse=True)
def reset_plugin_registries():
    global _PLUGINS
    original_plugins = _PLUGINS.copy()

    _PLUGINS = [
        printer.printer,
        json.plugin,
    ]

    yield

    _PLUGINS = original_plugins


def test_can_use_serialize_function():
    c_code = """
    // cmy:reflect
    // cmy:json_serialize_function(serializer_1)
    typedef struct {
        int x;
    } MyStruct;

    // cmy:reflect
    // cmy:json_serialize_function(serializer_2)
    typedef enum {
        A,
    } MyEnum;
    """

    reflector = Reflector()
    generate_reflection(reflector, "test.h", c_code)
    reflector.resolve()

    generated_content = str(reflector)

    for f in ["serializer_1", "serializer_2"]:
        func_def = f"extern ReflectResult {f}(const void* exact_data_ptr, FIELD_TYPE actual_type, const StructFieldInfo* field_ctx, _cmy_json_state* state);"
        case_def = f"return {f}(exact_data_ptr, actual_type, field_ctx, state);"

        assert func_def in generated_content
        assert case_def in generated_content
