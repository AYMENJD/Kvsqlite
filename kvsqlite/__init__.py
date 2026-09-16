__version__ = "0.3.0"
__copyright__ = "Copyright (c) 2023-2026 AYMENJD ~ https://github.com/AYMENJD"
__license__ = "MIT License"

VERSION = __version__

__all__ = ["Client", "PickleEncoder", "StringEncoder", "sync"]

from . import sync
from .client import Client
from .encoders import PickleEncoder, StringEncoder
