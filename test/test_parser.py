import re
import subprocess
from pathlib import Path

import pytest

import cmy_reflector
from cmy_reflector import Plugin, Reflector, generate_reflection, sort_plugins


@pytest.fixture(autouse=True)
def reset_plugin_registries():
    cmy_reflector._PLUGINS.clear()

    yield

    cmy_reflector._PLUGINS.clear()


def test_array_setter_generation(tmp_path: Path):
    """Tests that arrays correctly generate base types for the setter macros to avoid the sizeof() pointer bug."""

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    mock_header = src_dir / "test_struct.h"

    mock_header.write_text("""
    // cmy:reflect
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
    // cmy:reflect
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
    // cmy:reflect
    typedef struct {
        int public_1;

        int private_1; // cmy:private

        void* public_2;

        // cmy:private
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
    // cmy:reflect
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
    assert parsed_struct.name == "UglyStruct"

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
    // cmy:reflect
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
    // cmy:reflect
    typedef enum {
        VAL1,

        // cmy:private
        VAL2,

        VAL3, // cmy:private

        VAL4 = 4, // cmy:private

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
    // cmy:reflect
    // cmy:unchecked
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
    // cmy:reflect
    typedef struct
    {
        uint32_t count;

        // cmy:length(count)
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
    // cmy:reflect
    typedef struct
    {
        uint32_t count;

        // cmy:length(size)
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
    // cmy:reflect
    typedef struct
    {
        void* data;
    } super;

    // cmy:reflect
    typedef struct
    {
        a* aptr;

        size_t blen;
        b* dyn_arr; // cmy:length(blen)

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


def test_can_create_struct_field_tag():
    test_plugin = cmy_reflector.Plugin(name="test plugin")

    @test_plugin.setup
    def setup_description_hook(reflector):
        reflector.define_field_extension("description", "const char*")

    @test_plugin.struct_field_tag("description")
    def handle_field_description(reflector, struct, field, tag_value):
        reflector.set_field_extension(field, "description", tag_value)

    @test_plugin.emit_code
    def inject_desc_getter(reflector):
        return """
static inline const char* get_field_description(const FieldInfo* field)
{
    if (!field || !field->user_data) { return NULL; }
    return ((StructFieldExtension*)(field->user_data))->description;
}
"""

    cmy_reflector.add_plugin(test_plugin)

    c_code = """
    // cmy:reflect
    typedef struct
    {
        // cmy:description("cool")
        int stuff;
    } Options;
    """

    reflector = cmy_reflector.Reflector()
    cmy_reflector.generate_reflection(reflector, "test_enum.h", c_code)
    reflector.resolve()

    generated_content = str(reflector)

    assert "} StructFieldExtension;" in generated_content
    assert "const char* description" in generated_content

    assert (
        '{ "stuff", TYPE_INT, offsetof(Options, stuff), sizeof(int), 1, FIELD_ACCESS_RW, NULL, (void*)&ext_Options_stuff }'
        in generated_content
    )


def test_type_mapper_creates_guard_clause():
    test_plugin = cmy_reflector.Plugin(name="test plugin")

    @test_plugin.setup
    def setup_description_hook(reflector):
        pass

    @test_plugin.type_mapper(
        signature="void do_a(const void* a, FIELD_TYPE a)",
        switch_var="a",
        default_case="return;",
        guard_clause="if (!a) return;",
    )
    def type_mapper(reflector, type_name, type_enum, ctype, suffix):
        func_def = f"""
static inline void foo_{suffix}(const void* a)
{{
    (void)a;
    return;
}}
"""
        case_code = f"foo_{suffix}(a); return;"
        return (func_def, case_code)

    c_code = """
    // cmy:reflect
    typedef struct
    {
        type_a a;
        type_b b;
        type_c b;
    } types;
    """

    cmy_reflector.add_plugin(test_plugin)

    reflector = cmy_reflector.Reflector()
    cmy_reflector.generate_reflection(reflector, "test_enum.h", c_code)
    reflector.resolve()

    generated_content = str(reflector)
    assert "if (!a) return;" in generated_content


def test_helpers_work_as_expected():
    c_code = """
    // cmy:reflect
    // cmy:no_json
    typedef struct
    {
        int a;
        char b;
        unsigned long l;

        int* b;
    } StructA;


    // cmy:reflect
    // cmy:value_tag("hello")
    typedef struct
    {
        char* str;
        StructA* ptr;

        StructA arr[32];
        char buf[32];
    } StructB;

    // cmy:reflect
    // cmy:serialize
    typedef enum
    {
        TYPE_A,
    } Enum;
    """
    reflector = cmy_reflector.Reflector()
    cmy_reflector.generate_reflection(reflector, "test_enum.h", c_code)

    try:
        reflector.resolve()
    except ValueError:
        pass

    assert reflector.normalze_type_identifier("Enum") == "Enum"
    assert reflector.normalze_type_identifier("TYPE_ENUM_ENUM") == "Enum"
    assert reflector.normalze_type_identifier("TYPE_STRUCT_STRUCTB") == "StructB"
    assert reflector.normalze_type_identifier("TYPE_STRUCTA_ARR") == "StructA_arr"
    assert reflector.normalze_type_identifier("typex") == "typex"
    assert reflector.normalze_type_identifier("TYPE_STRUCTA_PTR") == "StructA*"
    assert reflector.normalze_type_identifier("TYPE_UNSIGNEDLONG") == "unsignedlong"

    assert reflector.has_struct_tag("StructA", "no_json")
    assert reflector.get_struct_tag("StructB", "value_tag") == '"hello"'
    assert reflector.has_enum_tag("Enum", "serialize")

    assert reflector.get_base_type_name("StructA*") == "StructA"
    assert reflector.get_base_type_name("TYPE_STRUCTA_PTR") == "StructA"
    assert reflector.get_base_type_name("TYPE_STRUCTA_ARR") == "StructA"
    assert reflector.get_base_type_name("TYPE_CHAR_ARR") == "char"

    assert reflector.is_enum("Enum")
    assert reflector.is_enum("TYPE_ENUM_ENUM")
    assert not reflector.is_struct("Enum")

    assert reflector.is_struct("StructA")
    assert reflector.is_struct("TYPE_STRUCT_STRUCTA")
    assert not reflector.is_enum("StructA")

    assert reflector.is_struct("StructB")
    assert reflector.is_struct("TYPE_STRUCT_STRUCTB")
    assert not reflector.is_enum("StructB")

    assert reflector.get_base_type_name("StructB") == "StructB"


def test_errors_on_undefined_member_tag():
    c_code = """
    // cmy:reflect
    // cmy:dne
    typedef enum {
        // cmy:t(1)
        s1,

        // cmy:t(2)
        s2,
    } State;
    """
    reflector = cmy_reflector.Reflector()
    cmy_reflector.generate_reflection(reflector, "test_enum.h", c_code)
    with pytest.raises(ValueError) as exc_info:
        reflector.resolve()

    error_msg = str(exc_info.value)

    assert "cmy:dne" in error_msg
    assert "cmy:t" in error_msg
    assert "State" in error_msg


def test_errors_on_tag_collision():
    p1 = Plugin("p1")
    p2 = Plugin("p2")

    @p1.type_tag("test")
    def p1_handle(reflector, struct, field, tag_value):
        pass

    @p2.type_tag("test")
    def p2_handle(reflector, struct, field, tag_value):
        pass

    cmy_reflector.add_plugin(p1)
    cmy_reflector.add_plugin(p2)

    c_code = """
    // cmy:reflect
    // cmy:test
    typedef struct
    {
        char* buf;
    } str_view;
    """

    reflector = Reflector()
    generate_reflection(reflector, "test.h", c_code)

    with pytest.raises(ValueError) as exc_info:
        reflector.resolve()

    error_msg = str(exc_info.value)

    assert (
        "- Tag collision: 'cmy:test' (Types) is claimed by 2 plugins: p1, p2."
    ) in error_msg


class MockPlugin:
    def __init__(self, name, depends_on=None):
        self.name = name
        self.depends_on = depends_on or []


def test_plugin_sort_alphabetical():
    p1 = MockPlugin("gamma")
    p2 = MockPlugin("alpha")
    p3 = MockPlugin("beta")

    result = sort_plugins([p1, p2, p3])
    names = [p.name for p in result]
    assert names == ["alpha", "beta", "gamma"]


def test_plugin_sort_dependency():
    p_a = MockPlugin("a", ["b"])
    p_b = MockPlugin("b", ["c"])
    p_c = MockPlugin("c")

    result = sort_plugins([p_a, p_b, p_c])
    names = [p.name for p in result]
    assert names == ["c", "b", "a"]


def test_plugin_sort_complex():
    p1 = MockPlugin("a", ["c", "b"])
    p2 = MockPlugin("b", ["d"])
    p3 = MockPlugin("c", ["e"])
    p4 = MockPlugin("d")
    p5 = MockPlugin("e")

    result = sort_plugins([p1, p2, p3, p4, p5])
    names = [p.name for p in result]
    assert names == ["d", "b", "e", "c", "a"]
