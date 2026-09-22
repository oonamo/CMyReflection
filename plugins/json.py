import cmy_reflector
from cmy_reflector import (
    CEnum,
    Macro,
    Plugin,
    Reflector,
)

# ----------------------------------------
# Plugin Configuration
# ----------------------------------------
PLUGIN_NAME = "json"
PLUGIN_VERSION = "0.0.1"
PLUGIN_MAINTAINERS = ["oonamo"]
PLUGIN_DESCRIPTION = "A json serializer plugin"

# Helpers for user's and authors to determine whether plugin is available
PLUGIN_DEFINE_MACRO = f"CMY_HAS_{PLUGIN_NAME.upper()}_PLUGIN"
PLUGIN_ENABLED_MACRO = f"CMY_PLUGIN_{PLUGIN_NAME.upper()}_ENABLED"

# Instantiate plugin
plugin = Plugin(
    name=PLUGIN_NAME,
    version=PLUGIN_VERSION,
    maintainers=PLUGIN_MAINTAINERS,
    description=PLUGIN_DESCRIPTION,
    includes=["<stdbool.h>", "<stdint.h>", "<stdarg.h>"],
    depends_on=["Printer"],
    macros=[
        Macro.define(PLUGIN_DEFINE_MACRO, "1", f"{PLUGIN_NAME} plugin is available"),
        Macro.default(PLUGIN_ENABLED_MACRO, "1", f"Enables the {PLUGIN_NAME} plugin"),
        Macro.default(
            "CMY_JSON_FMT_BUF_LEN",
            "256",
            "Buffer length to use for custom format strings",
        ),
        Macro.raw(
            "CMY_JSON_DEBUG",
            """\
#ifndef CMY_JSON_DEBUG
    #ifdef NDEBUG
        #define CMY_JSON_DEBUG 1
    #else
        #define CMY_JSON_DEBUG 0
    #endif
#endif
""",
            "Adds debug information during certain operations",
        ),
        Macro.define(
            "CMY_JSON_WRITE(state_ptr, ...)",
            "json_write_internal(state_ptr, __VA_ARGS__)",
            "Wrapper for json writing function",
        ),
    ],
)


# ----------------------------------------
# Setup & Extensions
# ----------------------------------------
@plugin.setup
def setup(reflector: Reflector):
    """Registers custom field extensions that will be added to the C extension structs"""
    reflector.define_field_extension(
        "json_key_name", "char*", requires=PLUGIN_ENABLED_MACRO
    )
    pass


# ----------------------------------------
# Tag Handlers
# ----------------------------------------
@plugin.enum_tag(
    "json_serialize_function",
    enforce_value=True,
    description="""Function to call to serialize this type
Example:
+  @json_serialize_function(MyCoolEnum_Serializer)
+  typedef enum { ... } MyCoolEnum;
+  // in a seperate file
+  #include "reflection.h"
+  void MyCoolEnum_Serializer(const void* instance, const StructFieldInfo* field, _cmy_json_state* state);
""",
)
def handle_enum_serialize_func(reflector: Reflector, enum: CEnum, tag_value: str):
    """Injects the value into the custom struct metadata"""
    pass


@plugin.struct_tag(
    "json_serialize_function",
    enforce_value=True,
    description="""Function to call to serialize this type
Example:
+  @json_serialize_function(MyCoolStruct_Serializer)
+  typedef struct { ... } MyCoolStruct;
+  // in a seperate file
+  #include "reflection.h"
+  void MyCoolStruct_Serializer(const void* instance, const StructFieldInfo* field, _cmy_json_state* state);
""",
)
def handle_struct_serialize_func(reflector: Reflector, enum: CEnum, tag_value: str):
    """Injects the value into the custom struct metadata"""
    pass


def validate_json_key_name(tag_name, tag_value) -> (bool, str):
    clean_value = tag_value.strip('"')
    return (
        len(clean_value) > 0,
        f"Tag '{tag_name}' requires a non-empty string: got '{tag_value}'",
    )


@plugin.struct_field_tag(
    "json_key_name",
    enforce_value=True,
    validator=validate_json_key_name,
    description="""Name of the json key
Example:
+  typedef struct
+  {
+      // cmy:json_key_name("new name")
+      char* old_name;
+  } MyType;
Result:
=  {
=      "new name": "TYPE_CHAR_PTR"
=  }
""",
)
def handle_json_key_name(reflector: Reflector, struct, field, tag_value):
    clean_value = tag_value.strip('"')
    clean_value = clean_value.replace('"', '\\"')
    c_string_literal = f'"{clean_value}"'

    reflector.set_field_extension(field, "json_key_name", c_string_literal)


