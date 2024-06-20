__version__ = "0.2.1"
__copyright__ = f"Copyright (c) {__import__("datetime").datetime.now().year} AYMEN Mohammed ~ https://github.com/AYMENJD"
__license__ = "MIT License"

VERSION = __version__

__all__ = ["Client", "PickleEncoder", "StringEncoder", "sync"]

from .client import Client
from .encoders import PickleEncoder, StringEncoder
from . import sync
