import pathlib


def enable_mypy(approved_path: pathlib.Path) -> None:
    """
    Update the mypy directive in the approved client file.
    It asserts that the third line is "# type: ignore\n" and then replaces it
    with the updated mypy comment.
    """
    # Read the file text with line endings preserved
    lines = approved_path.read_text().splitlines(keepends=True)
    assert (
        lines[2] == "# type: ignore\n"
    ), f"Expected third line to be '# type: ignore', got {lines[2]!r} in {approved_path}"
    # Replace the third line with the updated mypy comment
    lines[2] = '# mypy: disable-error-code="no-any-return, no-untyped-call, misc, type-arg"\n'
    approved_path.write_text("".join(lines))
