#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include "utils.h"
#include <stdlib.h>

#include "mocks/game_type.h"
#include "mocks/readme_example.h"
#include "mocks/generated.inc"

#define LOCAL_TGROUP ENUM
TEST_GROUP(ENUM);
#include "test_utils.h"

SETUP()
{
}
TEAR_DOWN()
{
}

T(Can_Find_Enum_Member)
{
    const EnumMemberInfo *m =
        find_member(BallSize_Members, BallSize_MemberCount, "BALL_TYPE_SMALL");

    TEST_ASSERT_NOT_NULL(m);
    TEST_ASSERT_EQUAL_INT(BALL_TYPE_SMALL, m->value);
    TEST_ASSERT_EQUAL_STRING("BALL_TYPE_SMALL", m->name);
}

T(Fails_To_Find_Private_Member)
{
    TEST_ASSERT_NULL(find_member(BallSize_Members, BallSize_MemberCount, "BALL_TYPE_NONE"));
}

T(Fails_To_Find_Invalid_Member)
{
    TEST_ASSERT_NULL(find_member(BallSize_Members, BallSize_MemberCount, "BALL_TYPE_DNE"));
}

T(Can_Set_Enum_Member)
{
    Game g = {0};

    const StructFieldInfo *f = find_field(Ball_Metadata, Ball_FieldCount, "size");

    TEST_ASSERT_TRUE(set_field_BallSize(&g.ball, f, BALL_TYPE_SMALL) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(g.ball.size, BALL_TYPE_SMALL);

    TEST_ASSERT_TRUE(set_field_BallSize(&g.ball, f, BALL_TYPE_BIG) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(g.ball.size, BALL_TYPE_BIG);
}

T(SafeSetField_Sets_Enums_Correctly)
{
    Game g = {0};

    const StructFieldInfo *f = find_field(Ball_Metadata, Ball_FieldCount, "size");

    BallSize new_size = BALL_TYPE_MEDIUM;

    TEST_ASSERT_TRUE(safe_set_field(&g.ball, f, &new_size, 1) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(BALL_TYPE_MEDIUM, g.ball.size);
}

T(Can_Get_Enum_Metadata_From_Registry)
{
    EnumMetaData meta = {0};

    TEST_ASSERT_EQUAL(REFLECT_OK, get_enum_metadata(TYPE_ENUM_BALLSIZE, &meta));
    TEST_ASSERT_EQUAL_PTR(BallSize_Members, meta.members);
    TEST_ASSERT_EQUAL_size_t(BallSize_MemberCount, meta.count);

    TEST_ASSERT_EQUAL(REFLECT_ERR_ENUM_INVALID, get_enum_metadata(TYPE_INT, &meta));
}

T(CheckedEnum_Validates_Valid_Member)
{
    TEST_ASSERT_TRUE(is_valid_BallSize(BALL_TYPE_BIG));
}

T(CheckedEnum_InValidates_InValid_Member)
{
    TEST_ASSERT_FALSE(is_valid_BallSize(-1));
}

T(CheckedEnum_Accepts_Valid_Member)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Ball_Metadata, Ball_FieldCount, "size");

    TEST_ASSERT_TRUE(set_field_BallSize(&g.ball, f, BALL_TYPE_MEDIUM) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(BALL_TYPE_MEDIUM, g.ball.size);
}

T(CheckedEnum_Rejects_Invalid_Member)
{
    Game g                   = {0};
    g.ball.size              = BALL_TYPE_SMALL;
    const StructFieldInfo *f = find_field(Ball_Metadata, Ball_FieldCount, "size");

    TEST_ASSERT_FALSE(set_field_BallSize(&g.ball, f, (BallSize)-1) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(BALL_TYPE_SMALL, g.ball.size);
}

T(SafeSetField_Rejects_Invalid_Enum)
{
    Game g                   = {0};
    g.ball.size              = BALL_TYPE_SMALL;
    const StructFieldInfo *f = find_field(Ball_Metadata, Ball_FieldCount, "size");

    int bad_val = -23;

    TEST_ASSERT_FALSE(safe_set_field(&g.ball, f, &bad_val, 1) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(BALL_TYPE_SMALL, g.ball.size);
}

typedef enum
{
    FLAG_A = 1 << 0,
    FLAG_B = 1 << 1,
} bit_flags;

static inline bool check_sys_flags(bit_flags f)
{
    return f >= 1 && f <= (FLAG_A | FLAG_B);
}

DEFINE_ENUM_SETTER(bit_flags, 99, bit_flags, check_sys_flags);

T(CustomValidator_Accepts_And_Rejects_Correctly)
{
    StructFieldInfo custom_field = {"flags", 99, 0, sizeof(bit_flags), 1, FIELD_ACCESS_RW};
    bit_flags       flags        = 0;

    TEST_ASSERT_TRUE(set_field_bit_flags(&flags, &custom_field, FLAG_A | FLAG_B) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(FLAG_A | FLAG_B, flags);

    TEST_ASSERT_FALSE(set_field_bit_flags(&flags, &custom_field, 4) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(FLAG_A | FLAG_B, flags);
}

T(Can_Use_EnumMetaData_Macro)
{
    EnumMetaData md = EnumMetaData_FromName(BallSize);

    TEST_ASSERT_POINTERS_EQUAL(BallSize_Members, md.members);
    TEST_ASSERT_EQUAL_INT(BallSize_MemberCount, md.count);
}

T(Can_Use_Reverse_Lookup_For_Enum)
{
    TEST_ASSERT_EQUAL_STRING(
        "BALL_TYPE_SMALL",
        get_enum_member_name(BallSize_Members, BallSize_MemberCount, BALL_TYPE_SMALL));
}

T(Can_Use_Find_Enum_Macro)
{
    const EnumMemberInfo *f = Find_Enum_Member(EnumMetaData_FromName(BallSize), "BALL_TYPE_SMALL");

    TEST_ASSERT_NOT_NULL(f);
    TEST_ASSERT_EQUAL(BALL_TYPE_SMALL, f->value);
}

GROUP_RUNNER()
{
    RUN(Can_Find_Enum_Member);
    RUN(Fails_To_Find_Private_Member);
    RUN(Fails_To_Find_Invalid_Member);
    RUN(Can_Get_Enum_Metadata_From_Registry);
    RUN(SafeSetField_Sets_Enums_Correctly);
    RUN(Can_Set_Enum_Member);
    RUN(SafeSetField_Rejects_Invalid_Enum);
    RUN(CheckedEnum_Rejects_Invalid_Member);
    RUN(CheckedEnum_Validates_Valid_Member);
    RUN(CustomValidator_Accepts_And_Rejects_Correctly);
    RUN(Can_Use_EnumMetaData_Macro);
    RUN(Can_Use_Reverse_Lookup_For_Enum);
    RUN(Can_Use_Find_Enum_Macro);
    RUN(CheckedEnum_Accepts_Valid_Member);
    RUN(CheckedEnum_InValidates_InValid_Member);
}
