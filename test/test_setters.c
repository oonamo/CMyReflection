#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include "utils.h"
#include <stdlib.h>

#include "mocks/game_type.h"
#include "mocks/readme_example.h"
#include "mocks/generated.inc"

#define LOCAL_TGROUP SETTER
TEST_GROUP(SETTER);
#include "test_utils.h"

SETUP()
{
}

TEAR_DOWN()
{
}

T(Can_Use_Generated_Setter)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");

    bool success = set_field_float(&g, f, 18.0f) == REFLECT_OK;

    TEST_ASSERT_TRUE(success);
    TEST_ASSERT_EQUAL_FLOAT(18.0f, g.health);
}

T(Has_Type_Safety)
{
    Game g = {0};

    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "level");
    TEST_ASSERT_EQUAL(TYPE_INT, f->type);

    bool success = set_field_float(&g, f, 80.0f) == REFLECT_OK;

    TEST_ASSERT_FALSE(success);
    TEST_ASSERT_EQUAL_INT(0, g.level);
}

T(Is_Null_Safe)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");
    TEST_ASSERT_NOT_NULL(f);

    float val = 23.45f;

    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, set_field_value(NULL, f, &val, sizeof(float)));
    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, set_field_value(&g, NULL, &val, sizeof(float)));
    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, set_field_value(&g, f, NULL, sizeof(float)));
}

T(Is_Null_Safe_With_Type)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, set_field_float(&g, NULL, 23.7f));
}

T(Custom_Struct_Setter_Works)
{
    Game                   g       = {0};
    const StructFieldInfo *f       = find_field(Game_Metadata, Game_FieldCount, "player_pos");
    Vector2                new_pos = {.x = 100.0f, .y = 250.0f};

    TEST_ASSERT_EQUAL(REFLECT_OK, set_field_Vector2(&g, f, new_pos));
    TEST_ASSERT_EQUAL_FLOAT(100.0f, g.player_pos.x);
    TEST_ASSERT_EQUAL_FLOAT(250.0f, g.player_pos.y);
}

T(Respects_Struct_Padding)
{
    Game g  = {0};
    g.level = 23;

    // NOTE: level is right after health
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");
    set_field_float(&g, f, 50.0f);

    TEST_ASSERT_EQUAL_INT(23, g.level);
}

T(Can_Set_Nested_Struct_Field)
{
    Game g = {0};

    const StructFieldInfo *leaf = NULL;
    void                  *target_struct =
        resolve_field_path(&g, Game_Metadata, Game_FieldCount, "player_pos.x", &leaf);

    TEST_ASSERT_NOT_NULL(target_struct);
    TEST_ASSERT_NOT_NULL(leaf);
    TEST_ASSERT_EQUAL_STRING("x", leaf->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, leaf->type);

    TEST_ASSERT_TRUE(set_field_float(target_struct, leaf, 30.0f) == REFLECT_OK);
    TEST_ASSERT_EQUAL_FLOAT(30.0f, g.player_pos.x);
}

T(Set_FIeld_Fails_On_Type_MisMatch)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "score");

    TEST_ASSERT_FALSE(set_field_int(&g, f, 32) == REFLECT_OK);
    TEST_ASSERT_TRUE(g.score == 0);
}

T(Set_Array_Can_Write_Partial_Data)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "grid");

    uint8_t partial_write[2] = {23, 12};

    TEST_ASSERT_TRUE(set_field_u8_arr(&g, f, partial_write, 2) == REFLECT_OK);
    TEST_ASSERT_EQUAL_UINT8(23, g.grid[0]);
    TEST_ASSERT_EQUAL_UINT8(12, g.grid[1]);

    for (int i = 2; i < 9; i++)
    {
        TEST_ASSERT_EQUAL_UINT8(0, g.grid[i]);
    }
}

T(SafeSetField_Sets_Primitive_Correctly)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");

    float new_health = 712;
    TEST_ASSERT_TRUE(safe_set_field(&g, f, &new_health, 1) == REFLECT_OK);
    TEST_ASSERT_EQUAL_FLOAT(new_health, g.health);
}

T(SafeSetField_Sets_Arrays_Correctly)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "grid");

    uint8_t new_grid[9];
    for (int i = 0; i < 9; i++)
    {
        new_grid[i] = (i % 2) * 5;
    }

    TEST_ASSERT_TRUE(safe_set_field(&g, f, new_grid, 8) == REFLECT_OK);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(new_grid, g.grid, 9);
}

T(Does_Not_Corrupt_Adjacent_Fields_When_Setting)
{
    Game g = {0};

    g.score        = 1337;
    g.health       = 100.0f;
    g.level        = 32;
    g.ball.speed.x = 23.0f;
    g.ball.radius  = 40.0f;

    const StructFieldInfo *leaf = NULL;
    void                  *target_struct =
        resolve_field_path(&g, Game_Metadata, Game_FieldCount, "ball.radius", &leaf);

    TEST_ASSERT_NOT_NULL(target_struct);
    TEST_ASSERT_NOT_NULL(leaf);

    TEST_ASSERT_TRUE(set_field_float(target_struct, leaf, 88.5f) == REFLECT_OK);
    TEST_ASSERT_EQUAL_FLOAT(88.5f, g.ball.radius);
    TEST_ASSERT_EQUAL_INT(1337, g.score);
    TEST_ASSERT_EQUAL_FLOAT(100.0f, g.health);
    TEST_ASSERT_EQUAL_INT(32, g.level);
    TEST_ASSERT_EQUAL_FLOAT(23.0f, g.ball.speed.x);
}

T(ReadOnly_Tag_Prevent_Setters)
{
    Game g       = {0};
    g.game_flags = 2 << 1;

    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "game_flags");

    uint8_t new_flag = 1 << 1;

    TEST_ASSERT_EQUAL(REFLECT_ERR_ACCESS_DENIED, set_field_u8(&g, f, new_flag));

    uint8_t extracted = 0;
    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_u8(&g, f, &extracted));
    TEST_ASSERT_EQUAL_UINT8(2 << 1, extracted);
}

GROUP_RUNNER()
{
    RUN(Can_Use_Generated_Setter);
    RUN(Has_Type_Safety);
    RUN(Is_Null_Safe);
    RUN(Is_Null_Safe_With_Type);
    RUN(Custom_Struct_Setter_Works);
    RUN(Respects_Struct_Padding);
    RUN(Can_Set_Nested_Struct_Field);
    RUN(Set_FIeld_Fails_On_Type_MisMatch);
    RUN(Set_Array_Can_Write_Partial_Data);
    RUN(SafeSetField_Sets_Arrays_Correctly);
    RUN(SafeSetField_Sets_Primitive_Correctly);
    RUN(Does_Not_Corrupt_Adjacent_Fields_When_Setting);
    RUN(ReadOnly_Tag_Prevent_Setters);
}
