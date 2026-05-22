import sys

__version__ = '1.0.0'

# Global flags read from sys.argv at import time, exactly like Anvio.
DEBUG = '--debug' in sys.argv
QUIET = '--quiet' in sys.argv
