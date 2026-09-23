/*
 * ================================================================================
 * CMyReflection - A simple reflection framework for C99+
 *
 * Version: 0.0.0
 * LICENSE: MIT
 * ================================================================================
 *
 * HOW TO USE THIS LIBRARY
 *
 * 1. In EXACTLY ONE source C file, define CMYREFLECTION_IMPLEMENTATION before including
 *    this header to create the implementation
 *    #define CMYREFLECTION_IMPLEMENTATION
 *    #include "cmyreflection.h"
 * 2. If using the parser, define REFLECTION_IMPLEMENTATION before including the generated header
 *
 *    // 1. Include your files used for type generation
 *    #include "my_types.h"
 *
 *    // 2. Define the implementation macros in exactly one file
 *    #define CMYREFLECTION_IMPLEMENTATION
 *    #define REFLECTION_IMPLEMENTATION
 *
 *    // 3. Include the generated header
 *    #include "refl.generated.h"
 * 3. In any other file, inaclude the headers
 *    // If using the parser
 *    #include "refl.generated.h"
 *
 *    // If using standalone (requires implementing metadata)
 *    #include "cmyreflection.h"
 * ================================================================================
 * ARCHITECTURE & GENERATOR
 *
 * This library provides the runtime engine. The reflection data is generated
 * by `cmy_reflector.py` by parsing source code.
 * See the GitHub repository for documentation on the generator and plugins
 * (https://github.com/oonamo/CMyReflection)
 * ================================================================================
 */
#ifndef _CMYREFLECTION_H
#define _CMYREFLECTION_H

#ifdef _WIN32
    #define _CRT_SECURE_NO_WARNINGS
#endif

#define CMYREFLECTION_MAJOR 1 // x-release-please-major
#define CMYREFLECTION_MINOR 0 // x-release-please-minor
#define CMYREFLECTION_PATCH 1 // x-release-please-patch

#ifdef __cplusplus
extern "C"
{
#endif

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
    REFLECT_ERR_TYPE_INVALID,  /*!< Type is invalid */
    REFLECT_ERR_ACCESS_DENIED, /*!< Attempted to access field without sufficient permissions */
    REFLECT_ERR_NOT_FOUND,     /*!< Item was not found */
} ReflectResult;

typedef enum
{
    FIELD_ACCESS_READ  = 1 << 0,
    FIELD_ACCESS_WRITE = 1 << 1,
    FIELD_ACCESS_RW    = FIELD_ACCESS_READ | FIELD_ACCESS_WRITE
} FieldAccessFlags;

typedef struct
{
    const char      *name;              /*!< Name of field */
    FIELD_TYPE       type;              /*!< Type of field */
    size_t           offset;            /*!< Struct offset of field */
    size_t           size;              /*!< sizeof type */
    size_t           count;             /*!< Number of array elements in field */
    FieldAccessFlags flags;             /*!< Access flags */
    const char      *length_field_name; /*!< Associated field length string */
    void            *user_data;         /*!< User data */
} StructFieldInfo;

typedef struct
{
    const StructFieldInfo *fields; /*!< Members of struct  */
    size_t                 count;  /*!< Number of members in struct */
} StructMetaData;

/**
 * @brief Constructs a StructMetaData object for a given reflected struct
 *
 * @note Requires that `StructName_Metadata` and `StructName_FieldCount` are available in scope
 */
#define StructMetaData_FromName(StructName)                                                        \
    (StructMetaData)                                                                               \
    {                                                                                              \
        StructName##_Metadata, StructName##_FieldCount                                             \
    }

typedef struct
{
    int         value;     /*!< Integer value of enum member */
    const char *name;      /*!< String literal of enum member */
    void       *user_data; /*!< User data */
} EnumMemberInfo;

typedef struct
{
    const EnumMemberInfo *members; /*!< Members of enum */
    size_t                count;   /*!< Numbers of members in enum */
} EnumMetaData;

