"""Terminal output helpers — Run and Progress — mirroring the Anvio pattern."""

import sys


# ANSI color codes used by Run output.
_CYAN  = '\033[36m'
_YELLOW = '\033[33m'
_GREEN = '\033[32m'
_RED   = '\033[31m'
_RESET = '\033[0m'
_BOLD  = '\033[1m'

_COLOR = {
    'cyan':   _CYAN,
    'yellow': _YELLOW,
    'green':  _GREEN,
    'red':    _RED,
    'white':  '',
    None:     '',
}


def pretty_print(x):
    """Format an integer with commas."""
    if isinstance(x, int):
        return f"{x:,}"
    return str(x)


pp = pretty_print


class Run:
    """Structured key-value terminal output, mirroring anvio.terminal.Run."""

    def __init__(self, verbose=True, log_file_path=None):
        self.verbose = verbose
        self.log_file_path = log_file_path

    def _write(self, text):
        if self.verbose:
            sys.stdout.write(text)
            sys.stdout.flush()
        if self.log_file_path:
            with open(self.log_file_path, 'a') as f:
                f.write(text)

    def info(self, key, value, mc=None, lc=None, nl_before=0, nl_after=0, quiet=False, cut_after=80):
        if quiet or not self.verbose:
            return
        for _ in range(nl_before):
            self._write('\n')
        key_color = _COLOR.get(lc, '')
        val_color = _COLOR.get(mc, _YELLOW)
        line = f"  {key_color}{_BOLD}{key}{_RESET} {val_color}{value}{_RESET}\n"
        self._write(line)
        for _ in range(nl_after):
            self._write('\n')

    def info_single(self, msg, level=1, mc=None, nl_before=0, nl_after=0, cut_after=80):
        if not self.verbose:
            return
        indent = '  ' * level
        color = _COLOR.get(mc, '')
        for _ in range(nl_before):
            self._write('\n')
        self._write(f"{indent}* {color}{msg}{_RESET}\n")
        for _ in range(nl_after):
            self._write('\n')

    def warning(self, msg, header='WARNING', lc=None, nl_before=1, nl_after=1):
        if not self.verbose:
            return
        color = _COLOR.get(lc, _YELLOW)
        for _ in range(nl_before):
            self._write('\n')
        if header:
            bar = '-' * 60
            #self._write(f"  {color}{bar}{_RESET}\n")
            self._write(f"  {color}{_BOLD}➡ {header}{_RESET}\n")
            self._write(f"  {color}{bar}{_RESET}\n")
        if msg:
            self._write(f"  {msg}\n")
        for _ in range(nl_after):
            self._write('\n')


class Progress:
    """Live stderr progress line, mirroring anvio.terminal.Progress."""

    def __init__(self):
        self.header = None
        self.pid_set = False

    def new(self, msg, progress_total_items=None):
        self.header = msg
        sys.stderr.write(f"\n  {_BOLD}{msg}{_RESET} ...\n")
        sys.stderr.flush()

    def update(self, msg):
        sys.stderr.write(f"\r  {self.header}: {msg}    ")
        sys.stderr.flush()

    def end(self):
        sys.stderr.write('\n')
        sys.stderr.flush()
        self.header = None

    def reset(self):
        sys.stderr.write('\r')
        sys.stderr.flush()

    def increment(self):
        pass

    def clear(self):
        sys.stderr.write('\r' + ' ' * 80 + '\r')
        sys.stderr.flush()
