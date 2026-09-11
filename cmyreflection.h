#ifndef _CMYREFLECTION_H
#define _CMYREFLECTION_H

#ifdef _WIN32
    #define _CRT_SECURE_NO_WARNINGS
#endif

#define CMYREFLECTION_MAJOR 0
#define CMYREFLECTION_MINOR 1
#define CMYREFLECTION_PATCH 0

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#ifdef CMYREFLECTION_USE_DEFAULT_TYPES
typedef enum
{
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_STR,

    #ifdef CMYREFLECTION_REFLECTION_TYPES
    CMYREFLECTION_REFLECTION_TYPES
    #endif
} FieldType;
#endif // CMYREFLECTION_USE_DEFAULT_TYPES

#if defined(CMYREFLECTION_TYPE_ENUM_DEF)
    #define FIELD_TYPE CMYREFLECTION_TYPE_ENUM_DEF
#elif !defined(CMYREFLECTION_USE_DEFAULT_TYPES) && !defined(CMYREFLECTION_PARSED)
    #define FIELD_TYPE int
#else
    #define FIELD_TYPE FieldType
#endif

typedef enum
{
    REFLECT_OK = 0,            /*!< Ok */
    REFLECT_ERR_NULL_PTR,      /*!< A null pointer was passed as a parameter */
    REFLECT_ERR_TYPE_MISMATCH, /*!< A type mismatch occured */
    REFLECT_ERR_OUT_OF_BOUNDS, /*!< Memory requested was out of bounds */
    REFLECT_ERR_ENUM_INVALID,  /*!< Checked enum is not a member of the enum */
    REFLECT_ERR_TYPE_INVALID,
    REFLECT_ERR_ACCESS_DENIED,
} ReflectResult;

typedef enum
{
    FIELD_ACCESS_READ  = 1 << 0,
    FIELD_ACCESS_WRITE = 1 << 1,
    FIELD_ACCESS_RW    = FIELD_ACCESS_READ | FIELD_ACCESS_WRITE
} FieldAccessFlags;

typedef struct
{
    const char      *name;   /*!< Name of field */
    FIELD_TYPE       type;   /*!< Type of field */
    size_t           offset; /*!< Struct offset of field */
    size_t           size;   /*!< sizeof type */
    size_t           count;  /*!< Number of array elements in field */
    FieldAccessFlags flags;  /*!< Access flags */
} FieldInfo;

typedef struct
{
    const FieldInfo *fields; /*!< Members of struct  */
    size_t           count;  /*!< Number of members in struct */
} StructMetaData;

#define MetaData_FromName(StructName)                                                              \
    (StructMetaData)                                                                               \
    {                                                                                              \
        StructName##_Metadata, StructName##_FieldCount                                             \
    }

typedef struct
{
    int         value; /*!< Integer value of enum member */
    const char *name;  /*!< String literal of enum member */
} EnumMemberInfo;

typedef struct
{
    const EnumMemberInfo *members; /*!< Members of enum */
    size_t                count;   /*!< Numbers of members in enum */
} EnumMetaData;

#define EnumMetaData_FromName(EnumName)                                                            \
    (EnumMetaData)                                                                                 \
    {                                                                                              \
        EnumName##_Members, EnumName##_MemberCount                                                 \
    }

#define Find_Struct_Field(MetaStruct, FieldName)                                                   \
    find_field((MetaStruct).fields, (MetaStruct).count, FieldName)

#define Find_Enum_Member(MetaEnum, MemberName)                                                     \
    find_member((MetaEnum).members, (MetaEnum).count, MemberName)

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
ReflectResult get_struct_metadata(FIELD_TYPE type, StructMetaData *out_meta);

/**
 * @brief Get's the enum's metadata
 *
 * @note Implemented in python generation script
 *
 * @param type     [in] Type of enum
 * @param out_meta [out] The returned enum metadata
 *
 * @return true if found, false otherwise
 */
ReflectResult get_enum_metadata(FIELD_TYPE type, EnumMetaData *out_meta);

/**
 * @brief Safely sets a field given metadata
 *
 * @note Implemented in python generation script
 *
 * @param instance      [out] Instance to write
 * @param field         [in]  Metadata of instance
 * @param value         [in]  Value to write to
 * @param element_count [in]  elements to write (if array)
 *
 * @return true if found, false otherwise
 */
