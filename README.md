# CMyReflection

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/oonamo/CMyReflection/tests.yml?style=flat-square)
![GitHub License](https://img.shields.io/github/license/oonamo/CMyReflection?style=flat-square)
![Memory Safety](https://img.shields.io/badge/Memory_Safety-ASAN_Tested-success?style=flat-square)
![Static Badge](https://img.shields.io/badge/C_Standard-99%2B-blue?style=flat-square&logo=C)
![Generator](https://img.shields.io/badge/Generator-Python_3.9+-blue?logo=python)
![Version](https://img.shields.io/github/v/tag/oonamo/CMyReflection?filter=v*&label=version)

A zero-overhead reflection and code-generation framework for C99+

## Features
- **Registry** Look up nested structures through paths (gdb-like) `"my_struct_arr[2].x"`
- **Optional Automatic code generation** with `cmy_reflector.py` that automatically parses annotations
- **Single Header** (`cmyreflection.h`)
- **Plugin System**
- **Type Safety** Compile time definitions are created for runtime safety
- **Zero Allocation** Strictly uses stack or in-place objects

> [!NOTE]
> **Current Limitations**: *unions* and *nested structs* are not supported.

## Dependencies
- C99+ compiler
- (Optional) python3 (Required for plugins and automatic code generation support)

*Ready to see examples? Ready to build [CMake](examples/cmake_example) and [Makefile](examples/make_example) are available.*

## Quick Start
Annotate your existing c code

### Your Code
```c
// player.h
// cmy:reflect
typedef struct
{
    int health;
    float speed;
} Player;

// main.c
#include <stdio.h>
#include "player.h"

// Define implementations in one file
#define CMYREFLECTION_IMPLEMENTATION
#define REFLECTION_IMPLEMENTATION
#include "refl.generated.h" // Your auto-generated metadata

int main(void) {
    Player p1 = {100, 10.0f};

    // Safely look up and modify a field using a string at runtime
    const StructFieldInfo* field = find_field(Player_Metadata, Player_FieldCount, "health");

    if (field) {
        set_field_int(&p1, field, 150);
        printf("Player health updated to %d\n", p1.health);
    }

    return 0;
}
```

### Build Step
```sh
python3 cmy_reflector.py --input player.h --output refl.generated.h
```

## Table of Contents
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [1. Annotate Structs & Enums](#1-annotate-structs--enums)
  - [2. Generate Reflection Data](#2-generate-reflection-data)
  - [3. Use in C Code](#3-use-in-c-code)
- [Examples](#examples)
- [Standard Tags](#standard-tags)
- [Standard Plugins](#standard-plugins)
- [Enabling Plugins](#enabling-plugins)
- [Testing](#testin

## Usage
### 1. Annotate Structs & Enums
```c
// cmy:reflect
typedef struct
{
    float voltage;
    float temp;
} SensorData;

// cmy:reflect
typedef enum
{
    DEVICE_RX,
    DEVICE_TX,
} DeviceState;

// cmy:reflect
typedef struct
{
    char        device_id[32];
    int         baud_rate;
    SensorData  data;
    DeviceState state;

    // cmy:readonly
    uint64_t uuid;
} IoTDevice;

// cmy:reflect
// cmy:unchecked
typedef enum
{
    MANAGER_NONE  = 1 << 0,
    MANAGER_READ  = 1 << 1,
    MANAGER_WRITE = 1 << 2,
} ManagerPermissions;

#define MAX_BUF_LEN 64

// cmy:reflect
typedef struct
{
    unsigned char      op_mode;

    // cmy:readonly
    ManagerPermissions permissions;

    char               device_location[MAX_BUF_LEN];
    IoTDevice          devices[8];
} DeviceManager;
```

### 2. Generate Reflection Data
```sh
# Recursively finds all *.h and *.c files in ./src
python cmy_reflector.py -i ./src/ -o reflection.generated.h
```

### 3. Use in C Code
```c
// 1. Include your type definitions first
#include "iot_device_types.h"

// 2. Define implementations in EXACTLY ONE source file
#define CMYREFLECTION_IMPLEMENTATION
#define REFLECTION_IMPLEMENTATION

// 3. Include the generated file last
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
    find_field(DeviceManager_Metadata, DeviceManager_FieldCount, "device_location");
char *location = "bedroom1";

if (set_field_str(&manager, location_field, location) != REFLECT_OK)
{
    printf("Oops, forget that its a char arr!\n");

    // Ensures that the array has enough size to store the new string
    set_field_char_arr(&manager, location_field, location, strlen(location));
}
```

## Examples
Ready to build, localized examples

- [CMake Integration Example](examples/cmake_example/)
- [Makefile Integration Example](examples/make_example)

## Standard Tags


### reflect
Placed before the typedef struct|enum definition
Instructs the parser to reflect the struct|enum definition

```c
// cmy:reflect
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

### enum(NAME)
Placed before the typedef struct definition, after `reflect`
Renames the type enum to be NAME

```c
// cmy:reflect
// cmy:enum(TYPE_U8_DYN_ARR)
typedef struct
{
    uint8_t* data;
    size_t len;
    size_t capacity;
} DynamicArrayU8;

// Creates
// TYPE_U8_DYN_ARR
```

### private
Placed before the field, or after

```c
// cmy:reflect
typedef struct
{
    // cmy:private
    char data[256];
    uint32_t uuid32; // cmy:private

    int did_ack;
} recv_buffer_t;

// No field information is generated for data or uuid32
```

### readonly
```c
// cmy:reflect
typedef struct
{
    char data[256];

    // cmy:readonly
    size_t attempts;
} send_buffer_t;

// set_field_size_t for field attempts is denied
```

### writeonly
```c
// cmy:reflect
typedef struct
{
    // cmy:writeonly
    char* hash_str;
} hash;

// get_field_str for hash_str is denied
```

### length
```c
// cmy:reflect
typedef struct
{
    size_t len;

    // cmy:length(len)
    void* buffer;
} mem_pool;

// Creates
// set_dynamic_mem_pool_buffer
// get_dynamic_mem_pool_buffer
```

### unchecked
```c
// cmy:reflect
// cmy:unchecked
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

## Standard Plugins

For detailed API usage, configuration macros, and tag documentation, see the [Plugin Documentation](plugins/README.md)

- **Format (`plugins/format.py`)**: Generate printing functions for types.
- **Json (`plugins/json.py`)**: Generates JSON serialization and schemas.

## Enabling Plugins
Enable plugins by passing `--plugin path/to/plugin1 path/to/plugin2` flag, or through the provided CMake integration:

```cmake
cmy_add_reflection(my_app
    INPUTS "src/types.h"
    OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/refl.generated.h"
    STD_PLUGINS json format
    PLUGINS "${PROJECT_SOURCE_DIR}/plugins/my_custom_plugin.py"
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
