#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include "utils.h"
#include <stdlib.h>

#include "mocks/game_type.h"
#include "mocks/readme_example.h"
#include "mocks/generated.inc"

#define LOCAL_TGROUP GETTER
TEST_GROUP(GETTER);
#include "test_utils.h"

SETUP()
{
}

TEAR_DOWN()
{
}

T(FieldGetter_Extracts_Valid_Data)
{
    Vector2                v = {3.14f, 2.71f};
    const StructFieldInfo *f = find_field(Vector2_Metadata, Vector2_FieldCount, "x");

    float extracted_value = 0.0f;

    TEST_ASSERT_TRUE(get_field_float(&v, f, &extracted_value) == REFLECT_OK);
    TEST_ASSERT_EQUAL_FLOAT(3.14f, extracted_value);
}

T(FieldGetter_Rejects_Type_Mismatch)
{
    Vector2                v = {3.14f, 2.71f};
    const StructFieldInfo *f =
        find_field(Vector2_Metadata, Vector2_FieldCount, "x"); // x is TYPE_FLOAT

    int extracted_value = 99;

    TEST_ASSERT_FALSE(get_field_int(&v, f, &extracted_value) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(99, extracted_value);
}

T(FieldGetter_Extracts_Enum_Correctly)
{
    Game g      = {0};
    g.ball.size = BALL_TYPE_BIG;

    const StructFieldInfo *f = find_field(Ball_Metadata, Ball_FieldCount, "size");

    BallSize extracted_size = BALL_TYPE_SMALL;

    TEST_ASSERT_TRUE(get_field_BallSize(&g.ball, f, &extracted_size) == REFLECT_OK);
    TEST_ASSERT_EQUAL_INT(BALL_TYPE_BIG, extracted_size);
}

T(FieldGetter_Respects_Arrays)
{
    Game    g = {0};
    uint8_t expected[9];
    for (int i = 0; i < 9; i++)
    {
        g.grid[i]   = i;
        expected[i] = i;
    }

    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "grid");

    uint8_t out_grid[9];

    TEST_ASSERT_TRUE(get_field_u8_arr(&g, f, out_grid, 9) == REFLECT_OK);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(expected, out_grid, 9);

    memset(out_grid, 0, 9);
    TEST_ASSERT_TRUE(get_field_u8_arr(&g, f, out_grid, 3) == REFLECT_OK);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(expected, out_grid, 3);

    uint8_t arr_zero[6] = {0};
    TEST_ASSERT_EQUAL_UINT8_ARRAY(arr_zero, out_grid + 3, 6);
}

T(FieldGetter_Rejects_OutOfBounds_Read)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "history");

    float out_history[MAX_ARR_LEN + 1];
    TEST_ASSERT_FALSE(get_field_float_arr(&g, f, out_history, MAX_ARR_LEN + 1) == REFLECT_OK);
}

T(GetFieldValue_Enforces_Bounds_And_Null_Safety)
{
    Vector2                v = {1.0f, 1.0f};
    const StructFieldInfo *f =
        find_field(Vector2_Metadata, Vector2_FieldCount, "x"); // size is 4 (sizeof(float))

    float out_val = 0.0f;

    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, get_field_value(NULL, f, &out_val, sizeof(float)));
    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, get_field_value(&v, NULL, &out_val, sizeof(float)));
    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, get_field_value(&v, f, NULL, sizeof(float)));
    TEST_ASSERT_EQUAL(REFLECT_ERR_OUT_OF_BOUNDS, get_field_value(&v, f, &out_val, sizeof(double)));
}

T(WriteOnly_Tag_Prevents_Getters)
{
    Game g = {0};
    g.hash = 15812;

    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "hash");

    uint32_t new_hash = 32;

    TEST_ASSERT_EQUAL(REFLECT_OK, set_field_u32(&g, f, new_hash));

    uint32_t extracted = 0;
    TEST_ASSERT_EQUAL(REFLECT_ERR_ACCESS_DENIED, get_field_u32(&g, f, &extracted));
    TEST_ASSERT_EQUAL_UINT32(new_hash, g.hash);
}

GROUP_RUNNER()
{
    RUN(FieldGetter_Extracts_Valid_Data);
    RUN(FieldGetter_Rejects_Type_Mismatch);
    RUN(FieldGetter_Extracts_Enum_Correctly);
    RUN(FieldGetter_Respects_Arrays);
    RUN(FieldGetter_Rejects_OutOfBounds_Read);
    RUN(GetFieldValue_Enforces_Bounds_And_Null_Safety);
    RUN(WriteOnly_Tag_Prevents_Getters);
}
