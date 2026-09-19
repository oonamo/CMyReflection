#ifndef _TEST_PRINTER_TYPES_H
#define _TEST_PRINTER_TYPES_H

#include <stddef.h>
#include <stdint.h>

#define BUF_LEN 32

// cmy:reflect
typedef struct
{
    char *char_ptr;
    char  char_arr[BUF_LEN];

    const char *constchar_ptr;
    char        constchar_arr[BUF_LEN];
} StringType;

// cmy:reflect
typedef struct
{
    int          i;
    unsigned int ui;

    short          s;
    unsigned short us;

    long          l;
    unsigned long ul;

    char          c;
    unsigned char uc;

    float  f;
    double d;

    uint8_t  u8;
    uint16_t u16;
    uint32_t u32;
    uint64_t u64;

    int8_t  i8;
    int16_t i16;
    int32_t i32;
    int64_t i64;

    uint32_t private;
} NumTypes;

// cmy:reflect
typedef enum
{
    ENUM_A,
    ENUM_B,
    ENUM_C,

    // cmy:display("Error Enum")
    ENUM_ERR,
} EnumType;

// cmy:reflect
typedef struct
{
    EnumType enum_type;
} MockStruct;

// cmy:reflect
typedef struct
{
    // cmy:format("0x%x")
    int as_hex;

    // cmy:format("my str: %s")
    char *with_prefix;

    // cmy:format("%.2f%%")
    float percent;
} Specified;

#endif // _TEST_PRINTER_TYPES_H
