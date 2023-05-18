from pathlib import Path

from algokit_utils import ApplicationSpecification

from algokit_client_generator.document import DocumentParts, RenderContext, convert_part
from algokit_client_generator.generator import GenerateContext, GenerationSettings, generate


def generate_client(input_path: Path, output_path: Path, settings: GenerationSettings | None = None) -> None:
    app_spec = ApplicationSpecification.from_json(input_path.read_text())

    context = GenerateContext(app_spec)
    if settings:
        context.settings = settings
    output = render(generate(context), context.settings)
    output_path.write_text(output)
    print(f"Output typed client for {app_spec.contract.name} to {output_path}")


def render(parts: DocumentParts, settings: GenerationSettings) -> str:
    context = RenderContext(indent_inc=settings.indent)
    return "".join(convert_part(parts, context))
