import sys
from pathlib import Path

import pytest

# test_json_plugin.py -> json/ -> plugins/ -> test/ -> ROOT
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import cmy_reflector
import plugins.format as stdformat
from cmy_reflector import _PLUGINS, Plugin, Reflector, generate_reflection


@pytest.fixture(autouse=True)
def reset_plugin_registries():
    global _PLUGINS
    original_plugins = _PLUGINS.copy()

    _PLUGINS = [
        stdformat.stdformat,
    ]

    yield

    _PLUGINS = original_plugins


def test_validator():
    TEST_CASES_VALID = [
        "%s",
        "%u",
        "%f%%",
        "%.2f",
        "%*s",
        "Hello, this has a print specifier %somewhere here",
        "New lines\n ok %d\n",
        "Maybe invalid %b specifier",
        "%f %% percent",
    ]

    assert all(stdformat.has_print_specifier(t) for t in TEST_CASES_VALID)

    TEST_CASES_INVALID = [
        "%%",
        "%%s",
        "%%s %%x %%d",
        "Ths one has nothing",
    ]

    assert not any(stdformat.has_print_specifier(t) for t in TEST_CASES_INVALID)


def test_struct_field_catches_missing_specifier():
    c_code = """
    // cmy:reflect
    typedef struct {
        // cmy:format("INVALID")
        int invalid;
    } InvalidStruct;
    """

    reflector = Reflector()
    reflector.load_plugins()

    generate_reflection(reflector, "test.h", c_code)
    reflector.resolve()

    try:
        _ = str(reflector)
        assert None
    except ValueError as e:
        err_str = str(e)

    assert (
        "Tag 'format' with value '\"INVALID\"' doesn't appear to have a format specifier."
    ) in err_str


def test_exports_format_specifiers():
    c_code = """
    // cmy:reflect
    typedef struct {
        int i;
    } my_struct_t;
    """

    dependent = Plugin("dep", depends_on=["format"])

    @dependent.setup
    def dep_setup(reflector):
        pass

    @dependent.function()
    def dep_func(reflector):
        print(reflector.plugin_data)
        exported_format_specifiers = reflector.get_plugin_data(
            "format.primitive_formats"
        )
        assert exported_format_specifiers == stdformat._PRIMITIVE_FORMATS

        exported_parse_specifiers = reflector.get_plugin_data(
            "format.primitive_parsers"
        )
        assert exported_parse_specifiers == stdformat._PRIMITIVE_PARSERS

        return "ReflectResult foo() { return REFLECT_OK; }"

    cmy_reflector.add_plugin(dependent)

    reflector = Reflector()
    reflector.load_plugins()

    generate_reflection(reflector, "test.h", c_code)
    reflector.resolve()

    content = str(reflector)

    assert "ReflectResult foo() { return REFLECT_OK; }" in content
