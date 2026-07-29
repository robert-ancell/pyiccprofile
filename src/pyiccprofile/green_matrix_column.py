from pyiccprofile.codec import decode_xyz, encode_xyz
from pyiccprofile.element import ICCTaggedElement


class ICCGreenMatrixColumn(ICCTaggedElement):
    SIGNATURE = b"gXYZ"

    def __init__(self, colors: list[tuple[float, float, float]]):
        self.colors = colors

    @classmethod
    def decode(cls, data: bytes) -> "ICCGreenMatrixColumn":
        colors = decode_xyz(data)
        return cls(colors)

    def encode(self, data: bytearray) -> None:
        encode_xyz(data, self.colors)

    def __eq__(self, other):
        return isinstance(other, ICCGreenMatrixColumn) and other.colors == self.colors

    def __repr__(self) -> str:
        return f"ICCGreenMatrixColumn({self.colors})"
