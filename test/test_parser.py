import re
import subprocess
from pathlib import Path

import pytest

import cmy_reflector
from cmy_reflector import Reflector, generate_reflection


@pytest.fixture(autouse=True)
def reset_plugin_registries():
    cmy_reflector._TYPE_TAG_HANDLERS.clear()
    cmy_reflector._FIELD_TAG_HANDLERS.clear()
    cmy_reflector._GENERATOR_HOOKS.clear()

    cmy_reflector._TYPE_MAPPERS.clear()

    yield

    cmy_reflector._TYPE_TAG_HANDLERS.clear()
    cmy_reflector._FIELD_TAG_HANDLERS.clear()
    cmy_reflector._GENERATOR_HOOKS.clear()
    cmy_reflector._TYPE_MAPPERS.clear()


def test_array_setter_generation(tmp_path: Path):
    """Tests that arrays correctly generate base types for the setter macros to avoid the sizeof() pointer bug."""

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    mock_header = src_dir / "test_struct.h"

    mock_header.write_text("""
    /// @reflect
    typedef struct {
        float history[MAX_ARR_LEN];
        int score;
    } Game;
    """)

    out_file = tmp_path / "generated.h"

    script_path = Path(__file__).parent.parent / "cmy_reflector.py"

    result = subprocess.run(
        ["python3", str(script_path), str(src_dir), "-o", str(out_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert out_file.exists(), "Output file was not generated"

    generated_content = out_file.read_text()

    assert "Game_FieldCount" in generated_content

    assert "TYPE_FLOAT_ARR" in generated_content

    assert (
        '{ "history", TYPE_FLOAT_ARR, offsetof(Game, history), sizeof(float[MAX_ARR_LEN]), MAX_ARR_LEN, FIELD_ACCESS_RW, NULL, NULL }'
        in generated_content
    )

    assert (
        "DEFINE_ARRAY_SETTER(float_arr, TYPE_FLOAT_ARR, float *, float)"
        in generated_content
    )

    assert "case TYPE_STRUCT_GAME:" in generated_content


def test_parses_char_arrays():
    c_code = """
    /// @reflect
    typedef struct {
        char buffer[64];
    } Buf;
    """

    ref = Reflector()
    generate_reflection(ref, "test.h", c_code)
    ref.resolve()

    assert "Buf" in ref.type_map

    buf_struct = ref.structs["Buf"]
    assert len(buf_struct.fields) == 1
    assert buf_struct.fields[0].name == "buffer"
    assert buf_struct.fields[0].type_name == "char"
    assert buf_struct.fields[0].type_enum == "TYPE_CHAR_ARR"
    assert buf_struct.fields[0].normalized_type_name == "char_arr"
    assert buf_struct.fields[0].array_bounds == "64"


def test_ignores_private_keys():
    c_code = """
    /// @reflect
    typedef struct {
        int public_1;

        int private_1; /// @private

        void* public_2;

        /// @private
        int private_2;

        unsigned int public_3;
    } PrivateStruct;
    """

    ref = Reflector()
    generate_reflection(ref, "test.h", c_code)
    ref.resolve()

    struct = ref.structs["PrivateStruct"]

    field_names = [f.name for f in struct.fields]

    assert len(field_names) == 3

    assert "public_1" in field_names
    assert "public_2" in field_names
    assert "public_3" in field_names

    assert "private_1" not in field_names
    assert "private_2" not in field_names


def test_parser_handles_bad_c_formatting():
    c_code = """
    /// @reflect
    typedef struct {
        int* type_attached;
        float *name_attached;
        char  *  detached;
        double array_spaced [ 5 ] ;
        unsigned int  *  ugly_combo  [ MAX_ARR ] ;
    } UglyStruct;
    """

    ref = Reflector()
    generate_reflection(ref, "test_spacing.h", c_code)
    ref.resolve()

    assert len(ref.structs) == 1
    parsed_struct = ref.structs["UglyStruct"]
    assert parsed_struct.struct_name == "UglyStruct"

    fields = {f.name: f for f in parsed_struct.fields}

    assert "type_attached" in fields
    assert fields["type_attached"].type_name.strip() == "int*"
    assert fields["type_attached"].array_bounds is None

    assert "name_attached" in fields
    assert fields["name_attached"].type_name.strip() == "float *"

    assert "detached" in fields
    assert fields["detached"].type_name.strip() == "char  *"

    assert "array_spaced" in fields
    assert fields["array_spaced"].type_name.strip() == "double"
    assert fields["array_spaced"].array_bounds.strip() == "5"

    assert "ugly_combo" in fields
    assert fields["ugly_combo"].type_name.strip() == "unsigned int  *"
    assert fields["ugly_combo"].array_bounds.strip() == "MAX_ARR"


def test_parser_generates_enum():
    c_code = """
    /// @reflect
    typedef enum {
        VALA,
        VALB,
        VALC
    } MyEnum;
    """

    ref = Reflector()
    generate_reflection(ref, "test.h", c_code)
    ref.resolve()

    assert "MyEnum" in ref.type_map
    assert "MyEnum" in ref.enums

    enum = ref.enums["MyEnum"]

    members = {m.name: m for m in enum.members}

    assert "VALA" in members
    assert "VALB" in members
    assert "VALC" in members


def test_parser_ignores_unreflected_enum():
    c_code = """
    typedef enum {
        VALA,
        VALB,
        VALC
    } MyEnum;
    """

    ref = Reflector()
    generate_reflection(ref, "test.h", c_code)
    ref.resolve()

    assert "MyEnum" not in ref.type_map
    assert "MyEnum" not in ref.enums


def test_parser_ignores_private_enum_fields():
    c_code = """
    /// @reflect
    typedef enum {
        VAL1,

        /// @private
        VAL2,

        VAL3, /// @private

        VAL4 = 4, /// @private

        VAL5
    } MyEnum;
    """

    ref = Reflector()
    generate_reflection(ref, "test.h", c_code)
    ref.resolve()

    assert "MyEnum" in ref.type_map
    assert "MyEnum" in ref.enums

    enum = ref.enums["MyEnum"]

    members = {m.name: m for m in enum.members}

    assert "VAL1" in members
    assert "VAL2" not in members
    assert "VAL3" not in members
    assert "VAL4" not in members
    assert "VAL5" in members


def test_parser_does_not_generate_validator_for_unchecked_enums(tmp_path: Path):
    c_code = """
    /// @reflect
    /// @unchecked
    typedef enum {
        VALA,
        VALB,
        VALC,
    } MyEnum;
    """

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    mock_header = src_dir / "test_enum.h"

    mock_header.write_text(c_code)

    out_file = tmp_path / "generated.h"

    script_path = Path(__file__).parent.parent / "cmy_reflector.py"

    result = subprocess.run(
        ["python3", str(script_path), str(src_dir), "-o", str(out_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert out_file.exists(), "Output file was not generated"

    generated_content = out_file.read_text()

    assert "MyEnum_Members" in generated_content
    assert "MyEnum_MemberCount" in generated_content

    assert "DEFINE_ENUM_SETTER" not in generated_content
    assert "DEFINE_FIELD_SETTER" in generated_content


def test_parser_extracts_length_tags():
    c_code = """\
    /// @reflect
    typedef struct
    {
        uint32_t count;

        /// @length(count)
        float* data;
    } Test;
    """

    ref = Reflector()
    generate_reflection(ref, "test.h", c_code)
    ref.resolve()

    assert "Test" in ref.type_map

    test = ref.structs["Test"]
    assert test is not None

    assert test.fields[0].name == "count"
    assert test.fields[1].name == "data"

    data = test.fields[1]
    assert "length" in data.tags

    assert data.tags["length"] == "count"


def test_parser_fails_on_invalid_length_field():
    c_code = """\
    /// @reflect
    typedef struct
    {
        uint32_t count;

        /// @length(size)
        float* data;
    } Test;
    """

    ref = Reflector()

    expected_err = "Error in struct 'Test': Field 'data' uses @length(size), but 'size' does not exist in the struct."
    with pytest.raises(ValueError, match=re.escape(expected_err)):
        generate_reflection(ref, "test.h", c_code)
        ref.resolve()


def test_parser_generates_correct_basetype(tmp_path: Path):
    c_code = """
    /// @reflect
    typedef struct
    {
        void* data;
    } super;

    /// @reflect
    typedef struct
    {
        a* aptr;

        size_t blen;
        b* dyn_arr; /// @length(blen)

        char* str;

        super* sptr;

        char buf[32];

        b** b_ref_ptr;

        unsigned int** x;
    } t;
    """

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    mock_header = src_dir / "test_enum.h"

    mock_header.write_text(c_code)

    out_file = tmp_path / "generated.h"

    script_path = Path(__file__).parent.parent / "cmy_reflector.py"

    result = subprocess.run(
        ["python3", str(script_path), str(src_dir), "-o", str(out_file)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert out_file.exists(), "Output file was not generated"

    generated_content = out_file.read_text()

    assert "case TYPE_A_PTR: return TYPE_A" in generated_content
    assert "case TYPE_B_PTR_PTR: return TYPE_B_PTR" in generated_content
    assert "case TYPE_B_PTR: return TYPE_B" in generated_content
    assert "case TYPE_CHAR_PTR: return TYPE_CHAR" in generated_content
    assert "case TYPE_CHAR_ARR: return TYPE_CHAR" in generated_content
    assert (
        "case TYPE_UNSIGNEDINT_PTR_PTR: return TYPE_UNSIGNEDINT_PTR"
        in generated_content
    )
    assert "case TYPE_UNSIGNEDINT_PTR: return TYPE_UNSIGNEDINT" in generated_content
    assert "case TYPE_SUPER_PTR: return TYPE_STRUCT_SUPER" in generated_content


def test_can_create_description_func(tmp_path: Path):
    @cmy_reflector.register_field_tag("description")
    def handle_description_tag(struct, field, tag_value):
        return f"""\
static inline char* get_{struct.struct_name}_{field.name}_description(void)
{{
    return "{tag_value}";
}}
"""

    c_code = """
    /// @reflect
    typedef struct
    {
        /// @description("process id")
        const int id;
    } x;
    """

    reflector = cmy_reflector.Reflector()
    cmy_reflector.generate_reflection(reflector, "test_enum.h", c_code)
    reflector.resolve()

    generated_content = str(reflector)

    assert "get_x_id_description" in generated_content


def test_generic_type_mapper():
    TYPES = {
        "int": "%d",
        "char*": "%s",
        "constchar*": "%s",
        "char_arr": "%s",
        "float": "%f",
        "double": "%f",
        "char": "%c",
    }

    @cmy_reflector.register_type_mapper(
        signature="ReflectResult print_field(const void* instance, const FieldInfo* field)",
        switch_var="field->type",
        default_case="return REFLECT_ERR_TYPE_MISMATCH;",
    )
    def handle_field_printer(type_name, type_enum, ctype, suffix):
        if type_name in TYPES:
            func_def = f"""\
static inline ReflectResult print_field_{suffix}(const void* instance, const FieldInfo* field) {{
    if (!instance || !field) {{ return REFLECT_ERR_NULL_PTR; }}
    {ctype} v;
    ReflectResult res = get_field_{ctype}(instance, field, &v);
    if (res != REFLECT_OK) {{ return res; }}

    printf("{TYPES[ctype]}", v);

    return REFLECT_OK;
}}
"""
            case_body = f"return print_field_{suffix}(instance, field);"
            return (func_def, case_body)
        return None

    c_code = """
    /// @reflect
    typedef struct
    {
        int i;
        char c;
        float f;
        double d;
        char* cptr;
        unknown x;
    } x;
    """

    reflector = cmy_reflector.Reflector()
    cmy_reflector.generate_reflection(reflector, "test_enum.h", c_code)
    reflector.resolve()

    generated_content = str(reflector)

    assert "print_field_int" in generated_content
    assert "print_field_char" in generated_content
    assert "print_field_str" in generated_content
    assert "print_field_float" in generated_content
    assert "print_field_unknown" not in generated_content

    assert "print_field" in generated_content


def test_can_set_enum_userdata():
    @cmy_reflector.register_enum_member_tag("color")
    def handle_enum_color(enum, member, tag_value):
        member.user_data_expr = f"(void*){tag_value}"

        return ""

    c_code = """
    /// @reflect
    typedef enum
    {
        /// @color(0x00FF00)
        STATE_OK,

        /// @color(0xFF0000)
        STATE_ERROR,
    } Status;
    """

    reflector = cmy_reflector.Reflector()
    cmy_reflector.generate_reflection(reflector, "test_enum.h", c_code)
    reflector.resolve()

    generated_content = str(reflector)

    assert '{ STATE_OK, "STATE_OK", (void*)0x00FF00 }' in generated_content
    assert '{ STATE_ERROR, "STATE_ERROR", (void*)0xFF0000 }' in generated_content


def test_can_set_stuct_userdata():
    @cmy_reflector.register_field_tag("description")
    def handle_field_description(struct, field, tag_value):
        field.user_data_expr = f"(void*){tag_value}"
        return f"// {struct.struct_name}"

    c_code = """
    /// @reflect
    typedef struct
    {
        /// @description("cool")
        int stuff;
    } Options;
    """

    reflector = cmy_reflector.Reflector()
    cmy_reflector.generate_reflection(reflector, "test_enum.h", c_code)
    reflector.resolve()

    generated_content = str(reflector)

    assert (
        '{ "stuff", TYPE_INT, offsetof(Options, stuff), sizeof(int), 1, FIELD_ACCESS_RW, NULL, (void*)"cool" }'
        in generated_content
    )