ReflectResult
safe_set_field(void *instance, const FieldInfo *field, const void *value, size_t element_count);

/**
 * @brief Gets the name of the type given
 *
 * @note Implemented in python generation script
 *
 * @param type [in] Type of enum to convert
 *
 * @return name of the enum, NULL if not implemented
 */
const char *get_name_of_type(FIELD_TYPE type);

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
 * @brief Find's a member in a struct
 *
 * @param meta  [in] Array of FieldInfo
 * @param count [in] Number of elements in meta
 * @param name  [in] Name of field
 *
 * @return Pointer to the field, NULL if not found
 */
const EnumMemberInfo *
find_member(const EnumMemberInfo *meta, size_t member_count, const char *name);

/**
 * @brief Gets the string name of an enum member given its integer value
 *
 * @param meta         [in] Array of EnumMemberInfo
 * @param member_count [in] Number of elements in meta
 * @param value        [in] Integer value to find
 *
 * @return String name of the member, NULL if not found
 */
const char *get_enum_member_name(const EnumMemberInfo *meta, size_t member_count, int value);

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
ReflectResult
set_field_value(void *instance, const FieldInfo *field, const void *new_value, size_t write_size);

/**
 * @brief Safely gets a field value
 *
 * @param instance  [in]  Pointer to struct instance
 * @param field     [in]  Field to read from
 * @param out_value [out] Buffer to copy data into
 * @param read_size [in]  Number of bytes expected
 *
 * @return true if successful, false otherwise
 */
ReflectResult
get_field_value(const void *instance, const FieldInfo *field, void *out_value, size_t read_size);

#define DEFINE_FIELD_SETTER(Suffix, EnumVal, CType)                                                \
    static inline ReflectResult set_field_##Suffix(                                                \
        void *instance, const FieldInfo *field, CType value)                                       \
    {                                                                                              \
        if (!instance || !field)                                                                   \
        {                                                                                          \
            return REFLECT_ERR_NULL_PTR;                                                           \
        }                                                                                          \
        if (field->type != EnumVal)                                                                \
        {                                                                                          \
            return REFLECT_ERR_TYPE_MISMATCH;                                                      \
        }                                                                                          \
        return set_field_value(instance, field, &value, sizeof(CType));                            \
    }

#define DEFINE_FIELD_GETTER(Suffix, EnumVal, CType)                                                \
    static inline ReflectResult get_field_##Suffix(                                                \
        void *instance, const FieldInfo *field, CType *out_value)                                  \
    {                                                                                              \
        if (!instance || !field)                                                                   \
        {                                                                                          \
            return REFLECT_ERR_NULL_PTR;                                                           \
        }                                                                                          \
        if (field->type != EnumVal)                                                                \
        {                                                                                          \
            return REFLECT_ERR_TYPE_MISMATCH;                                                      \
        }                                                                                          \
        return get_field_value(instance, field, out_value, sizeof(CType));                         \
    }

#define DEFINE_ENUM_SETTER(Suffix, EnumVal, CType, validator)                                      \
    static inline ReflectResult set_field_##Suffix(                                                \
        void *instance, const FieldInfo *field, CType value)                                       \
    {                                                                                              \
        if (!instance || !field)                                                                   \
        {                                                                                          \
            return REFLECT_ERR_NULL_PTR;                                                           \
        }                                                                                          \
        if (field->type != EnumVal)                                                                \
        {                                                                                          \
            return REFLECT_ERR_TYPE_MISMATCH;                                                      \
        }                                                                                          \
        if (!validator(value))                                                                     \
        {                                                                                          \
            return REFLECT_ERR_ENUM_INVALID;                                                       \
        }                                                                                          \
        return set_field_value(instance, field, &value, sizeof(CType));                            \
    }

