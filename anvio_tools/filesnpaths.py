"""File and path validation helpers, mirroring anvio.filesnpaths."""

import os
import shutil

from anvio_tools.errors import ConfigError, FilesNPathsError


def is_file_exists(path):
    if not os.path.exists(path):
        raise FilesNPathsError(f"File not found: '{path}'")
    if not os.path.isfile(path):
        raise FilesNPathsError(f"Not a file: '{path}'")


def is_output_file_writable(path):
    output_dir = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(output_dir):
        raise FilesNPathsError(f"Output directory does not exist: '{output_dir}'")
    if os.path.exists(path) and not os.access(path, os.W_OK):
        raise FilesNPathsError(f"Output file is not writable: '{path}'")


def is_program_exists(program, advice_if_not_exists=None):
    """Raise ConfigError if `program` is not found in PATH."""
    if shutil.which(program) is None:
        msg = f"Program '{program}' is not found in your PATH."
        if advice_if_not_exists:
            msg += f" {advice_if_not_exists}"
        raise ConfigError(msg)
