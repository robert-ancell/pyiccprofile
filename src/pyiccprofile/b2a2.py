from __future__ import annotations

from pyiccprofile.codec import decode_signature
from pyiccprofile.element import ICCTaggedElement
from pyiccprofile.lut8 import ICCLut8
from pyiccprofile.lut16 import ICCLut16
from pyiccprofile.lut_btoa import ICCLutBToA


class ICCB2A2(ICCTaggedElement):
    SIGNATURE = b"B2A2"

    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutBToA):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> ICCB2A2:
        signature = decode_signature(data, 0)
        transform: ICCLut8 | ICCLut16 | ICCLutBToA
        if signature == ICCLut8.SIGNATURE:
            transform = ICCLut8.decode(data)
        elif signature == ICCLut16.SIGNATURE:
            transform = ICCLut16.decode(data)
        elif signature == ICCLutBToA.SIGNATURE:
            transform = ICCLutBToA.decode(data)
        else:
            raise ValueError(f"Invalid signature: {signature!r}")
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCB2A2({self.transform})"
