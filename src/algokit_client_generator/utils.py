import re
from collections.abc import Iterable

from algosdk import abi

from algokit_client_generator.document import DocumentParts, Part


def get_parts(value: str) -> list[str]:
    """Splits value into a list of words, with boundaries at _, and transitions between casing"""
    return re.findall("[A-Z][a-z]+|[0-9A-Z]+(?=[A-Z][a-z])|[0-9A-Z]{2,}|[a-z0-9]{2,}|[a-zA-Z0-9]", value)


def get_class_name(name: str, string_suffix: str = "") -> str:
    parts = [p.title() for p in get_parts(name)]
    if string_suffix:
        parts.append(string_suffix.title())
    return "".join(p for p in parts)


def get_method_name(name: str, string_suffix: str = "") -> str:
    parts = [p.lower() for p in get_parts(name)]
    if string_suffix:
        parts.append(string_suffix.lower())
    return "_".join(p for p in parts)


def abi_type_to_python(abi_type: abi.ABIType) -> str:  # noqa: PLR0911: ignore[PLR0911]
    match abi_type:
        case abi.UintType():
            return "int"
        case abi.ArrayDynamicType() as array:
            child = array.child_type
            if isinstance(child, abi.ByteType):
                return "bytes | bytearray"
            return f"list[{abi_type_to_python(child)}]"
        case abi.ArrayStaticType() as array:
            child = array.child_type
            if isinstance(child, abi.ByteType):
                return f"bytes | bytearray | tuple[{', '.join('int' for _ in range(array.static_length))}]"
            inner_type = abi_type_to_python(child)
            return f"list[{inner_type}] | tuple[{', '.join(inner_type for _ in range(array.static_length))}]"
        case abi.AddressType():
            return "str"
        case abi.BoolType():
            return "bool"
        case abi.UfixedType():
            return "decimal.Decimal"
        case abi.TupleType() as tuple_type:
            return f"tuple[{', '.join(abi_type_to_python(t) for t in tuple_type.child_types)}]"
        case abi.ByteType():
            return "int"
        case abi.StringType():
            return "str"
        case _:
            return "typing.Any"


def map_abi_type_to_python(abi_type_str: str) -> str:
    match abi_type_str:
        case "void":
            return "None"
        case abi.reference.ABIReferenceType.ASSET | abi.reference.ABIReferenceType.APPLICATION:
            return "int"
        case abi.reference.ABIReferenceType.ACCOUNT:
            return "str | bytes"
    if abi.is_abi_transaction_type(abi_type_str):
        # TODO: generic TransactionWithSigner and/or allow unsigned types signed with signer used in transaction
        return "TransactionWithSigner"
    abi_type = abi.ABIType.from_string(abi_type_str)
    return abi_type_to_python(abi_type)


def get_unique_symbol_by_incrementing(existing_symbols: set[str], base_name: str) -> str:
    suffix = 0
    while True:
        suffix_str = str(suffix) if suffix else ""
        symbol = base_name + suffix_str
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
    return f'"{value}"'  # TODO escape quotes


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


def indented(code_block: str) -> DocumentParts:
    code_block = code_block.strip()
    current_indents = 0
    source_indent_size = 4
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
