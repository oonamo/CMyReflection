#include "stuff.h"
#include <stdint.h>
#include <stddef.h>

typedef struct
{
    char *format_str;
    char *desc;
} AdditionalData;

// cmy:deftag description(desc)
// cmy:sets (AdditionalData*)user_data->desc = {desc}

// cmy:deftag format(format_str)
// cmy:sets (AdditionalData*)user_data->format_str = {format_str}

// cmy:ifhastag format
// cmy:creates print_field_{{type}}
// cmy:requires GET
// cmy:calls
///     printf((AdditionalData*)user_data->format_str, value);
// cmy:endcall

// cmy:reflect
typedef enum
{
    BALL_TYPE_SMALL = 0,
    BALL_TYPE_MEDIUM,
    BALL_TYPE_BIG,

    // cmy:private
    BALL_TYPE_NONE,
} BallSize;

// cmy:reflect
// cmy:enum(TYPE_VEC2)
typedef struct
{
    float x;
    float y;
} Vector2;

#define MAX_ARR_LEN 256

// cmy:reflect
typedef struct
{
    Vector2  speed;
    float    radius;
    BallSize size;
} Ball;

// cmy:reflect
typedef struct
{
    Vector2 player_pos;
    Ball    ball;
    float   health;
    int     level;
    char   *player_name;

    DamageComponent damage;

    // cmy:readonly
    uint8_t game_flags;

    // cmy:writeonly
    uint32_t hash;

    unsigned char current_tile;

    // cmy:private
    uint32_t internal_count;

    void *userdata; // cmy:private

    long long score;

    uint8_t grid[9];

    unsigned char sliding_window[16];

    float history[MAX_ARR_LEN];

    size_t   num_waypoints;
    Vector2 *waypoints; // cmy:length(num_waypoints)

    Vector2 enemy_positions[20];

    const char *name;
} Game;
