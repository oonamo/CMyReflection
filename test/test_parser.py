import subprocess
from pathlib import Path

from cmy_reflector import Reflector, generate_reflection


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
        '{ "history", TYPE_FLOAT_ARR, offsetof(Game, history), sizeof(float[MAX_ARR_LEN]), MAX_ARR_LEN }'
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

    assert "Buf" in Reflector.TYPE_MAP

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

    fields = { f.name: f for f in parsed_struct.fields }

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
