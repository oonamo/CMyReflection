#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>

#include "mocks/game_type.h"
#include "mocks/generated.inc"
#include "mocks/readme_example.h"

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

    TEST_ASSERT_FALSE(set_field_value(NULL, f, &val, sizeof(float)));
    TEST_ASSERT_FALSE(set_field_value(&g, NULL, &val, sizeof(float)));
    TEST_ASSERT_FALSE(set_field_value(&g, f, NULL, sizeof(float)));
}

TEST(Unit, Type_Set_Field_Is_Null_Safe)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_FALSE(set_field_float(&g, NULL, 23.7f));
}

TEST(Unit, String_Has_Alias)
{
    Game g = {0};
    const FieldInfo *f =
        find_field(Game_Metadata, Game_FieldCount, "player_name");

    TEST_ASSERT_TRUE(set_field_str(&g, f, "player1"));
    TEST_ASSERT_EQUAL_STRING("player1", g.player_name);
}

TEST(Unit, Metadata_Stores_Correct_Sizes)
{
    const FieldInfo *f_health =
        find_field(Game_Metadata, Game_FieldCount, "health");
    TEST_ASSERT_EQUAL(sizeof(float), f_health->size);

    const FieldInfo *f_pos =
        find_field(Game_Metadata, Game_FieldCount, "player_pos");
    TEST_ASSERT_EQUAL(sizeof(Vector2), f_pos->size);

    const FieldInfo *f_name =
        find_field(Game_Metadata, Game_FieldCount, "player_name");
    TEST_ASSERT_EQUAL(sizeof(char *), f_name->size);
}

TEST(Unit, Can_Generate_Array_Literals)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "grid");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_EQUAL(sizeof(g.grid), f->size);
    TEST_ASSERT_EQUAL(TYPE_UINT8_T_ARR, f->type);

    const FieldInfo *winstats =
        find_field(Game_Metadata, Game_FieldCount, "sliding_window");
    TEST_ASSERT_NOT_NULL(winstats);

    TEST_ASSERT_EQUAL(sizeof(g.sliding_window), winstats->size);
    TEST_ASSERT_EQUAL(TYPE_UNSIGNEDCHAR_ARR, winstats->type);
}

TEST(Unit, Can_Generate_Array_Macro)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "history");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_EQUAL(sizeof(g.history), f->size);
    TEST_ASSERT_EQUAL(TYPE_FLOAT_ARR, f->type);
}

TEST(Unit, Handles_Spaced_Types)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "score");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_EQUAL(TYPE_LONGLONG, f->type);
    TEST_ASSERT_TRUE(set_field_ll(&g, f, 2393));
}

TEST(Unit, Array_Setter_Copies_Memory)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "history");
    TEST_ASSERT_NOT_NULL(f);

    float new_history[MAX_ARR_LEN] = {0.0f};
    for (int i = 0; i < MAX_ARR_LEN; i++)
    {
        new_history[i] = i + (i * 0.8f);
    }
    printf("\nDEBUG: Write Size: %zu, Field Size: %zu\n",
           MAX_ARR_LEN * sizeof(float), f->size);
    printf("\n\nDEBUG: Expected Type: %d, Actual Type: %d\n", TYPE_FLOAT_ARR,
           f->type);
    printf("DEBUG: Expected Count: %d, Actual Count: %zu\n", MAX_ARR_LEN,
           f->count);
    TEST_ASSERT_TRUE(set_field_float_arr(&g, f, new_history, MAX_ARR_LEN));

    for (int i = 0; i < MAX_ARR_LEN; i++)
    {
        TEST_ASSERT_EQUAL_FLOAT(i + (i * 0.8f), g.history[i]);
    }
}

TEST(Unit, Array_Setter_Fails_On_OOB)
{
    Game g = {0};
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "history");

    float new_history[MAX_ARR_LEN + 4] = {0.0f};
    for (int i = 0; i < MAX_ARR_LEN + 4; i++)
    {
        new_history[i] = i;
    }

    TEST_ASSERT_FALSE(set_field_float_arr(&g, f, new_history, MAX_ARR_LEN + 4));
    TEST_ASSERT_TRUE(set_field_float_arr(&g, f, new_history, MAX_ARR_LEN));
}

