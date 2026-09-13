#ifndef _TYPES_H
#define _TYPES_H
#include <stdbool.h>
#include <stdint.h>

#define MAX_TITLE_LEN 124

/// @reflect
/// @unchecked
typedef enum
{
    PERM_CREATE = 1 << 0,
    PERM_DELETE = 1 << 1,
    PERM_UPDATE = 1 << 2,
} Permissions;

/// @reflect
typedef enum
{
    ACCOUNT_ACTIVE,
    ACCOUNT_INACTIVE,
    ACCOUNT_STALE,
} AccountState;

/// @reflect
typedef struct Post
{
    char     title[MAX_TITLE_LEN];
    uint32_t likes;
} Post;

/// @reflect
typedef struct
{
    char language[32];
    bool prefers_dark;
} UserPrefernces;

#define PERMISSIONS_DEFAULT (PERM_CREATE | PERM_UPDATE)

/// @reflect
typedef struct
{
    char username[32];
    char email[64];

    /// @readonly
    uint64_t account_id;

    /// @writeonly
    char password_hash[64];

    Permissions  permissions;
    AccountState state;

    UserPrefernces settings;

    /// @private
    void *active_session_ptr;

    size_t post_count;

    /// @length(post_count)
    Post *posts;
} User;

#endif // _TYPES_H
