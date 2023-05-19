import importlib
import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-10s: %(message)s")
logger = logging.getLogger(__name__)
root_path = Path(__file__).parent


@contextmanager
def cwd(path: Path) -> Generator[None, None, None]:
    old_pwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_pwd)


def main() -> None:
    example_dirs = filter(lambda file: file.is_dir() and "__" not in file.name, root_path.glob("*"))
    for example in example_dirs:
        logger.info(f"Building example {example.name}")
        with cwd(root_path):
            evaluated_file = importlib.import_module(f"examples.{example.name}.{example.name}")
        app = evaluated_file.app
        logger.info(f"  Building app {app.name}")
        app_spec = app.build()
        logger.info(f"  Writing {example.name}/application.json")
        (example / "application.json").write_text(app_spec.to_json())


if __name__ == "__main__":
    main()
