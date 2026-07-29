from pyiccprofile.codec import (
    decode_multi_localized_unicode_type,
    encode_multi_localized_unicode_type,
)
from pyiccprofile.element import ICCTaggedElement


class ICCProfileDescription(ICCTaggedElement):
    SIGNATURE = b"desc"

    def __init__(self, description: list[tuple[str, str, str]]):
        self.description = description

    @classmethod
    def decode(cls, data: bytes) -> "ICCProfileDescription":
        description = decode_multi_localized_unicode_type(data)
        return cls(description)

    def encode(self, data: bytearray) -> None:
        encode_multi_localized_unicode_type(data, self.description)

    def __eq__(self, other):
        return (
            isinstance(other, ICCProfileDescription)
            and other.description == self.description
        )

    def __repr__(self) -> str:
        return f"ICCProfileDescription({self.description})"
