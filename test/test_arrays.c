#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include "utils.h"
#include <stdlib.h>

#include "mocks/game_type.h"
#include "mocks/readme_example.h"
#include "mocks/generated.inc"

#define LOCAL_TGROUP ARRAY
TEST_GROUP(ARRAY);
#include "test_utils.h"

SETUP()
{
}

TEAR_DOWN()
{
}

T(Can_Generate_Array_Literals)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "grid");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_EQUAL(sizeof(g.grid), f->size);
    TEST_ASSERT_EQUAL(TYPE_UINT8_T_ARR, f->type);

    const StructFieldInfo *winstats = find_field(Game_Metadata, Game_FieldCount, "sliding_window");
    TEST_ASSERT_NOT_NULL(winstats);

    TEST_ASSERT_EQUAL(sizeof(g.sliding_window), winstats->size);
    TEST_ASSERT_EQUAL(TYPE_UNSIGNEDCHAR_ARR, winstats->type);
}

T(Can_Generate_Array_Macro)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "history");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_EQUAL(sizeof(g.history), f->size);
    TEST_ASSERT_EQUAL(TYPE_FLOAT_ARR, f->type);
}

T(Setter_Copies_Memory)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "history");
    TEST_ASSERT_NOT_NULL(f);

    float new_history[MAX_ARR_LEN] = {0.0f};
    for (int i = 0; i < MAX_ARR_LEN; i++)
    {
        new_history[i] = i + (i * 0.8f);
    }

    TEST_ASSERT_EQUAL(REFLECT_OK, set_field_float_arr(&g, f, new_history, MAX_ARR_LEN));
    for (int i = 0; i < MAX_ARR_LEN; i++)
    {
        TEST_ASSERT_EQUAL_FLOAT(i + (i * 0.8f), g.history[i]);
    }
}

T(Setter_Fails_On_OOB)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "history");

    float new_history[MAX_ARR_LEN + 4] = {0.0f};
    for (int i = 0; i < MAX_ARR_LEN + 4; i++)
    {
        new_history[i] = i;
    }

    TEST_ASSERT_EQUAL(REFLECT_ERR_OUT_OF_BOUNDS,
                      set_field_float_arr(&g, f, new_history, MAX_ARR_LEN + 4));
    TEST_ASSERT_EQUAL(REFLECT_OK, set_field_float_arr(&g, f, new_history, MAX_ARR_LEN));
}

T(GetArrayElement_Gets_Valid_Element)
{
    Game                   g = {0};
    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(Game), "grid");

    for (int i = 0; i < 9; i++)
    {
        g.grid[i] = i;
    }

    for (int i = 0; i < 9; i++)
    {
        uint8_t res = 0;
        TEST_ASSERT_EQUAL(REFLECT_OK, get_array_element(&g, f, i, &res, sizeof(uint8_t)));
        TEST_ASSERT_EQUAL_UINT8(i, res);
    }
}

T(GetArrayElement_Gets_Struct)
{
    Game g = {0};

    g.enemy_positions[2].x = 45.0f;
    g.enemy_positions[2].y = 45.0f;

    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(Game), "enemy_positions");

    Vector2 out_vec = {0};
    TEST_ASSERT_EQUAL(REFLECT_OK, get_array_element(&g, f, 2, &out_vec, sizeof(Vector2)));
    TEST_ASSERT_EQUAL_FLOAT(45.0f, out_vec.x);
    TEST_ASSERT_EQUAL_FLOAT(45.0f, out_vec.y);
}

T(GetArrayElement_Rejects_OutOfBounds_Index)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "grid");

    uint8_t out_val = 0;
    TEST_ASSERT_EQUAL(REFLECT_ERR_OUT_OF_BOUNDS,
                      get_array_element(&g, f, 9, &out_val, sizeof(uint8_t)));
    TEST_ASSERT_EQUAL(REFLECT_ERR_OUT_OF_BOUNDS,
                      get_array_element(&g, f, 999, &out_val, sizeof(uint8_t)));
}

T(GetArrayElement_Rejects_Size_Mismatch)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "history"); // float array

    double out_val = 0;
    TEST_ASSERT_EQUAL(REFLECT_ERR_TYPE_MISMATCH,
                      get_array_element(&g, f, 0, &out_val, sizeof(double)));
}

T(GetArrayElement_Is_Null_Safe)
{
    Game                   g       = {0};
    const StructFieldInfo *f       = find_field(Game_Metadata, Game_FieldCount, "grid");
    uint8_t                out_val = 0;

    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR,
                      get_array_element(NULL, f, 0, &out_val, sizeof(uint8_t)));
    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR,
                      get_array_element(&g, NULL, 0, &out_val, sizeof(uint8_t)));
    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, get_array_element(&g, f, 0, NULL, sizeof(uint8_t)));
}