# ----------------------------------------
# Type Mappers
# ----------------------------------------
@plugin.type_mapper(
    signature="ReflectResult json_serialize_custom(const void* exact_data_ptr, FIELD_TYPE actual_type, const StructFieldInfo* field_ctx, _cmy_json_state* state)",
    switch_var="actual_type",
    default_case="return REFLECT_ERR_TYPE_MISMATCH;",
    requires=PLUGIN_ENABLED_MACRO,
    description="Process fields dynamically based on their type",
)
def map_custom_serializer(
    reflector: Reflector, type_name: str, type_enum: str, ctype: str, suffix: str
) -> (str | None, str | None):
    item = reflector.get_struct(type_name) or reflector.get_enum(type_name)
    if not item:
        return None

    tag = item.tags.get("json_serialize_function")
    if not tag:
        return None

    custom_func = tag

    func_def = f"extern ReflectResult {custom_func}(const void* exact_data_ptr, FIELD_TYPE actual_type, const StructFieldInfo* field_ctx, _cmy_json_state* state);"
    case_def = f"return {custom_func}(exact_data_ptr, actual_type, field_ctx, state);"

    return (func_def, case_def)


@plugin.type_mapper(
    signature="bool json_is_string_type(FIELD_TYPE type)",
    switch_var="type",
    default_case="return false;",
    requires=PLUGIN_ENABLED_MACRO,
    description="Checks if a type represents a string",
)
def map_is_string(
    reflector: Reflector, type_name: str, type_enum: str, ctype: str, suffix: str
) -> (str | None, str | None):
    if type_name in ["char*", "constchar*", "char_arr", "constchar_arr"]:
        return (None, "return true;")
    return None


@plugin.type_mapper(
    signature="bool json_needs_quote(FIELD_TYPE type)",
    switch_var="type",
    default_case="return false;",
    requires=PLUGIN_ENABLED_MACRO,
    description="Dynamically determines if the type requires JSON quotes",
)
def map_needs_quote(
    reflector: Reflector, type_name: str, type_enum: str, ctype: str, suffix: str
) -> (str | None, str | None):
    needs_quotes = False

    if reflector.is_enum(type_name):
        needs_quotes = True
    elif type_name in ["char*", "constchar*", "char_arr", "constchar_arr"]:
        needs_quotes = True

    if needs_quotes:
        return (None, "return true;")

    return None


@plugin.type_mapper(
    signature="bool json_is_string_array(FIELD_TYPE type)",
    switch_var="type",
    default_case="return false;",
    requires=PLUGIN_ENABLED_MACRO,
    description="Determines if a type is an inline array",
)
def map_is_string_array(
    reflector: Reflector, type_name: str, type_enum: str, ctype: str, suffix: str
) -> (str | None, str | None):
    if type_name in ["char_arr", "constchar_arr"]:
        return (None, "return true;")
    return None


@plugin.emit_header
def create_struct(reflector: Reflector):
    return r"""
typedef void (*cmy_json_write_cb)(const char* chunk, size_t len, void* user_ctx);

typedef struct
{
    char* _buf;
    size_t _capacity;
    size_t _current_offset;

    int indent;
    bool is_first_field;
    FIELD_TYPE current_parent_type;

    cmy_json_write_cb write_cb;
    void* cb_ctx;
} _cmy_json_state;

typedef struct
{
    char* buf;
    size_t capacity;
    size_t offset;
} _cmy_json_fixedbuf_ctx;
""".strip()


