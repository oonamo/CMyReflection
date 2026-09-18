import cmy_reflector
from cmy_reflector import CBuilder, Macro, Reflector

PLUGIN_NAME = "Printer"
PLUGIN_VERSION = "0.0.0"
PLUGIN_MAINTAINERS = ["oonamo"]
PLUGIN_DESCRIPTION = "Provides run time printing for primitive types"
PLUGIN_DEFINE_MACRO = f"CMY_HAS_{PLUGIN_NAME.upper()}_PLUGIN"
PLUGIN_ENABLED_MACRO = f"CMY_PLUGIN_{PLUGIN_NAME.upper()}_ENABLED"

PRINTER_MAX_BUF_LEN = "CMY_PRINTER_MAX_BUF_LEN"

printer = cmy_reflector.Plugin(
    name=PLUGIN_NAME,
    version=PLUGIN_VERSION,
    maintainers=PLUGIN_MAINTAINERS,
    description=PLUGIN_DESCRIPTION,
    includes=["<stdio.h>", "<stdlib.h>", "<inttypes.h>"],
    macros=[
        Macro.define(PLUGIN_DEFINE_MACRO, "1", f"{PLUGIN_NAME} plugin is available"),
        Macro.default(PLUGIN_ENABLED_MACRO, "1", f"Enables the {PLUGIN_NAME} plugin"),
        Macro.default(
            PRINTER_MAX_BUF_LEN,
            "256",
            "Default buffer len for printing (_MSC_VER)",
        ),
        Macro.default("CMY_PRINTF", "printf", "Defines the printf implementation"),
    ],
)


@printer.setup
def setup(reflector):
    reflector.define_field_extension(
        "format", "const char*", requires=PLUGIN_ENABLED_MACRO
    )

    reflector.define_member_extension(
        "display", "const char*", requires=PLUGIN_ENABLED_MACRO
    )


@printer.struct_field_tag(
    "format",
    enforce_value=True,
    description="""\
Specify a C format specifier for a struct.
Does not create a get_field_as_str function if not defined
Example:
+  @format("struct MyStruct @ addr: %p")
+  typedef struct { ... } MyStruct;
""",
)
def handle_field_format(reflector, struct, field, tag_value):
    reflector.set_field_extension(field, "format", tag_value)


@printer.enum_member_tag(
    "display",
    enforce_value=True,
    description="""\
Specifies how an enum should be displayed.
Defaults to name of the enum member if not provided
Example:
+  @display("enum a")
+  ENUM_A
""",
)
def handle_member_format(reflector, enum, member, tag_value):
    reflector.set_member_extension(member, "display", tag_value)


@printer.enum_tag(
    "no_print",
    description="Forces the plugin to not generate get_field_as_str for enum",
)
def handle_no_print(reflector, struct_or_enum, tag_value):
    pass


def q(s: str) -> str:
    return f'"{s}"'


def print_specifier(type: str) -> str:
    return f'"%" PRI{type}'


_PRIMITIVE_FORMATS = {
    "int": q("%d"),
    "unsignedint": q("%u"),
    "short": q("%hd"),
    "unsignedshort": q("%hu"),
    "long": q("%ld"),
    "unsignedlong": q("%lu"),
    "char": q("%c"),
    "unsignedchar": q("%hhu"),
    "float": q("%f"),
    "double": q("%lf"),
    "char*": q("%s"),
    "constchar*": q("%s"),
    "size_t": q("%zu"),
    "uint8_t": print_specifier("u8"),
    "uint16_t": print_specifier("u16"),
    "uint32_t": print_specifier("u32"),
    "uint64_t": print_specifier("u64"),
    "int8_t": print_specifier("d8"),
    "int16_t": print_specifier("d16"),
    "int32_t": print_specifier("d32"),
    "int64_t": print_specifier("d64"),
}


