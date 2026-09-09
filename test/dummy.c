#include <cmyreflection.h>

int main(void)
{
    int x = 0;
    set_field_int(NULL, NULL, x);
    set_field_float(NULL, NULL, 4.0f);
    set_field_str(NULL, NULL, "test");
    return x;
}
