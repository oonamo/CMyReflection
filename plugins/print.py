import cmy_reflector

_PRIMITIVE_FORMATS = {
    "int": "%d",
    "float": "%f",
    "double": "%lf",
    "char": "%c",
    "char*": "%s",
    "const char*": "%s",
    "size_t": "%zu",
    "uint8_t": "%u",
    "uint16_t": "%u",
    "uint32_t": "%u",
    "uint64_t": "%llu",
}


@cmy_reflector.register_generator_hook
def register_format_plugin(reflector):
    reflector.register_extension("format", "const char*")
    return "// Using print plugin v0.0.0"


@cmy_reflector.register_field_tag("format")
def handle_field_format(struct, field, tag_value):
    field.plugin_data["format"] = tag_value


@cmy_reflector.register_type_mapper(
    signature="ReflectResult print_field(const void* instance, const FieldInfo* field)",
    switch_var="field->type",
    default_case="return REFLECT_ERR_TYPE_MISMATCH;",
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
    const char* fmt = (ext && ext->format) ? ext->format : "{default_fmt}";

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