/**
 * @brief Constructs an EnumMetaData object for a given reflected enum
 *
 * @note Requires that `EnumName_Metadata` and `EnumName_FieldCount` are available in scope
 */
#define EnumMetaData_FromName(EnumName)                                                            \
    (EnumMetaData)                                                                                 \
    {                                                                                              \
        EnumName##_Members, EnumName##_MemberCount                                                 \
    }

/**
 * @brief Finds a struct field, given a field and metadat
 *
 * ```c
 * typedef struct {
 *   // ...
 *   int x;
 * } MyStruct;
 *
 * const StructFieldInfo* field = Find_Struct_Field(StructMetaData_FromName(MyStruct), "x");
 * ```
 */
#define Find_Struct_Field(MetaStruct, FieldName)                                                   \
    find_field((MetaStruct).fields, (MetaStruct).count, FieldName)

/**
 * @brief Finds a struct field, given a field and metadat
 *
 * ```c
 * typedef enum {
 *   // ...
 *   VALUE_A,
 * } MyEnum;
 *
 * const StructFieldInfo* field = Find_Enum_Member(EnumMetaData_FromName(MyEnum), "VALUE_A");
 * ```
 */
#define Find_Enum_Member(MetaEnum, MemberName)                                                     \
    find_member((MetaEnum).members, (MetaEnum).count, MemberName)

/**
 * @brief Get's the struct's metadata
 *
 * @note Implemented in python generation script
 *
 * ```c
 * StructMetaData meta = {};
 * get_struct_metadata(TYPE_STRUCT_MYSTRUCT, &meta);
 * if (get_struct_metadata(TYPE_STRUCT_MYSTRUCT, &meta) == REFLECT_OK) {
 *     // do stuff
 * }
 * ```
 *
 * @param type     [in] Type of struct
 * @param out_meta [out] The returned struct metadata
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult get_struct_metadata(FIELD_TYPE type, StructMetaData *out_meta);

/**
 * @brief Resolves the base type of a pointer or array enum.
 *
 * @note Implemented by the python script
 *
 * ```c
 * // Assumes TYPE_INT and TYPE_INT_PTR are defined
 * assert(TYPE_INT == get_base_type(TYPE_INT_PTR));
 * assert(TYPE_INT == get_base_type(TYPE_INT_ARR));
 * ```
 * @param type [in] The pointer type (e.g., TYPE_POST_PTR)
 * @return The underlying value type (e.g., TYPE_STRUCT_POST), or the original type if not a
 * pointer.
 */
FIELD_TYPE get_base_type(FIELD_TYPE type);

/**
 * @brief Gets the enum's metadata
 *
 * @note Implemented in python generation script
 *
 * ```c
 * EnumMetaData meta = {0};
 * if (get_enum_metadata(TYPE_ENUM_MYENUM, &meta) == REFLECT_OK) {
 *     // do stuff
 * }
 * ```
 * @param type     [in] Type of enum
 * @param out_meta [out] The returned enum metadata
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult get_enum_metadata(FIELD_TYPE type, EnumMetaData *out_meta);

/**
 * @brief Safely sets a field given metadata
 *
 * @note Implemented in python generation script.
 *
 * @param instance      [out] Instance to write
 * @param field         [in]  Metadata of instance
 * @param value         [in]  Value to write to
 * @param element_count [in]  elements to write (if array)
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult safe_set_field(void                  *instance,
                             const StructFieldInfo *field,
                             const void            *value,
                             size_t                 element_count);

/**
 * @brief Gets the name of the type given
 *
 * @note Implemented in python generation script
 *
 * ```c
 * assert(strcmp("TYPE_INT", get_name_of_type(TYPE_INT)) == 0);
 * ```
 *
 * @param type [in] Type of enum to convert
 *
 * @return name of the enum, NULL if not implemented
 */
const char *get_name_of_type(FIELD_TYPE type);

