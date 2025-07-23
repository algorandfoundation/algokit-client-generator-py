from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.spec import ContractMethod


def generate_abi_args_parser(indent_size: int = 4) -> DocumentParts:
    """Generate the shared ABI args parsing method that will be used across generated clients

    Args:
        indent_level: Number of indentation levels to apply (default: 1 for class-level method)
    """
    yield utils.indented(
        """
def _parse_abi_args(args: object | None = None) -> list[object] | None:
    \"\"\"Helper to parse ABI args into the format expected by underlying client\"\"\"
    if args is None:
        return None

    def convert_dataclass(value: object) -> object:
        if dataclasses.is_dataclass(value):
            return tuple(convert_dataclass(getattr(value, field.name)) for field in dataclasses.fields(value))
        elif isinstance(value, (list, tuple)):
            return type(value)(convert_dataclass(item) for item in value)
        return value

    match args:
        case tuple():
            method_args = list(args)
        case _ if dataclasses.is_dataclass(args):
            method_args = [getattr(args, field.name) for field in dataclasses.fields(args)]
        case _:
            raise ValueError("Invalid 'args' type. Expected 'tuple' or 'TypedDict' for respective typed arguments.")

    return [
        convert_dataclass(arg) if not isinstance(arg, algokit_utils.AppMethodCallTransactionArgument) else arg
        for arg in method_args
    ] if method_args else None
""",
        indent_size=indent_size,
    )


def generate_dataclass_initializer(context: GeneratorContext) -> DocumentParts:
    yield utils.indented(
        """
def _init_dataclass(cls: type, data: dict) -> object:
    \"\"\"
    Recursively instantiate a dataclass of type `cls` from `data`.

    For each field on the dataclass, if the field type is also a dataclass
    and the corresponding data is a dict, instantiate that field recursively.
    \"\"\"
    field_values = {}
    for field in dataclasses.fields(cls):
        field_value = data.get(field.name)
        # Check if the field expects another dataclass and the value is a dict.
        if dataclasses.is_dataclass(field.type) and isinstance(field_value, dict):
            field_values[field.name] = _init_dataclass(typing.cast(type, field.type), field_value)
        else:
            field_values[field.name] = field_value
    return cls(**field_values)
    """
    )


def generate_helpers(context: GeneratorContext) -> DocumentParts:
    yield Part.Gap1
    yield generate_abi_args_parser()
    yield Part.Gap1
    yield generate_dataclass_initializer(context)
    yield Part.Gap1


def get_abi_method_operations(context: GeneratorContext) -> dict[str, list[ContractMethod]]:
    operations = {}
    if context.mode == "full":
        operations["update"] = [
            m for m in context.methods.all_methods if m.call_config == "call" and "update_application" in m.on_complete
        ]
        operations["delete"] = [
            m for m in context.methods.all_methods if m.call_config == "call" and "delete_application" in m.on_complete
        ]

    operations["opt_in"] = [
        m for m in context.methods.all_methods if m.call_config == "call" and "opt_in" in m.on_complete
    ]
    operations["close_out"] = [
        m for m in context.methods.all_methods if m.call_config == "call" and "close_out" in m.on_complete
    ]

    return operations
