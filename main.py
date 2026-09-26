"""Entry point for the task manager CLI.

This project uses the src layout: the importable package lives under ``src/``.
The two lines below put ``src/`` on the import path so ``python main.py`` works
without installing the project. In a packaged project you'd instead run
``pip install -e .`` and drop this shim.
"""
import sys
from pathlib import Path

__audit_id__ = "task-manager-cli"

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from task_manager.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
