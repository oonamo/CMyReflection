import argparse
import dataclasses
import importlib.util
import re
import sys
import textwrap
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable

SIG_REGEX = re.compile(
    r"^\s*(?P<prefix>(?:\w+\s+)*)"
    r"(?P<rettype>[a-zA-Z_][\w\s\*]*?)"
    r"\s+(?P<fname>\w+)"
    r"\s*(?P<params>\([^)]*\))",
    re.MULTILINE,
)


@dataclass
class Tag:
    func: Callable
    enforced: bool = False
    validator: Callable[[str, str], [bool, str]] | None = None
    description: str = None


@dataclass
class TypeMapper:
    func: Callable
    signature: str
    switch_var: str
    default_case: str
    requires: str | None = None
    guard_clause: str | None = ""
    description: str = None


class MacroType(Enum):
    DEFINE = auto()
    RAW = auto()
    DEFAULT = auto()
    UNDEF = auto()
    INCLUDE = auto()


@dataclass
class Macro:
    name: str
    value: str
    macro_type: MacroType
    description: str = ""

    @classmethod
    def default(cls, name: str, value: str, description: str = ""):
        """C Macro with a default value, if not defined (#ifndef <name> ...)"""
        return cls(
            name=name,
            value=value,
            macro_type=MacroType.DEFAULT,
            description=description,
        )

    @classmethod
    def define(cls, name: str, value: str, description: str = ""):
        """Default C Macro definition (#define <name> <value>)"""
        return cls(
            name=name, value=value, macro_type=MacroType.DEFINE, description=description
        )

    @classmethod
    def undef(cls, name: str, value: str, description: str = ""):
        """Undefines a C Macro (#undef <name>)"""
        return cls(
            name=name, value=value, macro_type=MacroType.UNDEF, description=description
        )

    @classmethod
    def raw(cls, name: str, value: str, description: str = ""):
        """Creates a raw macro. No processing is done to 'value'"""
        return cls(
            name=name, value=value, macro_type=MacroType.RAW, description=description
        )

    @classmethod
    def include(cls, name: str, value: str, description: str = ""):
        """Defines an include statement (Prefer to use include in the Plugin constructor)"""
        return cls(
            name=name,
            value=value,
            macro_type=MacroType.INCLUDE,
            description=description,
        )

    def to_c_string(self) -> str:
        """Converts a macro to it's C implementation"""
        if self.macro_type == MacroType.DEFAULT:
            return f"#ifndef {self.name}\n#    define {self.name} {self.value}\n#endif //{self.name}"
        elif self.macro_type == MacroType.DEFINE:
            return f"#define {self.name} {self.value}"
        elif self.macro_type == MacroType.UNDEF:
            return f"#undef {self.name}"
        elif self.macro_type == MacroType.INCLUDE:
            return f'#include "{self.name}"'
        else:
            return self.value

    def to_doc_string(self) -> str:
        """Converts a macro to it's header doc string"""
        desc_str = f" - {self.description}" if self.description else ""

        if self.macro_type == MacroType.DEFAULT:
            return (
                f" *    - Provides macro: {self.name} (Default: {self.value}){desc_str}"
            )
        elif self.macro_type == MacroType.DEFINE:
            return (
                f" *    - Provides macro: {self.name} (Value: {self.value}){desc_str}"
            )
        elif self.macro_type == MacroType.UNDEF:
            return f" *    - Removes macro: {self.name}{desc_str}"
        elif self.macro_type == MacroType.RAW:
            return f" *    - Provides macro: {self.name} {desc_str}"
        return ""


@dataclass
class FunctionType:
    func: Callable
    description: str = ""
    requires: str | None = None


@dataclass(frozen=True)
class FuncDef:
    qualifiers: str | None
    rettype: str
    name: str
    params: str

    def prototype_string(self, with_qualifiers: bool = True) -> str:
        """Converts a FuncDef to it's C prototype"""
        q = f"{self.qualifiers} " if with_qualifiers else ""
        return f"{q}{self.rettype} {self.name}{self.params};"

    def doc_string(self) -> str:
        """Used for the documentation block"""
        return f"{self.rettype} {self.name}(...)"


@dataclass(frozen=True)
class FunctionPrimitive:
    fdef: FuncDef
    requires: str
    description: str


@dataclass
class TypeContext:
    name: str
    enun_id: str
    ctype: str
    suffix: str


