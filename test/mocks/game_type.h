#include "stuff.h"
#include <stdint.h>

/// @reflect
/// @enum TYPE_VEC2
typedef struct
{
    float x;
    float y;
} Vector2;

/// @reflect
typedef struct
{
    Vector2 player_pos;
    float health;

    int level;
    char *player_name;

    DamageComponent damage;

    uint8_t game_flags;

    unsigned int other_flags;

    unsigned char tile_type;

    /// @private
    uint32_t internal_count;

    void *userdata; /// @private

    long long score;
} Game;
