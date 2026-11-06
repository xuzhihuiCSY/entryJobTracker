"""Run the project's assertion-based Python regression modules without network."""
from pathlib import Path
import runpy


def main() -> None:
    paths = sorted(Path(__file__).resolve().parent.glob("test_*.py"))
    for path in paths:
        runpy.run_path(str(path), run_name="__main__")
    print(f"Passed {len(paths)} Python regression modules")


if __name__ == "__main__":
    main()