@dataclass
class Plugin:
    name: str
    version: str = "1.0.0"
    description: str = "No description"

    maintainers: list[str] = dataclasses.field(default_factory=list)
    includes: list[str] = dataclasses.field(default_factory=list)
    macros: list[Macro] = dataclasses.field(default_factory=list)
    depends_on: list[str] = dataclasses.field(default_factory=list)

    _setup_hook: Callable[[Any], None] = dataclasses.field(default=None, init=False)
    _struct_field_tags: dict = dataclasses.field(default_factory=dict, init=False)
    _struct_tags: dict = dataclasses.field(default_factory=dict, init=False)
    _enum_tags: dict = dataclasses.field(default_factory=dict, init=False)
    _enum_member_tags: dict = dataclasses.field(default_factory=dict, init=False)
    _type_mappers: list[TypeMapper] = dataclasses.field(
        default_factory=list, init=False
    )
    _code_emitters: list[Callable] = dataclasses.field(default_factory=list, init=False)
    _header_emitters: list[Callable] = dataclasses.field(
        default_factory=list, init=False
    )
    _functions: list[FunctionType] = dataclasses.field(default_factory=list, init=False)

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
    def struct_tags(self) -> dict:
        return MappingProxyType(self._struct_tags)

    @property
    def enum_tags(self) -> dict:
        return MappingProxyType(self._enum_tags)

    @property
    def type_mappers(self) -> tuple:
        return tuple(self._type_mappers)

    @property
    def code_emitters(self) -> tuple:
        return tuple(self._code_emitters)

    @property
    def header_emitters(self) -> tuple:
        return tuple(self._header_emitters)

    @property
    def functions(self) -> tuple:
        return tuple(self._functions)

    def format_description(
        self, description: str, first_level_format: str, subsequent_format: str
    ) -> str:
        lines = []
        desc_lines = description.strip().splitlines()

        lines.append(first_level_format.format(desc_lines[0]))
        for extra_line in desc_lines[1:]:
            lines.append(subsequent_format.format(extra_line))

        return "\n".join(lines)

    def generate_header(
        self,
        inferred_prototypes: list[FunctionPrimitive],
        mapped_types: dict[str, list[str]],
    ) -> str:
        lines = []
        m_str = f" by {', '.join(self.maintainers)}" if self.maintainers else ""
        lines.append(
            self.format_description(
                self.description,
                first_level_format=f" *  -> {self.name} (v{self.version}){m_str} - {{}}",
                subsequent_format=" *      {}",
            )
        )

        def gen_str_for_tag_dict(tag_dict: dict[str, Tag], scope: str):
            for tag_name, tag in tag_dict.items():
                val_str = "(value)" if tag.enforced else ""
                if tag.description:
                    lines.append(
                        self.format_description(
                            tag.description,
                            f" *    - Provides tag: @{tag_name}{val_str} ({scope}) - {{}}",
                            " *      {}",
                        )
                    )
                else:
                    lines.append(
                        f" *    - Provides tag: @{tag_name}{val_str} ({scope})"
                    )

        gen_str_for_tag_dict(self._struct_tags, "Structs")
        gen_str_for_tag_dict(self._enum_tags, "Enums")
        gen_str_for_tag_dict(self._struct_field_tags, "Struct Fields")
        gen_str_for_tag_dict(self._enum_member_tags, "Enum Members")

        for macro in self.macros:
            lines.append(macro.to_doc_string())

        for mapper in self._type_mappers:
            types = mapped_types.get(mapper.signature, []) if mapped_types else []

            if mapper.description:
                sig = SIG_REGEX.match(mapper.signature)
                if sig:
                    sig_str = f"{sig.group('rettype').strip()} {sig.group('fname')}(..)"
                else:
                    sig_str = mapper.signature
                lines.append(
                    self.format_description(
                        mapper.description,
                        f" *    - Provides router: {sig_str} - {{}}",
                        " *      {}",
                    )
                )
            else:
                lines.append(f" *    - Provides router: {mapper.signature}")

            if types:
                types_joined = ", ".join(types)

                wrapped_types = textwrap.fill(
                    types_joined,
                    width=80,
                    initial_indent=" *      + Types: ",
                    subsequent_indent=" *        ",
                )
                lines.extend(wrapped_types.splitlines())
            else:
                lines.append(" (No types mapped)")

        if inferred_prototypes:
            for proto in sorted(inferred_prototypes, key=lambda f: f.fdef.name):
                if proto.description:
                    lines.append(
                        self.format_description(
                            proto.description,
                            f" *    - Provides function: {proto.fdef.doc_string()} - {{}}",
                            " *        {}",
                        )
                    )
                else:
                    lines.append(
                        f" *    - Provides function: {proto.fdef.doc_string()}"
                    )

        return "\n".join(lines)

    def setup(self, func):
        """Decorator to register the plugin setup"""
        self._setup_hook = func
        return func

    def emit_code(self, func):
        """Decorator for functions that return raw C code strings."""
        self._code_emitters.append(func)
        return func

    def emit_header(self, func):
        """Emit code at the header level"""
        self._header_emitters.append(func)

    def function(self, requires: str = None, description: str = ""):
        """Decorator to register a function"""

        def decorator(func):
            f = FunctionType(
                func=func,
                description=description,
                requires=requires,
            )
            self._functions.append(f)
            return func

        return decorator

    def struct_field_tag(
        self,
        tag_name: str,
        enforce_value=False,
        validator: Callable[[str, str], tuple[bool, str]] = None,
        description: str = "",
    ):
        """Decorator to register a struct field tag"""

        def decorator(func):
            self._struct_field_tags[tag_name] = Tag(
                func=func,
                enforced=enforce_value,
                validator=validator,
                description=description,
            )
            return func

        return decorator

    def enum_member_tag(
        self,
        tag_name: str,
        enforce_value=False,
        validator: Callable[[str, str], tuple[bool, str]] = None,
        description: str = "",
    ):
        """Decorator for tags applied to enum members."""

        def decorator(func):
            self._enum_member_tags[tag_name] = Tag(
                func=func,
                enforced=enforce_value,
                validator=validator,
                description=description,
            )

        return decorator

    def struct_tag(
        self,
        tag_name: str,
        enforce_value=False,
        validator: Callable[[str, str], tuple[bool, str]] = None,
        description: str = "",
    ):
        """Decorator for tags applied to structs"""

        def decorator(func):
            self._struct_tags[tag_name] = Tag(
                func=func,
                enforced=enforce_value,
                validator=validator,
                description=description,
            )
            return func

        return decorator

    def enum_tag(
        self,
        tag_name: str,
        enforce_value=False,
        validator: Callable[[str, str], tuple[bool, str]] = None,
        description: str = "",
    ):
        """Decorator for tags applied to structs"""

        def decorator(func):
            self._enum_tags[tag_name] = Tag(
                func=func,
                enforced=enforce_value,
                validator=validator,
                description=description,
            )
            return func

        return decorator

    def type_mapper(
        self,
        signature: str,
        switch_var: str,
        default_case: str = "break;",
        guard_clause: str = "",
        requires=None,
        description: str = "",
    ):
        """Decorator for creating a function for all types"""

        def decorator(func):
            mapper = TypeMapper(
                func=func,
                signature=signature,
                switch_var=switch_var,
                default_case=default_case,
                guard_clause=guard_clause,
                requires=requires,
                description=description,
            )
            self._type_mappers.append(mapper)

            # TODO: Maybe cutoff actual signature?
            # func_name = signature
            # self.description += f"\n *    - Provides router: {func_name}"
            return func

        return decorator