# ----------------------------------------
# Standalone Functions
# ----------------------------------------
@plugin.function(
    requires=PLUGIN_ENABLED_MACRO, description="Serialize a value into valid json"
)
def json_serialize_value(reflector: Reflector) -> str:
    return r"""
static inline void json_serialize_value(const void* exact_data_ptr, FIELD_TYPE actual_type, const StructFieldInfo* field_ctx, _cmy_json_state* state)
{
    if (json_serialize_custom(exact_data_ptr, actual_type, field_ctx, state) == REFLECT_OK)
    {
        return;
    }

    StructMetaData meta;
    if (get_struct_metadata(actual_type, &meta) == REFLECT_OK) {
        CMY_JSON_WRITE(state, "{\n");

        _cmy_json_state nested_state = *state;
        nested_state.indent += 4;
        nested_state.is_first_field = true;
        nested_state.current_parent_type = actual_type;

        visit_struct_fields(exact_data_ptr, actual_type, _json_traversal_iterator, &nested_state);

        state->_current_offset = nested_state._current_offset;
        CMY_JSON_WRITE(state, "\n%*s}", state->indent, "");
        return;
    }

    if (exact_data_ptr && json_is_string_type(actual_type)) {
        const StructFieldExtension* ext = GET_FIELD_EXT(field_ctx);
        const char* fmt = (ext && ext->format) ? ext->format : "%s";

        StructFieldInfo element_field = {0};
        if (field_ctx) {
            element_field = *field_ctx;
            element_field.offset = 0;

            if (!json_is_string_array(actual_type)) {
                element_field.count = 0;
            }
        }

        // Default
        if (strcmp(fmt, "%s") == 0) {
            const char* str_ptr = NULL;

            // exact_data_ptr is ptr to static array
            if (json_is_string_array(actual_type)) {
                str_ptr = (const char*)exact_data_ptr;
            } else {
                get_field_value(exact_data_ptr, &element_field, (void*)&str_ptr, sizeof(const char*));
            }

            json_write_string_escaped(state, str_ptr);
        } else {
            char fmt_buf[CMY_JSON_FMT_BUF_LEN];
            if (field_ctx) {
                get_field_as_str(exact_data_ptr, &element_field, fmt_buf, sizeof(fmt_buf));
            }
            json_write_string_escaped(state, fmt_buf);
        }
        return;
    }

    char val_buf[256] = "null";
    bool force_quotes = false;
    bool is_explicit_null = false;

    if (exact_data_ptr) {
        StructFieldInfo element_field = *field_ctx;
        element_field.type = actual_type;
        element_field.offset = 0;

        if (!json_is_string_type(actual_type)) {
            element_field.count = 1;
        }

        if (get_field_as_str(exact_data_ptr, &element_field, val_buf, sizeof(val_buf)) != REFLECT_OK) {
#if CMY_JSON_DEBUG
            snprintf(val_buf, sizeof(val_buf), "<unsupported: %s at %p>", get_name_of_type(actual_type), exact_data_ptr);
#else
            snprintf(val_buf, sizeof(val_buf), "<unsupported: %s>", get_name_of_type(actual_type));
#endif
            force_quotes = true;
        }
        else if (strcmp(val_buf, "(null)") == 0) {
            snprintf(val_buf, sizeof(val_buf), "null");
            is_explicit_null = true;
        }
    } else {
        snprintf(val_buf, sizeof(val_buf), "%s", get_name_of_type(actual_type));
    }

    if (force_quotes || !exact_data_ptr || (json_needs_quote(actual_type) && !is_explicit_null)) {
        CMY_JSON_WRITE(state, "\"%s\"", val_buf);
    } else {
        CMY_JSON_WRITE(state, "%s", val_buf);
    }
}
"""


@plugin.function(requires=PLUGIN_ENABLED_MACRO, description="Internal Writing Function")
def json_write_internal(reflector: Reflector) -> str:
    return r"""
static inline void json_write_internal(_cmy_json_state* state, const char* fmt, ...)
{
    char scratch[128];

    va_list args;
    va_start(args, fmt);
    int written = vsnprintf(scratch, sizeof(scratch), fmt, args);
    va_end(args);

    if (written < 0) { return; }

    size_t len_to_write = ((size_t)written < sizeof(scratch)) ? (size_t)written : sizeof(scratch) - 1;

    state->write_cb(scratch, len_to_write, state->cb_ctx);
}
"""


@plugin.function(requires=PLUGIN_ENABLED_MACRO, description="Json Traversal serializer")
def json_traverse(reflector: Reflector) -> str:
    return r"""
static inline void _json_traversal_iterator(const void            *base_instance,
                             const StructFieldInfo  *field,
                             void                   *user_data)
{
    if (!field || !(field->flags & FIELD_ACCESS_READ)) { return; }

    _cmy_json_state *state = (_cmy_json_state*)user_data;
    if (!state->is_first_field) {
        CMY_JSON_WRITE(state, ",\n");
    } else {
        state->is_first_field = false;
    }

    // Print Key
    const StructFieldExtension* ext = GET_FIELD_EXT(field);
    const char* key = (ext && ext->json_key_name) ? ext->json_key_name : field->name;
    CMY_JSON_WRITE(state, "%*s\"%s\": ", state->indent, "", key);

    bool is_string = json_is_string_type(field->type);
    bool is_dynamic = field->length_field_name != NULL;
    bool is_arr = (is_dynamic || (field->count > 1)) && !is_string;

    if (is_arr) {
        if (!base_instance) {
            const char* type_name = get_name_of_type(get_base_type(field->type));
            if (is_dynamic) {
                CMY_JSON_WRITE(state, "[\"%s (dynamic: %s)\"]", type_name, field->length_field_name);
            } else if (is_arr) {
                CMY_JSON_WRITE(state, "[\"%s (max: %zu)\"]", type_name, field->count);
            }
            return;
        }

        size_t array_len = 0;
        const void* array_ptr = NULL;
        FIELD_TYPE base_type = get_base_type(field->type);
        size_t base_size = get_type_size(base_type);

        if (is_dynamic) {
            if (get_dynamic_array_length(base_instance, state->current_parent_type, field, &array_len) != REFLECT_OK) {
                CMY_JSON_WRITE(state, "null");
                return;
            }
            if (get_field_value(base_instance, field, (void*)&array_ptr, sizeof(void*)) != REFLECT_OK)
            {
                CMY_JSON_WRITE(state, "null");
                return;
            }
        } else {
            array_len = field->count;
            array_ptr = (const char*)base_instance + field->offset;
        }

        CMY_JSON_WRITE(state, "[\n");
        _cmy_json_state arr_state = *state;
        arr_state.indent += 4;

        for (size_t i = 0; i < array_len; i++)
        {
            CMY_JSON_WRITE(&arr_state, "%*s", arr_state.indent, "");
            void* ith_element = (char*)array_ptr + (i * base_size);

            if (!ith_element) {
                CMY_JSON_WRITE(&arr_state, "null");
            } else {
                json_serialize_value(ith_element, base_type, field, &arr_state);
            }

            if (i < array_len - 1) {
                CMY_JSON_WRITE(&arr_state, ",\n");
            } else {
                CMY_JSON_WRITE(&arr_state, "\n");
            }
        }
        state->_current_offset = arr_state._current_offset;
        CMY_JSON_WRITE(state, "%*s]", state->indent, "");

        return;
    } else {
        const void* data_ptr = base_instance ? ((const char*)base_instance + field->offset) : NULL;
        json_serialize_value(data_ptr, field->type, field, state);
    }
}
"""