/**
 * @brief Finds the struct containing the path
 *
 * Evaluates a gdb-like path string against the provided metadata.
 * If the path is valid and accessible, the memory address of the parent
 * struct is returned, along with the out_leaf_field pointer to the field.
 *
 * ```c
 * DeviceManager manager = {0};
 * const StructFieldInfo* leaf = NULL;
 *
 * void *target = resolve_field_target(&manager,
 *                                     DeviceManager_Metadata,
 *                                     DeviceManager_FieldCount,
 *                                     "devices[2].data.voltage",
 *                                     &leaf)
 * if (target && leaf) {
 *    set_field_float(target, leaf, 240.5f);
 * }
 * ```
 *
 * @param base_instance  [in] Struct to begin traversal
 * @param base_meta      [in] FieldInfo of root struct
 * @param base_count     [in] Number of fields in root struct
 * @param path           [in] string path to look for
 * @param out_leaf_field [out] FieldInfo returned if found
 *
 * @return Pointer to the resolved struct, or NULL if not found
 */
void *resolve_field_path(void                   *base_instance,
                         const StructFieldInfo  *base_meta,
                         size_t                  base_count,
                         const char             *path,
                         const StructFieldInfo **out_leaf_field);

/**
 * @brief Resolves metadata for a specific field path without an instance.
 *
 * ```c
 * typedef struct {
 *   int x;
 * } StructA;
 *
 * typedef struct {
 *    StructA other_struct;
 * } StructB;
 *
 * // ...
 * const StructFieldInfo* field = resolve_field_metadata(StructB_Metadata, Struct2_Count,
 * "other_struct.x")
 * assert(field != NULL);
 * ```
 *
 * @param base_meta  [in] Array of FieldInfo representing the root struct
 * @param base_count [in] Number of elements in base_meta
 * @param path       [in] String path to the field (e.g., "nested.field[0]")
 *
 * @return Pointer to the resolved field's metadata, or NULL if not found
 */
const StructFieldInfo *
resolve_field_metadata(const StructFieldInfo *base_meta, size_t base_count, const char *path);

/**
 * @brief Queries an instance for a field. Can be nested
 *
 * @param instance  [in] Pointer to the root struct instance
 * @param meta      [in] Metadata of the root struct
 * @param query     [in] Field name or dot-delimited string path to look for
 * @param out_field [out] Pointer to the resolved FieldInfo
 *
 * @return Pointer to the resolved struct/field data, or NULL if not found
 */
void *reflect_query(void                   *instance,
                    const StructMetaData   *meta,
                    const char             *query,
                    const StructFieldInfo **out_field);

/**
 * @brief Find's a field in a struct
 *
 * ```c
 * typedef struct {
 *     int x;
 *     float y;
 * } StructA;
 *
 * // ...
 * const StructFieldInfo* field = find_field(StructA_Metadata, StructA_FieldCount, "y");
 * assert(field->type == TYPE_FLOAT);
 * ```
 *
 * @param meta  [in] Array of FieldInfo
 * @param count [in] Number of elements in meta
 * @param name  [in] Name of field
 *
 * @return Pointer to the field, NULL if not found
 */
const StructFieldInfo *find_field(const StructFieldInfo *meta, size_t count, const char *name);

/**
 * @brief Find's a member in a struct
 *
 * ```c
 * typedef enum {
 *     VALUE_A,
 *     VALUE_B,
 * } EnumA;
 *
 * // ...
 * const EnumMemberInfo* member = find_member(EnumA_Members, EnumA_MemberCount, "VALUE_A");
 * assert(field->type == TYPE_FLOAT);
 * ```
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
 * ```c
 * assert(strcmp("VALUE_A", get_enum_member_name(EnumA_Members, EnumA_MemberCount, VALUE_A)) == 0);
 * ```
 * @param meta         [in] Array of EnumMemberInfo
 * @param member_count [in] Number of elements in meta
 * @param value        [in] Integer value to find
 *
 * @return String name of the member, NULL if not found
 */
