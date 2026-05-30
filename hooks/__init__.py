"""omp hooks package — UserPromptSubmit/PostToolUse hooks + shared stdlib helpers.

Hook entry-point scripts (omp_route_emit.py, omp_verify_emit.py) are run as
standalone subprocesses by Claude Code; this `__init__.py` only makes shared
helpers (e.g. omp_atomic) importable by tests and skills. stdlib only.
"""
