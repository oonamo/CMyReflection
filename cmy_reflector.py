import argparse
import dataclasses
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable


@dataclass
class TypeMapper:
    func: Callable
    signature: str
    switch_var: str
    default_case: str
    requires: str | None = None
    guard_clause: str | None = ""


@dataclass
class Plugin:
    name: str
    version: str = "1.0.0"
    description: str = ""

    maintainers: list[str] = dataclasses.field(default_factory=list)
    includes: list[str] = dataclasses.field(default_factory=list)
    macros: list[str] = dataclasses.field(default_factory=list)
    depends_on: list[str] = dataclasses.field(default_factory=list)

    _setup_hook: Callable[[Any], None] = dataclasses.field(default=None, init=False)
    _struct_field_tags: dict = dataclasses.field(default_factory=dict, init=False)
    _type_tags: dict = dataclasses.field(default_factory=dict, init=False)
    _enum_member_tags: dict = dataclasses.field(default_factory=dict, init=False)
    _type_mappers: list[TypeMapper] = dataclasses.field(
        default_factory=list, init=False
    )
    _code_emitters: list[Callable] = dataclasses.field(default_factory=list, init=False)

    @property
    def setup_hook(self) -> Callable:
        return self._setup_hook

    @property
    def struct_field_tags(self) -> dict:
        return MappingProxyType(self._struct_field_tags)

    @property
    def enum_member_tags(self) -> dict:
        return MappingProxyType(self._enum_member_tags)

    @property
    def type_tags(self) -> dict:
        return MappingProxyType(self._type_tags)

    @property
    def type_mappers(self) -> tuple:
        return tuple(self._type_mappers)

    @property
    def code_emitters(self) -> tuple:
        return tuple(self._code_emitters)

    def setup(self, func):
        """Decorator to register the plugin setup"""
        self._setup_hook = func
        return func

    def emit_code(self, func):
        """Decorator for functions that return raw C code strings."""
        self._code_emitters.append(func)
        return func

    def struct_field_tag(self, tag_name: str):
        """Decorator to register a struct field tag"""

        def decorator(func):
            self._struct_field_tags[tag_name] = func
            self.description += f"\n *    - Provides tag: @{tag_name} (Struct Fields)"
            return func

        return decorator

    def enum_member_tag(self, tag_name: str):
        """Decorator for tags applied to enum members."""

        def decorator(func):
            self._enum_member_tags[tag_name] = func
            self.description += f"\n *    - Provides tag: @{tag_name} (Enum Members)"
            return func

        return decorator

    def type_tag(self, tag_name: str):
        """Decorator for tags applied to enum members."""

        def decorator(func):
            self._type_tags[tag_name] = func
            self.description += f"\n *    - Provides tag: @{tag_name} (Types)"
            return func

        return decorator

    def type_mapper(
        self,
        signature: str,
        switch_var: str,
        default_case: str = "break;",
        guard_clause: str = "",
        requires=None,
    ):
        def decorator(func):
            mapper = TypeMapper(
                func=func,
                signature=signature,
                switch_var=switch_var,
                default_case=default_case,
                guard_clause=guard_clause,
                requires=requires,
            )
            self._type_mappers.append(mapper)

            # TODO: Maybe cutoff actual signature?
            func_name = signature
            self.description += f"\n *    - Provides router: {func_name}"
            return func

        return decorator


_PLUGINS: list[Plugin] = []


def add_plugin(plugin: Plugin):
    _PLUGINS.append(plugin)


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
        self.user_data_expr = "NULL"
        self.plugin_data = {}

        base_name = type_name.replace(" ", "")

        self.normalized_type_name = base_name + ("_arr" if array_bounds else "")

        self.length_field = None

        if "length" in self.tags:
            if not isinstance(self.tags["length"], str):
                raise ValueError(
                    f"Error in field '{self.name}': @length tag requires a field name "
                    f"in parentheses. Did you mean @length(count)?"
                )
            self.length_field = self.tags["length"]

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

        length_field_name = f'"{self.length_field}"' if self.length_field else "NULL"

        return f'    {{ "{self.name}", {self.type_enum}, offsetof({struct_name}, {self.name}), sizeof({self.type_name}{arr_suffix}), {count}, {flags}, {length_field_name}, {self.user_data_expr} }}'


