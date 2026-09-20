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
    User u = {
        .username           = "oonamo",                  // Default serialization
        .name               = "onam",                    // Default serialization
        .str                = "my\n \"cool\" str",       // \n Escaped, \" Escaped
        .email              = "myemail@provider.com",    // Regular string
        .account_id         = 0x13532,                   // Readoly, present in json
        .password_hash      = "hash123",                 // Writeonly, not present in json
        .permissions        = PERM_CREATE | PERM_UPDATE, // Serialized by serialize_permissions
        .state              = ACCOUNT_ACTIVE,            // Converted to string
        .active_session_ptr = &g_session                 // Private,
    };

    u.post_count = 10;
    u.posts      = malloc(sizeof(Post) * u.post_count);

    strncpy(u.settings.language, "en", 32);
    u.settings.prefers_dark = true;

    // Dynamic Array of Objects is rendered
    for (size_t i = 0; i < u.post_count; i++)
    {
        u.posts[i].likes = i;
        strncpy(u.posts[i].title, "TEST", MAX_TITLE_LEN);
    }

    return u;
}

typedef struct
{
    FILE  *fp;
    size_t bytes_written;
} file_stream_t;

void write_to_file(const char *chunk, size_t len, void *user_ctx)
{
    file_stream_t *ctx     = (file_stream_t *)user_ctx;
    size_t         written = fwrite(chunk, 1, len, ctx->fp);
    ctx->bytes_written += written;
}

int main()
{
    User user = default_acount();

    char buf[2056];
    char schema[2056];

    // Converts the User into JSON
    to_json(&user, TYPE_STRUCT_USER, buf, sizeof(buf));
    printf("%s\n", buf);

    // Converts the User into a Schema
    to_json(NULL, TYPE_STRUCT_USER, schema, sizeof(schema));
    printf("%s\n", schema);

    char filepath[512];
#ifdef EXAMPLE_OUT_DIR
    snprintf(filepath, sizeof(filepath), "%s/json_example.json", EXAMPLE_OUT_DIR);
#else
    snprintf(filepath, sizeof(filepath), "json_example.json");
#endif

    FILE *fp = fopen(filepath, "w");
    if (!fp)
    {
        printf("Failed to open file for writing.\n");
        return 1;
    }

    file_stream_t fs = {
        .fp            = fp,
        .bytes_written = 0,
    };

    // Uses the stream function to write to disk
    to_json_stream(&user, TYPE_STRUCT_USER, write_to_file, &fs);
    fclose(fp);

    printf("Succesfully streamed %zu bytes to file '%s'.\n", fs.bytes_written, filepath);
    return 0;
}
