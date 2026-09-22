#ifndef TYPES_H
#define TYPES_H

#include <stddef.h>

// cmy:reflect
typedef enum
{
    // cmy:display("*")
    MUL,

    // cmy:display("^-1")
    INVERSE,

    // cmy:display("^T")
    TRANSPOSE,

    // cmy:display("det")
    DET,
} Operation;

// cmy:reflect
typedef struct
{
    float *data;
    size_t cols;
    size_t rows;
} Matrix;

// cmy:reflect
typedef struct
{
    char  *buf;
    size_t buflen;
} StringView;

// cmy:reflect
typedef struct
{
    char       shortname;
    StringView name;
    Matrix    matrix;
} Variable;

// cmy:reflect
typedef struct
{
    Variable  lhs;
    Variable  rhs;

    Operation op;
} Expression;

#endif // TYPES_H
