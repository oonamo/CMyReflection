#ifndef _TYPES_H
#define _TYPES_H
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#define MAX_TITLE_LEN 124

// cmy:reflect
// cmy:unchecked
// cmy:no_print
// cmy:json_serialize_function(serialize_permissions)
typedef enum
{
    PERM_CREATE = 1 << 0,
    PERM_DELETE = 1 << 1,
    PERM_UPDATE = 1 << 2,
} Permissions;

// cmy:reflect
typedef enum
{
    // cmy:display("Active")
    ACCOUNT_ACTIVE,

    // cmy:display("Inactive")
    ACCOUNT_INACTIVE,

    // cmy:display("Stale")
    ACCOUNT_STALE,
} AccountState;

// cmy:reflect
typedef struct Post
{
    char     title[MAX_TITLE_LEN];
    uint32_t likes;
} Post;

// cmy:reflect
typedef struct
{
    char language[32];
    bool prefers_dark;
} UserPrefernces;

#define PERMISSIONS_DEFAULT (PERM_CREATE | PERM_UPDATE)

// cmy:reflect
typedef struct
{
    // cmy:format("%s")
    char username[32];

    // cmy:format("%s")
    char email[64];

    const char *name;
    char       *str;

    // cmy:readonly
    uint64_t account_id;

    // cmy:writeonly
    char password_hash[64];

    Permissions  permissions;
    AccountState state;

    UserPrefernces settings;

    // cmy:private
    void *active_session_ptr;

    size_t post_count;

    // cmy:length(post_count)
    Post *posts;
} User;

#endif // _TYPES_H
