#ifndef _README_EXAMPLE_MOCK_H
#define _README_EXAMPLE_MOCK_H

/// @reflect
#include <stdint.h>
typedef struct
{
    float voltage;
    float temp;
} SensorData;

/// @reflect
typedef struct
{
    char device_id[32];
    int baud_rate;
    SensorData data;

    /// @private
    uint64_t uuid;
} IoTDevice;

#define MAX_BUF_LEN 64

/// @reflect
typedef struct
{
    char device_location[MAX_BUF_LEN];
    IoTDevice devices[8];
    unsigned char op_mode;
    uint32_t flags;
} DeviceManager;

#endif // _README_EXAMPLE_MOCK_H
