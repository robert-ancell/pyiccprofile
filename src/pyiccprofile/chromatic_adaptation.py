from pyiccprofile.decoder import decode_s15fixed16_array
from pyiccprofile.element import ICCTaggedElement
from pyiccprofile.encoder import encode_s15fixed16_array


class ICCChromaticAdaptation(ICCTaggedElement):
    def __init__(self, matrix: list[float]):
        self.matrix = matrix

    @classmethod
    def decode(cls, data: bytes) -> "ICCChromaticAdaptation":
        matrix = decode_s15fixed16_array(data)
        if len(matrix) != 9:
            raise ValueError("Invalid matrix")
        return cls(matrix)

    def encode(self, data: bytearray) -> None:
        encode_s15fixed16_array(data, self.matrix)

    def __repr__(self) -> str:
        return f"ICCChromaticAdaptation({self.matrix})"
