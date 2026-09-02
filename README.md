# CMyReflection

A simple, reflection framework for C99+

## Features
- **Single Header** (`cmyreflection.h`)
- **Automatic code generation** with `cmy_reflector.py` that parses automatically parses annotations
- **Registry** Look up nested structures through paths (gdb-like) `"my_struct_arr[2].x"`
- **Type Safety** Compile time definitions are created for runtime safety
- **Zero Allocation** Strictly uses stack or in-place objects

## Dependencies
- python3
- C99+ compiler

## Usage
### 1. Annotate Structs
```c
/// @reflect
typedef struct
{
    float voltage;
    float temp;
} SensorData;

/// @reflect
typedef struct
{
    char device_id[32];
    int baud_rate;
    SensorData data;

    /// @private
    uint64_t uuid;
} IoTDevice;

#define MAX_BUF_LEN 64

/// @reflect
typedef struct
{
    char device_location[MAX_BUF_LEN];
    IoTDevice devices[8];
    unsigned char op_mode;
    uint32_t flags;
} DeviceManager;
```

### 2. Generate Reflection Data
```sh
python3 cmy_reflector.py ./src/ -o reflection.generated.h
```

### 3. Use in C Code
```c
#define CMYREFLECTION_IMPLEMENTATION
#define REFLECTION_IMPLMENTATION
#include "reflection.generated.h"

// ...
DeviceManager manager = {0};

const FieldInfo *leaf   = NULL;
void            *target = resolve_field_path(
    &manager, DeviceManager_MetaData,
    DeviceManager_FieldCount, "devices[2].data.voltage", &leaf);

if (target && leaf)
{
    // Safely inject data to manager->devices[2].data.voltage
    set_field_float(target, leaf, 240.5f);
}

const FieldInfo *name_field =
    find_field(DeviceManager_MetaData, DeviceManager_FieldCount, "device_location");
char *location = "bedroom1";

if (!set_field_str(&manager, name_field, location))
{
    printf("Oops, forget that its a char arr!\n");

    // Ensures that the array has enough size to store the new string
    set_field_char_arr(&manager, name_field, location, strlen(location));
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
## Testing
Uses **Unity**

```sh
mkdir build
cmake -B build -S .
cmake --build build
ctest --test-dir build --output-on-failure
```
