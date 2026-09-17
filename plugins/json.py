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
    includes=["<stdbool.h>", "<stdint.h>"],
    depends_on=["Printer"],
    macros=[
        Macro.define(PLUGIN_DEFINE_MACRO, "1", f"{PLUGIN_NAME} plugin is available"),
        Macro.default(PLUGIN_ENABLED_MACRO, "1", f"Enables the {PLUGIN_NAME} plugin"),
        # Add Custom Macros Here
        # Macro.raw, Macro.include, Macro.default, Macro.define,
    ],
)


# ----------------------------------------
# Setup & Extensions
# ----------------------------------------
@plugin.setup
def setup(reflector: Reflector):
    """Registers custom field extensions that will be added to the C extension structs"""
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
+  typedef enum { ... } MyCoolStruct;
+  // in a seperate file
+  #include "reflection.h"
+  void MyCoolStruct_Serializer(const void* instance, const StructFieldInfo* field, _cmy_json_state* state);
""",
)
def handle_struct_serialize_func(reflector: Reflector, enum: CEnum, tag_value: str):
    """Injects the value into the custom struct metadata"""
    pass


# ----------------------------------------
# Type Mappers
# ----------------------------------------
@plugin.type_mapper(
    signature="ReflectResult json_serialize_custom(const void* instance, const StructFieldInfo* field, _cmy_json_state* state)",
    guard_clause="if (!field) { return REFLECT_ERR_NULL_PTR; }",
    switch_var="field->type",
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

    func_def = f"extern ReflectResult {custom_func}(const void* instance, const StructFieldInfo* field, _cmy_json_state* state);"
    case_def = f"return {custom_func}(instance, field, state);"

    return (func_def, case_def)


@plugin.type_mapper(
    signature="bool json_needs_quote(FIELD_TYPE type)",
    switch_var="type",
    default_case="return false;",
    requires=PLUGIN_ENABLED_MACRO,
    description="Dynamically determines if the type requires JSON quotes",
)
def map_json_quotes(
    reflector: Reflector, type_name: str, type_enum: str, ctype: str, suffix: str
) -> (str | None, str | None):
    needs_quotes = False

    if reflector.is_enum(type_name):
        needs_quotes = True
    elif type_name in ["char*", "constchar*", "char_arr"]:
        needs_quotes = True

    if needs_quotes:
        return (None, "return true;")

    return None


@plugin.emit_header
def create_struct(reflector: Reflector):
    return r"""
typedef struct
{
    int indent;
    bool is_first_field;
    FIELD_TYPE current_parent_type;

    char* _buf;
    size_t _max_len;
    size_t _current_offset;
} _cmy_json_state;

#define CMY_JSON_WRITE(state_ptr, fmt, ...)                               \
        do {                                                              \
            if ((state_ptr)->_current_offset < (state_ptr)->_max_len) {   \
                (state_ptr)->_current_offset += snprintf(                 \
                    (state_ptr)->_buf + (state_ptr)->_current_offset,     \
                    (state_ptr)->_max_len - (state_ptr)->_current_offset, \
                    fmt, ##__VA_ARGS__);                                  \
            }                                                             \
        } while(0);
""".strip()


# ----------------------------------------
# Standalone Functions
# ----------------------------------------
@plugin.function(requires=PLUGIN_ENABLED_MACRO, description="Json Traversal serializer")
def json_traverse(reflector: Reflector) -> str:
    return r"""
void _json_traversal_iterator(const void            *base_instance,
                             const StructFieldInfo  *field,
                             void                   *user_data)
{
    if (!field || !(field->flags & FIELD_ACCESS_WRITE)) { return; }

    _cmy_json_state *state = (_cmy_json_state*)user_data;
    if (!state->is_first_field) {
        CMY_JSON_WRITE(state, ",\n");
    } else {
        state->is_first_field = false;
    }

    // Print Key
    CMY_JSON_WRITE(state, "%*s\"%s\": ", state->indent + 4, "", field->name);

    if (json_serialize_custom(base_instance, field, state) == REFLECT_OK)
    {
        return;
    }

    StructMetaData meta;

    // If is struct
    if (get_struct_metadata(field->type, &meta) == REFLECT_OK) {
        CMY_JSON_WRITE(state, "{\n");

        _cmy_json_state nested_state = *state;
        nested_state.indent += 4;
        nested_state.is_first_field = true;
        nested_state.current_parent_type = field->type;

        const void* nested_instance = base_instance ? ((const char*)base_instance + field->offset) : NULL;
        visit_struct_fields(nested_instance, field->type, _json_traversal_iterator, &nested_state);

        state->_current_offset = nested_state._current_offset;
        CMY_JSON_WRITE(state, "\n%*s}", state->indent + 4, "");
        return;
    }

    char val_buf[256] = "null";
    if (base_instance) {
        get_field_as_str(base_instance, field, val_buf, sizeof(val_buf));
    } else {
        snprintf(val_buf, sizeof(val_buf), "%s", get_name_of_type(field->type));
    }

    if (json_needs_quote(field->type)) {
        CMY_JSON_WRITE(state, "\"%s\"", val_buf);
    } else {
        CMY_JSON_WRITE(state, "%s", val_buf);
    }
}
"""


@plugin.function(
    requires=PLUGIN_ENABLED_MACRO,
    description="Converts a given type to a json string",
)
def to_json(reflector: Reflector) -> str:
    return r"""
static inline ReflectResult to_json(const void* instance, FIELD_TYPE root_type, char* out_buf, size_t buflen)
{
    if (!out_buf || buflen == 0) { return REFLECT_ERR_NULL_PTR; }
    _cmy_json_state state = {
        .indent = 0,
        .is_first_field = true,
        .current_parent_type = root_type,
        ._buf = out_buf,
        ._max_len = buflen,
        ._current_offset = 0,
    };

    CMY_JSON_WRITE(&state, "{\n");

    visit_struct_fields(instance, root_type, _json_traversal_iterator, &state);

    CMY_JSON_WRITE(&state, "\n}");

    return REFLECT_OK;
}
"""


# ----------------------------------------
# Registration
# ----------------------------------------
cmy_reflector.add_plugin(plugin)
