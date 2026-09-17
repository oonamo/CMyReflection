import os
import sys

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ask(question: str, default: str = "") -> str:
    prompt_text = f"{CYAN}?{RESET} {BOLD}{question}{RESET}"
    if default:
        prompt_text += f" {YELLOW}[{default}]{RESET}"
    prompt_text += ": "

    answer = input(prompt_text).strip()
    return answer if answer else default


def ask_bool(question: str, default: str = None):
    def_str = "Y/n" if default else "y/N"
    prompt_text = f"{CYAN}?{RESET} {BOLD}{question} {YELLOW}[{def_str}]{RESET}: "

    answer = input(prompt_text).strip()
    if not answer:
        return default
    return answer.lower() in ["y", "yes", "1"]


def gen_template():
    print(f"{BOLD}{GREEN}CMyReflection Plugin Generator{RESET}\n")

    name = ask("Plugin Name", "MyPlugin")
    version = ask("Version", "0.0.0")
    maintainers = ask("Maintainers", "unknown")
    description = ask("Description", f"Adds {name} plugin")

    filename = f"{name.lower().replace(' ', '')}.py"
    target_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)

    if os.path.exists(filepath):
        if not ask_bool(f"A file exists in {filepath}, Overwrite it?", False):
            print(f"\n{BOLD}{RED}Exiting as file already exists.{RESET}")
            sys.exit(1)

    file_header = f"""\
import cmy_reflector
from cmy_reflector import (
    CBuilder,
    CEnum,
    CStruct,
    EnumMember,
    Field,
    Macro,
    Plugin,
    Reflector,
)

# ----------------------------------------
# Plugin Configuration
# ----------------------------------------
PLUGIN_NAME = "{name}"
PLUGIN_VERSION = "{version}"
PLUGIN_MAINTAINERS = ["{maintainers}"]
PLUGIN_DESCRIPTION = "{description}"

"""

    with open(filepath, "w") as f:
        f.write(
            file_header
            + """\
# Helpers for user's and authors to determine whether plugin is available
PLUGIN_DEFINE_MACRO = f"CMY_HAS_{PLUGIN_NAME.upper()}_PLUGIN"
PLUGIN_ENABLED_MACRO = f"CMY_PLUGIN_{PLUGIN_NAME.upper()}_ENABLED"

# Instantiate plugin
plugin = Plugin(
    name=PLUGIN_NAME,
    version=PLUGIN_VERSION,
    maintainers=PLUGIN_MAINTAINERS,
    includes=["<stdbool.h>"],
    macros=[
        Macro.define(PLUGIN_DEFINE_MACRO, "1", f"{PLUGIN_NAME} plugin is available"),
        Macro.default(PLUGIN_ENABLED_MACRO, "1", f"Enables the {PLUGIN_NAME} plugin"),
        # Add Custom Macros Here
        # Macro.raw, Macro.include, Macro.default, Macro.define,
    ],
)


# ----------------------------------------
# Setup & Extensions
# ----------------------------------------
@plugin.setup
def setup(reflector: Reflector):
    \"\"\"Registers custom field extensions that will be added to the C extension structs\"\"\"
    reflector.define_field_extension(
        "my_plugin_field_data", "const char*", requires=PLUGIN_ENABLED_MACRO
    )
    reflector.define_member_extension(
        "my_plugin_member_data", "const char*", requires=PLUGIN_ENABLED_MACRO
    )


# ----------------------------------------
# Tag Handlers
# ----------------------------------------
@plugin.struct_field_tag(
    "my_tag",
    enforce_value=True,
    description=\"\"\"\
Sets custom data for a struct field
Example:
+  @my_tag("a value")
+  int var;
\"\"\",
)
def handle_my_struct_field_tag(
    reflector: Reflector, struct: CStruct, field: Field, tag_value: str
):
    \"\"\"Injects the value into the custom struct metadata\"\"\"
    # Extension field must be previously defined
    reflector.set_field_extension(field, "my_plugin_field_data", tag_value)


@plugin.enum_member_tag(
    "my_tag",
    enforce_value=True,
    description=\"\"\"\
Sets custom data for an enum field
Example:
+  @my_tag("a value")
+  ENUM_A;
\"\"\",
)
def handle_my_enum_member_tag(
    reflector: Reflector, enum: CEnum, member: EnumMember, tag_value: str
):
    \"\"\"Injects the value into the custom enum metadata\"\"\"
    # Extension member must be previously defined
    reflector.set_member_extension(member, "my_plugin_member_data", tag_value)


# ----------------------------------------
# Type Mappers
# ----------------------------------------
@plugin.type_mapper(
    signature="ReflectResult process_field(const void* instance, const StructFieldInfo* field)",
    guard_clause="if (!instance || !field) { return REFLECT_ERR_NULL_PTR: }",
    switch_var="field->type",
    default_case="return REFLECT_ERR_TYPE_MISMATCH;",
    requires=PLUGIN_ENABLED_MACRO,
    description="Process fields dynamically based on their type",
)
def map_types(
    reflector: Reflector, type_name: str, type_enum: str, ctype: str, suffix: str
) -> (str | None, str | None):
    \"\"\"
    Generates a unique static inline function for each type.
    Return None to skip a type
    \"\"\"

    # Don't map enum types
    if reflector.is_enum(type_name):
        return

    builder = CBuilder(reflector)
    func_name = f"process_{suffix}_field"

    # Use CBuilder to generate a safer, declarative C Code
    c_lines = [
        builder.var(ctype, "val"),
        builder.var(
            "ReflectResult",
            "res",
            builder.struct_field_getter(
                suffix, "&val", instance_name="instance", field_name="field"
            ),
        ).checked("res != REFLECT_OK", "return res;"),
        "",
        "// TODO: Do someething with val!",
        "(void)val;",
        "return REFLECT_OK;",
    ]

    # Constructs the function
    func_def = builder.build_func(
        signature=f"{func_name}(const void* instance, const StructFieldInfo* field)",
        retval="ReflectResult",
        body_lines=c_lines,
    )

    # Construct the switch statement for the type
    case_def = f"return {func_name}(instance, field);"

    # Return the generated function and switch statement
    return (func_def, case_def)


# ----------------------------------------
# Standalone Functions
# ----------------------------------------
@plugin.function(
    requires=PLUGIN_DEFINE_MACRO,
    description="My standalone function",
)
def my_plugin_api(reflector: Reflector) -> str:
    \"\"\"Return a function that should be generated\"\"\"

    return \"\"\"\
static inline ReflectResult plugin_do_work(const void* instance, const StructFieldInfo* field)
{
    if (!instance || !field) { return REFLECT_ERR_NULL_PTR; }

    return process_field(instance, field);
}
\"\"\"


# ----------------------------------------
# Registration
# ----------------------------------------
cmy_reflector.add(plugin)
"""
        )

    print(f"\n{GREEN}✔ Plugin successfully generated at:{RESET} {filepath}\n")


if __name__ == "__main__":
    try:
        gen_template()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Plugin Generation Cancelled{RESET}")
        sys.exit(0)