@plugin.function(
    requires=PLUGIN_ENABLED_MACRO,
    description="Internal fixed buffer callback wrapper",
)
def json_fixedbuf_cb(reflector: Reflector) -> str:
    return r"""
static void _fixed_buf_write_cb(const char* chunk, size_t len, void* user_ctx)
{
    _cmy_json_fixedbuf_ctx* mem = (_cmy_json_fixedbuf_ctx*)user_ctx;

    size_t available = mem->capacity - mem->offset - 1;
    if (available == 0) return;

    size_t to_write = (len < available) ? len : available;

    memcpy(mem->buf + mem->offset, chunk, to_write);
    mem->offset += to_write;
}
"""


@plugin.function(
    requires=PLUGIN_ENABLED_MACRO, description="Safely escapes and streams strings"
)
def json_write_string_escaped(reflector: Reflector):
    return r"""
static inline void json_write_string_escaped(_cmy_json_state* state, const char* str)
{
    if (!str) {
        state->write_cb("null", 4, state->cb_ctx);
        return;
    }

    state->write_cb("\"", 1, state->cb_ctx);

    const char* p = str;
    while (*p) {
        switch(*p) {
            case '"':  state->write_cb("\\\"", 2, state->cb_ctx); break;
            case '\\': state->write_cb("\\\\", 2, state->cb_ctx); break;
            case '\b': state->write_cb("\\b",  2, state->cb_ctx); break;
            case '\f': state->write_cb("\\f",  2, state->cb_ctx); break;
            case '\n': state->write_cb("\\n",  2, state->cb_ctx); break;
            case '\r': state->write_cb("\\r",  2, state->cb_ctx); break;
            case '\t': state->write_cb("\\t", 2, state->cb_ctx); break;
            default:   state->write_cb(p, 1, state->cb_ctx); break;
        }
        p++;
    }

    state->write_cb("\"", 1, state->cb_ctx);
}
"""


@plugin.function(
    requires=PLUGIN_ENABLED_MACRO,
    description="Converts a given type to a json string (streamed)",
)
def to_json_stream(reflector: Reflector) -> str:
    return r"""
static inline ReflectResult to_json_stream(const void* instance, FIELD_TYPE root_type, cmy_json_write_cb write_cb, void* user_ctx)
{
    if (!write_cb) { return REFLECT_ERR_NULL_PTR; }

    _cmy_json_state state = {
        .indent = 0,
        .is_first_field = true,
        .current_parent_type = root_type,
        .write_cb = write_cb,
        .cb_ctx = user_ctx,
    };

    json_serialize_value(instance, root_type, NULL, &state);

    return REFLECT_OK;
}
"""


@plugin.function(
    requires=PLUGIN_ENABLED_MACRO,
    description="Converts a given type to a json string using a fixed buffer",
)
def to_json(reflector: Reflector) -> str:
    return r"""
static inline ReflectResult to_json(const void* instance, FIELD_TYPE root_type, char* out_buf, size_t buflen)
{
    if (!out_buf || buflen == 0) { return REFLECT_ERR_NULL_PTR; }

    _cmy_json_fixedbuf_ctx ctx = {
        .buf = out_buf,
        .capacity = buflen,
        .offset = 0
    };

    ReflectResult res = to_json_stream(instance, root_type, _fixed_buf_write_cb, &ctx);

    ctx.buf[ctx.offset] = '\0';

    return res;
}
"""


# ----------------------------------------
# Registration
# ----------------------------------------
cmy_reflector.add_plugin(plugin)
