import cmy_reflector


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


@printer.type_tag("no_print")
def handle_no_print(reeflector, struct_or_enum, tag_value):
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
    func_name = f"get_field_{suffix}_as_str"
    case_def = f"return {func_name}(instance, field, out_buf, buflen);"
    val_setup = f"{ctype} val;"
    field_getter = f"get_field_{suffix}(instance, field, &val);"
    res_bad = "return res;"
    user_data = "const StructFieldExtension* ext = GET_FIELD_EXT(field);"
    snprintf_fmt = "snprintf(out_buf, buflen, fmt, val);"
    fmt = ""
    done = "return REFLECT_OK;"

    if not has_field_str_attribute(reflector, type_name):
        return

    if reflector.is_enum(type_name):
        enum = reflector.get_enum(type_name)
        user_data = f"""
    EnumMetaData meta = EnumMetaData_FromName({ctype});
    const char* enum_val = get_enum_member_name(meta.members, meta.count, val);
    const EnumMemberInfo* info = enum_val ? Find_Enum_Member(meta, enum_val) : NULL;
    const EnumMemberExtension* ext = GET_MEMBER_EXT(info);
"""
        fmt = 'const char* fmt = (ext && ext->display) ? ext->display : (enum_val ? enum_val : "<unknown>");'
        snprintf_fmt = 'snprintf(out_buf, buflen, "%s", fmt);'
    elif type_name not in _PRIMITIVE_FORMATS:
        if type_name == "bool":
            snprintf_fmt = 'snprintf(out_buf, buflen, "%s", val ? "true": "false");'
        elif type_name == "char_arr":
            val_setup = """\
                    char val[field->count];
"""
            field_getter = "get_field_char_arr(instance, field, val, field->count);"
            res_bad = """\
        return res;
"""
            fmt = 'const char* fmt = (ext && ext->format) ? ext->format : "%s";'
            snprintf_fmt = "snprintf(out_buf, buflen, fmt, val);"
        else:
            return
    else:
        fmt = f"const char* fmt = (ext && ext->format) ? ext->format : {_PRIMITIVE_FORMATS[type_name]};"

    lines = [
        f"static inline ReflectResult {func_name}(const void* instance, const StructFieldInfo* field, char* out_buf, size_t buflen) {{",
        "    if (!instance || !field) { return REFLECT_ERR_NULL_PTR; }",
        "",
        f"    {val_setup}",
        f"    ReflectResult res = {field_getter}",
        "    if (res != REFLECT_OK) {",
        f"        {res_bad}",
        "    }",
        f"    {user_data}",
        "    (void)ext; // Prevent unused variable warnings for bools",
        f"    {fmt}",
        f"    {snprintf_fmt}",
        "",
        f"    {done}",
        "}",
    ]
    func_def = "\n".join(lines) + "\n"
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
    get_field_as_str(instance, field, buf, sizeof(buf));
    printf("%s", buf);

    return REFLECT_OK;
}}
"""
    switch_case = f"return print_field_{suffix}(instance, field);"

    return (func_def, switch_case)


cmy_reflector.add_plugin(printer)
