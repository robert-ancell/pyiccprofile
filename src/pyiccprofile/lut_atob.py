class ICCLutAToB:
    SIGNATURE = b"mAB "

    def __init__(self):
        pass

    @classmethod
    def decode(cls, data: bytes) -> "ICCLutAToB":
        signature = data[:4]
        if signature != ICCLutAToB.SIGNATURE:
            raise ValueError(f"Invalid signature: {signature!r}")
        if data[4:8] != b"\x00\x00\x00\x00":
            raise ValueError("Invalid reserved bytes")
        # n_input_channels = data[8]
        # n_output_channels = data[9]
        if data[10] != 0 or data[11] != 0:
            raise ValueError("Invalid reserved bytes")
        return cls()

    def encode(self, data: bytearray) -> None:
        data.extend(ICCLutAToB.SIGNATURE)
        data.extend(b"\x00\x00\x00\x00")
        # FIXME

    def __repr__(self) -> str:
        return "ICCLutAToB()"
