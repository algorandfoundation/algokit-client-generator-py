import dataclasses

from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, Part
from algokit_client_generator.generators.app_spec import generate_app_spec
from algokit_client_generator.generators.composer import generate_composer
from algokit_client_generator.generators.header_comments import generate_header_comments
from algokit_client_generator.generators.helpers import generate_helpers
from algokit_client_generator.generators.imports import generate_imports
from algokit_client_generator.generators.typed_client import generate_typed_client
from algokit_client_generator.generators.typed_factory import generate_typed_factory

ESCAPED_QUOTE = r"\""


@dataclasses.dataclass(kw_only=True)
class GenerationSettings:
    indent: str = "    "
    max_line_length: int = 80

    @property
    def indent_length(self) -> int:
        return len(self.indent)


def generate(context: GeneratorContext) -> DocumentParts:
    yield generate_header_comments(context)
    yield generate_imports(context)
    yield Part.Gap1
    yield generate_app_spec(context)
    yield Part.Gap1
    yield generate_helpers(context)
    yield Part.Gap2
    yield generate_typed_client(context)
    if context.mode == "full":
        yield Part.Gap2
        yield generate_typed_factory(context)
    yield Part.Gap2
    yield generate_composer(context)
