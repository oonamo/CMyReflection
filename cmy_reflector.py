import argparse
import re
import sys
from pathlib import Path


class Field:
    def __init__(
        self,
        name: str,
        type_name: str,
        array_bounds: str = None,
        tags: dict[str, str] = {},
    ):
        self.name = name
        self.type_name = type_name
        self.array_bounds = array_bounds
        self.tags = tags

        base_name = type_name.replace(" ", "")

        self.normalized_type_name = base_name + ("_arr" if array_bounds else "")

        # set by reflector.resolve
        self.type_enum = "TYPE_UNKNOWN"

    def gen_field_str(self, struct_name: str) -> str:
        """Generates a formatted string of a field in the metadata struct"""
        arr_suffix = f"[{self.array_bounds}]" if self.array_bounds else ""
        count = self.array_bounds if self.array_bounds else "1"

        if "readonly" in self.tags:
            flags = "FIELD_ACCESS_READ"
        elif "writeonly" in self.tags:
            flags = "FIELD_ACCESS_WRITE"
        else:
            flags = "FIELD_ACCESS_RW"

        return f'    {{ "{self.name}", {self.type_enum}, offsetof({struct_name}, {self.name}), sizeof({self.type_name}{arr_suffix}), {count}, {flags} }}'


class CStruct:
    def __init__(
        self,
        fname: str,
        struct_name: str,
        fields: list[Field] = None,
        tags: dict[str, str] = {},
    ):
        self.fname = fname
        self.struct_name = struct_name
        self.fields = fields if fields is not None else []
        self.tags = tags
        pass

    def append_field(self, field: Field):
        self.fields.append(field)

    def generate_declaration(self) -> str:
        """Generates a declaration for the struct metadata"""
        return (
            f"extern const FieldInfo {self.struct_name}_Metadata[];\n"
            f"extern const size_t {self.struct_name}_FieldCount;"
        )

    def generate_definition(self) -> str:
        """Generates a definition for the struct metadata"""
        lines = [f"const FieldInfo {self.struct_name}_Metadata[] = {{"]
        for field in self.fields:
            lines.append(field.gen_field_str(self.struct_name) + ",")
        lines.append("};")
        lines.append(
            f"const size_t {self.struct_name}_FieldCount = sizeof({self.struct_name}_Metadata) / sizeof(FieldInfo);"
        )

        return "\n".join(lines)


class EnumMember:
    def __init__(self, name: str, tags: dict[str, str] = None):
        self.name = name
        self.tags = tags

    def gen_member_str(self) -> str:
        return f'   {{ {self.name}, "{self.name}" }}'


class CEnum:
    def __init__(
        self,
        fname: str,
        name: str,
        members: list[EnumMember] = None,
        tags: dict[str, str] = None,
    ):
        self.fname = fname
        self.name = name
        self.members = members if members is not None else []
        self.tags = tags if tags is not None else {}

    def generate_definition(self) -> str:
        """Generates a definition for the enum metadata"""
        lines = [f"const EnumMemberInfo {self.name}_Members[] = {{"]
        for member in self.members:
            lines.append(member.gen_member_str() + ",")
        lines.append("};")
        lines.append(
            f"const size_t {self.name}_MemberCount = sizeof({self.name}_Members) / sizeof(EnumMemberInfo);"
        )

        return "\n".join(lines)

    def generate_validator(self) -> str:
        """Generates a function that validates that a given integer is a member of the enum"""

        if "unchecked" in self.tags:
            return f"// {self.name} is unchecked"

        switch_cases = []
        for member in self.members:
            switch_cases.append(f"      case {member.name}:")

        if switch_cases:
            switch_cases.append("           return true;")

        switch_body = "\n".join(switch_cases)

        template = f"""\
static inline bool is_valid_{self.name}({self.name} value) {{
    switch(value) {{
{switch_body}
    default:
        return false;
    }}
}}
"""
        return template

    def generate_declaration(self) -> str:
        """Generates a declaration for the enum metadata"""
        return (
            f"extern const EnumMemberInfo {self.name}_Members[];\n"
            f"extern const size_t {self.name}_MemberCount;"
        )


