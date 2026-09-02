#define CMYREFLECTION_REFLECTION_TYPES TYPE_VECTOR2, TYPE_GAMEOBJECT,
#define CMYREFLECTION_IMPLEMENTATION
#include "../cmyreflection.h"
#include <stdio.h>

typedef struct
{
    float x, y;
} Vector2;

DEFINE_FIELD_SETTER(vec2, TYPE_VECTOR2, Vector2);

const FieldInfo Player_Metadata[] = {
    {"position", TYPE_VECTOR2, 0, sizeof(Vector2)} // Note the sizeof!
};

int main()
{
    struct
    {
        Vector2 position;
    } my_player = {0};

    Vector2 new_pos = {10.5f, 20.0f};
    set_field_vec2(&my_player, &Player_Metadata[0], new_pos);

    printf("Player pos: %.1f, %.1f\n", my_player.position.x,
           my_player.position.y);
    return 0;
}
