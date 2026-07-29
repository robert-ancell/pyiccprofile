class ICCTaggedElement:
    SIGNATURE = b"\x00x00x00x00"

    @classmethod
    def decode(cls, data: bytes) -> "ICCTaggedElement":
        raise NotImplementedError()

    def encode(self, data: bytearray) -> None:
        raise NotImplementedError()


class ICCUnknownTaggedElement(ICCTaggedElement):
    def __init__(self, signature: bytes, data: bytes):
        self.signature = signature
        self.data = data

    def encode(self, data: bytearray) -> None:
        data.extend(self.data)

    def __repr__(self) -> str:
        return f"ICCUnknownTaggedData({self.signature!r}, ...)"