def has_field_str_attribute(reflector, type_name):
    if reflector.is_enum(type_name):
        return True
    if type_name in _PRIMITIVE_FORMATS:
        return True
    if type_name in ["bool", "char_arr"]:
        return True
    return False


def _generate_enum_str(
    reflector: Reflector, cb: CBuilder, type_name, type_enum, ctype, suffix
) -> list[str]:
    return [
        cb.check("!instance || !field", "return REFLECT_ERR_NULL_PTR;"),
        cb.var(ctype, "var"),
        cb.var("ReflectResult", "res", cb.struct_field_getter(suffix, "&var")).checked(
            "res != REFLECT_OK", "return res;"
        ),
        cb.var("EnumMetaData", "meta", cb.enum_metadata(type_name)).as_const(),
        cb.var(
            "char*",
            "enum_val",
            "get_enum_member_name(meta.members, meta.count, var)",
        ).as_const(),
        cb.var("EnumMemberInfo*", "info")
        .val_with_default("enum_val", "Find_Enum_Member(meta, enum_val)", "NULL")
        .as_const(),
        cb.var(
            "EnumMemberExtension*", "ext", cb.enum_member_extension("info")
        ).as_const(),
        "",
        cb.var("char*", "fmt")
        .val_with_default(
            "ext && ext->display", "ext->display", '(enum_val ? enum_val : "<unknown>")'
        )
        .as_const(),
        'snprintf(out_buf, buflen, "%s", fmt);',
        "return REFLECT_OK;",
    ]


def _generate_bool_str(
    reflector: Reflector, cb: CBuilder, type_name, type_enum, ctype, suffix
) -> list[str]:
    return [
        cb.check("!instance || !field", "return REFLECT_ERR_NULL_PTR;"),
        cb.var(ctype, "var"),
        cb.var("ReflectResult", "res", cb.struct_field_getter(suffix, "&var")).checked(
            "res != REFLECT_OK", "return res;"
        ),
        cb.var(
            "StructFieldExtension*", "ext", cb.struct_field_extension("field")
        ).as_const(),
        "(void)ext;",
        "",
        'snprintf(out_buf, buflen, "%s", var ? "true" : "false");',
        "return REFLECT_OK;",
    ]


def _generate_char_arr_str(
    reflector: Reflector, cb: CBuilder, type_name, type_enum, ctype, suffix
) -> list[str]:
    return [
        cb.check("!instance || !field", "return REFLECT_ERR_NULL_PTR;"),
        "#ifdef _MSC_VER",
        "    if (field->count > CMY_PRINTER_MAX_BUF_LEN) { return REFLECT_ERR_OUT_OF_BOUNDS; }",
        "    " + cb.var("char", "var[CMY_PRINTER_MAX_BUF_LEN];"),
        "#else",
        "    " + cb.var("char", "var[field->count]"),
        "#endif",
        cb.var("size_t", "arr_len", "field->count"),
        "",
        cb.var(
            "ReflectResult",
            "res",
            cb.struct_field_getter(suffix, "var", array_len="arr_len"),
        ).checked("res != REFLECT_OK", "return res;"),
        cb.var(
            "StructFieldExtension*", "ext", cb.struct_field_extension("field")
        ).as_const(),
        "",
        cb.var("char*", "fmt")
        .val_with_default("ext && ext->format", "ext->format", '"%s"')
        .as_const(),
        "snprintf(out_buf, buflen, fmt, var);",
        "return REFLECT_OK;",
    ]


def _generate_type_str(
    reflector: Reflector, cb: CBuilder, type_name, type_enum, ctype, suffix
) -> list[str]:
    default_fmt = _PRIMITIVE_FORMATS[type_name]
    return [
        "if (!instance || !field) { return REFLECT_ERR_NULL_PTR; }",
        "",
        cb.var(ctype, "var"),
        cb.var(
            "ReflectResult",
            "res",
            cb.struct_field_getter(suffix, "&var"),
        ).checked("res != REFLECT_OK", "return res;"),
        cb.var(
            "StructFieldExtension*", "ext", cb.struct_field_extension("field")
        ).as_const(),
        "",
        cb.var("char*", "fmt")
        .val_with_default("ext && ext->format", "ext->format", default_fmt)
        .as_const(),
        "snprintf(out_buf, buflen, fmt, var);",
        "return REFLECT_OK;",
    ]


