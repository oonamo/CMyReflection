#include <stdlib.h>

typedef enum
{
    t_a,
    t_b,
    t_c
} custom_enums;

#define CMYREFLECTION_TYPE_ENUM_DEF custom_enums
#define CMYREFLECTION_IMPLEMENTATION
#include <cmyreflection.h>

int main(void)
{
    int x = 0;
    x     = x >> 2;

    set_field_value(NULL, NULL, NULL, 0);
    return x;
}
