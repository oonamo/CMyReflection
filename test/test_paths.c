#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include "utils.h"
#include <stdlib.h>

#include "mocks/game_type.h"
#include "mocks/readme_example.h"
#include "mocks/generated.inc"

#define LOCAL_TGROUP PATH
TEST_GROUP(PATH);

#include "test_utils.h"

SETUP()
{
}

TEAR_DOWN()
{
}

T(Recursive_Lookup_Fails_On_Invalid_Path)
{
    Game                   g    = {0};
    const StructFieldInfo *leaf = NULL;

    void *target1 = resolve_field_path(&g, Game_Metadata, Game_FieldCount, "health.xyz", &leaf);
    TEST_ASSERT_NULL(target1);

    void *target2 = resolve_field_path(&g, Game_Metadata, Game_FieldCount, "player_pos.z", &leaf);
    TEST_ASSERT_NULL(target2);
}

T(Can_Use_Indicies_On_Lookup)
{
    Game g = {0};

    g.enemy_positions[19].x     = 18.32f;
    const StructFieldInfo *leaf = NULL;

    void *target_struct =
        resolve_field_path(&g, Game_Metadata, Game_FieldCount, "enemy_positions[19].x", &leaf);

    TEST_ASSERT_NOT_NULL(target_struct);
    TEST_ASSERT_NOT_NULL(leaf);
    TEST_ASSERT_EQUAL_STRING("x", leaf->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, leaf->type);

    Vector2 *target = (Vector2 *)target_struct;
    TEST_ASSERT_EQUAL(18.32, target->x);
    TEST_ASSERT_POINTERS_EQUAL(target, &g.enemy_positions[19]);
    TEST_ASSERT_TRUE(set_field_float(target_struct, leaf, 30.0f) == REFLECT_OK);
    TEST_ASSERT_EQUAL_FLOAT(30.0f, g.enemy_positions[19].x);
}

T(Lookup_Safely_Ignores_OOB)
{
    Game g = {0};

    const StructFieldInfo *leaf = NULL;
    void                  *target_struct =
        resolve_field_path(&g, Game_Metadata, Game_FieldCount, "enemy_positions[21].x", &leaf);
    TEST_ASSERT_NULL(target_struct);
    TEST_ASSERT_NULL(leaf);
}

T(ResolveMetaData_Finds_Top_Level)
{
    const StructFieldInfo *f = resolve_field_metadata(Game_Metadata, Game_FieldCount, "health");

    TEST_ASSERT_NOT_NULL(f);
    TEST_ASSERT_EQUAL_STRING("health", f->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, f->type);
}

T(ResolveMetaData_Finds_Nested_Field)
{
    const StructFieldInfo *f =
        resolve_field_metadata(Game_Metadata, Game_FieldCount, "ball.speed.y");

    TEST_ASSERT_NOT_NULL(f);
    TEST_ASSERT_EQUAL_STRING("y", f->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, f->type);
}

T(ResolveMetadata_Handles_Valid_Array_Indices)
{
    const StructFieldInfo *f =
        resolve_field_metadata(Game_Metadata, Game_FieldCount, "enemy_positions[5].x");

    TEST_ASSERT_NOT_NULL(f);
    TEST_ASSERT_EQUAL_STRING("x", f->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, f->type);
}

T(ResolveMetadata_Rejects_Out_Of_Bounds_Indices)
{
    const StructFieldInfo *f =
        resolve_field_metadata(Game_Metadata, Game_FieldCount, "enemy_positions[9999].x");

    TEST_ASSERT_NULL(f);
}

T(ResolveMetadata_Fails_On_Invalid_Paths)
{
    TEST_ASSERT_NULL(resolve_field_metadata(Game_Metadata, Game_FieldCount, "fake_field"));
    TEST_ASSERT_NULL(resolve_field_metadata(Game_Metadata, Game_FieldCount, "ball.dne"));
    TEST_ASSERT_NULL(resolve_field_metadata(Game_Metadata, Game_FieldCount, "ball.speed.fake"));
}

T(ResolveMetadata_Is_Null_Safe)
{
    TEST_ASSERT_NULL(resolve_field_metadata(NULL, Game_FieldCount, "health"));
    TEST_ASSERT_NULL(resolve_field_metadata(Game_Metadata, Game_FieldCount, NULL));
}

T(ReflectQuery_Works_On_Top_Level)
{
    Game                   g    = {0};
    StructMetaData         meta = StructMetaData_FromName(Game);
    const StructFieldInfo *leaf = NULL;

    void *target = reflect_query(&g, &meta, "health", &leaf);

    TEST_ASSERT_NOT_NULL(target);
    TEST_ASSERT_POINTERS_EQUAL(&g, target);
    TEST_ASSERT_NOT_NULL(leaf);
    TEST_ASSERT_EQUAL_STRING("health", leaf->name);
}