_PLUGINS: list[Plugin] = []


def sort_plugins(plugins: list[Plugin]) -> list[Plugin]:
    """Sorts plugin by dependencies, then name"""
    plugin_map = {p.name: p for p in plugins}
    deps_count_map = {p.name: 0 for p in plugins}
    dependents = {p.name: [] for p in plugins}

    for p in plugins:
        for dep in p.depends_on:
            if dep in plugin_map:
                dependents[dep].append(p.name)
                deps_count_map[p.name] += 1

    # Freely available plugins
    available = [p for p in plugins if deps_count_map[p.name] == 0]
    sorted_plugins = []

    while available:
        available.sort(key=lambda x: x.name)

        current = available.pop(0)
        sorted_plugins.append(current)

        for dep in dependents[current.name]:
            deps_count_map[dep] -= 1

            # No more dependencies, plugin is free
            if deps_count_map[dep] == 0:
                available.append(plugin_map[dep])

    if len(sorted_plugins) != len(plugins):
        raise ValueError(
            "Circular dependency detected in plugins! "
            "Two or more plugins depend on each other."
        )

    return sorted_plugins


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
        """Generates a field in EnumMemberInfo"""
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

        self.builtin_struct_tags = {"reflect", "enum"}
        self.builtin_enum_tags = {"reflect", "enum", "unchecked"}
        self.builtin_field_tags = {"private", "readonly", "writeonly", "length"}
        self.builtin_member_tags = {"private"}

        self.base_types = {}

        self.member_extensions_members = {}
        self.field_extension_members = {}
        self.active_struct_field_tags = {}
        self.active_enum_member_tags = {}
        self.active_enum_tags = {}
        self.active_struct_tags = {}
        self.active_type_mappers = []

        self.private_plugin_prototypes: dict[str, set[FunctionPrimitive]] = defaultdict(
            set
        )
        self.public_plugin_prototypes: dict[str, set[FunctionPrimitive]] = defaultdict(
            set
        )
        self.plugin_mapped_types: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def validate_tags(self):
        """Checks for any unregistered tags"""
        errors = []

        valid_struct_tags = self.builtin_struct_tags | set(self.active_struct_tags)
        valid_enum_tags = self.builtin_enum_tags | set(self.active_enum_tags)
        valid_field_tags = self.builtin_field_tags | set(self.active_struct_field_tags)
        valid_member_tags = self.builtin_member_tags | set(self.active_enum_member_tags)

        for struct_name, struct in self.structs.items():
            for tag in struct.tags:
                if tag not in valid_struct_tags:
                    errors.append(
                        f"- Unknown struct tag 'cmy:{tag}' on struct '{struct_name}"
                    )
            for field in struct.fields:
                for tag in field.tags:
                    if tag not in valid_field_tags:
                        errors.append(
                            f"- Unknown field tag 'cmy:{tag}' on field '{field.name}', in struct '{struct_name}'"
                        )

        for enum_name, enum in self.enums.items():
            for tag in enum.tags:
                if tag not in valid_enum_tags:
                    errors.append(
                        f"- Unknown enum tag 'cmy:{tag}' on enum '{enum_name}'"
                    )
            for member in enum.members:
                for tag in member.tags:
                    if tag not in valid_member_tags:
                        errors.append(
                            f"- Unknown member tag 'cmy:{tag}' on '{enum_name}'"
                        )

        if errors:
            error_message = (
                "Tag Validation failed. Did you make a type or forget to include a plugin?\n"
                + "\n".join(errors)
            )
            raise ValueError(error_message)

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

    def is_arr(self, identifier: str) -> bool:
        """Checks if the identifier is of an array"""
        return self.normalze_type_identifier(identifier).endswith("_arr")

    def is_struct(self, identifier: str) -> bool:
        """Checks if the identifier is a struct"""
        return self.get_base_type_name(identifier) in self.structs

    def is_enum(self, identifier: str) -> bool:
        """Checks if the identifier is an enum"""
        return self.get_base_type_name(identifier) in self.enums

    def load_plugins(self):
        global _PLUGINS

        _PLUGINS = sort_plugins(_PLUGINS)

        active_plugin_names = {p.name for p in _PLUGINS}
        errors = []

        struct_field_claims = defaultdict(list)
        enum_member_claims = defaultdict(list)
        struct_claims = defaultdict(list)
        enum_claims = defaultdict(list)

        for p in _PLUGINS:
            for dep in p.depends_on:
                if dep not in active_plugin_names:
                    errors.append(f"- Plugin '{p.name}' requires '{dep}'")

            if p.setup_hook:
                p.setup_hook(self)

            for tag_name, handler in p.struct_field_tags.items():
                struct_field_claims[tag_name].append((p.name, handler))

            for tag_name, handler in p.enum_member_tags.items():
                enum_member_claims[tag_name].append((p.name, handler))

            for tag_name, handler in p.struct_tags.items():
                struct_claims[tag_name].append((p.name, handler))

            for tag_name, handler in p.enum_tags.items():
                enum_claims[tag_name].append((p.name, handler))

            self.active_type_mappers.extend(p.type_mappers)

        def resolve_claims(claims, active_dict, context_name):
            for tag_name, claim_list in claims.items():
                if len(claim_list) > 1:
                    competing_plugs = [claim[0] for claim in claim_list]
                    errors.append(
                        f"- Tag collision: 'cmy:{tag_name}' ({context_name}) is claimed by "
                        f"{len(competing_plugs)} plugins: {', '.join(competing_plugs)}."
                    )
                else:
                    active_dict[tag_name] = claim_list[0][1]

        resolve_claims(
            struct_field_claims, self.active_struct_field_tags, "Struct Fields"
        )
        resolve_claims(enum_member_claims, self.active_enum_member_tags, "Enum Members")
        resolve_claims(struct_claims, self.active_struct_tags, "Structs")
        resolve_claims(enum_claims, self.active_enum_tags, "Enums")

        if errors:
            raise ValueError(
                "Plugin loading failed due to the following errors:\n"
                + "\n".join(errors)
            )

    def get_struct(self, identifier: str) -> CStruct | None:
        """Returns the CStruct object or None if not found"""
        base = self.get_base_type_name(identifier)
        return self.structs.get(base)

    def get_enum(self, identifier: str) -> CEnum | None:
        """Returns the CEnum object or None if not found"""
        base = self.get_base_type_name(identifier)
        return self.enums.get(base)

    def has_struct_tag(self, identifier: str, tag_name: str) -> bool:
        """Checks if the struct has a struct tag"""
        struct = self.get_struct(identifier)
        return struct is not None and tag_name in struct.tags

    def get_struct_tag(self, identifier: str, tag_name: str) -> str | None:
        """Get's the value of the struct tag"""
        struct = self.get_struct(identifier)
        return struct.tags.get(tag_name) if struct else None

    def has_enum_tag(self, identifier: str, tag_name: str) -> bool:
        """Get's the value of the enum tag"""
        enum = self.get_enum(identifier)
        return enum is not None and tag_name in enum.tags

    def define_field_extension(self, name: str, ctype: str, requires: str = None):
        """Defines an extension to the StructFieldExtension type in C"""
        self.field_extension_members[name] = (ctype, requires)

    def define_member_extension(self, name: str, ctype: str, requires: str = None):
        """Defines an extension to the EnumMemberExtension type in C"""
        self.member_extensions_members[name] = (ctype, requires)

    def set_field_extension(self, field: Field, name: str, value: str):
        """Set's the value of an field extension in C"""
        if name not in self.field_extension_members:
            raise ValueError(
                f"Validation Error: Cannot set extension '{name}' on field '{field.name}'. "
                f"It must be registered first using reflector.define_field_extension()."
            )

        field.plugin_data[name] = value

    def set_member_extension(self, member: EnumMember, name: str, value: str):
        """Sets's the value of a member extension in C"""
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
        """Adds a CEnum if unique"""
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

        self.load_plugins()
        self.validate_tags()

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
        """Generates the validator function for enums"""
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

        lines.append(self.generate_type_size_function())

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

        if self.field_extension_members:
            lines.append("""\
#define GET_FIELD_EXT(field_ptr) \\
    ((field_ptr) && (field_ptr)->user_data ? (const StructFieldExtension*)((field_ptr)->user_data) : NULL)
""")

        if self.member_extensions_members:
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
        """Gets the type suffix. (char_arr -> char), (char* -> char_ptr)"""
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

    def generate_type_size_function(self) -> str:
        lines = [
            "size_t get_type_size(FIELD_TYPE type) {",
            "    switch(type) {",
        ]
        for type_name, type_enum in self.type_map.items():
            if type_name == "unknown":
                continue
            ctype = self.ctypes.get(type_name, type_name)
            lines.append(f"        case {type_enum}: return sizeof({ctype});")

        lines.append("        default: return 0;")
        lines.append("    }")
        lines.append("}")

        return "\n".join(lines)

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
        header_code = []

        includes = set()
        declarations = []
        macros = []

        for p in _PLUGINS:
            public_prototypes = self.public_plugin_prototypes.get(p.name, set())
            mapped_types = self.plugin_mapped_types.get(p.name, [])

            lines.append(
                p.generate_header(public_prototypes, mapped_types=mapped_types)
            )

            prototypes = public_prototypes | self.private_plugin_prototypes.get(
                p.name, set()
            )

            plugin_header_code = []
            for emitter in p.header_emitters:
                code_snippet = emitter(self)
                if code_snippet:
                    plugin_header_code.append(code_snippet)

            if plugin_header_code:
                header_code.append(f"// {'-' * 40}")
                header_code.append(f"// Generated by '{p.name}'")
                header_code.append(f"// {'-' * 40}")
                header_code.extend(plugin_header_code)

            if prototypes:
                declarations.append(f"// {'#' * 40}")
                declarations.append(f"// {p.name} Declarations")
                declarations.append(f"// {'#' * 40}")

                grouped_protos = defaultdict(list)
                for f in prototypes:
                    grouped_protos[f.requires].append(f.fdef)

                if None in grouped_protos:
                    for fdef in sorted(grouped_protos[None], key=lambda f: f.name):
                        declarations.append(fdef.prototype_string())
                    declarations.append("")

                valid_reqs = [r for r in grouped_protos.keys() if r is not None]
                for req in sorted(valid_reqs):
                    fdefs = grouped_protos[req]

                    declarations.append(f"#ifdef {req}")
                    for sig in sorted(fdefs, key=lambda f: f.name):
                        declarations.append(sig.prototype_string())
                    declarations.append(f"#endif // {req}")

                declarations.append("")

            includes.update(p.includes)
            macro_defs = [m.to_c_string() for m in p.macros]
            macros.extend(macro_defs)

        lines.append(" */\n")

        if header_code:
            lines.append("")
            lines.extend(header_code)
            lines.append("")

        if macros:
            lines.append("")
            lines.extend(macros)
            lines.append("")

        if declarations:
            lines.append("")
            lines.extend(declarations)
            lines.append("")

        for inc in sorted(includes):
            if not inc.startswith("<") and not inc.startswith('"'):
                inc = f"<{inc}>"
            lines.append(f"#include {inc}")

        return "\n".join(lines)

    def _check_tag_value(
        self,
        tag_name: str,
        tag_value: str | None,
        enforced: bool,
        scope: str,
        validator: Callable[[str, str], tuple[bool, str]] = None,
    ):
        if enforced and tag_value is True:
            raise ValueError(f"Tag '{tag_name}' ({scope}) requires a value")
        if validator:
            valid, reason = validator(tag_name, tag_value)
            if not valid:
                raise ValueError(
                    f"Tag '{tag_name}' ({scope}) with value '{tag_value}' could not be validated. Reason:\n    {reason}"
                )

    def _add_proto(
        self,
        plugin: Plugin,
        c_code: str,
        public: bool,
        requires: str | None = None,
        description: str | None = None,
    ) -> FuncDef:
        match = SIG_REGEX.match(c_code)

        if match:
            fdef = FuncDef(
                qualifiers=match.group("prefix"),
                rettype=match.group("rettype"),
                name=match.group("fname"),
                params=match.group("params"),
            )
            func = FunctionPrimitive(
                fdef=fdef, requires=requires, description=description
            )

            if public:
                self.public_plugin_prototypes[plugin.name].add(func)
            else:
                self.private_plugin_prototypes[plugin.name].add(func)

            return fdef
        return None

    def generate_plugin_extensions(self) -> str:
        extension_lines = ["// --- Plugin-Generated-Extensions ---"]

        for p in _PLUGINS:
            plugin_code = []
            for emitter in p.code_emitters:
                snippet = emitter(self)
                if snippet:
                    plugin_code.append(snippet)
            for f in p.functions:
                c_code = f.func(self)
                self._add_proto(p, c_code, True, f.requires, f.description)

                if f.requires:
                    plugin_code.append(f"#ifdef {f.requires}")
                plugin_code.append(c_code)
                if f.requires:
                    plugin_code.append(f"#endif // {f.requires}")

            for mapper in p.type_mappers:
                standalone_funcs = []
                switch_cases = []

                for type_name, type_enum in self.type_map.items():
                    if type_name == "unknown":
                        continue
                    ctype = self.ctypes.get(type_name, type_name)
                    suffix = self.get_type_suffix(type_name)

                    result = mapper.func(self, type_name, type_enum, ctype, suffix)

                    if result:
                        func_code, case_code = result
                        self.plugin_mapped_types[p.name][mapper.signature].append(
                            type_name
                        )
                        if func_code:
                            fdef = self._add_proto(p, func_code, False, mapper.requires)
                            if fdef and "extern" not in fdef.qualifiers:
                                standalone_funcs.append(func_code)
                        if case_code:
                            switch_cases.append(
                                f"        case {type_enum}: {case_code}"
                            )
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
                else:
                    router = f"""\
static inline {mapper.signature} {{
    {mapper.guard_clause}
    {mapper.default_case}
}}
"""

                if mapper.requires:
                    plugin_code.append(f"#ifdef {mapper.requires}")
                plugin_code.extend(standalone_funcs)
                plugin_code.append(router)
                self._add_proto(p, router, False, mapper.requires, mapper.description)
                if mapper.requires:
                    plugin_code.append(f"#endif // {mapper.requires}")

            for struct in self.structs.values():
                for tag_name, tag_value in struct.tags.items():
                    if tag_name in p.struct_tags:
                        tag = p.struct_tags[tag_name]
                        self._check_tag_value(
                            tag_name, tag_value, tag.enforced, "Type", tag.validator
                        )

                        snippet = tag.func(self, struct, tag_value)
                        if snippet:
                            plugin_code.append(snippet)

            for enum in self.enums.values():
                for tag_name, tag_value in enum.tags.items():
                    if tag_name in p.enum_tags:
                        tag = p.enum_tags[tag_name]
                        self._check_tag_value(
                            tag_name, tag_value, tag.enforced, "Type", tag.validator
                        )

                        snippet = tag.func(self, enum, tag_value)
                        if snippet:
                            plugin_code.append(snippet)

            for struct in self.structs.values():
                for field in struct.fields:
                    for tag_name, tag_value in field.tags.items():
                        if tag_name in p.struct_field_tags:
                            tag = p.struct_field_tags[tag_name]
                            self._check_tag_value(
                                tag_name,
                                tag_value,
                                tag.enforced,
                                "Struct",
                                tag.validator,
                            )

                            snippet = tag.func(self, struct, field, tag_value)
                            if snippet:
                                plugin_code.append(snippet)

            for enum in self.enums.values():
                for member in enum.members:
                    for tag_name, tag_value in member.tags.items():
                        if tag_name in p.enum_member_tags:
                            tag = p.enum_member_tags[tag_name]
                            self._check_tag_value(
                                tag_name,
                                tag_value,
                                tag.enforced,
                                "Struct",
                                tag.validator,
                            )

                            snippet = tag.func(self, enum, member, tag_value)
                            if snippet:
                                plugin_code.append(snippet)

            if plugin_code:
                extension_lines.append(
                    "\n// =========================================="
                )
                extension_lines.append(f"// Plugin: {p.name}")
                extension_lines.append("// ==========================================")
                extension_lines.extend(plugin_code)

        return "\n".join(extension_lines)

    def __str__(self):
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


