#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)
#define STRWRAP(x, delim) delim STRINGIFY(x) delim
#define QUOTE_VALUE(x) STRWRAP(x, "\"")
#define QUOTE(x) STRINGIFY(x)
