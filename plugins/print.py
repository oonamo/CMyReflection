import cmy_reflector
from cmy_reflector import CBuilder, Reflector


def print_specifier(type: str) -> str:
    return f'"%" PRI{type}'


printer = cmy_reflector.Plugin(
    name="Printer",
    version="0.0.0",
    maintainers=["oonamo"],
    description="Provides run time printing for primitive types",
    includes=["<stdio.h>", "<stdlib.h>", "<inttypes.h>"],
    macros=["#define CMY_PLUGIN_PRINTER_ENABLED 1"],
)


@printer.setup
def setup(reflector):
    reflector.define_field_extension(
        "format", "const char*", requires="CMY_PLUGIN_PRINTER_ENABLED"
    )

    reflector.define_member_extension(
        "display", "const char*", requires="CMY_PLUGIN_PRINTER_ENABLED"
    )


@printer.struct_field_tag("format")
def handle_field_format(reflector, struct, field, tag_value):
    reflector.set_field_extension(field, "format", tag_value)


@printer.enum_member_tag("display")
def handle_member_format(reflector, enum, member, tag_value):
    reflector.set_member_extension(member, "display", tag_value)


@printer.enum_tag("no_print")
def handle_no_print(reflector, struct_or_enum, tag_value):
    pass


_PRIMITIVE_FORMATS = {
    "int": '"%d"',
    "float": '"%f"',
    "double": '"%lf"',
    "char": '"%c"',
    "char*": '"%s"',
    "const char*": '"%s"',
    "constchar*": '"%s"',
    "size_t": '"%zu"',
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
        cb.var("char", "var[field->count]"),
        cb.var(
            "ReflectResult",
            "res",
            cb.struct_field_getter(suffix, "var", array_len="field->count"),
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
        cb.check("!instance || !field", "return REFLECT_ERR_NULL_PTR;"),
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
    requires="CMY_PLUGIN_PRINTER_ENABLED",
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


@printer.type_mapper(
    signature="ReflectResult print_field(const void* instance, const StructFieldInfo* field)",
    switch_var="field->type",
    default_case="return REFLECT_ERR_TYPE_MISMATCH;",
    guard_clause="if (!field) { return REFLECT_ERR_NULL_PTR; }",
    requires="CMY_PLUGIN_PRINTER_ENABLED",
)
def handle_primitive_printers(
    reflector: cmy_reflector.Reflector, type_name, type_enum, ctype, suffix
):
    if not has_field_str_attribute(reflector, type_name):
        return

    if reflector.is_enum(type_name):
        enum = reflector.get_enum(type_name)
        if "no_print" in enum.tags:
            return

    func_def = f"""\
static inline ReflectResult print_field_{suffix}(const void* instance, const StructFieldInfo* field) {{
    if (!instance || !field) {{ return REFLECT_ERR_NULL_PTR; }}

    char buf[field->count > 256 ? field->count : 256];
    ReflectResult res = get_field_as_str(instance, field, buf, sizeof(buf));
    if (res != REFLECT_OK) {{
        return res;
    }}

    printf("%s", buf);
    return REFLECT_OK;
}}
"""
    switch_case = f"return print_field_{suffix}(instance, field);"

    return (func_def, switch_case)


cmy_reflector.add_plugin(printer)
