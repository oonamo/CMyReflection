import cmy_reflector


def print_specifier(type: str) -> str:
    return f'"%" PRI{type}'


_PRIMITIVE_FORMATS = {
    "int": '"%d"',
    "float": '"%f"',
    "double": '"%lf"',
    "char": '"%c"',
    "char*": '"%s"',
    "const char*": '"%s"',
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


@cmy_reflector.register_plugin(
    name="Printer",
    version="0.0.0",
    maintainers=["oonamo"],
    description="Provides run time print_field routers, and @format() tag",
    includes=["<stdio.h>", "<stdlib.h>", "<inttypes.h>"],
    macros=["#define CMY_PLUGIN_PRINTER_ENABLED 1"],
)
def register_format_plugin(reflector):
    reflector.register_extension(
        "format", "const char*", requires="CMY_PLUGIN_PRINTER_ENABLED"
    )


@cmy_reflector.register_field_tag("format")
def handle_field_format(struct, field, tag_value):
    field.plugin_data["format"] = tag_value


@cmy_reflector.register_type_mapper(
    signature="ReflectResult print_field(const void* instance, const FieldInfo* field)",
    switch_var="field->type",
    default_case="return REFLECT_ERR_TYPE_MISMATCH;",
    requires="CMY_PLUGIN_PRINTER_ENABLED",
)
def handle_primitive_printers(type_name, type_enum, ctype, suffix):
    if type_name in _PRIMITIVE_FORMATS:
        default_fmt = _PRIMITIVE_FORMATS[type_name]

        func_def = f"""
static inline ReflectResult print_field_{suffix}(const void* instance, const FieldInfo* field) {{
    if (!instance || !field) {{ return REFLECT_ERR_NULL_PTR; }}

    {ctype} v;
    ReflectResult res = get_field_{suffix}(instance, field, &v);
    if (res != REFLECT_OK) {{ return res; }}

    const FieldExtensions* ext = (const FieldExtensions*)field->user_data;
    const char* fmt = (ext && ext->format) ? ext->format : {default_fmt};

    printf(fmt, v);
    return REFLECT_OK;
}}
"""
        case_code = f"return print_field_{suffix}(instance, field);"
        return (func_def, case_code)
    elif type_name == "bool":
        func_def = f"""
static inline ReflectResult print_field_{suffix}(const void* instance, const FieldInfo* field) {{
    if (!instance || !field) {{ return REFLECT_ERR_NULL_PTR; }}

    {ctype} v;
    ReflectResult res = get_field_{suffix}(instance, field, &v);
    if (res != REFLECT_OK) {{ return res; }}

    const FieldExtensions* ext = (const FieldExtensions*)field->user_data;
    const char* fmt = (ext && ext->format) ? ext->format : "%s";

    printf(fmt, v ? "true" : "false");
    return REFLECT_OK;
}}
"""
        case_code = f"return print_field_{suffix}(instance, field);"
        return (func_def, case_code)
    elif type_name == "char_arr":
        func_def = f"""\
static inline ReflectResult print_field_{suffix}(const void* instance, const FieldInfo* field) {{
    if (!instance || !field) {{ return REFLECT_ERR_NULL_PTR; }}

    char* val = (char*)malloc(field->size);
    if (!val) {{ return REFLECT_ERR_NULL_PTR; }} // Protect against allocation failure

    ReflectResult res = get_field_{suffix}(instance, field, val, field->count);
    if (res != REFLECT_OK) {{
        free(val); // Ensure memory is freed on error
        return res;
    }}

    const FieldExtensions* ext = (const FieldExtensions*)field->user_data;
    const char* fmt = (ext && ext->format) ? ext->format : "%s";

    printf(fmt, val);
    free(val);

    return REFLECT_OK;
}}
"""
        case_code = f"return print_field_{suffix}(instance, field);"
        return (func_def, case_code)
