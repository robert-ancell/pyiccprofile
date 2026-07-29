from pyiccprofile.codec import decode_signature_type, encode_signature_type
from pyiccprofile.element import ICCTaggedElement


class ICCPerceptualRenderingIntentGamutType:
    MEDIUM = b"prmg"


class ICCPerceptualRenderingIntentGamut(ICCTaggedElement):
    SIGNATURE = b"rig0"

    def __init__(self, gamut: bytes):
        if len(gamut) != 4:
            raise ValueError("gamut must be a 4-byte signature")
        self.gamut = gamut

    @classmethod
    def decode(cls, data: bytes) -> "ICCPerceptualRenderingIntentGamut":
        gamut = decode_signature_type(data)
        return cls(gamut)

    def encode(self, data: bytearray) -> None:
        encode_signature_type(data, self.gamut)

    def __repr__(self) -> str:
        return f"ICCPerceptualRenderingIntentGamut({self.gamut!r})"