T(DynamicArray_Allows_Valid_Set_Get)
{
    Game g          = {0};
    g.num_waypoints = 3;
    g.waypoints     = malloc(sizeof(Vector2) * g.num_waypoints);

    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "waypoints");
    TEST_ASSERT_NOT_NULL(f);
    Vector2 new_waypoints[3] = {
        {1.0f, 1.0f},
        {2.0f, 2.0f},
        {3.0f, 3.0f},
    };

    TEST_ASSERT_EQUAL(REFLECT_OK, set_dynamic_Game_waypoints(&g, f, new_waypoints, 3));

    Vector2 read_buf[2] = {0};
    TEST_ASSERT_EQUAL(REFLECT_OK, get_dynamic_Game_waypoints(&g, f, read_buf, 2));

    TEST_ASSERT_EQUAL_FLOAT(1.0f, read_buf[0].x);
    TEST_ASSERT_EQUAL_FLOAT(1.0f, read_buf[0].y);

    TEST_ASSERT_EQUAL_FLOAT(2.0f, read_buf[1].x);
    TEST_ASSERT_EQUAL_FLOAT(2.0f, read_buf[1].y);

    free(g.waypoints);
}

T(DynamicArray_Rejects_OutOfBounds)
{
    Game g          = {0};
    g.num_waypoints = 2;
    g.waypoints     = malloc(g.num_waypoints * sizeof(Vector2));

    const StructFieldInfo *f          = find_field(Game_Metadata, Game_FieldCount, "waypoints");
    Vector2                payload[3] = {0};

    TEST_ASSERT_EQUAL(REFLECT_ERR_OUT_OF_BOUNDS, set_dynamic_Game_waypoints(&g, f, payload, 3));

    free(g.waypoints);
}

T(DynamicArray_Is_Null_Safe)
{
    Game g          = {0};
    g.num_waypoints = 5;
    g.waypoints     = NULL;

    const StructFieldInfo *f          = find_field(Game_Metadata, Game_FieldCount, "waypoints");
    Vector2                payload[1] = {0};

    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, set_dynamic_Game_waypoints(&g, f, payload, 1));
    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, set_dynamic_Game_waypoints(NULL, f, payload, 1));
    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, set_dynamic_Game_waypoints(&g, NULL, payload, 1));
}

T(DynamicArray_Rejects_Type_Mismatch)
{
    Game game          = {0};
    game.num_waypoints = 5;
    game.waypoints     = malloc(5 * sizeof(Vector2));

    const StructFieldInfo *wrong_field =
        find_field(Game_Metadata, Game_FieldCount, "num_waypoints");
    Vector2 payload[1] = {0};

    TEST_ASSERT_EQUAL(REFLECT_ERR_TYPE_MISMATCH,
                      set_dynamic_Game_waypoints(&game, wrong_field, payload, 1));

    free(game.waypoints);
}

T(DynamicArray_Handles_Zero_Length)
{
    Game game          = {0};
    game.num_waypoints = 0; // Length is explicitly 0
    game.waypoints     = NULL;

    const StructFieldInfo *f          = find_field(Game_Metadata, Game_FieldCount, "waypoints");
    Vector2                payload[1] = {0};

    TEST_ASSERT_EQUAL(REFLECT_ERR_OUT_OF_BOUNDS, set_dynamic_Game_waypoints(&game, f, payload, 1));

    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, set_dynamic_Game_waypoints(&game, f, payload, 0));
}

GROUP_RUNNER()
{
    RUN(Can_Generate_Array_Literals);
    RUN(Can_Generate_Array_Macro);
    RUN(Setter_Copies_Memory);
    RUN(Setter_Fails_On_OOB);
    RUN(GetArrayElement_Gets_Valid_Element);
    RUN(GetArrayElement_Gets_Struct);
    RUN(GetArrayElement_Rejects_OutOfBounds_Index);
    RUN(GetArrayElement_Rejects_Size_Mismatch);
    RUN(GetArrayElement_Is_Null_Safe);
    RUN(DynamicArray_Allows_Valid_Set_Get);
    RUN(DynamicArray_Rejects_OutOfBounds);
    RUN(DynamicArray_Is_Null_Safe);
    RUN(DynamicArray_Rejects_Type_Mismatch);
    RUN(DynamicArray_Handles_Zero_Length);
}
