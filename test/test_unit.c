#include <unity.h>
#include <unity_fixture.h>

#include "mocks/game_type.h"
#include "mocks/stuff.h"

#define CMYREFLECTION_IMPLEMENTATION
#define REFLECTION_IMPLEMENTATION
#include "mocks/generated.inc"

TEST_GROUP(Unit);

TEST_SETUP(Unit) {}

TEST_TEAR_DOWN(Unit) {}

TEST(Unit, Can_Find_Field)
{
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");

    TEST_ASSERT_NOT_NULL(f);
    TEST_ASSERT_EQUAL_STRING("health", f->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, f->type);

    TEST_ASSERT_EQUAL(offsetof(Game, health), f->offset);
}

TEST(Unit, Fails_To_Find_Invalid_Field)
{
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "dne");

    TEST_ASSERT_NULL(f);
}

TEST(Unit, Can_Use_Generated_Setter)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");

    bool success = set_field_float(&g, f, 18.0f);

    TEST_ASSERT_TRUE(success);
    TEST_ASSERT_EQUAL_FLOAT(18.0f, g.health);
}

TEST(Unit, Setter_Has_Type_Safety)
{
    Game g = {0};

    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "level");
    TEST_ASSERT_EQUAL(TYPE_INT, f->type);

    bool success = set_field_float(&g, f, 80.0f);

    TEST_ASSERT_FALSE(success);
    TEST_ASSERT_EQUAL_INT(0, g.level);
}

TEST(Unit, Private_Fields_Are_Ignored)
{
    Game g = {0};

    g.internal_count = 5;
    const FieldInfo *f1 =
        find_field(Game_Metadata, Game_FieldCount, "internal_count");
    TEST_ASSERT_NULL_MESSAGE(f1, "internal_count was exposed");

    g.userdata = (void *)"dummy str to check field exists";
    const FieldInfo *f2 =
        find_field(Game_Metadata, Game_FieldCount, "userdata");
    TEST_ASSERT_NULL_MESSAGE(f2, "userdata was exposed");
}

TEST(Unit, Set_Field_Is_Null_Safe)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");
    TEST_ASSERT_NOT_NULL(f);

    float val = 23.45f;

    TEST_ASSERT_FALSE(set_field_value(NULL, f, &val));
    TEST_ASSERT_FALSE(set_field_value(&g, NULL, &val));
    TEST_ASSERT_FALSE(set_field_value(&g, f, NULL));
}

TEST(Unit, Type_Set_Field_Is_Null_Safe)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_FALSE(set_field_float(&g, NULL, 23.7f));
}

TEST_GROUP_RUNNER(Unit)
{
    RUN_TEST_CASE(Unit, Can_Find_Field);
    RUN_TEST_CASE(Unit, Fails_To_Find_Invalid_Field);
    RUN_TEST_CASE(Unit, Can_Use_Generated_Setter);
    RUN_TEST_CASE(Unit, Setter_Has_Type_Safety);
    RUN_TEST_CASE(Unit, Private_Fields_Are_Ignored);
    RUN_TEST_CASE(Unit, Set_Field_Is_Null_Safe);
    RUN_TEST_CASE(Unit, Type_Set_Field_Is_Null_Safe);
}
