import sys
from pathlib import Path

import pytest

# test_json_plugin.py -> json/ -> plugins/ -> test/ -> ROOT
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from cmy_reflector import _PLUGINS, generate_reflection, Reflector
import plugins.print as printer


@pytest.fixture(autouse=True)
def reset_plugin_registries():
    global _PLUGINS
    original_plugins = _PLUGINS.copy()

    _PLUGINS = [
            printer.printer,
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

    assert all(printer.has_print_specifier(t) for t in TEST_CASES_VALID)

    TEST_CASES_INVALID = [
        "%%",
        "%%s",
        "%%s %%x %%d",
        "Ths one has nothing",
    ]

    assert not any(printer.has_print_specifier(t) for t in TEST_CASES_INVALID)


def test_struct_field_catches_missing_specifier():
    c_code = """
    // cmy:reflect
    typedef struct {
        // cmy:format("INVALID")
        int invalid;
    } InvalidStruct;
    """

    reflector = Reflector()
    generate_reflection(reflector, "test.h", c_code)
    reflector.resolve()

    try:
        generated_content = str(reflector)
        assert None
    except ValueError as e:
        err_str = str(e)

    assert (
        "Tag 'format' with value '\"INVALID\"' doesn't appear to have a format specifier."
    ) in err_str
