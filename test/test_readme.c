#include <unity.h>
#include <unity_fixture.h>

#include "mocks/game_type.h"
#include "mocks/readme_example.h"

#include "mocks/generated.inc"

TEST_GROUP(IoT);

TEST_SETUP(IoT) {}
TEST_TEAR_DOWN(IoT) {}

TEST(IoT, Can_Do_Readme_Things)
{
    DeviceManager manager = {0};

    const FieldInfo *leaf = NULL;
    void *target = resolve_field_path(&manager, DeviceManager_Metadata,
                                      DeviceManager_FieldCount,
                                      "devices[2].data.voltage", &leaf);

    TEST_ASSERT_NOT_NULL(target);
    TEST_ASSERT_NOT_NULL(leaf);

    set_field_float(target, leaf, 240.5f);
    TEST_ASSERT_EQUAL_FLOAT(240.5f, manager.devices[2].data.voltage);

    const FieldInfo *location_field = find_field(
        DeviceManager_Metadata, DeviceManager_FieldCount, "device_location");

    char *location = "bedroom1";
    TEST_ASSERT_FALSE(set_field_str(&manager, location_field, location));
    TEST_ASSERT_TRUE(set_field_char_arr(&manager, location_field, location,
                                        strlen(location)));

    TEST_ASSERT_EQUAL_STRING("device_location", location_field->name);
    TEST_ASSERT_EQUAL(TYPE_CHAR_ARR, location_field->type);
    TEST_ASSERT_EQUAL_STRING("bedroom1", manager.device_location);
}

TEST_GROUP_RUNNER(IoT) { RUN_TEST_CASE(IoT, Can_Do_Readme_Things); }
