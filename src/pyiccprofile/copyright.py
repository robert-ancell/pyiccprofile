from pyiccprofile.codec import (
    decode_multi_localized_unicode_type,
    encode_multi_localized_unicode_type,
)
from pyiccprofile.element import ICCTaggedElement


class ICCCopyright(ICCTaggedElement):
    SIGNATURE = b"cprt"

    def __init__(self, copyright: list[tuple[str, str, str]]):
        self.copyright = copyright

    @classmethod
    def decode(cls, data: bytes) -> "ICCCopyright":
        copyright = decode_multi_localized_unicode_type(data)
        return cls(copyright)

    def encode(self, data: bytearray) -> None:
        encode_multi_localized_unicode_type(data, self.copyright)

    def __eq__(self, other):
        return isinstance(other, ICCCopyright) and other.copyright == self.copyright

    def __repr__(self) -> str:
        return f"ICCCopyright({self.copyright})"
