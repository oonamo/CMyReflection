#include "stuff.h"
#include <stdint.h>

/// @reflect
typedef enum
{
    BALL_TYPE_SMALL = 0,
    BALL_TYPE_MEDIUM,
    BALL_TYPE_BIG,

    /// @private
    BALL_TYPE_NONE,
} BallSize;

/// @reflect
/// @enum TYPE_VEC2
typedef struct
{
    float x;
    float y;
} Vector2;

#define MAX_ARR_LEN 256

/// @reflect
typedef struct
{
    Vector2 speed;
    float   radius;
    BallSize size;
} Ball;

/// @reflect
typedef struct
{
    Vector2 player_pos;
    Ball    ball;
    float   health;
    int     level;
    char   *player_name;

    DamageComponent damage;

    uint8_t game_flags;

    unsigned int other_flags;

    unsigned char current_tile;

    /// @private
    uint32_t internal_count;

    void *userdata; /// @private

    long long score;

    uint8_t grid[9];

    unsigned char sliding_window[16];

    float history[MAX_ARR_LEN];

    Vector2 **waypoints;

    Vector2 enemy_positions[20];
} Game;
