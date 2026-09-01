import re
import sys

TYPE_MAP = {
    "int": "TYPE_INT",
    "float": "TYPE_FLOAT",
    "char": "TYPE_CHAR",
    "char*": "TYPE_STR",
    "constchar*": "TYPE_STR",
    "unknown": "TYPE_UNKNOWN",
}


class Field:
    def __init__(self, name: str, type_name: str):
        self.name = name
        self.type_name = type_name
        self.normalized_type_name = (
            type_name.replace(" ", "") if "*" in type_name else type_name
        )
        self.type_enum = TYPE_MAP.get(self.normalized_type_name, TYPE_MAP["unknown"])

    def gen_field_str(self, struct_name: str) -> str:
        return f'    {{ "{self.name}", {self.type_enum}, offsetof({struct_name}, {self.name}), sizeof({self.type_name}) }}'


class CStruct:
    def __init__(self, fname: str, struct_name: str, fields: list[Field] = None):
        self.fname = fname
        self.struct_name = struct_name
        self.fields = fields if fields is not None else []
        pass

    def append_field(self, field: Field):
        self.fields.append(field)

    def __str__(self):
        lines = [f"const FieldInfo {self.struct_name}_Metadata[] = {{"]
        for field in self.fields:
            lines.append(field.gen_field_str(self.struct_name) + ",")
        lines.append("};")
        lines.append(
            f"const size_t {self.struct_name}_FieldCount = sizeof({self.struct_name}_Metadata) / sizeof(FieldInfo);"
        )

        return "\n".join(lines)


class Reflector:
    def __init__(self, structs: dict[str, CStruct] = None):
        self.structs = structs if structs is not None else {}
        pass

    def add_cstruct(self, struct: CStruct) -> bool:
        if struct.struct_name in self.structs:
            return False

        self.structs[struct.struct_name] = struct
        return True

    def resolve(self):
        for key, struct in self.structs.items():
            for field in struct.fields:
                if field.type_enum == TYPE_MAP["unknown"]:
                    field.type_enum = TYPE_MAP.get(
                        field.normalized_type_name, TYPE_MAP["unknown"]
                    )

    def __str__(self):
        files: dict[str, list[str]] = {}

        for struct in self.structs.values():
            if struct.fname not in files:
                files[struct.fname] = []
            files[struct.fname].append(str(struct))

        lines = []
        for file, contents in files.items():
            lines.append(f"// --- Generated from {file} ---")
            lines.append("\n\n".join(contents) + "\n")

        return "\n".join(lines)


def generate_reflection(reflector: Reflector, fname: str, code: str):
    struct_pattern = re.compile(
        r"(///\s*@reflect[\s\S]*?)typedef\s+struct[^{]*\{([^}]+)\}\s*(\w+);"
    )

    for struct_match in struct_pattern.finditer(code):
        header_comments = struct_match.group(1)
        body = struct_match.group(2)
        struct_name = struct_match.group(3)

        enum_match = re.search(r"///\s*@enum\s+([A-Za-z0-9_]+)", header_comments)
        if enum_match:
            custom_enum = enum_match.group(1)
            TYPE_MAP[struct_name] = custom_enum

        current_struct = CStruct(fname, struct_name)
        skip_next = False

        for line in body.split("\n"):
            line = line.strip()
            if not line or ("///" in line and "@private" in line and ";" not in line):
                skip_next = True if "@private" in line else skip_next
                continue

            if ";" in line:
                decl, _ = line.split(";", 1)
                if "@private" in line or skip_next:
                    skip_next = False
                    continue

                match = re.search(r"^(.*[\s\*])([a-zA-Z0-9_]+)$", decl.strip())
                if match:
                    raw_type = match.group(1).strip()
                    field_name = match.group(2).strip()

                    current_struct.append_field(Field(field_name, raw_type))

        reflector.add_cstruct(current_struct)


def main():
    if len(sys.argv) < 2:
        print(f"USAGE: {sys.argv[0]} <file>")
        exit(1)

    file_paths = sys.argv[1:]

    reflector = Reflector()

    for file in file_paths:
        try:
            with open(file, "r") as f:
                generate_reflection(reflector, file, f.read())
        except FileNotFoundError:
            print(f"Could not open file {sys.argv[1]}")

    reflector.resolve()
    print(str(reflector))


if __name__ == "__main__":
    main()
