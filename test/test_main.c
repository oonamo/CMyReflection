#include <unity.h>
#include <unity_fixture.h>

static void RunAllTests(void)
{
    RUN_TEST_GROUP(Unit);
    RUN_TEST_GROUP(IoT);
}

int main(int argc, const char *argv[])
{
    return UnityMain(argc, argv, RunAllTests);
}
