from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part


def generate_app_spec(context: GeneratorContext) -> DocumentParts:
    yield Part.InlineMode
    yield '_APP_SPEC_JSON = r"""'
    yield context.app_spec.to_json(indent=None)
    yield '"""'
    yield Part.RestoreLineMode
    yield "APP_SPEC = algokit_utils.Arc56Contract.from_json(_APP_SPEC_JSON)"