const char *get_enum_member_name(const EnumMemberInfo *meta, size_t member_count, int value);

/**
 * @brief Get's the size of the type
 *
 * @note Implemented in python script
 * ```c
 * assert(sizeof(int) == get_type_size(TYPE_INT));
 * ```
 * @param type [in] Type to check size
 *
 * @return The size of the type, or 0 if not found
 */
size_t get_type_size(FIELD_TYPE type);

/**
 * @brief Safely sets a field value
 *
 * @param instance   [in] Pointer to struct instance to write to
 * @param field      [in] Field to write to
 * @param new_value  [in] Value to set
 * @param write_size [in] Number of bytes to write
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult set_field_value(void                  *instance,
                              const StructFieldInfo *field,
                              const void            *new_value,
                              size_t                 write_size);

/**
 * @brief Safely gets a field value
 *
 * @param instance  [in]  Pointer to struct instance
 * @param field     [in]  Field to read from
 * @param out_value [out] Buffer to copy data into
 * @param read_size [in]  Number of bytes expected
 *
 * @return REFLECT_OK if successful, or an error code otherwise
 */
ReflectResult get_field_value(const void            *instance,
                              const StructFieldInfo *field,
                              void                  *out_value,
                              size_t                 read_size);

/**
 * @brief Retrieves a specific element from a statically allocated inline array.
 *
 * @param instance     [in] Pointer to the struct instance
 * @param field        [in] Metadata of the inline array field
 * @param index        [in] The array index to retrieve
 * @param out_value    [out] Buffer to copy the retrieved element into
 * @param element_size [in] Expected byte size of a single array element
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult get_array_element(const void            *instance,
                                const StructFieldInfo *field,
                                size_t                 index,
                                void                  *out_value,
                                size_t                 element_size);

/**
 * @brief Resolves the runtime length of a tagged dynamic array pointer.
 *
 * @param base_instance [in] Pointer to the parent struct instance
 * @param parent_type   [in] Type enum of the parent struct
 * @param field         [in] Metadata of the dynamically allocated array field
 * @param out_length    [out] Extracted runtime length of the array
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult get_dynamic_array_length(const void            *base_instance,
                                       FIELD_TYPE             parent_type,
                                       const StructFieldInfo *field,
                                       size_t                *out_length);
/**
 * @brief Safely writes data to a dynamically allocated array
 *
 * @param instance   [in] Pointer to the parent struct instance
 * @param field      [in] Metadata of the tagged pointer field
 * @param new_data   [in] Pointer to the data to write
 * @param write_size [in] Number of bytes to copy into the dynamic array memory
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult set_dynamic_array_data(void                  *instance,
                                     const StructFieldInfo *field,
                                     const void            *new_data,
                                     size_t                 write_size);

/**
 * @brief Safely reads data from a dynamically allocated array
 *
 * @param instance  [in] Pointer to the parent struct instance
 * @param field     [in] Metadata of the tagged pointer field
 * @param out_data  [out] Buffer to copy the retrieved array data into
 * @param read_size [in] Number of bytes expected to read
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult get_dynamic_array_data(const void            *instance,
                                     const StructFieldInfo *field,
                                     void                  *out_data,
                                     size_t                 read_size);

#define DEFINE_DYNAMIC_ARRAY_GETTER(Suffix, EnumVal, CType, DownCastType)                          \
    static inline ReflectResult get_dynamic_##Suffix(                                              \
        const void *instance, const StructFieldInfo *field, CType out_data, size_t element_count)  \
    {                                                                                              \
        if (!instance || !field)                                                                   \
        {                                                                                          \
            return REFLECT_ERR_NULL_PTR;                                                           \
        }                                                                                          \
        if (field->type != EnumVal)                                                                \
        {                                                                                          \
            return REFLECT_ERR_TYPE_MISMATCH;                                                      \
        }                                                                                          \
        return get_dynamic_array_data(                                                             \
            instance, field, (void *)out_data, element_count * sizeof(DownCastType));              \
    }

#define DEFINE_DYNAMIC_ARRAY_SETTER(Suffix, EnumVal, CType, DownCastType, ParentEnumVal)           \
    static inline ReflectResult set_dynamic_##Suffix(                                              \
        void *instance, const StructFieldInfo *field, CType new_data, size_t element_count)        \
    {                                                                                              \
        if (!instance || !field)                                                                   \
        {                                                                                          \
            return REFLECT_ERR_NULL_PTR;                                                           \
        }                                                                                          \
        if (field->type != EnumVal)                                                                \
        {                                                                                          \
            return REFLECT_ERR_TYPE_MISMATCH;                                                      \
        }                                                                                          \
        size_t        current_len = 0;                                                             \
        ReflectResult len_res =                                                                    \
            get_dynamic_array_length(instance, ParentEnumVal, field, &current_len);                \
        if (len_res != REFLECT_OK)                                                                 \
        {                                                                                          \
            return len_res;                                                                        \
        }                                                                                          \
        if (element_count > current_len)                                                           \
        {                                                                                          \
            return REFLECT_ERR_OUT_OF_BOUNDS;                                                      \
        }                                                                                          \
        return set_dynamic_array_data(                                                             \
            instance, field, new_data, element_count * sizeof(DownCastType));                      \
    }

/**
 * @brief Callback function type for iterating over struct fields.
 *
 * @param base_instance [in] Pointer to the struct instance being visited
 * @param field         [in] Metadata of the current field being visited
 * @param user_data     [in] User data passed through the traversal
 */
