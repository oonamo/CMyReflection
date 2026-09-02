include(FetchContent)
set(UNITY_VERSION 2.7.0)

message(STATUS "Compiling unit tests...")
FetchContent_Declare(
    unity
    GIT_REPOSITORY https://github.com/ThrowTheSwitch/Unity.git
    GIT_TAG        v${UNITY_VERSION}
)

set(UNITY_EXTENSION_FIXTURE ON CACHE BOOL "Enable Unity Fixtures" FORCE)

FetchContent_MakeAvailable(unity)

if (CMAKE_C_COMPILER_ID MATCHES "MSVC")
  message(NOTICE "Detected MSVC, silencing Unity compilation warnings")
  target_compile_options(unity PRIVATE
    # Disable the following to get rid of cmake noise for Unity
    /wd4711
    /wd5045
  )
endif()

target_compile_definitions(unity
  PRIVATE
  UNITY_OUTPUT_COLOR # Show colored output
  UNITY_INCLUDE_COMMAND_LINE_ARGS # Allows for parsing command line arguments
  PUBLIC
  UNITY_FIXTURE_NO_EXTRAS
)


find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(GENERATED_HEADER "${CMAKE_CURRENT_SOURCE_DIR}/mocks/generated.inc")

file(GLOB_RECURSE REFLECTION_SOURCE_FILES CONFIGURE_DEPENDS "mocks/*.h" "mocks/*.c")

add_custom_command(
  OUTPUT ${GENERATED_HEADER}
  COMMAND Python3::Interpreter "${PROJECT_SOURCE_DIR}/cmy_reflector.py" "${CMAKE_CURRENT_SOURCE_DIR}/mocks" -o "${GENERATED_HEADER}"
  DEPENDS "${PROJECT_SOURCE_DIR}/cmy_reflector.py" ${REFLECTION_SOURCE_FILES}
  COMMENT "Generating C reflection data..."
)

set(TEST_SOURCES
  test_main.c
  test_unit.c
  test_readme.c
  reflection_impl.c
  ${GENERATED_HEADER}
)


add_executable(test_runner)
target_link_libraries(test_runner PRIVATE unity)
target_sources(test_runner PRIVATE ${TEST_SOURCES})
target_include_directories(test_runner PUBLIC ${PROJECT_SOURCE_DIR})
add_test(NAME UnitTests COMMAND test_runner -v)
