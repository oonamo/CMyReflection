#ifndef _CMYREFLECTION_H
#define _CMYREFLECTION_H

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#ifndef CMYREFLECTION_PARSED
typedef enum
{
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_STR,

#ifdef CMYREFLECTION_REFLECTION_TYPES
    CMYREFLECTION_REFLECTION_TYPES
#endif
} FieldType;
#endif // CMYREFLECTION_PARSED

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

#define DEFINE_FIELD_SETTER(Suffix, EnumVal, CType)                            \
    static inline bool set_field_##Suffix(void *instance,                      \
                                          const FieldInfo *field, CType value) \
    {                                                                          \
        if (field && field->type == EnumVal)                                   \
        {                                                                      \
            return set_field_value(instance, field, &value);                   \
        }                                                                      \
        return false;                                                          \
    }


#ifndef CMYREFLECTION_PARSED
DEFINE_FIELD_SETTER(int, TYPE_INT, int);
DEFINE_FIELD_SETTER(float, TYPE_FLOAT, float);
DEFINE_FIELD_SETTER(str, TYPE_STR, char *);
#endif

#endif // _CMYREFLECTION_H

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

    return NULL;
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

#endif // CMYREFLECTION_IMPLEMENTATION
