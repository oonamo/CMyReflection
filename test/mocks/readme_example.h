#ifndef _README_EXAMPLE_MOCK_H
#define _README_EXAMPLE_MOCK_H

#include <stdint.h>

// cmy:reflect
typedef struct
{
    float voltage;
    float temp;
} SensorData;

// cmy:reflect
typedef enum
{
    DEVICE_RX,
    DEVICE_TX,
} DeviceState;

// cmy:reflect
typedef struct
{
    char        device_id[32];
    int         baud_rate;
    SensorData  data;
    DeviceState state;

    // cmy:readonly
    uint64_t uuid;
} IoTDevice;

// cmy:reflect
// cmy:unchecked
typedef enum
{
    MANAGER_NONE  = 1 << 0,
    MANAGER_READ  = 1 << 1,
    MANAGER_WRITE = 1 << 2,
} ManagerPermissions;

#define MAX_BUF_LEN 64

// cmy:reflect
typedef struct
{
    unsigned char      op_mode;

    // cmy:readonly
    ManagerPermissions permissions;

    char               device_location[MAX_BUF_LEN];
    IoTDevice          devices[8];
} DeviceManager;

#endif // _README_EXAMPLE_MOCK_H
