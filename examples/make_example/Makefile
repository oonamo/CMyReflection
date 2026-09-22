CC     ?= gcc
CFLAGS ?= -Wall -Wextra -std=c99 -Isrc
PYTHON ?= python3

# NOTE: Ensure that this is accurate to your project.
CMY_DIR   ?= ../..

GENERATOR := $(CMY_DIR)/cmy_reflector.py
PLUGINS   := $(CMY_DIR)/plugins/json.py $(CMY_DIR)/plugins/print.py

CFLAGS    += -I$(CMY_DIR)

TARGET    := my_app
HEADERS   := $(wildcard src/*.h)
SRCS      := $(wildcard src/*.c)
OBJS      := $(SRCS:.c = .o)

GEN_OUT   ?= src/refl.generated.h

.PHONY: all clean

all: $(TARGET)

$(GEN_OUT): $(HEADERS) $(GENERATOR) $(PLUGINS)
	@echo "Generating C reflection metadata..."
	$(PYTHON) $(GENERATOR) \
		--input $(HEADERS) \
		--output $(GEN_OUT) \
		--plugin $(PLUGINS)

$(TARGET): $(OBJS) $(GEN_OUT)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(GEN_OUT)
