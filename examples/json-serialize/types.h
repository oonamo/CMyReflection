#ifndef _TYPES_H
#define _TYPES_H
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
    char         title[MAX_TITLE_LEN];
    uint32_t     likes;
    struct Post *references;
} Post;

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

    Permissions permissions;

    AccountState state;

    /// @private
    void *active_session_ptr;

    Post *posts;
} User;

#endif // _TYPES_H
