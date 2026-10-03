#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include "utils.h"
#include <stdlib.h>

#include "mocks/game_type.h"
#include "mocks/readme_example.h"
#include "mocks/generated.inc"

#define LOCAL_TGROUP VISITOR
TEST_GROUP(VISITOR);
#include "test_utils.h"

SETUP()
{
}

TEAR_DOWN()
{
}

typedef struct
{
    int         visited_count;
    const void *last_seen_instance;
} VisitorTestState;

static void test_mock_visitor(const void *instance, const StructFieldInfo *field, void *user_data)
{
    VisitorTestState *state = (VisitorTestState *)user_data;
    state->visited_count++;
    state->last_seen_instance = instance;
}

T(VisitStruct_Iterates_Top_Level_Fields)
{
    Game             g      = {0};
    VisitorTestState state  = {0};
    int              indent = 0;

    TEST_ASSERT_EQUAL(REFLECT_OK,
                      visit_struct_fields(&g, TYPE_STRUCT_GAME, test_mock_visitor, &state));
    TEST_ASSERT_EQUAL_INT(Game_FieldCount, state.visited_count);
    TEST_ASSERT_POINTERS_EQUAL(&g, state.last_seen_instance);
}

T(VisitStruct_Works_Without_Instance)
{
    VisitorTestState state = {0};

    TEST_ASSERT_EQUAL(REFLECT_OK,
                      visit_struct_fields(NULL, TYPE_STRUCT_BALL, test_mock_visitor, &state));
    TEST_ASSERT_EQUAL_INT(Ball_FieldCount, state.visited_count);
    TEST_ASSERT_NULL(state.last_seen_instance);
}

T(VisitStruct_Rejects_Invalid_Types)
{
    VisitorTestState state = {0};
    Game             g     = {0};

    TEST_ASSERT_EQUAL(REFLECT_ERR_TYPE_MISMATCH,
                      visit_struct_fields(&g, TYPE_INT, test_mock_visitor, &state));
    TEST_ASSERT_EQUAL(REFLECT_ERR_TYPE_MISMATCH,
                      visit_struct_fields(&g, TYPE_FLOAT_ARR, test_mock_visitor, &state));

    TEST_ASSERT_EQUAL_INT(0, state.visited_count);
}

T(VisitStruct_Is_Null_Safe)
{
    Game g = {0};

    TEST_ASSERT_EQUAL(REFLECT_ERR_NULL_PTR, visit_struct_fields(&g, TYPE_STRUCT_GAME, NULL, NULL));
}

GROUP_RUNNER()
{
    RUN(VisitStruct_Iterates_Top_Level_Fields);
    RUN(VisitStruct_Works_Without_Instance);
    RUN(VisitStruct_Rejects_Invalid_Types);
    RUN(VisitStruct_Is_Null_Safe);
}
