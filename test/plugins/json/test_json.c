#include <stdio.h>
#include <unity.h>
#include <unity_fixture.h>
#include <stdlib.h>

#include "test_json_types.h"
#include "json.generated.h"

static char            json_buffer[4096];
static _cmy_json_state state;

TEST_GROUP(Json);

TEST_SETUP(Json)
{
    memset(json_buffer, 0, sizeof(json_buffer));
    state._buf                = json_buffer;
    state._max_len            = sizeof(json_buffer);
    state._current_offset     = 0;
    state.indent              = 0;
    state.is_first_field      = true;
    state.current_parent_type = TYPE_UNKNOWN;
}

TEST_TEAR_DOWN(Json)
{
    if (Unity.CurrentTestFailed)
    {
        printf("\nFailed json output: \n%s\n", json_buffer);
    }
}

ReflectResult serialize_interactions(const void            *exact_data_ptr,
                                     FIELD_TYPE             actual_type,
                                     const StructFieldInfo *field_ctx,
                                     _cmy_json_state       *lstate)
{
    if (actual_type != TYPE_ENUM_POSTINTERACTION)
    {
        TEST_FAIL_MESSAGE("wrong type was passed to serialize_interactions");
    }

    PostInteraction interactions = *(PostInteraction *)exact_data_ptr;

    CMY_JSON_WRITE(lstate, "\"");
    if (interactions & POST_SAVE)
    {
        CMY_JSON_WRITE(lstate, "s");
    }
    else
    {
        CMY_JSON_WRITE(lstate, "-");
    }

    if (interactions & POST_FRIENDS_ONLY)
    {
        CMY_JSON_WRITE(lstate, "f")
    }
    else
    {
        CMY_JSON_WRITE(lstate, "-");
    }

    if (interactions & POST_DOWNLOAD)
    {
        CMY_JSON_WRITE(lstate, "d")
    }
    else
    {
        CMY_JSON_WRITE(lstate, "-");
    }
    CMY_JSON_WRITE(lstate, "\"");

    return REFLECT_OK;
}

#define Q(s) "\"" s "\""

TEST(Json, Serializes_Strings)
{
    Post my_posts[2] = {
        {.likes = 100, .title = "Hello World", .interactions = (POST_SAVE | POST_FRIENDS_ONLY)},
        {.likes = 250, .title = "CMyReflection", .interactions = (POST_SAVE | POST_DOWNLOAD)}};

    User u = {
        .username      = "oonamo",
        .email         = "test@domain.com",
        .bio           = "EE",
        .password_hash = "super_secret",
        .status        = ACCOUNT_ACTIVE,
        .settings      = {.prefers_dark_mode = true, .login_attempts = 5},
        .is_verified   = true,
        .post_count    = 2,
        .posts         = my_posts,
        .friends       = {"Alice", "Bob", NULL} // Rest are NULL
    };

    json_serialize_value(&u, TYPE_STRUCT_USER, NULL, &state);

    char filepath[512];

#ifdef TEST_OUT_DIR
    snprintf(filepath, sizeof(filepath), "%s/test_payload.json", TEST_OUT_DIR);
#else
    snprintf(filepath, sizeof(filepath), "test_payload.json");
#endif

    FILE *fp = fopen(filepath, "w");
    if (fp)
    {
        fputs(state._buf, fp);
        fclose(fp);
    }
    else
    {
        TEST_FAIL_MESSAGE("Could not open test_payload.json for writing");
    }

    // 1. String
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("username") ": " Q("oonamo")),
                                 "Static string failed");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("bio") ": " Q("EE")),
                                 "Dynamic string pointer failed");

    // 2. Primitives & Enums (No quotes around true/false)
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("is_verified") ": true"),
                                 "Boolean formatting failed");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("status") ": " Q("Active")),
                                 "Enum @display tag formatting failed");

    // 3. Check Write-Only
    TEST_ASSERT_NULL_MESSAGE(strstr(state._buf, Q("password_hash")),
                             "Write-only field leaked data");

    // 4. Check Nested Struct
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("settings") ": {\n"),
                                 "Nested struct did not open correctly");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("prefers_dark_mode") ": true"),
                                 "Nested struct field failed");

    // 5. Check Dynamic Array
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("posts") ": [\n"),
                                 "Dynamic array did not open correctly");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("title") ": " Q("Hello World")),
                                 "Array element 0 failed");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("title") ": " Q("CMyReflection")),
                                 "Array element 1 failed");

    // 6. Check Static Array of Pointers
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("friends") ": [\n"),
                                 "Static array did not open correctly");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("Alice")),
                                 "Valid pointer in string array failed");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, "null"),
                                 "NULL pointer in string array did not output 'null'");

    // 7. Check Custom Interaction Serializer
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("interactions") ": " Q("sf-")),
                                 "Post 0 failed");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("interactions") ": " Q("s-d")),
                                 "Post 1 failed");
}

TEST(Json, Handles_Empty_And_Null_Pointers)
{
    User u = {0};

    json_serialize_value(&u, TYPE_STRUCT_USER, NULL, &state);

    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("bio") ": null"),
                                 "NULL char* did not result in null");
}

TEST(Json, Generates_Valid_Schema)
{
    json_serialize_value(NULL, TYPE_STRUCT_USER, NULL, &state);

    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("username") ": " Q("TYPE_CHAR_ARR")),
                                 "Schema primitive missing");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("email") ": " Q("TYPE_CHAR_ARR")),
                                 "Schema primitive missing");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("bio") ": " Q("TYPE_CHAR_PTR")),
                                 "Schema primitive missing");
    TEST_ASSERT_NOT_NULL_MESSAGE(
        strstr(state._buf, Q("posts") ": [" Q("TYPE_STRUCT_POST (dynamic: post_count)") "]"),
        "Schema dynamic array missing");

    TEST_ASSERT_NOT_NULL_MESSAGE(
        strstr(state._buf, Q("friends") ": [" Q("TYPE_CHAR_PTR (max: 10)") "]"),
        "Schema static array missing");
}

TEST_GROUP_RUNNER(Json)
{
    RUN_TEST_CASE(Json, Serializes_Strings);
    RUN_TEST_CASE(Json, Handles_Empty_And_Null_Pointers);
    RUN_TEST_CASE(Json, Generates_Valid_Schema);
}