class Reflector:
    def __init__(
        self, structs: dict[str, CStruct] = None, enums: dict[str, CEnum] = None
    ):
        self.structs = structs if structs is not None else {}
        self.enums = enums if enums is not None else {}
        self.type_map = {
            "char*": "TYPE_STR",
            "constchar*": "TYPE_CONSTSTR",
            "unknown": "TYPE_UNKNOWN",
        }
        self.type_aliases = {
            "char*": "str",
            "constchar*": "conststr",
            "uint8_t": "u8",
            "uint16_t": "u16",
            "uint32_t": "u32",
            # NOTE: If the original type has a space, ensure that it is also added to CTYPES with the appropiate type
            "unsignedint": "uint",
            "longlong": "ll",
        }
        self.ctypes = {
            "char*": "char *",
            "constchar*": "const char *",
            "unsignedint": "unsigned int",
            "longlong": "long long",
        }

    def add_cstruct(self, struct: CStruct) -> bool:
        """Adds a CStruct if unique"""
        if struct.struct_name in self.structs:
            return False

        self.structs[struct.struct_name] = struct
        return True

    def add_cenum(self, enum: CEnum) -> bool:
        if enum.name in self.enums:
            return False

        self.enums[enum.name] = enum

    def resolve(self):
        """Resolves all fields and ensures that an enum exists for every type"""
        for key, struct in self.structs.items():
            for field in struct.fields:
                mapped_enum = self.type_map.get(
                    field.normalized_type_name, self.type_map["unknown"]
                )

                if mapped_enum == self.type_map["unknown"]:
                    safe_name = field.normalized_type_name.upper().replace("*", "_PTR")
                    mapped_enum = f"TYPE_{safe_name}"

                    self.type_map[field.normalized_type_name] = mapped_enum

                    if field.array_bounds:
                        self.ctypes[field.normalized_type_name] = field.type_name + " *"
                    else:
                        self.ctypes[field.normalized_type_name] = field.type_name

                field.type_enum = mapped_enum

    def generate_file_header(self) -> str:
        return """\
/*
* Auto Generated by CMyReflection python script
* Version 0.0.0
*/
// clang-format off
"""

    def generate_type_setter(self, type_name: str, type_enum: str) -> str:
        """Generates a macro for setting a field"""
        type_suffix = self.get_type_suffix(type_name)
        ctype = self.ctypes.get(type_name, type_name)

        enum_obj = next((e for e in self.enums.values() if e.name == type_name), None)

        if "_arr" in type_name:
            base_type = ctype.replace("*", "", 1).strip()
            return (
                f"DEFINE_ARRAY_SETTER({type_suffix}, {type_enum}, {ctype}, {base_type})\n"
                f"DEFINE_ARRAY_GETTER({type_suffix}, {type_enum}, {ctype}, {base_type})\n"
            )
        elif enum_obj and "unchecked" not in enum_obj.tags:
            return (
                f"DEFINE_ENUM_SETTER({type_suffix}, {type_enum}, {ctype}, is_valid_{enum_obj.name})\n"
                f"DEFINE_FIELD_GETTER({type_suffix}, {type_enum}, {ctype})\n"
            )
        else:
            return (
                f"DEFINE_FIELD_SETTER({type_suffix}, {type_enum}, {ctype})\n"
                f"DEFINE_FIELD_GETTER({type_suffix}, {type_enum}, {ctype})\n"
            )

    def generate_types(self) -> str:
        """Generates the FieldType enum from TYPE_MAP"""
        lines = ["typedef enum {"]

        unique_enums = sorted(set(self.type_map.values()))
        for enum in unique_enums:
            lines.append(f"    {enum},")

        lines.append("} FieldType;\n")

        return "\n".join(lines)

    def generate_enum_validators(self) -> str:
        funcs = ["// --- Auto-Generated Enum Validators ---"]
        for enum in self.enums.values():
            funcs.append(enum.generate_validator())

        return "\n\n".join(funcs)

    def generate_definitions(self) -> str:
        """Generates the definitions for the metadata"""
        files: dict[str, list[str]] = {}

        for struct in self.structs.values():
            if struct.fname not in files:
                files[struct.fname] = []
            files[struct.fname].append(struct.generate_definition())

        for enum in self.enums.values():
            if enum.fname not in files:
                files[enum.fname] = []
            files[enum.fname].append(enum.generate_definition())

        lines = ["// --- Metadata Definitions", "#ifdef REFLECTION_IMPLEMENTATION\n"]
        for file, contents in files.items():
            lines.append(f"// --- Generated from {file} ---")
            lines.append("\n\n".join(contents) + "\n")

        lines.append(self.generate_struct_registry_definition() + "\n")

        lines.append(self.generate_enum_registry_definition() + "\n")

        lines.append(self.generate_generic_type_setter())

        lines.append(self.generate_type_name_converter())

        lines.append("#endif // REFLECTION_IMPLEMENTATION")

        return "\n".join(lines)

    def generate_declarations(self) -> str:
        """Generates the declarations for the metadata"""
        lines = ["// --- Metadata Declarations"]
        for struct in self.structs.values():
            lines.append(struct.generate_declaration())

        for enum in self.enums.values():
            lines.append(enum.generate_declaration())

        lines.append("")

        return "\n".join(lines)

    def generate_enum_registry_definition(self) -> str:
        switch_cases = []
        for enum in self.enums.values():
            normalized = enum.name.replace(" ", "")
            type_enum = self.type_map.get(normalized)

            if type_enum:
                switch_cases.append(f"      case {type_enum}:")
                switch_cases.append(
                    f"          out_meta->members = {enum.name}_Members;"
                )
                switch_cases.append(
                    f"          out_meta->count = {enum.name}_MemberCount;"
                )
                switch_cases.append("          return REFLECT_OK;")

        switch_body = "\n".join(switch_cases)

        template = f"""\
// --- Auto-Generated Type Registry
ReflectResult get_enum_metadata(FieldType type, EnumMetaData* out_meta) {{
    if (!out_meta) return false;
    switch(type) {{
{switch_body}
        default: return REFLECT_ERR_ENUM_INVALID;
    }}
}}
"""
        return template

    def generate_struct_registry_definition(self) -> str:
        switch_cases = []
        for struct in self.structs.values():
            normalized = struct.struct_name.replace(" ", "")
            type_enum = self.type_map.get(normalized)
            type_enum_arr = self.type_map.get(normalized + "_arr")

            if type_enum:
                switch_cases.append(f"      case {type_enum}:")
            if type_enum_arr:
                switch_cases.append(f"      case {type_enum_arr}:")

            if type_enum or type_enum_arr:
                switch_cases.append(
                    f"          out_meta->fields = {struct.struct_name}_Metadata;"
                )
                switch_cases.append(
                    f"          out_meta->count = {struct.struct_name}_FieldCount;"
                )
                switch_cases.append("          return REFLECT_OK;")

        switch_body = "\n".join(switch_cases)

        template = f"""\
// --- Auto-Generated Type Registry
ReflectResult get_struct_metadata(FieldType type, StructMetaData* out_meta) {{
    if (!out_meta) return false;
    switch(type) {{
{switch_body}
        default: return REFLECT_ERR_TYPE_INVALID;
    }}
}}"""

        return template

    def generate_type_name_converter(self) -> str:
        switch_cases = []

        unique_enums = sorted(set(self.type_map.values()))
        for enum in unique_enums:
            switch_cases.append(f'     case {enum}: return "{enum}";')

        switch_body = "\n".join(switch_cases)

        template = f"""\
// --- Auto-Generated enum->name converter
const char* get_name_of_type(FieldType type) {{
    switch(type) {{
{switch_body}
        default: return NULL;
    }};
}}
"""
        return template

    def get_type_suffix(self, type_name: str) -> str:
        if type_name == "unknown":
            return "unknown"
        aliased_name = (
            type_name.replace("_arr", "") if "_arr" in type_name else type_name
        )

        if "_arr" in type_name and aliased_name in self.type_aliases:
            type_suffix = self.type_aliases[aliased_name] + "_arr"
        elif type_name in self.type_aliases:
            type_suffix = self.type_aliases[type_name]
        else:
            type_suffix = type_name.replace("*", "_ptr").replace(" ", "_")

        return type_suffix

    def generate_generic_type_setter(self) -> str:
        switch_cases = []
        for type_name, type_enum in self.type_map.items():
            if type_name == "unknown":
                continue

            type_suffix = self.get_type_suffix(type_name)

            ctype = self.ctypes.get(type_name, type_name)

            if "_arr" in type_name:
                base_type = ctype.replace("*", "", 1).strip()
                switch_cases.append(
                    f"      case {type_enum}: "
                    f"return set_field_{type_suffix}(instance, field, ({base_type}*)value, element_count);"
                )
            else:
                switch_cases.append(
                    f"      case {type_enum}: "
                    f"return set_field_{type_suffix}(instance, field, *({ctype}*)value);"
                )

        switch_body = "\n".join(switch_cases)

        template = f"""\
// --- Auto-Generated Safe Type Setter
ReflectResult safe_set_field(void* instance, const FieldInfo* field, const void* value, size_t element_count) {{
    if (!instance || !field || !value) return false;
    switch(field->type) {{
{switch_body}
        default: return REFLECT_ERR_TYPE_INVALID;
    }}
}}
"""
        return template

    def __str__(self):
        lines = [
            self.generate_file_header(),
            "#define CMYREFLECTION_PARSED",
            "#ifndef CMYREFLECTION_AUTOGEN_H",
            "#define CMYREFLECTION_AUTOGEN_H",
            "#define CMYREFLECTION_REGISTRY",
            self.generate_types(),
            "#include <cmyreflection.h>",
            self.generate_declarations(),
        ]

        lines.append(self.generate_enum_validators())

        for type_name, type_enum in self.type_map.items():
            if type_name == "unknown":
                continue
            lines.append(self.generate_type_setter(type_name, type_enum))

        lines.append("\n#endif // CMYREFLECTION_AUTOGEN_H")
        lines.append(self.generate_definitions())

        # Prevent -Wnewline-eof
        lines.append("\n")

        return "\n".join(lines)


