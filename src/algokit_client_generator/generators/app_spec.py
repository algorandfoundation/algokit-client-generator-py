from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part


def generate_app_spec(context: GeneratorContext) -> DocumentParts:
    yield Part.InlineMode
    yield '_APP_SPEC_JSON = r"""'
    yield context.app_spec.to_json(indent=None)
    yield '"""'
    yield Part.RestoreLineMode
    yield """
_STRUCT_NAME_TO_TYPE: dict[str, type] = {"""
    # produce a mapping from original name to generated type
    yield Part.IncIndent
    for struct_name, generated_struct_name in context.generated_structs.items():
        yield f"{struct_name!r}: {generated_struct_name},"
    yield Part.DecIndent
    yield """}

APP_SPEC = arc56.Arc56Contract.from_json(
    _APP_SPEC_JSON,
    lambda s: _STRUCT_NAME_TO_TYPE[s.struct_name],
)"""
