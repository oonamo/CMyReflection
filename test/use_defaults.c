#define CMYREFLECTION_USE_DEFAULT_TYPES
#define CMYREFLECTION_IMPLEMENTATION
#include <cmyreflection.h>

int main(void)
{
    int   i = 0;
    float f = 0;
    char *s = 0;

    set_field_int(NULL, NULL, i);
    get_field_int(NULL, NULL, &i);

    set_field_float(NULL, NULL, f);
    get_field_float(NULL, NULL, &f);

    set_field_str(NULL, NULL, s);
    get_field_str(NULL, NULL, &s);
}
