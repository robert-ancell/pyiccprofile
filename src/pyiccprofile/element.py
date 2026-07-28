class ICCTaggedElement:
    @classmethod
    def decode(cls, data: bytes) -> "ICCTaggedElement":
        raise NotImplementedError()
