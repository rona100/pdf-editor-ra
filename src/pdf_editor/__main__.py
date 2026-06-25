"""Main entry point for running pdf_editor as a module."""

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        from pdf_editor._serve import main
        main()
    else:
        from .cli import main
        main()