def extract_tags(comment_text: str) -> dict:
    tags = {}

    for match in re.finditer(r"///\s*@([a-zA-Z0-9_]+)(?:\s+([^/\n]+))?", comment_text):
        tag_name = match.group(1)
        tag_value = match.group(2).strip() if match.group(2) else True
        tags[tag_name] = tag_value

    return tags


def generate_reflection(reflector: Reflector, fname: str, code: str):
    """Constructs the reflection data from the file"""
    # NOTE: captures all tags after @reflect
    block_pattern = re.compile(
        r"(///\s*@reflect[\s\S]*?)typedef\s+(struct|enum)[^{]*\{([^}]+)\}\s*(\w+);"
    )

    for match in block_pattern.finditer(code):
        block_tags = extract_tags(match.group(1))
        block_type = match.group(2)
        body = match.group(3)
        block_name = match.group(4)

        if block_type == "struct":
            if "enum" in block_tags:
                reflector.type_map[block_name] = block_tags["enum"]
            else:
                reflector.type_map[block_name] = f"TYPE_STRUCT_{block_name.upper()}"
            current_block = CStruct(fname, block_name, tags=block_tags)
        else:
            type_enum = f"TYPE_ENUM_{block_name.upper()}"
            reflector.type_map[block_name] = type_enum
            current_block = CEnum(fname, block_name, tags=block_tags)

        pending_tags = {}

        for line in body.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("///"):
                pending_tags.update(extract_tags(line))
                continue

            parts = line.split("//", 1)
            decl = parts[0].strip()
            inline_comment = f"//{parts[1]}" if len(parts) > 1 else ""

            if not decl:
                continue

            field_tags = {**pending_tags, **extract_tags(inline_comment)}
            pending_tags = {}

            if "private" in field_tags:
                continue

            if block_type == "struct":
                decl = decl.split(";")[0].strip()
                match = re.search(r"^(.*[\s\*])([a-zA-Z0-9_]+)(?:\s*\[(.*)\])?$", decl)

                if match:
                    raw_type = match.group(1).strip()
                    field_name = match.group(2).strip()
                    array_bounds = match.group(3)
                    current_block.append_field(
                        Field(field_name, raw_type, array_bounds, tags=field_tags)
                    )
            else:
                decl = decl.split(",")[0].split("=")[0].strip()
                match = re.search(r"^([a-zA-Z0-9_]+)", decl)

                if match:
                    member_name = match.group(1)
                    current_block.members.append(
                        EnumMember(member_name, tags=field_tags)
                    )

        if block_type == "struct":
            reflector.add_cstruct(current_block)
        else:
            reflector.add_cenum(current_block)