typedef void (*StructFieldVisitor)(const void            *base_instance,
                                   const StructFieldInfo *field,
                                   void                  *user_data);

/**
 * @brief Iterates over all fields of a struct and invokes a callback for each.
 *
 * ```c
 * void traverse_all(const void* base_instance, const StructFieldInfo* field, void* user_data)
 * {
 *     StructMetaData meta;
 *
 *     // If type is struct
 *     if (get_struct_metadata(field->type, &meta) == REFLECT_OK)
 *     {
 *         const void* next_base_instance = (const char*)(base_instance) + field->offset;
 *         visit_struct_fields(next_base_instance, field->type, traverse_all, NULL);
 *         return;
 *     }
 *     // Do some action on the primitive types
 * }
 * ```
 * @param instance  [in] Pointer to the struct instance
 * @param type      [in] Type enum of the struct to visit
 * @param visitor   [in] Callback function to execute per field
 * @param user_data [in] Pointer to arbitrary state data for the callback
 *
 * @return REFLECT_OK on success, or an error code otherwise
 */
ReflectResult visit_struct_fields(const void        *instance,
                                  FIELD_TYPE         type,
                                  StructFieldVisitor visitor,
                                  void              *user_data);

#define DEFINE_FIELD_SETTER(Suffix, EnumVal, CType)                                                \
    static inline ReflectResult set_field_##Suffix(                                                \
        void *instance, const StructFieldInfo *field, CType value)                                 \
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
        const void *instance, const StructFieldInfo *field, CType *out_value)                      \
    {                                                                                              \
        if (!instance || !field)                                                                   \
        {                                                                                          \
            return REFLECT_ERR_NULL_PTR;                                                           \
        }                                                                                          \
        if (field->type != EnumVal)                                                                \
        {                                                                                          \
            return REFLECT_ERR_TYPE_MISMATCH;                                                      \
        }                                                                                          \
        return get_field_value(instance, field, (void *)out_value, sizeof(CType));                 \
    }

#define DEFINE_ENUM_SETTER(Suffix, EnumVal, CType, validator)                                      \
    static inline ReflectResult set_field_##Suffix(                                                \
        void *instance, const StructFieldInfo *field, CType value)                                 \
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
        void *instance, const StructFieldInfo *field, CType value, size_t element_count)           \
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
    static inline ReflectResult get_field_##Suffix(                                                \
        const void *instance, const StructFieldInfo *field, CType value, size_t element_count)     \
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
        return get_field_value(                                                                    \
            instance, field, (void *)value, element_count * sizeof(DownCastType));                 \
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
#include <stdint.h>

