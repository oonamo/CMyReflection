#ifndef _TEST_JSON_TYPES_H
#define _TEST_JSON_TYPES_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define MAX_FRIEND_COUNT 10

// cmy:reflect
// cmy:unchecked
// cmy:json_serialize_function(serialize_interactions)
typedef enum
{
    POST_SAVE         = (1 << 0),
    POST_FRIENDS_ONLY = (1 << 1),
    POST_DOWNLOAD     = (1 << 2),
} PostInteraction;

// cmy:reflect
typedef struct
{
    char           *title;
    uint32_t        likes;
    PostInteraction interactions;
} Post;

// cmy:reflect
typedef enum
{
    // cmy:display("Active")
    ACCOUNT_ACTIVE,

    // cmy:display("Inactive")
    ACCOUNT_INACTIVE,

    // cmy:display("Deleted")
    ACCOUNT_DELETED,
} AccountState;

// cmy:reflect
typedef struct
{
    bool prefers_dark_mode;
    int  login_attempts;
} AccountSettings;

// cmy:reflect
typedef struct
{
    char username[64];
    char email[64];

    char *bio;

    // cmy:writeonly
    char password_hash[16];

    AccountState    status;
    AccountSettings settings;
    bool            is_verified;

    size_t post_count;

    // cmy:length(post_count)
    Post *posts;

    char *friends[MAX_FRIEND_COUNT];
} User;

// cmy:reflect
typedef struct
{
    char *longstring;
} LongString;

// cmy:reflect
typedef struct
{
    // cmy:json_key_name("int")
    int my_int;

    // cmy:json_key_name("character value")
    char c;
} DumbStruct;

#endif // _TEST_JSON_TYPES_H
