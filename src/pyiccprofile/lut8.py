from pyiccprofile.decoder import decode_s15fixed16_number
from pyiccprofile.encoder import encode_s15fixed16_number


class ICCLut8:
    def __init__(self, e1, e2, e3, e4, e5, e6, e7, e8, e9):
        self.e1 = e1
        self.e2 = e2
        self.e3 = e3
        self.e4 = e4
        self.e5 = e5
        self.e6 = e6
        self.e7 = e7
        self.e8 = e8
        self.e9 = e9

    @classmethod
    def decode(cls, data: bytes) -> "ICCLut8":
        if len(data) < 48:
            raise ValueError("Insufficient data")
        signature = data[:4]
        if signature != b"mft1":
            raise ValueError(f"Invalid signature: {signature!r}")
        if data[4:8] != b"\x00\x00\x00\x00":
            raise ValueError("Invalid reserved bytes")
        # n_input_channels = data[8]
        # n_output_channels = data[9]
        # n_clut_grid_points = data[10]
        if data[11] != 0:
            raise ValueError("Reserved byte must be 0")
        e1 = decode_s15fixed16_number(data, 12)
        e2 = decode_s15fixed16_number(data, 16)
        e3 = decode_s15fixed16_number(data, 20)
        e4 = decode_s15fixed16_number(data, 24)
        e5 = decode_s15fixed16_number(data, 28)
        e6 = decode_s15fixed16_number(data, 32)
        e7 = decode_s15fixed16_number(data, 36)
        e8 = decode_s15fixed16_number(data, 40)
        e9 = decode_s15fixed16_number(data, 44)
        # FIXME

        return cls(e1, e2, e3, e4, e5, e6, e7, e8, e9)

    def encode(self, data: bytearray) -> None:
        data.extend(b"mft1")
        data.extend(b"\x00\x00\x00\x00")
        data.append(0)  # n_input_channels
        data.append(0)  # n_output_channels
        data.append(0)  # n_clut_grid_points
        data.append(0)
        encode_s15fixed16_number(data, self.e1)
        encode_s15fixed16_number(data, self.e2)
        encode_s15fixed16_number(data, self.e3)
        encode_s15fixed16_number(data, self.e4)
        encode_s15fixed16_number(data, self.e5)
        encode_s15fixed16_number(data, self.e6)
        encode_s15fixed16_number(data, self.e7)
        encode_s15fixed16_number(data, self.e8)
        encode_s15fixed16_number(data, self.e9)
        # FIXME