class CVar:
    def __init__(self, ctype: str, name: str, val: str = None):
        """Declares a variable builder for C"""
        self.ctype = ctype
        self.name = name
        self._val = val

        self.after: str = None

    def val(self, val: str):
        """Assigns the variable a value"""
        self._val = val
        return self

    def as_const(self):
        """Defines the variable as a constant"""
        self.ctype = "const " + self.ctype
        return self

    def remove_const(self):
        """Removes const qualifiers"""
        self.ctype = self.ctype.replace("const", "")
        return self

    def as_static(self):
        """Defines the variable as static"""
        self.ctype = "static " + self.ctype
        return self

    def val_with_default(self, cond: str, val: str, default: str = None):
        """Ternary assignment. Assigns the variable to a default value if condition is not met"""
        if self._val:
            raise ValueError(
                f"Var '{self.ctype} {self.name}' already has value '{self._val}'."
            )

        if default:
            self._val = f"({cond}) ? {val} : {default}"

        return self

    def checked(self, cond: str, ifbad: str):
        """Checks for the condition, then calls ifbad"""
        indented_ifbad = ifbad.replace("\n", "\n    ")
        self.after = f"if ({cond}) {{\n    {indented_ifbad}\n}}\n"
        return self

    def gen_str(self) -> str:
        """Generate the CVar as a string"""
        if self._val:
            var = f"{self.ctype} {self.name} = {self._val};"
        else:
            var = f"{self.ctype} {self.name};"

        if self.after:
            var += f"\n{self.after}"

        return var

    def __str__(self) -> str:
        return self.gen_str()

    def __radd__(self, other) -> str:
        if isinstance(other, str):
            return other + self.gen_str()

        if isinstance(other, CVar):
            return other.gen_str() + self.gen_str()

    def __add__(self, other) -> str:
        if isinstance(other, str):
            return self.gen_str() + other

        if isinstance(other, CVar):
            return self.gen_str() + other.gen_str()

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.gen_str() == other

        if isinstance(other, CVar):
            return self.gen_str() == other.gen_str()

        return NotImplemented


