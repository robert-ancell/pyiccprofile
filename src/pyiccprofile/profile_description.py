from pyiccprofile.element import ICCTaggedElement
from pyiccprofile.multi_localized_unicode_type import ICCMultiLocalizedUnicodeType


class ICCProfileDescription(ICCTaggedElement):
    def __init__(self, description: ICCMultiLocalizedUnicodeType):
        self.description = description

    @classmethod
    def decode(cls, data: bytes) -> "ICCProfileDescription":
        description = ICCMultiLocalizedUnicodeType.decode(data)
        return cls(description)

    def encode(self, data: bytearray) -> None:
        self.description.encode(data)

    def __repr__(self) -> str:
        return f"ICCProfileDescription({self.description})"
