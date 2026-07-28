from pyiccprofile.codec import decode_xyz, encode_xyz
from pyiccprofile.element import ICCTaggedElement


class ICCMediaWhitePoint(ICCTaggedElement):
    def __init__(self, colors: list[tuple[float, float, float]]):
        self.colors = colors

    @classmethod
    def decode(cls, data: bytes) -> "ICCMediaWhitePoint":
        colors = decode_xyz(data)
        # FIXME: Can this be more than one color?
        return cls(colors)

    def encode(self, data: bytearray) -> None:
        encode_xyz(data, self.colors)

    def __repr__(self) -> str:
        return f"ICCMediaWhitePoint({self.colors})"