class CBuilder:
    def __init__(self, reflector: Reflector):
        """Creates a safe, literate CBuilder for creating C code"""
        self.reflector = reflector
        self.valid_suffixes = set(
            [reflector.get_type_suffix(t) for t in reflector.type_map.keys()]
        )

    def var(self, ctype: str, name: str, val: str = None) -> CVar:
        """Returns a CVar builder object"""
        return CVar(ctype, name, val)

    def _has_suffix(self, suffix: str) -> bool:
        return suffix in self.valid_suffixes

    def get_suffix_from_ident(self, identifier: str) -> str:
        """Gets the suffix given an identifier"""
        if self._has_suffix(identifier):
            return identifier
        else:
            base_name = self.reflector.get_base_type_name(identifier)
            suffix = self.reflector.get_type_suffix(base_name)
            if not self._has_suffix(suffix):
                raise ValueError(
                    f"Identifier '{identifier}' with base name '{base_name}' has invalid suffix '{suffix}'"
                )

            return suffix

    def struct_field_getter(
        self,
        identifier: str,
        val_ptr: str,
        instance_name: str = "instance",
        field_name: str = "field",
        array_len: str = None,
    ) -> str:
        """Type checked wrapper for get_field_<suffix> function"""
        suffix = self.get_suffix_from_ident(identifier)
        if self.reflector.is_arr(identifier):
            if not array_len:
                array_len = f"{field_name}->count"
            return f"get_field_{suffix}({instance_name}, {field_name}, {val_ptr}, {array_len});"
        elif array_len:
            raise ValueError(
                f"'{identifier}' is not an array, but array_len is provided."
            )
        return f"get_field_{suffix}({instance_name}, {field_name}, {val_ptr});"

    def struct_field_extension(self, field_name: str = "field"):
        """Wrapper for GET_FIELD_EXT"""
        return f"GET_FIELD_EXT({field_name})"

    def enum_member_extension(self, member_name: str = "member"):
        """Wrapper for GET_MEMBER_EXT"""
        return f"GET_MEMBER_EXT({member_name})"

    def struct_metadata(self, struct_name: str) -> str:
        """Type checked wrapper for StructMetaData_FromName macro"""
        if not self.reflector.is_struct(struct_name):
            raise ValueError(f"'{struct_name}' has no struct metadata.")
        return f"StructMetaData_FromName({struct_name})"

    def enum_metadata(self, enum_name: str) -> str:
        """Type checked wrapper for EnumMetaData_FromName macro"""
        if not self.reflector.is_enum(enum_name):
            raise ValueError(f"'{enum_name}' has no enum metadata.")
        return f"EnumMetaData_FromName({enum_name})"

    def check(self, cond: str, ifbad: str) -> str:
        """Creates an if statement"""
        ifbad_indented = ifbad.replace("\n", "\n    ")
        return f"if ({cond}) {{\n    {ifbad_indented}\n}}\n"

    def build_func(
        self,
        signature: str,
        body_lines: list[str],
        static="static",
        inline="inline",
        retval="ReflectResult",
    ) -> str:
        """Generates the CBuilder as a function"""
        flat_lines = []
        for item in body_lines:
            if item is not None:
                flat_lines.extend(str(item).split("\n"))
        indented_lines = [f"    {line}" if line.strip() else "" for line in flat_lines]
        body = "\n".join(indented_lines)

        modifiers = f"{static} {inline}".strip()
        prefix = f"{modifiers} {retval}".strip()

        return f"{prefix} {signature} {{\n{body}\n}}\n"


def extract_tags(comment_text: str) -> dict:
    tags = {}
    pattern = re.compile(r"cmy:([a-zA-Z0-9_]+)(?:\(([^)]+)\))?")

    for match in re.finditer(pattern, comment_text):
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
        r"(//\s*cmy:reflect[\s\S]*?)typedef\s+(struct|enum)[^{]*\{([^}]+)\}\s*(\w+);"
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

            line_tags = extract_tags(line)
            decl = line.split("//")[0].strip()
            if not decl:
                pending_tags.update(line_tags)
                continue

            field_tags = {**pending_tags, **line_tags}
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
