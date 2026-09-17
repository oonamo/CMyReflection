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

#define Q(s) "\"" s "\""

#define Q_WORD(word) "\"" #word "\""

TEST(Json, Serializes_Strings)
{
    User u = {0};

    strncpy(u.username, "oonamo", sizeof(u.username) - 1);
    strncpy(u.email, "myemail@provider.com", sizeof(u.email) - 1);

    char  *bio     = "cool stuff here";
    size_t bio_len = strlen(bio);
    u.bio          = malloc(bio_len + 1);
    strncpy(u.bio, bio, bio_len);
    u.bio[bio_len] = '\0';

    json_serialize_value(&u, TYPE_STRUCT_USER, NULL, &state);

    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("username") ": " Q("oonamo")),
                                 "Username was not serialized");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("email") ": " Q("myemail@provider.com")),
                                 "Email was not serialized");
    TEST_ASSERT_NOT_NULL_MESSAGE(strstr(state._buf, Q("bio") ": " Q("cool stuff here")),
                                 "Email was not serialized");

    free(u.bio);
}

TEST_GROUP_RUNNER(Json)
{
    RUN_TEST_CASE(Json, Serializes_Strings);
}
