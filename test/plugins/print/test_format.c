#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include <stdlib.h>

#include "test_format_types.h"
#include <stdarg.h>

char   g_buf[1024];
size_t g_offset;

#include "format.generated.h"

TEST_GROUP(Print);

#define CLEAR_BUF(s) memset(s, 0, sizeof(s))

TEST_SETUP(Print)
{
}

TEST_TEAR_DOWN(Print)
{
}

TEST(Print, Formats_String_Types)
{
    StringType s    = {0};
    s.char_ptr      = "Pointer";
    s.constchar_ptr = "ConstPointer";

    strncpy(s.char_arr, "Array", sizeof(s.char_arr) - 1);
    strncpy(s.constchar_arr, "ConstArray", sizeof(s.constchar_arr) - 1);

    char buf[64];

    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(StringType), "char_ptr");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("Pointer", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(StringType), "constchar_ptr");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("ConstPointer", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(StringType), "char_arr");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("Array", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(StringType), "constchar_arr");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("ConstArray", buf);
    CLEAR_BUF(buf);
}

TEST(Print, Formats_Number_Types)
{
    NumTypes a = {
        .i  = -255,
        .ui = 255,

        .s  = -15,
        .us = 15,

        .l  = -65535,
        .ul = 65535,

        .c  = 'X',
        .uc = 12,

        .f = 3.142f,
        .d = 2.141,

        .u8  = 8,
        .u16 = 16,
        .u32 = 32,
        .u64 = 64,
        .i8  = -8,
        .i16 = -16,
        .i32 = -32,
        .i64 = -64,
    };

    char                   buf[64] = {0};
    const StructFieldInfo *f;

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "i");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("-255", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "ui");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("255", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "s");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("-15", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "us");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("15", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "l");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("-65535", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "ul");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("65535", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "c");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("X", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "uc");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("12", buf);
    CLEAR_BUF(buf);

    // Default C %f formatter prints 6 decimal places
    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "f");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("3.142000", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "d");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("2.141000", buf);
    CLEAR_BUF(buf);

    // Exact width integer tests
    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "u8");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("8", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "u16");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("16", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "u32");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("32", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "u64");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("64", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "i8");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("-8", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "i16");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("-16", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "i32");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("-32", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "i64");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&a, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("-64", buf);
    CLEAR_BUF(buf);
}

TEST(Print, Formats_Enums)
{
    MockStruct             s = {ENUM_A};
    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(MockStruct), "enum_type");

    char buf[64];

    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("ENUM_A", buf);
    CLEAR_BUF(buf);

    s.enum_type = ENUM_B;
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("ENUM_B", buf);
    CLEAR_BUF(buf);

    s.enum_type = ENUM_C;
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("ENUM_C", buf);
    CLEAR_BUF(buf);

    s.enum_type = ENUM_ERR;
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("Error Enum", buf);
    CLEAR_BUF(buf);
}

TEST(Print, Struct_Fields_Can_Have_Custom_Specifiers)
{
    Specified s = {
        .as_hex      = 0xab12ff,
        .with_prefix = "this test",
        .percent     = 75.8723f,
    };

    char buf[64];

    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(Specified), "as_hex");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("0xab12ff", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(Specified), "with_prefix");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("my str: this test", buf);
    CLEAR_BUF(buf);

    f = Find_Struct_Field(StructMetaData_FromName(Specified), "percent");
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_as_str(&s, f, buf, sizeof(buf)));
    TEST_ASSERT_EQUAL_STRING("75.87%", buf);
    CLEAR_BUF(buf);
}

TEST_GROUP_RUNNER(Print)
{
    RUN_TEST_CASE(Print, Formats_String_Types);
    RUN_TEST_CASE(Print, Formats_Number_Types);
    RUN_TEST_CASE(Print, Formats_Enums);
    RUN_TEST_CASE(Print, Struct_Fields_Can_Have_Custom_Specifiers);
}
