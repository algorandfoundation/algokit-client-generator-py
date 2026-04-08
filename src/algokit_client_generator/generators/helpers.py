from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.spec import ContractMethod


def generate_helpers(context: GeneratorContext) -> DocumentParts:
    yield '''
_T = typing.TypeVar("_T")
def _extend(
    new_type: type[_T], base_instance: typing.Any, **changes: object
) -> _T:
    """Creates a new type from an existing object and additional fields"""
    old_type_fields = {f.name : f for f in dataclasses.fields(base_instance)}
    new_type_fields = dataclasses.fields(new_type) # type: ignore[arg-type]
    for field in new_type_fields:
        if not field.init:
            continue
        attr_name = field.name
        if attr_name not in changes and attr_name in old_type_fields:
            changes[attr_name] = getattr(base_instance, attr_name)
    return new_type(**changes)
'''
    yield Part.Gap2
    yield """
def _unpack_args(args: object | tuple | None) -> tuple | None:
    if dataclasses.is_dataclass(args):
        return tuple(getattr(args, f.name) for f in dataclasses.fields(args))
    elif isinstance(args, tuple | None):
        return args
    else:
        raise TypeError("unsupported argument type")
"""


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
