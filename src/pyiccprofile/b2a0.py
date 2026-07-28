from __future__ import annotations

from pyiccprofile.element import ICCTaggedElement
from pyiccprofile.lut8 import ICCLut8
from pyiccprofile.lut16 import ICCLut16
from pyiccprofile.lut_btoa import ICCLutBToA


class ICCB2A0(ICCTaggedElement):
    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutBToA):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> ICCB2A0:
        transform = ICCLutBToA.decode(data)
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCB2A0({self.transform})"
