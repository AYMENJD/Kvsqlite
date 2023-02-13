from pickle import dumps, loads, HIGHEST_PROTOCOL
from sqlite3 import Binary


class PickleEncoder:
    """Encoder which uses pickle to serialize/deserialize the object"""

    def __init__(self) -> None:
        pass

    def encode(self, obj):
        return Binary(dumps(obj, protocol=HIGHEST_PROTOCOL))

    def decode(self, obj):
        return loads(bytes(obj))


class StringEncoder:
    """This encoder can be used instead of :class:`PickleEncoder`. This encoder accpets :py:class:`str` only"""

    def __init__(self) -> None:
        pass

    def encode(self, text):
        assert isinstance(text, str), "text is not str"
        return Binary(text.encode("utf-8"))

    def decode(self, text):
        assert isinstance(text, str), "text is not str"
        return text
