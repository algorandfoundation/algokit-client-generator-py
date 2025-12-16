import re
from collections.abc import Iterable
from enum import Enum
from typing import Protocol

from algokit_abi import abi, arc56

from algokit_client_generator.document import DocumentParts, Part

NEW_LINE = "\n"


class Sanitizer(Protocol):
    def make_safe_type_identifier(self, value: str) -> str:
        """Convert string to a safe type identifier (PascalCase)"""
        ...

    def make_safe_method_identifier(self, value: str) -> str:
        """Convert string to a safe method identifier (snake_case)"""
        ...

    def make_safe_variable_identifier(self, value: str) -> str:
        """Convert string to a safe variable identifier (snake_case)"""
        ...

    def make_safe_property_identifier(self, value: str) -> str:
        """Convert string to a safe property identifier (snake_case)"""
        ...

    def make_safe_string_type_literal(self, value: str) -> str:
        """Convert string to a safe string literal by escaping quotes"""
        ...

    def get_safe_member_accessor(self, value: str) -> str:
        """Get safe member accessor syntax"""
        ...

    def is_safe_variable_identifier(self, value: str) -> bool:
        """Check if string is a safe variable identifier"""
        ...


class BaseSanitizer:
    def replace_invalid_with_underscore(self, value: str) -> str:
        return re.sub(r"[^a-z0-9_$]+", "_", value, flags=re.IGNORECASE)

    def escape_quotes(self, value: str) -> str:
        return re.sub(r'[\'"]', lambda m: f"\\{m.group(0)}", value)

    def remove_enclosing_quotes(self, value: str) -> str:
        return re.sub(r'^"|"$', "", value)

    def is_safe_variable_identifier(self, value: str) -> bool:
        return bool(re.match(r"^[a-z$_][a-z0-9_$]*$", value, re.IGNORECASE))


class DefaultSanitizer(BaseSanitizer):
    def make_safe_property_identifier(self, value: str) -> str:
        safe_value = self.replace_invalid_with_underscore(value)
        return to_snake_case(safe_value)

    def make_safe_type_identifier(self, value: str) -> str:
        safe_value = self.replace_invalid_with_underscore(value)
        return to_pascal_case(safe_value)

    def make_safe_method_identifier(self, value: str) -> str:
        safe_value = self.replace_invalid_with_underscore(value)
        return to_snake_case(safe_value)

    def make_safe_variable_identifier(self, value: str) -> str:
        safe_value = self.replace_invalid_with_underscore(value)
        return to_snake_case(safe_value)

    def make_safe_string_type_literal(self, value: str) -> str:
        return self.escape_quotes(value)

    def get_safe_member_accessor(self, value: str) -> str:
        if self.is_safe_variable_identifier(value):
            return f".{value}"
        return f"['{self.make_safe_string_type_literal(value)}']"


class PreservingSanitizer(BaseSanitizer):
    def make_safe_method_identifier(self, value: str) -> str:
        if self.is_safe_variable_identifier(value):
            return value
        return f'"{self.make_safe_string_type_literal(value)}"'

    def make_safe_property_identifier(self, value: str) -> str:
        if self.is_safe_variable_identifier(value):
            return value
        return f'"{self.make_safe_string_type_literal(value)}"'

    def make_safe_type_identifier(self, value: str) -> str:
        return self.replace_invalid_with_underscore(value)

    def make_safe_variable_identifier(self, value: str) -> str:
        return self.replace_invalid_with_underscore(value)

    def make_safe_string_type_literal(self, value: str) -> str:
        return self.escape_quotes(value)

    def get_safe_member_accessor(self, value: str) -> str:
        if self.is_safe_variable_identifier(value):
            return f".{value}"
        return f"['{self.remove_enclosing_quotes(value)}']"


def get_sanitizer(*, preserve_names: bool = False) -> Sanitizer:
    """Get appropriate sanitizer based on configuration"""
    return PreservingSanitizer() if preserve_names else DefaultSanitizer()


# Helper functions
def to_pascal_case(value: str) -> str:
    """Convert string to PascalCase, handling both snake_case and existing PascalCase inputs"""
    # First split on underscores
    words = value.split("_")
    split_words = []
    for word in words:
        if word:
            parts = get_parts(word)
            split_words.extend(parts)
    return "".join(word.capitalize() for word in split_words)


def to_snake_case(text: str) -> str:
    """Convert string to snake_case"""
    return "_".join([c.lower() for c in get_parts(text)]).lstrip("_")


class IOType(Enum):
    INPUT = "input"
    OUTPUT = "output"


def get_parts(value: str) -> list[str]:
    """Splits value into a list of words, with boundaries at _, and transitions between casing"""
    return re.findall("[A-Z][a-z]+|[0-9A-Z]+(?=[A-Z][a-z])|[0-9A-Z]{2,}|[a-z0-9]{2,}|[a-zA-Z0-9]", value)


