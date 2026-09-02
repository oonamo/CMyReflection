#ifndef _CMYREFLECTION_H
#define _CMYREFLECTION_H

#define CMYREFLECTION_MAJOR 0
#define CMYREFLECTION_MINOR 1
#define CMYREFLECTION_PATCH 0

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
    const char *name;   /*!< Name of field */
    FieldType   type;   /*!< Type of field */
    size_t      offset; /*!< Struct offset of field */
    size_t      size;   /*!< sizeof type */
    size_t      count;  /*!< Number of array elements in field */
} FieldInfo;

typedef struct
{
    const FieldInfo *fields; /*!< Members of struct  */
    size_t           count;  /*!< Number of members in struct */
} StructMetaData;

/**
 * @brief Get's the struct's metadata
 *
 * @note Implemented in python generation script
 *
 * @param type     [in] Type of struct
 * @param out_meta [out] The returned struct metadata
 *
 * @return true if found, false otherwise
 */
bool get_struct_metadata(FieldType type, StructMetaData *out_meta);

/**
 * @brief Finds the struct containing the path
 *
 * @param base_instance [in] Struct to begin traversal
 * @param base_meta     [in] FieldInfo of root struct
 * @param base_count    [in] Number of fields in root struct
 * @param path          [in] string path to look for
 * @param out_leaf_field [out] FieldInfo returned if found
 *
 * @return Pointer to the resolved struct
 */
void *resolve_field_path(void             *base_instance,
                         const FieldInfo  *base_meta,
                         size_t            base_count,
                         const char       *path,
                         const FieldInfo **out_leaf_field);

/**
 * @brief Find's a field in a struct
 *
 * @param meta  [in] Array of FieldInfo
 * @param count [in] Number of elements in meta
 * @param name  [in] Name of field
 *
 * @return Pointer to the field, NULL if not found
 */
const FieldInfo *find_field(const FieldInfo *meta, size_t count, const char *name);

/**
 * @brief Safely sets a field value
 *
 * @param instance   [in] Pointer to struct instance to write to
 * @param field      [in] Field to write to
 * @param new_value  [in] Value to set
 * @param write_size [in] Number of bytes to write
 *
 * @return true if successful, false otherwise
 */
bool set_field_value(void            *instance,
                     const FieldInfo *field,
                     const void      *new_value,
                     size_t           write_size);

#define DEFINE_FIELD_SETTER(Suffix, EnumVal, CType)                                                \
    static inline bool set_field_##Suffix(void *instance, const FieldInfo *field, CType value)     \
    {                                                                                              \
        if (field && field->type == EnumVal)                                                       \
        {                                                                                          \
            return set_field_value(instance, field, &value, sizeof(CType));                        \
        }                                                                                          \
        return false;                                                                              \
    }

#define DEFINE_ARRAY_SETTER(Suffix, EnumVal, CType, DownCastType)                                  \
    static inline bool set_field_##Suffix(                                                         \
        void *instance, const FieldInfo *field, CType value, size_t element_count)                 \
    {                                                                                              \
        if (field && field->type == EnumVal)                                                       \
        {                                                                                          \
            if (element_count > field->count)                                                      \
            {                                                                                      \
                return false;                                                                      \
            }                                                                                      \
            return set_field_value(instance, field, value, element_count * sizeof(DownCastType));  \
        }                                                                                          \
        return false;                                                                              \
    }

#ifndef CMYREFLECTION_PARSED
DEFINE_FIELD_SETTER(int, TYPE_INT, int);
DEFINE_FIELD_SETTER(float, TYPE_FLOAT, float);
DEFINE_FIELD_SETTER(str, TYPE_STR, char *);
#endif

#endif // _CMYREFLECTION_H

#ifdef CMYREFLECTION_IMPLEMENTATION

#ifdef CMYREFLECTION_REGISTRY

    #ifdef _WIN32
        #define _CRT_SECURE_NO_WARNINGS
    #endif

    #include <stdlib.h>

void *resolve_field_path(void             *base_instance,
                         const FieldInfo  *base_meta,
                         size_t            base_count,
                         const char       *path,
                         const FieldInfo **out_leaf_field)
{
    if (!base_instance || !base_meta || !path || !out_leaf_field)
    {
        return NULL;
    }

    char buffer[256];
    strncpy(buffer, path, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';

    char *token = buffer;
    char *next  = strchr(token, '.');

    void            *current_instance = base_instance;
    const FieldInfo *current_meta     = base_meta;
    size_t           current_count    = base_count;
    const FieldInfo *current_field    = NULL;

    while (token)
    {
        if (next)
        {
            // Chop seperator for find_field to look for current field
            *next = '\0';
        }

        char *bracket = strchr(token, '[');
        int   index   = -1;
        if (bracket)
        {
            *bracket = '\0';
            index    = atoi(bracket + 1);
        }

        current_field = find_field(current_meta, current_count, token);

        if (!current_field)
        {
            return NULL;
        }

        current_instance = (char *)current_instance + current_field->offset;
        if (index >= 0)
        {
            if (index >= current_field->count)
            {
                return NULL;
            }

            // Shift instance to correct index
            size_t elem_size = current_field->size / current_field->count;
            current_instance = (char *)current_instance + (index * elem_size);
        }

        if (next)
        {
            StructMetaData next_meta;
            if (!get_struct_metadata(current_field->type, &next_meta))
            {
                return NULL;
            }

            current_meta  = next_meta.fields;
            current_count = next_meta.count;

            token = next + 1;
            next  = strchr(token, '.');
        }
        else
        {
            break;
        }
    }

    *out_leaf_field = current_field;
    return current_instance;
}

#endif // CMYREFLECTION_REGISTRY

const FieldInfo *find_field(const FieldInfo *meta, size_t count, const char *name)
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

bool set_field_value(void            *instance,
                     const FieldInfo *field,
                     const void      *new_value,
                     size_t           write_size)
{
    if (!instance || !field || !new_value)
    {
        return false;
    }

    if (write_size > field->size)
    {
        return false;
    }

    void *field_ptr = (char *)instance + field->offset;
    memcpy(field_ptr, new_value, write_size);

    return true;
}

#endif // CMYREFLECTION_IMPLEMENTATION
