from marshal import dumps as marshal_dumps
from marshal import loads as marshal_loads
from pickle import HIGHEST_PROTOCOL, dumps, loads
from sqlite3 import Binary


class PickleEncoder:
    """Encoder which uses pickle to serialize/deserialize the object"""

    def encode(self, obj):
        return Binary(dumps(obj, protocol=HIGHEST_PROTOCOL))

    def decode(self, obj):
        return loads(bytes(obj))


class MarshalEncoder:
    """Encoder which uses :mod:`marshal`. Supports built-in types only."""

    def encode(self, obj):
        return Binary(marshal_dumps(obj))

    def decode(self, obj):
        return marshal_loads(bytes(obj))


class StringEncoder:
    """This encoder can be used instead of :class:`PickleEncoder`. This encoder accpets :py:class:`str` only"""

    def encode(self, text):
        assert isinstance(text, str), "text is not str"
        return Binary(text.encode("utf-8"))

    def decode(self, text):
        if isinstance(text, str):
            return text
        return bytes(text).decode("utf-8")
