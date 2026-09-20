#include "types.h"
#include <stdio.h>

#define CMYREFLECTION_IMPLEMENTATION
#define REFLECTION_IMPLEMENTATION
#include "generated.h"

typedef struct
{
    int data;
} Session;

static Session g_session = {0};

ReflectResult serialize_permissions(const void            *exact_data_ptr,
                                    FIELD_TYPE             actual_type,
                                    const StructFieldInfo *field_ctx,
                                    _cmy_json_state       *state)
{
    if (!exact_data_ptr)
    {
        CMY_JSON_WRITE(state, "\"Permissions Bitmask\"");
        return REFLECT_OK;
    }

    Permissions permissions = *(Permissions *)exact_data_ptr;

    CMY_JSON_WRITE(state, "\"");
    if (permissions & PERM_CREATE)
    {
        CMY_JSON_WRITE(state, "c");
    }
    if (permissions & PERM_DELETE)
    {
        CMY_JSON_WRITE(state, "d");
    }
    if (permissions & PERM_UPDATE)
    {
        CMY_JSON_WRITE(state, "u");
    }
    CMY_JSON_WRITE(state, "\"");

    return REFLECT_OK;
}

static User default_acount(void)
{
    User u = {.username           = "oonamo",
              .name               = "onam",
              .str                = "my cool str",
              .email              = "myemail@provider.com",
              .account_id         = 0x13532,
              .password_hash      = "hash123",
              .permissions        = PERM_CREATE | PERM_UPDATE,
              .state              = ACCOUNT_ACTIVE,
              .active_session_ptr = &g_session};

    u.post_count = 10;
    u.posts      = malloc(sizeof(Post) * u.post_count);

    strncpy(u.settings.language, "en", 32);
    u.settings.prefers_dark = true;

    for (size_t i = 0; i < u.post_count; i++)
    {
        u.posts[i].likes = i;
        strncpy(u.posts[i].title, "TEST", MAX_TITLE_LEN);
    }

    return u;
}

int main()
{
    User user = default_acount();

    char buf[2056];
    char schema[2056];

    to_json(&user, TYPE_STRUCT_USER, buf, sizeof(buf));
    to_json(NULL, TYPE_STRUCT_USER, schema, sizeof(schema));

    printf("%s\n", buf);
    printf("%s\n", schema);
}
