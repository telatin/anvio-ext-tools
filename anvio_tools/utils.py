"""General-purpose utilities, mirroring the relevant subset of anvio.utils."""

import os
import shutil
import subprocess

import anvio_tools
import anvio_tools.filesnpaths as filesnpaths

from anvio_tools.errors import ConfigError


def format_cmdline(cmdline):
    """Normalize a command to a list of strings."""
    if isinstance(cmdline, str):
        cmdline = cmdline.split()
    return [str(x) for x in cmdline]


def is_program_exists(program, advice_if_not_exists=None):
    """Raise ConfigError if `program` is not found in PATH."""
    filesnpaths.is_program_exists(program, advice_if_not_exists=advice_if_not_exists)


def run_command(cmdline, log_file_path, first_line_of_log_is_cmdline=True, remove_log_file_if_exists=True):
    """Run `cmdline`, sending all output to `log_file_path`.

    Mirrors anvio.utils.run_command — fire-and-forget, output goes to disk.
    Uses subprocess.call; returns the exit code.
    Raises ConfigError on OSError or negative exit code.
    """
    cmdline = format_cmdline(cmdline)

    if anvio_tools.DEBUG:
        import sys
        sys.stderr.write(f"[DEBUG] run_command: {' '.join(cmdline)}\n")

    filesnpaths.is_output_file_writable(log_file_path)

    if remove_log_file_if_exists and os.path.exists(log_file_path):
        os.remove(log_file_path)

    try:
        if first_line_of_log_is_cmdline:
            with open(log_file_path, 'a') as f:
                f.write(f"# CMD: {' '.join(cmdline)}\n")

        with open(log_file_path, 'a') as log_file:
            ret_val = subprocess.call(cmdline, shell=False, stdout=log_file, stderr=subprocess.STDOUT)

        if ret_val < 0:
            raise ConfigError(f"Command was terminated by a signal: '{' '.join(cmdline)}'")

        return ret_val

    except OSError as e:
        raise ConfigError(f"Command failed: '{e}' ('{' '.join(cmdline)}')")


def run_command_and_get_output(cmdline, raise_on_error=True, log_file_path=None):
    """Run `cmdline` and return its stdout as a string.

    Mirrors anvio.utils.run_command_and_get_output — the modern preferred style
    using subprocess.run() that captures stdout for programmatic parsing while
    optionally logging stderr to a file.

    Parameters
    ==========
    cmdline : str or list
    raise_on_error : bool, True
        Raise ConfigError when the command exits with a non-zero status.
    log_file_path : str or None
        If provided, stderr is written here; otherwise it is captured silently.

    Returns
    =======
    str
        The stdout of the command.
    """
    cmdline = format_cmdline(cmdline)

    if anvio_tools.DEBUG:
        import sys
        sys.stderr.write(f"[DEBUG] run_command_and_get_output: {' '.join(cmdline)}\n")

    try:
        proc = subprocess.run(
            cmdline,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if proc.returncode != 0:
            error_msg = f"Command failed (exit {proc.returncode}): {' '.join(cmdline)}"
            if proc.stderr:
                error_msg += f"\n{proc.stderr.strip()}"

            if log_file_path:
                filesnpaths.is_output_file_writable(log_file_path)
                with open(log_file_path, 'w') as f:
                    f.write(f"# CMD: {' '.join(cmdline)}\n")
                    f.write(f"# EXIT CODE: {proc.returncode}\n")
                    f.write(proc.stderr)

            if raise_on_error:
                raise ConfigError(error_msg)

        return proc.stdout

    except OSError as e:
        raise ConfigError(f"Command failed: '{e}' ('{' '.join(cmdline)}')")