def _generate_type_str(
    reflector: Reflector, cb: CBuilder, type_name, type_enum, ctype, suffix
) -> list[str]:
    default_fmt = _PRIMITIVE_FORMATS[type_name]
    return [
        "if (!instance || !field) { return REFLECT_ERR_NULL_PTR; }",
        "",
        cb.var(ctype, "var"),
        cb.var(
            "ReflectResult",
            "res",
            cb.struct_field_getter(suffix, "&var"),
        ).checked("res != REFLECT_OK", "return res;"),
        cb.var(
            "StructFieldExtension*", "ext", cb.struct_field_extension("field")
        ).as_const(),
        "",
        cb.var("char*", "fmt")
        .val_with_default("ext && ext->format", "ext->format", default_fmt)
        .as_const(),
        "snprintf(out_buf, buflen, fmt, var);",
        "return REFLECT_OK;",
    ]


@printer.type_mapper(
    signature="ReflectResult get_field_as_str(const void* instance, const StructFieldInfo* field, char* out_buf, size_t buflen)",
    switch_var="field->type",
    default_case="return REFLECT_ERR_TYPE_MISMATCH;",
    guard_clause="if (!field) { return REFLECT_ERR_NULL_PTR; }",
    requires=PLUGIN_ENABLED_MACRO,
    description="""\
Creates a get_type_as_str for the type for primitives and enums
By default, enums are enabled
""",
)
def handle_field_str(
    reflector: cmy_reflector.Reflector, type_name, type_enum, ctype, suffix
):
    if not has_field_str_attribute(reflector, type_name):
        return None
    builder = CBuilder(reflector)
    if reflector.is_enum(type_name):
        c_lines = _generate_enum_str(
            reflector, builder, type_name, type_enum, ctype, suffix
        )
    elif type_name == "bool":
        c_lines = _generate_bool_str(
            reflector, builder, type_name, type_enum, ctype, suffix
        )
    elif type_name == "char_arr":
        c_lines = _generate_char_arr_str(
            reflector, builder, type_name, type_enum, ctype, suffix
        )
    elif type_name in _PRIMITIVE_FORMATS:
        c_lines = _generate_type_str(
            reflector, builder, type_name, type_enum, ctype, suffix
        )
    else:
        return None

    if not c_lines:
        return None

    func_name = f"get_field_{suffix}_as_str"
    case_def = f"return {func_name}(instance, field, out_buf, buflen);"
    func_def = builder.build_func(
        signature=f"{func_name}(const void* instance, const StructFieldInfo* field, char* out_buf, size_t buflen)",
        retval="ReflectResult",
        body_lines=c_lines,
    )

    return (func_def, case_def)


@printer.function(
    requires=PLUGIN_ENABLED_MACRO,
    description="Prints a field, if it implements get_field_as_str",
)
def print_field(reflector):
    return """\
static inline ReflectResult print_field(const void* instance, const StructFieldInfo* field)
{
    if (!instance || !field) { return REFLECT_ERR_NULL_PTR; }

#ifdef _MSC_VER
    size_t buflen = CMY_PRINTER_MAX_BUF_LEN;
    char buf[CMY_PRINTER_MAX_BUF_LEN];
#else // May have VLA support
    size_t buflen = field->count > 256 ? field->count : 256;
    char buf[buflen];
#endif

    ReflectResult res = get_field_as_str(instance, field, buf, buflen);
    if (res != REFLECT_OK) {
        return res;
    }

    CMY_PRINTF("%s", buf);
    return REFLECT_OK;
}
"""

cmy_reflector.add_plugin(printer)
