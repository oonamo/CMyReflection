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

    return u;
}

typedef struct
{
    int  indent;
    bool is_first_field;
} JsonState;

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
        printf("{");
        JsonState   nested_state = {.indent = state->indent + 4, .is_first_field = true};
        const void *nested_instance =
            base_instance ? ((const char *)base_instance + field->offset) : NULL;

        visit_struct_fields(nested_instance, field->type, json_account_serializer, &nested_state);
        printf("\n%*s}", state->indent, "");
    }
    else
    {
        const void *data_ptr = base_instance ? ((const char *)base_instance + field->offset) : NULL;
        if (data_ptr == NULL)
        {
            printf("\"%s\"", get_name_of_type(field->type));
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
        case TYPE_STRUCT_USER:
        case TYPE_UINT64_T:
        {
            uint64_t val = 0;
            get_field_uint64_t(base_instance, field, &val);
            printf("%llu", val);
            break;
        }
        case TYPE_UNKNOWN:
        case TYPE_CONSTSTR:
        case TYPE_STR:
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
    JsonState state = {4, false};
    printf("{");
    visit_struct_fields(&user, TYPE_STRUCT_USER, json_account_serializer, &state);
    printf("\n}\n");
}
