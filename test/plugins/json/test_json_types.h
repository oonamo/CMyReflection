#ifndef _TEST_JSON_TYPES_H
#define _TEST_JSON_TYPES_H

#include <stdint.h>

typedef struct
{
    char    *title;
    uint32_t likes;
} Post;

// cmy:reflect
typedef struct
{
    char username[64];
    char email[64];

    char* bio;

    // cmy:writeonly
    char password_hash[16];

    size_t post_count;

    // cmy:length(post_count)
    Post *posts;
} User;

#endif // _TEST_JSON_TYPES_H
