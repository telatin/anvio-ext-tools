import sys

__version__ = '1.0.0'

# Global flags read from sys.argv at import time, exactly like Anvio.
DEBUG = '--debug' in sys.argv
QUIET = '--quiet' in sys.argv

# Executor backend: path | conda | docker | singularity (default: path).
# Each driver reads anvio_tools.EXEC to decide how to invoke its binary.
_EXEC_CHOICES = ('path', 'conda', 'docker', 'singularity')
EXEC = 'path'
if '--exec' in sys.argv:
    _idx = sys.argv.index('--exec')
    if _idx + 1 < len(sys.argv):
        EXEC = sys.argv[_idx + 1]
