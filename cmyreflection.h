#ifndef _CMYREFLECTION_H
#define _CMYREFLECTION_H

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

typedef enum
{
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_STRING,

#ifdef CMYREFLECTION_REFLECTION_TYPES
    CMYREFLECTION_REFLECTION_TYPES
#endif

} FieldType;

typedef struct
{
    const char *name;
    FieldType type;
    size_t offset;
    size_t size;
} FieldInfo;

const FieldInfo *find_field(const FieldInfo *meta, size_t count,
                            const char *name);

bool set_field_value(void *instance, const FieldInfo *field,
                     const void *new_value);

#define DEFINE_FIELD_SETTER_PROTOTYPE(Suffix, CType)                           \
    bool set_field_##Suffix(void *instance, const FieldInfo *field,            \
                            CType value);

DEFINE_FIELD_SETTER_PROTOTYPE(int, int);
DEFINE_FIELD_SETTER_PROTOTYPE(float, float);
DEFINE_FIELD_SETTER_PROTOTYPE(str, char *);

#define DEFINE_FIELD_SETTER(Suffix, EnumVal, CType)                            \
    bool set_field_##Suffix(void *instance, const FieldInfo *field,            \
                            CType value)                                       \
    {                                                                          \
        if (field && field->type == EnumVal)                                   \
        {                                                                      \
            return set_field_value(instance, field, &value);                   \
        }                                                                      \
        return false;                                                          \
    }

#endif // _CMYREFLECTION_H

#define CMYREFLECTION_IMPLEMENTATION

#ifdef CMYREFLECTION_IMPLEMENTATION

const FieldInfo *find_field(const FieldInfo *meta, size_t count,
                            const char *name)
{
    for (size_t i = 0; i < count; i++)
    {
        if (strcmp(meta[i].name, name) == 0)
        {
            return &meta[i];
        }
    }

    return false;
}

bool set_field_value(void *instance, const FieldInfo *field,
                     const void *new_value)
{
    if (!instance || !field || !new_value)
    {
        return false;
    }

    void *field_ptr = (char *)instance + field->offset;
    memcpy(field_ptr, new_value, field->size);

    return true;
}

DEFINE_FIELD_SETTER(int, TYPE_INT, int)
DEFINE_FIELD_SETTER(float, TYPE_FLOAT, float)
DEFINE_FIELD_SETTER(str, TYPE_STRING, char *)

#endif // CMYREFLECTION_IMPLEMENTATION