#define DEFINE_ARRAY_SETTER(Suffix, EnumVal, CType, DownCastType)                                  \
    static inline ReflectResult set_field_##Suffix(                                                \
        void *instance, const FieldInfo *field, CType value, size_t element_count)                 \
    {                                                                                              \
        if (!instance || !field)                                                                   \
        {                                                                                          \
            return REFLECT_ERR_NULL_PTR;                                                           \
        }                                                                                          \
        if (field->type != EnumVal)                                                                \
        {                                                                                          \
            return REFLECT_ERR_TYPE_MISMATCH;                                                      \
        }                                                                                          \
        if (element_count > field->count)                                                          \
        {                                                                                          \
            return REFLECT_ERR_OUT_OF_BOUNDS;                                                      \
        }                                                                                          \
        return set_field_value(instance, field, value, element_count * sizeof(DownCastType));      \
    }

#define DEFINE_ARRAY_GETTER(Suffix, EnumVal, CType, DownCastType)                                  \
    static inline bool get_field_##Suffix(                                                         \
        void *instance, const FieldInfo *field, CType value, size_t element_count)                 \
    {                                                                                              \
        if (!instance || !field)                                                                   \
        {                                                                                          \
            return REFLECT_ERR_NULL_PTR;                                                           \
        }                                                                                          \
        if (field->type != EnumVal)                                                                \
        {                                                                                          \
            return REFLECT_ERR_TYPE_MISMATCH;                                                      \
        }                                                                                          \
        if (element_count > field->count)                                                          \
        {                                                                                          \
            return REFLECT_ERR_OUT_OF_BOUNDS;                                                      \
        }                                                                                          \
        return get_field_value(instance, field, value, element_count * sizeof(DownCastType));      \
    }

#if defined(CMYREFLECTION_USE_DEFAULT_TYPES)
DEFINE_FIELD_SETTER(int, TYPE_INT, int)
DEFINE_FIELD_GETTER(int, TYPE_INT, int)

DEFINE_FIELD_SETTER(float, TYPE_FLOAT, float)
DEFINE_FIELD_GETTER(float, TYPE_FLOAT, float)

DEFINE_FIELD_SETTER(str, TYPE_STR, char *)
DEFINE_FIELD_GETTER(str, TYPE_STR, char *)
#endif

#endif // _CMYREFLECTION_H

#ifdef CMYREFLECTION_IMPLEMENTATION

#ifdef CMYREFLECTION_REGISTRY

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

        if (next)
        {
            current_instance = (char *)current_instance + current_field->offset;
            if (index >= 0)
            {
                if ((size_t)index >= current_field->count)
                {
                    return NULL;
                }

                // Shift instance to correct index
                size_t elem_size = current_field->size / current_field->count;
                current_instance = (char *)current_instance + ((size_t)index * elem_size);
            }
            StructMetaData next_meta;
            if (get_struct_metadata(current_field->type, &next_meta) != REFLECT_OK)
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

const EnumMemberInfo *find_member(const EnumMemberInfo *meta, size_t member_count, const char *name)
{
    for (size_t i = 0; i < member_count; i++)
    {
        if (strcmp(meta[i].name, name) == 0)
        {
            return &meta[i];
        }
    }

    return NULL;
}

const char *get_enum_member_name(const EnumMemberInfo *meta, size_t member_count, int value)
{
    for (size_t i = 0; i < member_count; i++)
    {
        if (meta[i].value == value)
        {
            return meta[i].name;
        }
    }
    return NULL;
}

ReflectResult
set_field_value(void *instance, const FieldInfo *field, const void *new_value, size_t write_size)
{
    if (!instance || !field || !new_value)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    if (!(field->flags & FIELD_ACCESS_WRITE))
    {
        return REFLECT_ERR_ACCESS_DENIED;
    }

    if (write_size > field->size)
    {
        return REFLECT_ERR_OUT_OF_BOUNDS;
    }

    void *field_ptr = (char *)instance + field->offset;
    memcpy(field_ptr, new_value, write_size);

    return REFLECT_OK;
}

ReflectResult
get_field_value(const void *instance, const FieldInfo *field, void *out_value, size_t read_size)
{
    if (!instance || !field || !out_value)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    if (!(field->flags & FIELD_ACCESS_READ))
    {
        return REFLECT_ERR_ACCESS_DENIED;
    }

    if (read_size > field->size)
    {
        return REFLECT_ERR_OUT_OF_BOUNDS;
    }

    const void *field_ptr = (const char *)instance + field->offset;
    memcpy(out_value, field_ptr, read_size);

    return REFLECT_OK;
}

#endif // CMYREFLECTION_IMPLEMENTATION
