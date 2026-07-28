from __future__ import annotations

from pyiccprofile.codec import decode_signature
from pyiccprofile.element import ICCTaggedElement
from pyiccprofile.lut8 import ICCLut8
from pyiccprofile.lut16 import ICCLut16
from pyiccprofile.lut_atob import ICCLutAToB


class ICCA2B0(ICCTaggedElement):
    SIGNATURE = b"A2B0"

    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutAToB):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> ICCA2B0:
        signature = decode_signature(data, 0)
        transform: ICCLut8 | ICCLut16 | ICCLutAToB
        if signature == ICCLut8.SIGNATURE:
            transform = ICCLut8.decode(data)
        elif signature == ICCLut16.SIGNATURE:
            transform = ICCLut16.decode(data)
        elif signature == ICCLutAToB.SIGNATURE:
            transform = ICCLutAToB.decode(data)
        else:
            raise ValueError(f"Invalid signature: {signature!r}")
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCA2B0({self.transform})"
