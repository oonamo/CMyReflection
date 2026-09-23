# CMyReflection plugins

Plugins hook into the reflection engine to automatically generate functions based on types.

## Json Plugin (`json.py`)
Provides functions for converting types into JSON
Requires the *Format* plugin

**[Json Example](../examples/json-serialize/)**

### Available Tags
*   **`json_serialize_function(FunctionName)`** (Structs & Enums)
    Overrides the default serializer with a custom one, for a type
    ```c
    // cmy:reflect
    // cmy:json_serialize_function(MyCoolStruct_Serializer)
    typedef struct { ... } MyCoolStruct;

    // In your C file:
    ReflectResult MyCoolStruct_Serializer(const void            *exact_data_ptr,
                                          FIELD_TYPE             actual_type,
                                          const StructFieldInfo *field_ctx,
                                          _cmy_json_state       *state);
    ```
*   **`json_key_name("name")`** (Structs Field)
    Overrides the JSON key name for a specific field
    ```c
    // cmy:reflect
    typedef struct {
        // cmy:json_key_name("new name")
        char* old_name;
    } MyType;
    ```

### Configuration Macros
You can define these macros before including the generated header to configure the plugin:

* `CMY_PLUGIN_JSON_ENABLED` - Set to `0` to disable the plugin (Default: `1`)
* `CMY_JSON_FMT_BUF_LEN` - Buffer length used for custom format strings (Default: `256`)
* `CMY_JSON_DEBUG` - Set to `1` to include debug information during serialization. Useful for catching serialization bugs. (Default: `0`)

*The plugin also provides `CMY_HAS_JSON_PLUGIN` so your C code can detect if the plugin ran.*

### Public API
```c
// Converts a given type to a JSON string using a fixed buffer
// Set instance to NULL for schema generation
ReflectResult to_json(const void* instance, FIELD_TYPE root_type, char* out_buf, size_t buflen);

// Callback function for streamed serialization
typedef void (*cmy_json_write_cb)(const char* chunk, size_t len, void* user_ctx);

// Converts a given type to a JSON string using a chunked stream callback
// Set instance to NULL for schema generation
ReflectResult to_json_stream(const void* instance, FIELD_TYPE root_type, cmy_json_write_cb write_cb, void* user_ctx);


// Serializes a raw value into valid JSON
void json_serialize_value(const void* exact_data_ptr, FIELD_TYPE actual_type, const StructFieldInfo* field_ctx, _cmy_json_state* state);
```

## Format Plugin (`format.py`)
Provides run time printing for primitive types and enums

### Available Tags
*    **`no_print`** (Enums)
    Prevents `get_field_as_str` from being generated for the enum.
    ```c
    // cmy:reflect
    // cmy:no_print
    typedef enum { ... } MyEnum;
    // get_field_MyEnum_as_str(...) is unimplemented
    ```

*   **`format(FormatString)`** (Struct Fields)
    Overrides the format string for the field
    ```c
    // cmy:reflect
    typedef struct {
        // cmy:format("as hex: %x")
        int x;
    } MyStruct;
    ```
*   **`display(DisplayName)`** (Enum Members)
    Defines how the enum member should be displayed
    Defaults to the name of the enum member
    ```c
    // cmy:reflect
    typedef enum {
        // cmy:display("enum a")
        ENUM_A,
    } MyEnum;
    ```
### Configuration Macros

* `CMY_PLUGIN_FORMAT_ENABLED` - Set to `0` to disable the plugin (Default: `1`)
* `CMY_FORMAT_MAX_BUF_LEN` - Buffer size to use for formatting (Default: `256`)
* `CMY_PRINTF` - `printf` implementation to use (Default: `printf`)

*The plugin also provides `CMY_HAS_FORMAT_PLUGIN` so your C code can detect if the plugin ran.*

### Public API
All get_field_* are considered as Public, but removed for brevity
```c
// Converts a field to a string, if implemented.
// Returns REFLECT_ERR_TYPE_MISMATCH if not implemented for the type
// Returns REFLECT_ERR_ACCESS_DENIED if the type does not provide read access
ReflectResult get_field_as_str(const void* instance, const StructFieldInfo* field, char* out_buf, size_t buflen);

// Print's the field using CMY_PRINTF
// Returns REFLECT_ERR_TYPE_MISMATCH if get_field_as_str is not implemented for the type
// Returns REFLECT_ERR_ACCESS_DENIED if the type does not provide read access
ReflectResult print_field(const void* instance, const StructFieldInfo* field);
```