class CStruct:
    def __init__(
        self,
        fname: str,
        name: str,
        fields: list[Field] = None,
        tags: dict[str, str] = {},
    ):
        self.fname = fname
        self.name = name
        self.fields = fields if fields is not None else []
        self.tags = tags
        pass

    def append_field(self, field: Field):
        self.fields.append(field)

    def generate_declaration(self) -> str:
        """Generates a declaration for the struct metadata"""
        lines = [
            f"extern const StructFieldInfo {self.name}_Metadata[];",
            f"extern const size_t {self.name}_FieldCount;",
        ]

        for field in self.fields:
            if field.plugin_data:
                ext_var_name = f"ext_{self.name}_{field.name}"
                lines.append(f"extern const StructFieldExtension {ext_var_name};")

        return "\n".join(lines)

    def generate_definition(self, extensions: dict[str, (str, str | None)]) -> str:
        """Generates a definition for the struct metadata"""
        lines = []

        for field in self.fields:
            if field.plugin_data:
                ext_var_name = f"ext_{self.name}_{field.name}"
                lines.append(f"const StructFieldExtension {ext_var_name} = {{")

                for key, val in field.plugin_data.items():
                    _, req = extensions.get(key, (None, None))
                    if req:
                        lines.append(f"#ifdef {req}")
                    lines.append(f".{key} = {val},")
                    if req:
                        lines.append(f"#endif // {req}")
                lines.append("};")
                field.user_data_expr = f"(void*)&{ext_var_name}"
            else:
                field.user_data_expr = "NULL"

        if any(f.plugin_data for f in self.fields):
            lines.append("")

        lines.append(f"const StructFieldInfo {self.name}_Metadata[] = {{")
        for field in self.fields:
            lines.append(field.gen_field_str(self.name) + ",")
        lines.append("};")
        lines.append(
            f"const size_t {self.name}_FieldCount = sizeof({self.name}_Metadata) / sizeof(StructFieldInfo);"
        )

        return "\n".join(lines)


class EnumMember:
    def __init__(self, name: str, tags: dict[str, str] = None):
        self.name = name
        self.tags = tags
        self.user_data_expr = "NULL"
        self.plugin_data = {}

    def gen_member_str(self) -> str:
        return f'   {{ {self.name}, "{self.name}", {self.user_data_expr} }}'


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

    def generate_definition(self, extensions: dict[str, (str, str | None)]) -> str:
        """Generates a definition for the enum metadata"""
        lines = []

        for member in self.members:
            if member.plugin_data:
                ext_var_name = f"ext_{self.name}_{member.name}"
                lines.append(f"const EnumMemberExtension {ext_var_name} = {{")

                for key, val in member.plugin_data.items():
                    _, req = extensions.get(key, (None, None))
                    if req:
                        lines.append(f"#ifdef {req}")
                    lines.append(f".{key} = {val},")
                    if req:
                        lines.append(f"#endif // {req}")
                lines.append("};")
                member.user_data_expr = f"(void*)&{ext_var_name}"
            else:
                member.user_data_expr = "NULL"

        lines.append(f"const EnumMemberInfo {self.name}_Members[] = {{")
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
        lines = [
            f"extern const EnumMemberInfo {self.name}_Members[];",
            f"extern const size_t {self.name}_MemberCount;",
        ]

        has_plugin_data = False

        for member in self.members:
            if member.plugin_data:
                ext_var_name = f"ext_{self.name}_{member.name}"
                lines.append(f"extern const EnumMemberExtension {ext_var_name};")
                has_plugin_data

        return "\n".join(lines)


