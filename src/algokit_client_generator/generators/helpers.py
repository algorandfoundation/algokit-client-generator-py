from algokit_client_generator import utils
from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part


def generate_abi_args_parser(indent_size: int = 4) -> DocumentParts:
    """Generate the shared ABI args parsing method that will be used across generated clients

    Args:
        indent_level: Number of indentation levels to apply (default: 1 for class-level method)
    """
    yield utils.indented(
        """
def _parse_abi_args(args: typing.Any | None = None) -> list[typing.Any] | None:
    \"\"\"Helper to parse ABI args into the format expected by underlying client\"\"\"
    if args is None:
        return None

    def convert_dataclass(value: typing.Any) -> typing.Any:
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


def generate_helper_aliases(context: GeneratorContext) -> DocumentParts:
    yield utils.indented(
        """
ON_COMPLETE_TYPES = typing.Literal[
    OnComplete.NoOpOC,
    OnComplete.UpdateApplicationOC,
    OnComplete.DeleteApplicationOC,
    OnComplete.OptInOC,
    OnComplete.CloseOutOC,
]"""
    )


def generate_helpers(context: GeneratorContext) -> DocumentParts:
    yield Part.Gap1
    yield generate_abi_args_parser()
    yield Part.Gap1
    yield generate_helper_aliases(context)
    yield Part.Gap2
