class ICCTaggedElement:
    @classmethod
    def decode(cls, data: bytes) -> "ICCTaggedElement":
        raise NotImplementedError()


class ICCUnknownTaggedElement(ICCTaggedElement):
    def __init__(self, signature: bytes, data: bytes):
        self.signature = signature
        self.data = data

    def __repr__(self) -> str:
        return f"ICCUnknownTaggedData({self.signature!r}, ...)"