class Reflector:
    def __init__(
        self, structs: dict[str, CStruct] = None, enums: dict[str, CEnum] = None
    ):
        self.structs = structs if structs is not None else {}
        self.enums = enums if enums is not None else {}
        self.type_map = {
            "unknown": "TYPE_UNKNOWN",
        }
        self.type_aliases = {
            "char*": "str",
            "constchar*": "conststr",
            "uint8_t": "u8",
            "uint16_t": "u16",
            "uint32_t": "u32",
            "uint64_t": "u64",
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
        self.base_types = {}

        self.member_extensions_members = {}
        self.field_extension_members = {}
        self.active_struct_field_tags = {}
        self.active_enum_member_tags = {}
        self.active_type_tags = {}
        self.active_type_mappers = []

    def normalze_type_identifier(self, identifier: str) -> str:
        """Converts a ctype, type_enum, or type_name into the internal type_name"""
        if identifier in self.type_map:
            return identifier

        for t_name, t_enum in self.type_map.items():
            if t_enum == identifier:
                return t_name

        for t_name, c_type in self.ctypes.items():
            if c_type == identifier:
                return c_type

        return identifier

    def get_base_type_name(self, identifier: str) -> str:
        """Gets the primitive type (char* -> char)"""
        norm = self.normalze_type_identifier(identifier)
        if norm.endswith("_arr"):
            norm = norm[:-4]
        if "*" in norm:
            norm = norm[: norm.rfind("*")]
        return norm.strip()

    def is_struct(self, identifier: str) -> bool:
        return self.get_base_type_name(identifier) in self.structs

    def is_enum(self, identifier: str) -> bool:
        return self.get_base_type_name(identifier) in self.enums

    def load_plugins(self):
        active_plugin_names = {p.name for p in _PLUGINS}

        for p in _PLUGINS:
            for dep in p.depends_on:
                if dep not in active_plugin_names:
                    raise RuntimeError(f"'{p.name}' requires '{dep}'")

            if p.setup_hook:
                p.setup_hook(self)

            for tag_name, handler in p.struct_field_tags.items():
                if tag_name in self.active_struct_field_tags:
                    raise ValueError(
                        f"Tag collision: '@{tag_name}' (Struct Fields) is defined multiple times."
                    )
                self.active_struct_field_tags[tag_name] = handler

            for tag_name, handler in p.enum_member_tags.items():
                if tag_name in self.active_enum_member_tags:
                    raise ValueError(
                        f"Tag collision: '@{tag_name}' (Enum Member) is defined multiple times."
                    )
                self.active_enum_member_tags[tag_name] = handler

            for tag_name, handler in p.type_tags.items():
                if tag_name in self.active_type_tags:
                    raise ValueError(
                        f"Tag collision: '@{tag_name}' (Type) is defined multiple times."
                    )
                self.active_type_tags[tag_name] = handler

            self.active_type_mappers.extend(p.type_mappers)

    def get_struct(self, identifier: str) -> CStruct | None:
        """Returns the CStruct object or None if not found"""
        base = self.get_base_type_name(identifier)
        return self.structs.get(base)

    def get_enum(self, identifier: str) -> CEnum | None:
        """Returns the CEnum object or None if not found"""
        base = self.get_base_type_name(identifier)
        return self.enums.get(base)

    def has_struct_tag(self, identifier: str, tag_name: str) -> bool:
        struct = self.get_struct(identifier)
        return struct is not None and tag_name in struct.tags

    def get_struct_tag(self, identifier: str, tag_name: str) -> str | None:
        struct = self.get_struct(identifier)
        return struct.tags.get(tag_name) if struct else None

    def has_enum_tag(self, identifier: str, tag_name: str) -> bool:
        enum = self.get_enum(identifier)
        return enum is not None and tag_name in enum.tags

    def define_field_extension(self, name: str, ctype: str, requires: str = None):
        self.field_extension_members[name] = (ctype, requires)

    def define_member_extension(self, name: str, ctype: str, requires: str = None):
        self.member_extensions_members[name] = (ctype, requires)

    def set_field_extension(self, field: Field, name: str, value: str):
        if name not in self.field_extension_members:
            raise ValueError(
                f"Validation Error: Cannot set extension '{name}' on field '{field.name}'. "
                f"It must be registered first using reflector.define_field_extension()."
            )

        field.plugin_data[name] = value

    def set_member_extension(self, member: EnumMember, name: str, value: str):
        if name not in self.member_extensions_members:
            raise ValueError(
                f"Validation Error: Cannot set extension '{name}' on field '{member.name}'. "
                f"It must be registered first using reflector.define_member_extension()."
            )
        member.plugin_data[name] = value

    def generate_struct_extension_type(self) -> str:
        if not self.field_extension_members:
            return "// No Struct Extensions"
        lines = ["typedef struct {"]
        for name, (c_type, req) in self.field_extension_members.items():
            if req:
                lines.append(f"#ifdef {req}")
            lines.append(f"     {c_type} {name};")
            if req:
                lines.append(f"#endif // {req}")
        lines.append("} StructFieldExtension;")
        return "\n".join(lines)

    def generate_enum_extension_type(self) -> str:
        if not self.member_extensions_members:
            return "// No Enum Extensions"
        lines = ["typedef struct {"]
        for name, (c_type, req) in self.member_extensions_members.items():
            if req:
                lines.append(f"#ifdef {req}")
            lines.append(f"     {c_type} {name};")
            if req:
                lines.append(f"#endif // {req}")
        lines.append("} EnumMemberExtension;")
        return "\n".join(lines)

    def add_cstruct(self, struct: CStruct) -> bool:
        """Adds a CStruct if unique"""
        if struct.name in self.structs:
            return False

        self.structs[struct.name] = struct
        return True

    def add_cenum(self, enum: CEnum) -> bool:
        if enum.name in self.enums:
            return False

        self.enums[enum.name] = enum

    def resolve(self):
        """Resolves all fields and ensures that an enum exists for every type"""
        for key, struct in self.structs.items():
            valid_field_names = {field.name for field in struct.fields}

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

                curr_norm = field.normalized_type_name
                curr_ctype = field.type_name

                while True:
                    if curr_norm.endswith("_arr"):
                        parent_norm = curr_norm[:-4]
                        parent_ctype = (
                            curr_ctype.rsplit("[", 1)[0].strip()
                            if "[" in curr_ctype
                            else curr_ctype
                        )
                    elif "*" in curr_norm:
                        idx = curr_norm.rfind("*")
                        parent_norm = curr_norm[:idx] + curr_norm[idx + 1 :]
                        c_idx = curr_ctype.rfind("*")
                        parent_ctype = (
                            (curr_ctype[:c_idx] + curr_ctype[c_idx + 1 :]).strip()
                            if c_idx != -1
                            else curr_ctype
                        )
                    else:
                        break

                    if parent_norm and parent_norm not in self.type_map:
                        safe_base_name = parent_norm.upper().replace("*", "_PTR")
                        self.type_map[parent_norm] = f"TYPE_{safe_base_name}"
                        self.ctypes[parent_norm] = parent_ctype

                    curr_norm = parent_norm
                    curr_ctype = parent_ctype

                if field.length_field and field.length_field not in valid_field_names:
                    raise ValueError(
                        f"Error in struct '{struct.name}': Field '{field.name}' uses "
                        f"@length({field.length_field}), but '{field.length_field}' "
                        f"does not exist in the struct."
                    )

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
            files[struct.fname].append(
                struct.generate_definition(self.field_extension_members)
            )

        for enum in self.enums.values():
            if enum.fname not in files:
                files[enum.fname] = []
            files[enum.fname].append(
                enum.generate_definition(self.member_extensions_members)
            )

        lines = ["// --- Metadata Definitions", "#ifdef REFLECTION_IMPLEMENTATION\n"]
        for file, contents in files.items():
            lines.append(f"// --- Generated from {file} ---")
            lines.append("\n\n".join(contents) + "\n")

        lines.append(self.generate_struct_registry_definition() + "\n")

        lines.append(self.generate_enum_registry_definition() + "\n")

        lines.append(self.generate_generic_type_setter())

        lines.append(self.generate_type_name_converter())

        lines.append(self.generate_basetype_caster())

        lines.append("#endif // REFLECTION_IMPLEMENTATION")

        return "\n".join(lines)

    def generate_declarations(self) -> str:
        """Generates the declarations for the metadata"""
        lines = ["// --- Metadata Declarations"]
        has_field_extension = False
        has_member_extension = False
        for struct in self.structs.values():
            lines.append(struct.generate_declaration())

            if any(field.plugin_data for field in struct.fields):
                has_field_extension = True

        for enum in self.enums.values():
            lines.append(enum.generate_declaration())

            if any(member.plugin_data for member in enum.members):
                has_member_extension = True

        lines.append("")

        if has_field_extension:
            lines.append("""\
#define GET_FIELD_EXT(field_ptr) \\
    ((field_ptr) && (field_ptr)->user_data ? (const StructFieldExtension*)((field_ptr)->user_data) : NULL)
""")

        if has_member_extension:
            lines.append("""\
#define GET_MEMBER_EXT(member_ptr) \\
    ((member_ptr) && (member_ptr)->user_data ? ((const EnumMemberExtension*)(member_ptr->user_data)) : NULL)
""")

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
    if (!out_meta) return REFLECT_ERR_NULL_PTR;
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
            normalized = struct.name.replace(" ", "")
            type_enum = self.type_map.get(normalized)
            type_enum_arr = self.type_map.get(normalized + "_arr")

            if type_enum:
                switch_cases.append(f"      case {type_enum}:")
            if type_enum_arr:
                switch_cases.append(f"      case {type_enum_arr}:")

            if type_enum or type_enum_arr:
                switch_cases.append(
                    f"          out_meta->fields = {struct.name}_Metadata;"
                )
                switch_cases.append(
                    f"          out_meta->count = {struct.name}_FieldCount;"
                )
                switch_cases.append("          return REFLECT_OK;")

        switch_body = "\n".join(switch_cases)

        template = f"""\
// --- Auto-Generated Type Registry
ReflectResult get_struct_metadata(FieldType type, StructMetaData* out_meta) {{
    if (!out_meta) return REFLECT_ERR_NULL_PTR;
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

    def generate_dynamic_array_accessors(self, struct_name: str, field: Field) -> str:
        if not field.length_field or "*" not in field.type_name:
            return ""

        suffix = f"{struct_name}_{field.name}"
        parent_enum = self.type_map[struct_name]
        type_enum = field.type_enum

        ctype = self.ctypes.get(field.normalized_type_name, field.type_name)
        base_type = ctype.replace("*", "", 1).strip()

        return (
            f"DEFINE_DYNAMIC_ARRAY_SETTER({suffix}, {type_enum}, {ctype}, {base_type}, {parent_enum})\n"
            f"DEFINE_DYNAMIC_ARRAY_GETTER({suffix}, {type_enum}, {ctype}, {base_type})\n"
        )

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
ReflectResult safe_set_field(void* instance, const StructFieldInfo* field, const void* value, size_t element_count) {{
    if (!instance || !field || !value) return false;
    switch(field->type) {{
{switch_body}
        default: return REFLECT_ERR_TYPE_INVALID;
    }}
}}
"""
        return template

    def generate_basetype_caster(self) -> str:
        switch_cases = []

        for type_name, type_enum in self.type_map.items():
            if type_name == "unknown":
                continue

            parent_norm = None
            if type_name.endswith("_arr"):
                parent_norm = type_name[:-4]
            elif "*" in type_name:
                idx = type_name.rfind("*")
                parent_norm = type_name[:idx] + type_name[idx + 1 :]

            if parent_norm:
                parent_enum = self.type_map.get(parent_norm)
                if parent_enum and parent_enum != type_enum:
                    switch_cases.append(
                        f"      case {type_enum}: return {parent_enum};"
                    )

        switch_body = "\n".join(switch_cases)

        template = f"""\
FieldType get_base_type(FieldType type) {{
    switch(type) {{
{switch_body}
        default: return type;
    }}
}}
"""
        return template

    def generate_plugin_headers(self) -> str:
        if not _PLUGINS:
            return "// No plugins active"
        lines = ["/*", " * CMyReflection Active Plugins"]

        includes = set()
        macros = []

        for p in _PLUGINS:
            m_str = f" by {', '.join(p.maintainers)}" if p.maintainers else ""
            desc = f" - {p.description}" if p.description else ""
            lines.append(f" *  -> {p.name} (v{p.version}){m_str}{desc}")

            includes.update(p.includes)
            macros.extend(p.macros)

        lines.append(" */\n")

        for inc in sorted(includes):
            if not inc.startswith("<") and not inc.startwith('"'):
                inc = f"<{inc}>"
            lines.append(f"#include {inc}")

        if macros:
            lines.append("")
            lines.extend(macros)

        return "\n".join(lines)

    def generate_plugin_extensions(self) -> str:
        extension_lines = ["// --- Plugin-Generated-Extensions ---"]

        for p in _PLUGINS:
            for emitter in p.code_emitters:
                snippet = emitter(self)
                if snippet:
                    extension_lines.append(snippet)

        for mapper in self.active_type_mappers:
            hook_func = mapper.func

            standalone_funcs = []
            switch_cases = []

            for type_name, type_enum in self.type_map.items():
                ctype = self.ctypes.get(type_name, type_name)
                suffix = self.get_type_suffix(type_name)

                result = hook_func(type_name, type_enum, ctype, suffix)

                if result:
                    func_code, case_code = result
                    if func_code:
                        standalone_funcs.append(func_code)
                    if case_code:
                        switch_cases.append(f"      case {type_enum}: {case_code}")
            if switch_cases:
                switch_body = "\n".join(switch_cases)
                router = f"""\
static inline {mapper.signature} {{
    {mapper.guard_clause}
    switch({mapper.switch_var}) {{
{switch_body}
        default: {mapper.default_case}
    }}
}}
"""
                if mapper.requires:
                    extension_lines.append(f"#ifdef {mapper.requires}")
                extension_lines.extend(standalone_funcs)
                extension_lines.append(router)
                if mapper.requires:
                    extension_lines.append(f"#endif // {mapper.requires}")

        # TODO: Flatten for loops
        for struct in self.structs.values():
            for tag_name, tag_value in struct.tags.items():
                if tag_name in self.active_type_tags:
                    snippet = self.active_type_tags[tag_name](self, struct, tag_value)
                    if snippet:
                        extension_lines.append(snippet)

        for enum in self.enums.values():
            for tag_name, tag_value in enum.tags.items():
                if tag_name in self.active_type_tags:
                    snippet = self.active_type_tags[tag_name](self, enum, tag_value)
                    if snippet:
                        extension_lines.append(snippet)

        for struct in self.structs.values():
            for field in struct.fields:
                for tag_name, tag_value in field.tags.items():
                    if tag_name in self.active_struct_field_tags:
                        snippet = self.active_struct_field_tags[tag_name](
                            self, struct, field, tag_value
                        )
                        if snippet:
                            extension_lines.append(snippet)

        for enum in self.enums.values():
            for member in enum.members:
                for tag_name, tag_value in member.tags.items():
                    if tag_name in self.active_enum_member_tags:
                        snippet = self.active_enum_member_tags[tag_name](
                            self, enum, member, tag_value
                        )
                        if snippet:
                            extension_lines.append(snippet)

        return "\n\n".join(extension_lines)

    def __str__(self):
        self.load_plugins()
        plugin_code = self.generate_plugin_extensions()

        ext_struct_code = self.generate_struct_extension_type()
        ext_enum_code = self.generate_enum_extension_type()

        lines = [
            self.generate_file_header(),
            "#define CMYREFLECTION_PARSED",
            "#ifndef CMYREFLECTION_AUTOGEN_H",
            "#define CMYREFLECTION_AUTOGEN_H",
            "#define CMYREFLECTION_REGISTRY",
            self.generate_types(),
            "#include <cmyreflection.h>",
            "",
            self.generate_plugin_headers(),
            ext_struct_code,
            "",
            ext_enum_code,
            self.generate_declarations(),
        ]

        lines.append(self.generate_enum_validators())

        for type_name, type_enum in self.type_map.items():
            if type_name == "unknown":
                continue
            lines.append(self.generate_type_setter(type_name, type_enum))

        for struct in self.structs.values():
            for field in struct.fields:
                gen_str = self.generate_dynamic_array_accessors(struct.name, field)
                if gen_str != "":
                    lines.append(
                        self.generate_dynamic_array_accessors(struct.name, field)
                    )

        lines.append(plugin_code)
        lines.append("\n#endif // CMYREFLECTION_AUTOGEN_H")
        lines.append(self.generate_definitions())

        # Prevent -Wnewline-eof
        lines.append("\n")

        return "\n".join(lines)


def extract_tags(comment_text: str) -> dict:
    tags = {}

    for line in comment_text.splitlines():
        if "//#" not in line:
            continue

        reflection_part = line.split("//#", 1)[1]

        for match in re.finditer(r"@([a-zA-Z0-9_]+)(?:\(([^)]+)\))?", reflection_part):
            tag_name = match.group(1)
            if match.group(2):
                tag_value = match.group(2).strip()
            else:
                tag_value = True
            tags[tag_name] = tag_value

    return tags


def generate_reflection(reflector: Reflector, fname: str, code: str):
    """Constructs the reflection data from the file"""
    # NOTE: captures all tags after @reflect
    block_pattern = re.compile(
        r"(//#\s*@reflect[\s\S]*?)typedef\s+(struct|enum)[^{]*\{([^}]+)\}\s*(\w+);"
    )

    for match in block_pattern.finditer(code):
        block_tags = extract_tags(match.group(1))
        block_type = match.group(2)
        body = match.group(3)
        block_name = match.group(4)

        if block_type == "struct":
            if "enum" in block_tags and block_tags:
                if not isinstance(block_tags["enum"], str):
                    raise ValueError(
                        f"Error: Enum for {block_name} requires a value in parentheses."
                    )
                else:
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

            if line.startswith("//#"):
                pending_tags.update(extract_tags(line))
                continue

            parts = line.split("//#", 1)
            decl = parts[0].strip()
            inline_comment = f"//# {parts[1]}" if len(parts) > 1 else ""

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


def load_plugin(file_path: Path):
    if not file_path.exists() or file_path.suffix != ".py":
        return

    module_name = f"cmy_plugin_{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)


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

    parser.add_argument(
        "--plugin",
        action="append",
        type=Path,
        help="Path to a specific plugin file (can be used multiple times)",
    )

    parser.add_argument(
        "--plugin-dir",
        action="append",
        type=Path,
        help="Path to a directory containing a plugin file (can be used multiple times)",
    )

    args = parser.parse_args()

    target_files = gather_source_files(args.input_files)

    if not target_files:
        print("No target files found", file=sys.stderr)
        exit(1)

    reflector = Reflector()

    if args.plugin:
        for plugin_file in args.plugin:
            load_plugin(plugin_file)

    if args.plugin_dir:
        for plugin_dir in args.plugin_dir:
            if plugin_dir.is_dir():
                for plugin_file in plugin_dir.glob("*.py"):
                    load_plugin(plugin_file)

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
    try:
        sys.modules["cmy_reflector"] = sys.modules[__name__]
        main()
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
