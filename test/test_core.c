#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include "utils.h"
#include <stdlib.h>

#include "mocks/game_type.h"
#include "mocks/readme_example.h"
#include "mocks/generated.inc"

#define LOCAL_TGROUP CORE
TEST_GROUP(CORE);
#include "test_utils.h"

SETUP()
{
}

TEAR_DOWN()
{
}

T(Can_Find_Field)
{
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "health");

    TEST_ASSERT_NOT_NULL(f);
    TEST_ASSERT_EQUAL_STRING("health", f->name);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, f->type);

    TEST_ASSERT_EQUAL(offsetof(Game, health), f->offset);
}

T(Fails_To_Find_Invalid_Field)
{

    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "dne");

    TEST_ASSERT_NULL(f);
}

T(Private_Fields_Are_Ignored)
{
    Game g = {0};

    g.internal_count          = 5;
    const StructFieldInfo *f1 = find_field(Game_Metadata, Game_FieldCount, "internal_count");
    TEST_ASSERT_NULL_MESSAGE(f1, "internal_count was exposed");

    g.userdata                = (void *)"dummy str to check field exists";
    const StructFieldInfo *f2 = find_field(Game_Metadata, Game_FieldCount, "userdata");
    TEST_ASSERT_NULL_MESSAGE(f2, "userdata was exposed");
}

T(String_Has_Alias)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "player_name");

    TEST_ASSERT_EQUAL(REFLECT_OK, set_field_str(&g, f, "player1"));
    TEST_ASSERT_EQUAL_STRING("player1", g.player_name);
}

T(Metadata_Stores_Correct_Sizes)
{
    const StructFieldInfo *f_health = find_field(Game_Metadata, Game_FieldCount, "health");
    TEST_ASSERT_EQUAL(sizeof(float), f_health->size);

    const StructFieldInfo *f_pos = find_field(Game_Metadata, Game_FieldCount, "player_pos");
    TEST_ASSERT_EQUAL(sizeof(Vector2), f_pos->size);

    const StructFieldInfo *f_name = find_field(Game_Metadata, Game_FieldCount, "player_name");
    TEST_ASSERT_EQUAL(sizeof(char *), f_name->size);
}

T(Handles_Spaced_Types)
{
    Game                   g = {0};
    const StructFieldInfo *f = find_field(Game_Metadata, Game_FieldCount, "score");
    TEST_ASSERT_NOT_NULL(f);

    TEST_ASSERT_EQUAL(TYPE_LONGLONG, f->type);
    TEST_ASSERT_EQUAL(REFLECT_OK, set_field_ll(&g, f, 2393));
}

T(Can_Get_Names_Of_Primitives)
{
    const char *result = get_name_of_type(TYPE_INT);
    TEST_ASSERT_NOT_NULL(result);
    TEST_ASSERT_EQUAL_STRING("TYPE_INT", result);
}

T(Can_Get_Names_Of_Structs)
{
    const char *result = get_name_of_type(TYPE_STRUCT_BALL);
    TEST_ASSERT_NOT_NULL(result);
    TEST_ASSERT_EQUAL_STRING("TYPE_STRUCT_BALL", result);
}

T(Can_Get_Names_Of_Arrays)
{
    const char *result = get_name_of_type(TYPE_UINT8_T_ARR);
    TEST_ASSERT_NOT_NULL(result);
    TEST_ASSERT_EQUAL_STRING("TYPE_UINT8_T_ARR", result);
}

T(Can_Use_MetaData_Macro)
{

    StructMetaData game_metadata = StructMetaData_FromName(Game);

    TEST_ASSERT_EQUAL(Game_FieldCount, game_metadata.count);
    TEST_ASSERT_POINTERS_EQUAL(Game_Metadata, game_metadata.fields);
}

T(Can_Use_Find_Struct_Macro)
{
    const StructFieldInfo *f = Find_Struct_Field(StructMetaData_FromName(Game), "health");
    TEST_ASSERT_NOT_NULL(f);
    TEST_ASSERT_EQUAL(TYPE_FLOAT, f->type);
}

T(Can_Get_Constant_Types)
{
    Game game = {.name = "TESTING"};

    const StructFieldInfo *field = Find_Struct_Field(StructMetaData_FromName(Game), "name");
    const char            *name;

    get_field_conststr(&game, field, &name);

    TEST_ASSERT_EQUAL_STRING("TESTING", name);
}

#define EQ TEST_ASSERT_EQUAL

T(Type_Size_Function_Is_Accurate)
{
    EQ(sizeof(int), get_type_size(TYPE_INT));
    EQ(sizeof(float), get_type_size(TYPE_FLOAT));
    EQ(sizeof(char), get_type_size(TYPE_CHAR));
    EQ(sizeof(Game), get_type_size(TYPE_STRUCT_GAME));
    EQ(sizeof(Vector2 *), get_type_size(TYPE_VECTOR2_PTR));
}


GROUP_RUNNER()
{
    RUN(Can_Find_Field);
    RUN(Fails_To_Find_Invalid_Field);
    RUN(Private_Fields_Are_Ignored);
    RUN(String_Has_Alias);
    RUN(Metadata_Stores_Correct_Sizes);
    RUN(Handles_Spaced_Types);
    RUN(Can_Get_Names_Of_Primitives);
    RUN(Can_Get_Names_Of_Structs);
    RUN(Can_Get_Names_Of_Arrays);
    RUN(Can_Use_MetaData_Macro);
    RUN(Can_Use_Find_Struct_Macro);
    RUN(Can_Get_Constant_Types);
    RUN(Type_Size_Function_Is_Accurate);
}
