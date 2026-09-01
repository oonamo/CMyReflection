#include "stuff.h"

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
} Game;
