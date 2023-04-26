__version__ = "0.2.0"
__copyright__ = "Copyright (c) 2023 AYMEN Mohammed ~ https://github.com/AYMENJD"
__license__ = "MIT License"

VERSION = __version__

__all__ = ["Client", "PickleEncoder", "StringEncoder", "sync"]

from .client import Client
from .encoders import PickleEncoder, StringEncoder
from . import sync
