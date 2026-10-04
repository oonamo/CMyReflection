#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include <stdlib.h>

#include "test_format_types.h"
#include <stdarg.h>

char   g_buf[1024];
size_t g_offset;

#include "format.generated.h"

#define LOCAL_TGROUP FORMAT
TEST_GROUP(FORMAT);
#include "../../test_utils.h"

#define CLEAR_BUF(s) memset(s, 0, sizeof(s))

SETUP()
{
}

TEAR_DOWN()
{
}

T(Formats_String_Types)
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

T(Formats_Number_Types)
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

T(Formats_Enums)
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

T(Struct_Fields_Can_Have_Custom_Specifiers)
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

T(Can_Deserialize_Checked_Enums)
{
    char *enum_name = "ENUM_A";

    MockStruct m = {0};
    m.enum_type  = ENUM_B;

    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(MockStruct), "enum_type");

    OK(set_field_EnumType_from_str(&m, f, enum_name));

    TEST_ASSERT_EQUAL(ENUM_A, m.enum_type);
}

T(Can_Deserialize_UnChecked_Enums_With_Enum_Value)
{
    char      *enum_name = "C1";
    MockStruct m         = {0};
    m.unchecked          = C2;

    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(MockStruct), "unchecked");

    OK(set_field_EnumUnchecked_from_str(&m, f, enum_name));

    TEST_ASSERT_EQUAL(C1, m.unchecked);
}

T(Can_Deserialize_UnChecked_Enums_With_Integer)
{
    char      *enum_name = "23";
    MockStruct m         = {0};
    m.unchecked          = C2;

    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(MockStruct), "unchecked");

    OK(set_field_EnumUnchecked_from_str(&m, f, enum_name));

    TEST_ASSERT_EQUAL(23, m.unchecked);
}

T(Can_Deserialize_Bools)
{
    char      *true_str_lit = "true";
    MockStruct m            = {0};

    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(MockStruct), "works");

    OK(set_field_bool_from_str(&m, f, true_str_lit));
    TEST_ASSERT_EQUAL(true, m.works);

    char *false_str_lit = "false";
    OK(set_field_bool_from_str(&m, f, false_str_lit));
    TEST_ASSERT_EQUAL(false, m.works);

    char *true_str_int = "1";
    OK(set_field_bool_from_str(&m, f, true_str_int));
    TEST_ASSERT_EQUAL(true, m.works);
}

T(Can_Deserialize_chararr)
{
    char str[BUF_LEN] = "this is my buf";

    StringType s = {0};
    strncpy(s.char_arr, "This is my string", BUF_LEN);

    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(StringType), "char_arr");
    OK(set_field_char_arr_from_str(&s, f, str));
    TEST_ASSERT_EQUAL_STRING(str, s.char_arr);
}

T(Can_Deserialize_Types)
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

    const StructFieldInfo *f;

#define DO_TEST(field, value, setter, eq)                                                          \
    do                                                                                             \
    {                                                                                              \
        f = Find_Struct_Field(StructMetaData_FromName(NumTypes), #field);                          \
        OK(setter(&a, f, #value));                                                                 \
        eq(value, a.field);                                                                        \
    } while (0)

#define EQ TEST_ASSERT_EQUAL
#define FEQ TEST_ASSERT_EQUAL_FLOAT
#define CEQ TEST_ASSERT_EQUAL_CHAR
#define DEQ FEQ

    DO_TEST(i, -16, set_field_int_from_str, EQ);
    DO_TEST(ui, 312, set_field_uint_from_str, EQ);

    DO_TEST(s, -2, set_field_short_from_str, EQ);
    DO_TEST(us, 16, set_field_unsignedshort_from_str, EQ);

    DO_TEST(l, 213823, set_field_long_from_str, EQ);
    DO_TEST(ul, 7872323, set_field_unsignedlong_from_str, EQ);

    DO_TEST(c, 16, set_field_char_from_str, CEQ);
    DO_TEST(uc, 16, set_field_unsignedchar_from_str, EQ);

    f = Find_Struct_Field(StructMetaData_FromName(NumTypes), "f");
    OK(set_field_float_from_str(&a, f, "123.23"));
    TEST_ASSERT_EQUAL_FLOAT(123.23f, a.f);

    DO_TEST(d, 7461.3246321, set_field_double_from_str, DEQ);

    DO_TEST(u8, 12, set_field_u8_from_str, TEST_ASSERT_EQUAL_UINT8);
    DO_TEST(u16, 324, set_field_u16_from_str, TEST_ASSERT_EQUAL_UINT16);
    DO_TEST(u32, 2342, set_field_u32_from_str, TEST_ASSERT_EQUAL_UINT32);
    DO_TEST(u64, 35521, set_field_u64_from_str, TEST_ASSERT_EQUAL_UINT64);

    DO_TEST(i8, -24, set_field_int8_t_from_str, TEST_ASSERT_EQUAL_UINT8);
    DO_TEST(i16, 75, set_field_int16_t_from_str, TEST_ASSERT_EQUAL_UINT16);
    DO_TEST(i32, 123, set_field_int32_t_from_str, TEST_ASSERT_EQUAL_UINT32);
    DO_TEST(i64, -123, set_field_int64_t_from_str, TEST_ASSERT_EQUAL_UINT64);
}

GROUP_RUNNER()
{
    RUN(Formats_String_Types);
    RUN(Formats_Number_Types);
    RUN(Formats_Enums);
    RUN(Struct_Fields_Can_Have_Custom_Specifiers);
    RUN(Can_Deserialize_Checked_Enums);
    RUN(Can_Deserialize_UnChecked_Enums_With_Enum_Value);
    RUN(Can_Deserialize_UnChecked_Enums_With_Integer);
    RUN(Can_Deserialize_Bools);
    RUN(Can_Deserialize_chararr);
    RUN(Can_Deserialize_Types);
}