def gather_source_files(input_paths: list[str]) -> list[Path]:
    """Recursively resolves files in input_paths into sorted, unique list"""
    valid_files = set()

    for path_str in input_paths:
        path = Path(path_str)

        if path.is_file():
            if path.suffix in [".h", ".c"]:
                valid_files.add(path.resolve())
            else:
                print(f"Skipping non-C file {path}")
        elif path.is_dir():
            for ext in ("*.h", "*.c"):
                for file_path in path.rglob(ext):
                    valid_files.add(file_path.resolve())
        else:
            print(f"Warning: Path not found - {path}", file=sys.stderr)

    return sorted(list(valid_files))


def main():
    parser = argparse.ArgumentParser(
        description="A tool for generating reflection metadata"
    )

    parser.add_argument("input_files", nargs="+", help="One or more input files")

    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        default=None,
        help="The file to write the generated C code to. Prints to stdout if omitted",
    )

    args = parser.parse_args()

    target_files = gather_source_files(args.input_files)

    if not target_files:
        print("No target files found", file=sys.stderr)
        exit(1)

    reflector = Reflector()

    for file in target_files:
        try:
            with open(file, "r") as f:
                generate_reflection(reflector, file.name, f.read())
        except FileNotFoundError:
            print(f"Could not open file {sys.argv[1]}", file=sys.stderr)

    reflector.resolve()
    gen_file = str(reflector)

    if args.output_file:
        try:
            with open(args.output_file, "w") as f:
                f.write(gen_file)
            print(f"Wrote to {args.output_file}")
        except IOError:
            print(f"Error: Could not write to {args.output_file}", file=sys.stderr)
    else:
        print(gen_file)


if __name__ == "__main__":
    main()
