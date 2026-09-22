#include <stdio.h>
#include "types.h"

#define CMYREFLECTION_IMPLEMENTATION
#define REFLECTION_IMPLEMENTATION
#include "refl.generated.h"

#define JSON_BUF_LEN 32

typedef struct
{
    char   buf[JSON_BUF_LEN];
    size_t offset;
    size_t written;
} json_buf_stream_ctx;

void json_flush_buf_cb(const char *chunk, size_t len, void *user_ctx)
{
    json_buf_stream_ctx *ctx     = (json_buf_stream_ctx *)user_ctx;
    size_t               written = 0;

    while (written < len)
    {
        size_t space_left         = JSON_BUF_LEN - ctx->offset;
        size_t remaining_in_chunk = len - written;
        size_t bytes_to_copy = (remaining_in_chunk < space_left) ? remaining_in_chunk : space_left;

        memcpy(ctx->buf + ctx->offset, chunk + written, bytes_to_copy);
        written += bytes_to_copy;

        ctx->offset += bytes_to_copy;

        if (ctx->offset == JSON_BUF_LEN)
        {
            fwrite(ctx->buf, 1, JSON_BUF_LEN, stdout);
            ctx->written += JSON_BUF_LEN;
            ctx->offset = 0;
        }
    }
}

int main(void)
{
    json_buf_stream_ctx ctx = {0};

    to_json_stream(NULL, TYPE_STRUCT_EXPRESSION, json_flush_buf_cb, &ctx);

    // Flush remaining bytes
    if (ctx.offset > 0)
    {
        fwrite(ctx.buf, 1, ctx.offset, stdout);
        ctx.written += ctx.offset;
        ctx.offset = 0;
    }

    printf("\n");
    fflush(stdout);

    fprintf(stderr, "Total bytes streamed to screen: %zu\n", ctx.written);

    return 0;
}
