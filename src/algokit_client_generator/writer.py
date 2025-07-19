import logging
from pathlib import Path

from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts, RenderContext, convert_part
from algokit_client_generator.generator import generate
from algokit_client_generator.spec import load_from_json

logger = logging.getLogger(__name__)


def generate_client(input_path: Path, output_path: Path, *, preserve_names: bool = False, mode: str = "full") -> None:
    """Given a path to an ARC-32 application.json, output a typed python client

    :param Path input_path: Path to an ARC-32 application.json
    :param Path output_path: Path to write a typed python client to
    :param bool preserve_names: Preserve original names for structs and methods
    :param str mode: Generation mode - "full" or "minimal"
    """
    app_spec = load_from_json(input_path)
    context = GeneratorContext(app_spec, preserve_names=preserve_names, mode=mode)
    output = render(generate(context))
    output_path.write_text(output, encoding="utf-8")
    logger.info(f"Output typed client for {app_spec.name} to {output_path}")


def render(parts: DocumentParts) -> str:
    context = RenderContext(indent_inc="    ")
    return "".join(convert_part(parts, context))
