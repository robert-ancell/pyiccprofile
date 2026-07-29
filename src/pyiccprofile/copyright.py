from pyiccprofile.element import ICCTaggedElement
from pyiccprofile.multi_localized_unicode_type import ICCMultiLocalizedUnicodeType


class ICCCopyright(ICCTaggedElement):
    SIGNATURE = b"cprt"

    def __init__(self, copyright: ICCMultiLocalizedUnicodeType):
        self.copyright = copyright

    @classmethod
    def decode(cls, data: bytes) -> "ICCCopyright":
        copyright = ICCMultiLocalizedUnicodeType.decode(data)
        return cls(copyright)

    def encode(self, data: bytearray) -> None:
        self.copyright.encode(data)

    def __eq__(self, other):
        return isinstance(other, ICCCopyright) and other.copyright == self.copyright

    def __repr__(self) -> str:
        return f"ICCCopyright({self.copyright})"
