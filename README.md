# CMyReflection

A simple, 0-dependency, reflection framework for C99+

## Features
- **Registry** Look up nested structures through paths (gdb-like) `"my_struct_arr[2].x"`
- **Single Header** (`cmyreflection.h`)
- **Automatic code generation** with `cmy_reflector.py` that parses automatically parses annotations
- **Type Safety** Compile time definitions are created for runtime safety
- **Zero Allocation** Strictly uses stack or in-place objects

## Dependencies
- python3
- C99+ compiler

## Usage
### 1. Annotate Structs & Enums
```c
/// @reflect
typedef struct
{
    float voltage;
    float temp;
} SensorData;

/// @reflect
typedef enum
{
    DEVICE_RX,
    DEVICE_TX,
} DeviceState;

/// @reflect
typedef struct
{
    char        device_id[32];
    int         baud_rate;
    SensorData  data;
    DeviceState state;

    /// @readonly
    uint64_t uuid;
} IoTDevice;

/// @reflect
/// @unchecked
typedef enum
{
    MANAGER_NONE  = 1 << 0,
    MANAGER_READ  = 1 << 1,
    MANAGER_WRITE = 1 << 2,
} ManagerPermissions;

#define MAX_BUF_LEN 64

/// @reflect
typedef struct
{
    unsigned char      op_mode;

    /// @readonly
    ManagerPermissions permissions;

    char               device_location[MAX_BUF_LEN];
    IoTDevice          devices[8];
} DeviceManager;
```

### 2. Generate Reflection Data
```sh
python3 cmy_reflector.py ./src/ -o reflection.generated.h
```

### 3. Use in C Code
```c
#define CMYREFLECTION_IMPLEMENTATION // defines the CMyReflection implementation
#define REFLECTION_IMPLMENTATION // Defines the implementation for the generated header
#include "reflection.generated.h"

// ...
DeviceManager manager = {0};

const StructFieldInfo *leaf   = NULL;
void            *target = resolve_field_path(&manager,
                                  DeviceManager_Metadata,
                                  DeviceManager_FieldCount,
                                  "devices[2].data.voltage",
                                  &leaf);

if (target && leaf)
{
    // Safely inject data to manager->devices[2].data.voltage
    set_field_float(target, leaf, 240.5f);
}

const StructFieldInfo *location_field =
    find_field(DeviceManager_MetaData, DeviceManager_FieldCount, "device_location");
char *location = "bedroom1";

if (set_field_str(&manager, location_field, location) != REFLECT_OK)
{
    printf("Oops, forget that its a char arr!\n");

    // Ensures that the array has enough size to store the new string
    set_field_char_arr(&manager, location_field, location, strlen(location));
}
```

## CMake Integration
```cmake
find_package(Python3 REQUIRED COMPONENTS Interpreter)

file(GLOB_RECURSE SRC_FILES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.h")

add_custom_command(
    OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/reflection.generated.h"
    COMMAND Python3::Interpreter "${PROJECT_SOURCE_DIR}/cmy_reflector.py"
            "${CMAKE_CURRENT_SOURCE_DIR}" -o "${CMAKE_CURRENT_BINARY_DIR}/reflection.generated.h"
    DEPENDS "${PROJECT_SOURCE_DIR}/cmy_reflector.py" ${SRC_FILES}
    COMMENT "Generating C reflection metadata..."
)
```

## Annotations

> [!NOTE]
> Currently, *unions* and *nested structs* are not supported.

### @reflect
Placed before the typedef struct|enum definition
Instructs the parser to reflect the struct|enum definition

```c
/// @reflect
typedef struct
{
    int x;
} MyStruct;

// Creates:
// set_field_int()
// get_field_int()
// const StructFieldInfo MyStuct_Metadata[]
// const size_t MyStuct_FieldCount
// TYPE_STRUCT_MYSTRUCT
```

### @enum(NAME)
Placed before the typedef struct definition, after `@reflect`
Renames the type enum to be NAME

```c
/// @reflect
/// @enum(TYPE_U8_DYN_ARR)
typedef struct
{
    uint8_t* data;
    size_t len;
    size_t capacity;
} DynamicArrayU8;

// Creates
// TYPE_U8_DYN_ARR
```

### @private
Placed before the field, or after

```c
/// @reflect
typedef struct
{
    /// @private
    char data[256];
    uint32_t uuid32; /// @private

    int did_ack;
} recv_buffer_t;

// No field information is generated for data or uuid32
```

### @readonly
```c
/// @reflect
typedef struct
{
    char data[256];

    /// @readonly
    size_t attempts;
} send_buffer_t;

// set_field_size_t for field attempts is denied
```

### @writeonly
```c
/// @reflect
typedef struct
{
    /// @writeonly
    char* hash_str;
} hash;

// get_field_str for hash_str is denied
```

### @length
```c
/// @reflect
typedef struct
{
    size_t len;

    /// @length(len)
    void* buffer;
} mem_pool;

// Creates
// set_dynamic_mem_pool_buffer
// get_dynamic_mem_pool_buffer
```

### @unchecked
```c
/// @reflect
/// @unchecked
typedef enum
{
    HAS_A = 1 << 0,
    HAS_B = 1 << 1,
    HAS_C = HAS_A | HAS_B,
} flags;

// Removes:
// is_valid_flags()
// value checks on set_field_flags()
```

## Testing
Uses **Unity**

```sh
mkdir build
cmake -B build -S .
cmake --build build
ctest --test-dir build --output-on-failure
```
