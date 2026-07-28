from __future__ import annotations

from pyiccprofile.element import ICCTaggedElement
from pyiccprofile.lut8 import ICCLut8
from pyiccprofile.lut16 import ICCLut16
from pyiccprofile.lut_atob import ICCLutAToB


class ICCA2B1(ICCTaggedElement):
    SIGNATURE = b"A2B1"

    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutAToB):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> ICCA2B1:
        transform = ICCLutAToB.decode(data)
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCA2B1({self.transform})"