TEST(Unit, Custom_Struct_Setter_Works)
{
    Game g = {0};
    const FieldInfo *f =
        find_field(Game_Metadata, Game_FieldCount, "player_pos");
    Vector2 new_pos = {.x = 100.0f, .y = 250.0f};

    TEST_ASSERT_TRUE(set_field_Vector2(&g, f, new_pos));
    TEST_ASSERT_EQUAL_FLOAT(100.0f, g.player_pos.x);
    TEST_ASSERT_EQUAL_FLOAT(250.0f, g.player_pos.y);
}

TEST(Unit, Setter_Respects_Struct_Padding)
{
    Game g = {0};
    g.level = 23;

    // NOTE: level is right after health
    const FieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");
    set_field_float(&g, f, 50.0f);

    TEST_ASSERT_EQUAL_INT(23, g.level);
}

TEST(Unit, Can_Set_Nested_Struct_Field)
{
    Game g = {0};

    const FieldInfo *leaf = NULL;
    void *target_struct = resolve_field_path(&g, Game_Metadata, Game_FieldCount,
                                             "player_pos.x", &leaf);

    TEST_ASSERT_NOT_NULL(target_struct);
    TEST_ASSERT_NOT_NULL(leaf);
    TEST_ASSERT_EQUAL_STRING("x", leaf->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, leaf->type);

    TEST_ASSERT_TRUE(set_field_float(target_struct, leaf, 30.0f));
    TEST_ASSERT_EQUAL_FLOAT(30.0f, g.player_pos.x);
}

TEST(Unit, Recursive_Lookup_Fails_On_Invalid_Path)
{
    Game g = {0};
    const FieldInfo *leaf = NULL;

    void *target1 = resolve_field_path(&g, Game_Metadata, Game_FieldCount,
                                       "health.xyz", &leaf);
    TEST_ASSERT_NULL(target1);

    void *target2 = resolve_field_path(&g, Game_Metadata, Game_FieldCount,
                                       "player_pos.z", &leaf);
    TEST_ASSERT_NULL(target2);
}

TEST(Unit, Can_Use_Indicies_On_Lookup)
{
    Game g = {0};

    g.enemy_positions[19].x = 18.32f;
    const FieldInfo *leaf = NULL;

    void *target_struct = resolve_field_path(&g, Game_Metadata, Game_FieldCount,
                                             "enemy_positions[19].x", &leaf);

    TEST_ASSERT_NOT_NULL(target_struct);
    TEST_ASSERT_NOT_NULL(leaf);
    TEST_ASSERT_EQUAL_STRING("x", leaf->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, leaf->type);

    Vector2 *target = (Vector2 *)target_struct;
    TEST_ASSERT_EQUAL(18.32, target->x);
    TEST_ASSERT_POINTERS_EQUAL(target, &g.enemy_positions[19]);
    TEST_ASSERT_TRUE(set_field_float(target_struct, leaf, 30.0f));
    TEST_ASSERT_EQUAL_FLOAT(30.0f, g.enemy_positions[19].x);
}

TEST(Unit, Lookup_Safely_Ignores_OOB)
{
    Game g = {0};

    const FieldInfo *leaf = NULL;
    void *target_struct = resolve_field_path(&g, Game_Metadata, Game_FieldCount,
                                             "enemy_positions[21].x", &leaf);
    TEST_ASSERT_NULL(target_struct);
    TEST_ASSERT_NULL(leaf);
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
    RUN_TEST_CASE(Unit, String_Has_Alias);
    RUN_TEST_CASE(Unit, Metadata_Stores_Correct_Sizes);
    RUN_TEST_CASE(Unit, Can_Generate_Array_Literals);
    RUN_TEST_CASE(Unit, Can_Generate_Array_Macro);
    RUN_TEST_CASE(Unit, Handles_Spaced_Types);
    RUN_TEST_CASE(Unit, Array_Setter_Copies_Memory);
    RUN_TEST_CASE(Unit, Array_Setter_Fails_On_OOB);
    RUN_TEST_CASE(Unit, Custom_Struct_Setter_Works);
    RUN_TEST_CASE(Unit, Setter_Respects_Struct_Padding);
    RUN_TEST_CASE(Unit, Can_Set_Nested_Struct_Field);
    RUN_TEST_CASE(Unit, Recursive_Lookup_Fails_On_Invalid_Path);
    RUN_TEST_CASE(Unit, Can_Use_Indicies_On_Lookup);
    RUN_TEST_CASE(Unit, Lookup_Safely_Ignores_OOB);
}