#ifdef CMYREFLECTION_REGISTRY

    #include <stdlib.h>

    #include <stddef.h>

static ReflectResult resolve_path_internal(void                   *base_instance,
                                           const StructFieldInfo  *base_meta,
                                           size_t                  base_count,
                                           const char             *path,
                                           void                  **out_instance,
                                           const StructFieldInfo **out_leaf_field)
{
    if (!base_meta || !path || !out_leaf_field)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    char buffer[256];
    strncpy(buffer, path, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';

    char *token = buffer;
    char *next  = strchr(token, '.');

    void                  *current_instance = base_instance;
    const StructFieldInfo *current_meta     = base_meta;
    size_t                 current_count    = base_count;
    const StructFieldInfo *current_field    = NULL;

    while (token)
    {
        if (next)
        {
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
            return REFLECT_ERR_NOT_FOUND;
        }

        if (index >= 0 && (size_t)index >= current_field->count)
        {
            return REFLECT_ERR_NOT_FOUND;
        }

        if (next)
        {
            if (current_instance)
            {
                current_instance = (char *)current_instance + current_field->offset;
                if (index >= 0)
                {
                    size_t elem_size = current_field->size / current_field->count;
                    current_instance = (char *)current_instance + ((size_t)index * elem_size);
                }
            }

            StructMetaData next_meta;
            if (get_struct_metadata(current_field->type, &next_meta) != REFLECT_OK)
            {
                return REFLECT_ERR_TYPE_MISMATCH;
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
    if (out_instance)
    {
        *out_instance = current_instance;
    }
    return REFLECT_OK;
}

void *resolve_field_path(void                   *base_instance,
                         const StructFieldInfo  *base_meta,
                         size_t                  base_count,
                         const char             *path,
                         const StructFieldInfo **out_leaf_field)
{
    if (!base_instance)
    {
        return NULL;
    }

    void *resolved_instance = NULL;
    if (resolve_path_internal(
            base_instance, base_meta, base_count, path, &resolved_instance, out_leaf_field) ==
        REFLECT_OK)
    {
        return resolved_instance;
    }

    return NULL;
}

const StructFieldInfo *
resolve_field_metadata(const StructFieldInfo *base_meta, size_t base_count, const char *path)
{
    const StructFieldInfo *leaf = NULL;

    if (resolve_path_internal(NULL, base_meta, base_count, path, NULL, &leaf) == REFLECT_OK)
    {
        return leaf;
    }

    return NULL;
}

void *reflect_query(void                   *instance,
                    const StructMetaData   *meta,
                    const char             *query,
                    const StructFieldInfo **out_field)
{
    if (!instance || !meta || !query || !out_field)
    {
        return NULL;
    }

    // Fast path
    if (strpbrk(query, ".[") == NULL)
    {
        *out_field = find_field(meta->fields, meta->count, query);
        if (*out_field == NULL)
        {
            return NULL;
        }
        return instance;
    }

    // Slow path
    return resolve_field_path(instance, meta->fields, meta->count, query, out_field);
}

ReflectResult visit_struct_fields(const void        *instance,
                                  FIELD_TYPE         type,
                                  StructFieldVisitor visitor,
                                  void              *user_data)
{
    if (!visitor)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    StructMetaData meta;
    if (get_struct_metadata(type, &meta) != REFLECT_OK)
    {
        return REFLECT_ERR_TYPE_MISMATCH;
    }

    for (size_t i = 0; i < meta.count; i++)
    {
        const StructFieldInfo *field = &meta.fields[i];

        visitor(instance, field, user_data);
    }

    return REFLECT_OK;
}

ReflectResult get_dynamic_array_length(const void            *base_instance,
                                       FIELD_TYPE             parent_type,
                                       const StructFieldInfo *field,
                                       size_t                *out_length)
{
    if (!base_instance || !field || !out_length)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    if (field->length_field_name == NULL)
    {
        return REFLECT_ERR_TYPE_MISMATCH;
    }

    StructMetaData parent_meta;
    ReflectResult  meta_res = get_struct_metadata(parent_type, &parent_meta);
    if (meta_res != REFLECT_OK)
    {
        return meta_res;
    }

    const StructFieldInfo *len_field =
        find_field(parent_meta.fields, parent_meta.count, field->length_field_name);
    if (!len_field)
    {
        return REFLECT_ERR_NOT_FOUND;
    }

    const void *len_addr = (const char *)base_instance + len_field->offset;

    switch (len_field->size)
    {
    case 1:
        *out_length = (size_t)(*(const uint8_t *)len_addr);
        break;
    case 2:
        *out_length = (size_t)(*(const uint16_t *)len_addr);
        break;
    case 4:
        *out_length = (size_t)(*(const uint32_t *)len_addr);
        break;
    case 8:
        *out_length = (size_t)(*(const uint64_t *)len_addr);
        break;
    default:
        return REFLECT_ERR_TYPE_MISMATCH;
    }

    return REFLECT_OK;
}

#endif // CMYREFLECTION_REGISTRY

const StructFieldInfo *find_field(const StructFieldInfo *meta, size_t count, const char *name)
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

ReflectResult set_field_value(void                  *instance,
                              const StructFieldInfo *field,
                              const void            *new_value,
                              size_t                 write_size)
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

ReflectResult get_field_value(const void            *instance,
                              const StructFieldInfo *field,
                              void                  *out_value,
                              size_t                 read_size)
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

ReflectResult get_array_element(const void            *instance,
                                const StructFieldInfo *field,
                                size_t                 index,
                                void                  *out_value,
                                size_t                 element_size)
{
    if (!instance || !field || !out_value)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    if (index >= field->count)
    {
        return REFLECT_ERR_OUT_OF_BOUNDS;
    }

    size_t expected_elem_size = field->size / field->count;
    if (element_size != expected_elem_size)
    {
        return REFLECT_ERR_TYPE_MISMATCH;
    }

    const char *array_base = (const char *)instance + field->offset;
    const char *elem_ptr   = array_base + (index * expected_elem_size);

    memcpy(out_value, elem_ptr, expected_elem_size);

    return REFLECT_OK;
}

ReflectResult set_dynamic_array_data(void                  *instance,
                                     const StructFieldInfo *field,
                                     const void            *new_data,
                                     size_t                 write_size)
{
    if (!instance || !field || !new_data)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    if (!(field->flags & FIELD_ACCESS_WRITE))
    {
        return REFLECT_ERR_ACCESS_DENIED;
    }

    if (field->length_field_name == NULL)
    {
        return REFLECT_ERR_TYPE_MISMATCH;
    }

    void **ptr_addr = (void **)((char *)instance + field->offset);
    if (!*ptr_addr)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    memcpy(*ptr_addr, new_data, write_size);
    return REFLECT_OK;
}

ReflectResult get_dynamic_array_data(const void            *instance,
                                     const StructFieldInfo *field,
                                     void                  *out_data,
                                     size_t                 read_size)
{
    if (!instance || !field || !out_data)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    if (!(field->flags & FIELD_ACCESS_READ))
    {
        return REFLECT_ERR_ACCESS_DENIED;
    }

    if (field->length_field_name == NULL)
    {
        return REFLECT_ERR_TYPE_MISMATCH;
    }

    const void **ptr_addr = (const void **)((const char *)instance + field->offset);
    if (!*ptr_addr)
    {
        return REFLECT_ERR_NULL_PTR;
    }

    memcpy(out_data, *ptr_addr, read_size);
    return REFLECT_OK;
}

#endif // CMYREFLECTION_IMPLEMENTATION

#ifdef __cplusplus
}
#endif