T(ReflectQuery_Routes_Nested_Path)
{
    Game                   g    = {0};
    StructMetaData         meta = StructMetaData_FromName(Game);
    const StructFieldInfo *leaf = NULL;

    void *target = reflect_query(&g, &meta, "ball.speed.x", &leaf);

    TEST_ASSERT_NOT_NULL(target);
    TEST_ASSERT_POINTERS_EQUAL(&g.ball.speed, target);
    TEST_ASSERT_NOT_NULL(leaf);
    TEST_ASSERT_EQUAL_STRING("x", leaf->name);
}

T(ReflectQuery_Routes_Array_Paths)
{
    Game                   g    = {0};
    StructMetaData         meta = StructMetaData_FromName(Game);
    const StructFieldInfo *leaf = NULL;

    void *target = reflect_query(&g, &meta, "enemy_positions[5].y", &leaf);

    TEST_ASSERT_NOT_NULL(target);
    TEST_ASSERT_POINTERS_EQUAL(&g.enemy_positions[5], target);
    TEST_ASSERT_NOT_NULL(leaf);
    TEST_ASSERT_EQUAL_STRING("y", leaf->name);
}

T(ReflectQuery_Handles_Invalid_And_Nulls)
{
    Game                   g    = {0};
    StructMetaData         meta = StructMetaData_FromName(Game);
    const StructFieldInfo *leaf = NULL;

    TEST_ASSERT_NULL(reflect_query(&g, &meta, "invalid_field", &leaf));
    TEST_ASSERT_NULL(reflect_query(&g, &meta, "ball.dne", &leaf));
    TEST_ASSERT_NULL(reflect_query(NULL, &meta, "health", &leaf));
    TEST_ASSERT_NULL(reflect_query(&g, NULL, "health", &leaf));
    TEST_ASSERT_NULL(reflect_query(&g, &meta, NULL, &leaf));
    TEST_ASSERT_NULL(reflect_query(&g, &meta, "health", NULL));
}

T(Can_Get_Indice_Of_Struct)
{
#define TARGET_IDX 5

    Game g                        = {0};
    g.enemy_positions[TARGET_IDX] = (Vector2){1.0f, 2.0f};

    const StructFieldInfo *leaf = NULL;

    int   array_index = -1;
    void *ret         = resolve_field_path_ext(&g,
                                       Game_Metadata,
                                       Game_FieldCount,
                                       "enemy_positions[" TOSTRING(TARGET_IDX) "]",
                                       &leaf,
                                       &array_index);

    TEST_ASSERT_NOT_NULL(ret);
    TEST_ASSERT_NOT_NULL(leaf);
    TEST_ASSERT_EQUAL(TARGET_IDX, array_index);

    TEST_ASSERT_EQUAL(TYPE_VECTOR2_ARR, leaf->type);

    TEST_ASSERT_POINTERS_EQUAL(&g, ret);

    const StructFieldInfo *expected_field =
        Find_Struct_Field(StructMetaData_FromName(Game), "enemy_positions");

    TEST_ASSERT_POINTERS_EQUAL(expected_field, leaf);

    Vector2 ith = {0.0f, 0.0f};

    TEST_ASSERT_EQUAL(REFLECT_OK, get_field_Vector2_arr_elem(ret, leaf, &ith, array_index));
    TEST_ASSERT_EQUAL_FLOAT(1.0f, ith.x);
    TEST_ASSERT_EQUAL_FLOAT(2.0f, ith.y);

#undef TARGET_IDX
}

GROUP_RUNNER()
{
    RUN(ResolveMetaData_Finds_Top_Level);
    RUN(Recursive_Lookup_Fails_On_Invalid_Path);
    RUN(Can_Use_Indicies_On_Lookup);
    RUN(Lookup_Safely_Ignores_OOB);
    RUN(ResolveMetaData_Finds_Nested_Field);
    RUN(ResolveMetadata_Handles_Valid_Array_Indices);
    RUN(ResolveMetadata_Rejects_Out_Of_Bounds_Indices);
    RUN(ResolveMetadata_Fails_On_Invalid_Paths);
    RUN(ResolveMetadata_Is_Null_Safe);
    RUN(ReflectQuery_Works_On_Top_Level);
    RUN(ReflectQuery_Routes_Nested_Path);
    RUN(ReflectQuery_Routes_Array_Paths);
    RUN(ReflectQuery_Handles_Invalid_And_Nulls);
    RUN(Can_Get_Indice_Of_Struct);
}
