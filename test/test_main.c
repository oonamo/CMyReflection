#include <unity.h>
#include <unity_fixture.h>

static void RunAllTests(void)
{
    RUN_TEST_GROUP(CORE);
    RUN_TEST_GROUP(SETTER);
    RUN_TEST_GROUP(GETTER);
    RUN_TEST_GROUP(ARRAY);
    RUN_TEST_GROUP(PATH);
    RUN_TEST_GROUP(ENUM);
    RUN_TEST_GROUP(VISITOR);
    RUN_TEST_GROUP(README);
}

int main(int argc, const char *argv[])
{
    return UnityMain(argc, argv, RunAllTests);
}
