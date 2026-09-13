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

static User default_acount(void)
{
    User u = {.username           = "oonamo",
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

typedef struct
{
    int        indent;
    bool       is_first_field;
    FIELD_TYPE current_parent_type;
} JsonState;

void json_account_serializer(const void *base_instance, const FieldInfo *field, void *user_data);

void next_level(const void *base_instance, const FieldInfo *field, void *user_data)
{
    JsonState *state = (JsonState *)user_data;

    printf("{");
    JsonState nested_state = {
        .indent = state->indent + 4, .is_first_field = true, .current_parent_type = field->type};
    const void *nested_instance =
        base_instance ? ((const char *)base_instance + field->offset) : NULL;

    visit_struct_fields(nested_instance, field->type, json_account_serializer, &nested_state);
    printf("\n%*s}", state->indent, "");
}

void json_account_serializer(const void *base_instance, const FieldInfo *field, void *user_data)
{
    if (!(field->flags & FIELD_ACCESS_READ))
    {
        return;
    }

    JsonState *state = (JsonState *)user_data;
    //
    if (!state->is_first_field)
    {
        printf(",\n");
    }
    else
    {

        printf("\n");
        state->is_first_field = false;
    }

    printf("%*s\"%s\": ", state->indent, "", field->name);

    StructMetaData meta;
    if (get_struct_metadata(field->type, &meta) == REFLECT_OK)
    {
        next_level(base_instance, field, user_data);
    }
    else
    {
        const void *data_ptr = base_instance ? ((const char *)base_instance + field->offset) : NULL;
        if (data_ptr == NULL)
        {
            // printf("\"%s\"", get_name_of_type(field->type));
            if (field->length_field_name != NULL)
            {
                printf("[\"%s (dynamic: %s)\"]",
                       get_name_of_type(field->type),
                       field->length_field_name);
            }
            else if (field->count > 1)
            {
                printf("\"%s (max: %zu)\"", get_name_of_type(field->type), field->count);
            }
            else
            {
                printf("\"%s\"", get_name_of_type(field->type));
            }
            return;
        }
        switch (field->type)
        {
        case TYPE_CHAR_ARR:
        {
            char *val = malloc(field->size);
            get_field_char_arr(base_instance, field, val, field->count);
            printf("\"%s\"", val);
            free(val);
            break;
        }
        case TYPE_ENUM_PERMISSIONS:
        {
            char   perm_str[4];
            int    permissions = *(int *)data_ptr;
            size_t i           = 0;

            if (permissions & PERM_CREATE)
            {
                perm_str[i++] = 'c';
            }
            if (permissions & PERM_DELETE)
            {
                perm_str[i++] = 'x';
            }
            if (permissions & PERM_UPDATE)
            {
                perm_str[i++] = 'u';
            }
            if (i < 3)
            {
                perm_str[i] = '\0';
            }
            printf("\"%s\"", perm_str);
            break;
        }
        case TYPE_ENUM_ACCOUNTSTATE:
        {
            const char *val = get_enum_member_name(
                AccountState_Members, AccountState_MemberCount, *(int *)data_ptr);
            printf("\"%s\"", val);
            break;
        }
        case TYPE_UINT64_T:
        {
            uint64_t val = 0;
            get_field_uint64_t(base_instance, field, &val);
            printf("%llu", val);
            break;
        }
        case TYPE_SIZE_T:
        {
            size_t val = 0;
            get_field_size_t(base_instance, field, &val);
            printf("%zu", val);
            break;
        }
        case TYPE_POST_PTR:
        {
            Post *post_array = NULL;
            if (get_field_Post_ptr(base_instance, field, &post_array) != REFLECT_OK ||
                post_array == NULL)
            {
                printf("NULL");
                return;
            }

            if (field->length_field_name != NULL)
            {
                size_t array_len = 0;
                if (get_dynamic_array_length(
                        base_instance, state->current_parent_type, field, &array_len) != REFLECT_OK)
                {
                    printf("NULL");
                    return;
                }
                printf("[\n");
                for (size_t i = 0; i < array_len; i++)
                {
                    printf("%*s{\n", state->indent + 4, "");

                    JsonState nested_state = {.indent              = state->indent + 8,
                                              .is_first_field      = true,
                                              .current_parent_type = TYPE_STRUCT_POST};

                    // Native C iteration using the safely extracted pointer
                    visit_struct_fields(
                        &post_array[i], TYPE_STRUCT_POST, json_account_serializer, &nested_state);

                    printf("\n%*s}", state->indent + 4, "");
                    if (i < array_len - 1)
                    {
                        printf(",\n");
                    }
                }
                printf("\n%*s]", state->indent, "");
            }
            else
            {
                printf("{\n");
                JsonState nested_state = {.indent              = state->indent + 4,
                                          .is_first_field      = true,
                                          .current_parent_type = TYPE_STRUCT_POST};

                visit_struct_fields(
                    post_array, TYPE_STRUCT_POST, json_account_serializer, &nested_state);
                printf("\n%*s}", state->indent, "");
            }
            break;
        }
        case TYPE_UINT32_T:
        {
            uint32_t val = 0;
            get_field_u32(base_instance, field, &val);
            printf("%u", val);
            break;
        }
        case TYPE_BOOL:
        {
            bool val = false;
            get_field_bool(base_instance, field, &val);
            printf("\"%s\"", val ? "true" : "false");
            break;
        }
        case TYPE_STRUCT_POST:
        case TYPE_STRUCT_USER:
        default:

            fprintf(
                stderr, "\n\nError: Could not serialize type %s\n", get_name_of_type(field->type));
            exit(1);
            break;
        }
    }
}

int main()
{
    User      user  = default_acount();
    JsonState state = {
        .indent              = 4,
        .is_first_field      = true,
        .current_parent_type = TYPE_STRUCT_USER,
    };

    printf("{");
    visit_struct_fields(NULL, TYPE_STRUCT_USER, json_account_serializer, &state);
    printf("\n}\n");
}