def get_class_name(name: str, string_suffix: str = "") -> str:
    sanitizer = get_sanitizer(preserve_names=False)
    base_name = sanitizer.make_safe_type_identifier(name)
    if string_suffix:
        suffix = sanitizer.make_safe_type_identifier(string_suffix)
        return f"{base_name}{suffix}"
    return base_name


def get_method_name(name: str, string_suffix: str = "") -> str:
    sanitizer = get_sanitizer(preserve_names=False)
    base_name = sanitizer.make_safe_method_identifier(name)
    if string_suffix:
        suffix = sanitizer.make_safe_method_identifier(string_suffix)
        return f"{base_name}_{suffix}"
    return base_name


def abi_type_to_python(abi_type: abi.ABIType, io_type: IOType = IOType.OUTPUT) -> str:  # noqa: PLR0911, C901, PLR0912  # type: ignore[PLR0911]
    match abi_type:
        case abi.UintType():
            return "int"
        case abi.DynamicArrayType() as array:
            child = array.element
            if isinstance(child, abi.ByteType):
                return "bytes | str" if io_type == IOType.INPUT else "bytes"
            return f"list[{abi_type_to_python(child, io_type)}]"
        case abi.StaticArrayType() as array:
            child = array.element
            if isinstance(child, abi.ByteType):
                if io_type == IOType.INPUT:
                    return f"bytes | str | tuple[{', '.join('int' for _ in range(array.size))}]"
                return "bytes"
            inner_type = abi_type_to_python(child, io_type)
            return f"tuple[{', '.join(inner_type for _ in range(array.size))}]"
        case abi.AddressType():
            return "str"
        case abi.BoolType():
            return "bool"
        case abi.UfixedType():
            return "decimal.Decimal"
        case abi.TupleType() as tuple_type:
            return f"tuple[{', '.join(abi_type_to_python(t, io_type) for t in tuple_type.elements)}]"
        case abi.ByteType():
            return "int"
        case abi.StringType():
            return "str"
        case abi.StructType():
            return abi_type.decode_type.__name__
        case _:
            return "typing.Any"


def map_arc56_type_to_python(  # noqa: PLR0911
    arc56_type: arc56.AVMType | abi.ABIType | arc56.ReferenceType | arc56.TransactionType | arc56.VoidType,
    io_type: IOType = IOType.OUTPUT,
) -> str:
    match arc56_type:
        case arc56.Void:
            return "None"
        case arc56.AVMType.BYTES:
            return "bytes"
        case arc56.AVMType.UINT64:
            return "int"
        case arc56.AVMType.STRING:
            return "str"
        case arc56.ReferenceType.ASSET | arc56.ReferenceType.APPLICATION:
            return "int"
        case arc56.ReferenceType.ACCOUNT:
            return "str | bytes"
        case arc56.TransactionType():
            return "algokit_utils.AppMethodCallTransactionArgument"
        case _:
            return abi_type_to_python(arc56_type, io_type)


def get_unique_symbol_by_incrementing(
    existing_symbols: set[str], base_name: str, sanitizer: Sanitizer | None = None
) -> str:
    """Get a unique symbol by incrementing a number suffix if needed"""
    if sanitizer is None:
        sanitizer = get_sanitizer(preserve_names=False)
    base_name = sanitizer.make_safe_string_type_literal(base_name)
    suffix = 0
    while True:
        suffix_str = str(suffix) if suffix else ""
        symbol = f"{base_name}{suffix_str}"
        if symbol not in existing_symbols:
            existing_symbols.add(symbol)
            return symbol
        suffix += 1


SINGLE_QUOTE = '"'
TRIPLE_QUOTE = '"""'


def lines(block: str) -> DocumentParts:
    yield from block.splitlines()


def join(delimiter: str, items: Iterable[str]) -> DocumentParts:
    for idx, item in enumerate(m for m in items):
        if idx:
            yield delimiter
        yield item


def string_literal(value: str) -> str:
    return f'"{value}"'


def docstring(value: str) -> DocumentParts:
    yield Part.InlineMode
    yield TRIPLE_QUOTE
    value_lines = value.splitlines()
    last_idx = len(value_lines) - 1
    for idx, line in enumerate(value_lines):
        if idx == 0 and line.startswith(SINGLE_QUOTE):
            yield " "
        yield line
        if idx == last_idx and line.endswith(SINGLE_QUOTE):
            yield " "
        if idx != last_idx:
            yield Part.NewLine
    yield TRIPLE_QUOTE
    yield Part.RestoreLineMode


def indented(code_block: str, indent_size: int = 4) -> DocumentParts:
    code_block = code_block.strip()
    current_indents = 0
    source_indent_size = indent_size
    for line in code_block.splitlines():
        indents = (len(line) - len(line.lstrip(" "))) / source_indent_size
        while indents > current_indents:
            yield Part.IncIndent
            current_indents += 1
        while indents < current_indents:
            yield Part.DecIndent
            current_indents -= 1
        yield line.strip()
    while current_indents > 0:
        yield Part.DecIndent
        current_indents -= 1
