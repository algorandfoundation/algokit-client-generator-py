import logging
from pathlib import Path

from algokit_utils import ApplicationSpecification

from algokit_client_generator.document import DocumentParts, RenderContext, convert_part
from algokit_client_generator.generator import GenerateContext, generate

logger = logging.getLogger(__name__)


def generate_client(input_path: Path, output_path: Path) -> None:
    """Given a path to an ARC-32 application.json, output a typed python client

    :param Path input_path: Path to an ARC-32 application.json
    :param Path output_path: Path to write a typed python client to
    """
    app_spec = ApplicationSpecification.from_json(input_path.read_text())

    context = GenerateContext(app_spec)
    output = render(generate(context))
    output_path.write_text(output)
    logger.info(f"Output typed client for {app_spec.contract.name} to {output_path}")


def render(parts: DocumentParts) -> str:
    context = RenderContext(indent_inc="    ")
    return "".join(convert_part(parts, context))
