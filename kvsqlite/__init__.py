__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2023 AYMEN Mohammed ~ https://github.com/AYMENJD"
__license__ = "MIT License"

VERSION = __version__

__all__ = ["Client", "PickleEncoder", "StringEncoder"]

from .client import Client, PickleEncoder, StringEncoder
