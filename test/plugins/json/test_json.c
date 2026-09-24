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
    state._capacity           = sizeof(json_buffer);
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
    (void)field_ctx;
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
        CMY_JSON_WRITE(lstate, "f");
    }
    else
    {
        CMY_JSON_WRITE(lstate, "-");
    }

    if (interactions & POST_DOWNLOAD)
    {
        CMY_JSON_WRITE(lstate, "d");
    }
    else
    {
        CMY_JSON_WRITE(lstate, "-");
    }
    CMY_JSON_WRITE(lstate, "\"");

    return REFLECT_OK;
}

#define Q(s) "\"" s "\""

#define TEST_ASSERT_JSON_CONTAINS(expected_substr, json_str)                                       \
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr((json_str), (expected_substr)),                            \
                                 "Expected substring not found in JSON output: " expected_substr)

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

    to_json(&u, TYPE_STRUCT_USER, json_buffer, sizeof(json_buffer));

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

    to_json(&u, TYPE_STRUCT_USER, json_buffer, sizeof(json_buffer));

    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("bio") ": null"),
                                 "NULL char* did not result in null");
}

TEST(Json, Generates_Valid_Schema)
{
    to_json(NULL, TYPE_STRUCT_USER, json_buffer, sizeof(json_buffer));

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

TEST(Json, Handles_Long_Strings)
{
    LongString   l          = {0};
    const size_t string_len = 400;

    l.longstring = malloc(string_len + 1);
    TEST_ASSERT_NOT_NULL(l.longstring);

    for (size_t i = 0; i < string_len; i++)
    {
        l.longstring[i] = 'a' + (char)(i % 26);
    }
    l.longstring[string_len] = '\0';

    TEST_ASSERT_EQUAL(REFLECT_OK,
                      to_json(&l, TYPE_STRUCT_LONGSTRING, json_buffer, sizeof(json_buffer)));

    char expected_json[1024] = {0};
    snprintf(
        expected_json, sizeof(expected_json), "{\n    \"longstring\": \"%s\"\n}", l.longstring);

    TEST_ASSERT_EQUAL_STRING(expected_json, json_buffer);

    free(l.longstring);
}

TEST(Json, Escapes_Special_Characters)
{
    User u = {0};
    u.bio  = "L1\nL2\n\t\"Hello World\"";

    TEST_ASSERT_EQUAL(REFLECT_OK, to_json(&u, TYPE_STRUCT_USER, json_buffer, sizeof(json_buffer)));

    TEST_ASSERT_JSON_CONTAINS(Q("bio") ": " Q("L1\\nL2\\n\\t\\\"Hello World\\\""), json_buffer);
}

// Generic string implementation
typedef struct
{
    char  *buf;
    size_t capacity;
    size_t offset;
} dynamic_string_ctx;

static void dynamic_write_cb(const char *chunk, size_t len, void *user_ctx)
{
    dynamic_string_ctx *ctx = (dynamic_string_ctx *)user_ctx;

    // Generic grow buffer (+1 for null terminator)
    if (ctx->offset + len + 1 > ctx->capacity)
    {
        size_t new_cap = ctx->capacity == 0 ? 64 : ctx->capacity * 2;

        // Apply growth factor until needed capacity is met
        while (ctx->offset + len + 1 > new_cap)
        {
            new_cap *= 2;
        }

        ctx->buf = realloc(ctx->buf, new_cap);
        TEST_ASSERT_NOT_NULL_MESSAGE(ctx->buf, "Memroy allocation failes during json stream");
        ctx->capacity = new_cap;
    }

    memcpy(ctx->buf + ctx->offset, chunk, len);
    ctx->offset += len;
    ctx->buf[ctx->offset] = '\0';
}

TEST(Json, Stream_Dynamic_Allocation)
{
    User u = {0};
    u.bio  = "This string is dynamically allocated. We will verify it's validity";

    dynamic_string_ctx ctx = {0};

    TEST_ASSERT_EQUAL(REFLECT_OK, to_json_stream(&u, TYPE_STRUCT_USER, dynamic_write_cb, &ctx));
    TEST_ASSERT_NOT_NULL(ctx.buf);

    TEST_ASSERT_JSON_CONTAINS(
        Q("bio") ": " Q("This string is dynamically allocated. We will verify it's validity"),
        ctx.buf);

    free(ctx.buf);
}

TEST(Json, Can_Use_Key_Name_Output)
{
    DumbStruct u = {0};
    u.my_int     = 53;
    u.c          = 'A';

    TEST_ASSERT_EQUAL(REFLECT_OK,
                      to_json(&u, TYPE_STRUCT_DUMBSTRUCT, json_buffer, sizeof(json_buffer)));

    TEST_ASSERT_JSON_CONTAINS(Q("int") ": 53", json_buffer);
    TEST_ASSERT_JSON_CONTAINS(Q("character value") ": A", json_buffer);
}

TEST(Json, Can_Use_Struct_Generated_Output)
{
    AccountSettings settings = {true, 5};
    AccountSettings_to_json(&settings, json_buffer, sizeof(json_buffer));

    TEST_ASSERT_JSON_CONTAINS(Q("prefers_dark_mode") ": true", json_buffer);
    TEST_ASSERT_JSON_CONTAINS(Q("login_attempts") ": 5", json_buffer);
}

TEST_GROUP_RUNNER(Json)
{
    RUN_TEST_CASE(Json, Serializes_Strings);
    RUN_TEST_CASE(Json, Handles_Empty_And_Null_Pointers);
    RUN_TEST_CASE(Json, Generates_Valid_Schema);
    RUN_TEST_CASE(Json, Handles_Long_Strings);
    RUN_TEST_CASE(Json, Escapes_Special_Characters);
    RUN_TEST_CASE(Json, Stream_Dynamic_Allocation);
    RUN_TEST_CASE(Json, Can_Use_Key_Name_Output);
    RUN_TEST_CASE(Json, Can_Use_Struct_Generated_Output);
}
