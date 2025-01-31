from algokit_client_generator.context import GeneratorContext
from algokit_client_generator.document import DocumentParts


def disable_linting() -> DocumentParts:
    yield "# flake8: noqa"  # this works for flake8 and ruff
    yield "# fmt: off"  # disable formatting
    yield '# mypy: disable-error-code="no-any-return, no-untyped-call, misc, type-arg"'  # disable common type warnings


def generate_header_comments(context: GeneratorContext) -> DocumentParts:
    if context.disable_linting:
        yield disable_linting()
    yield "# This file was automatically generated by algokit-client-generator."
    yield "# DO NOT MODIFY IT BY HAND."
    yield "# requires: algokit-utils@^3.0.0"
