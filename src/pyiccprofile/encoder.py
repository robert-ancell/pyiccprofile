def encode_uint32(data: bytearray, value: int) -> None:
    data.extend(value.to_bytes(4, byteorder="big"))


def encode_uint64(data: bytearray, value: int) -> None:
    data.extend(value.to_bytes(8, byteorder="big"))


def encode_s15fixed16_number(data: bytearray, value: float) -> None:
    int_value = int(value * 65536)
    data.extend(int_value.to_bytes(4, byteorder="big"))


def encode_xyz_number(data: bytearray, value: tuple[float, float, float]) -> None:
    encode_s15fixed16_number(data, value[0])
    encode_s15fixed16_number(data, value[1])
    encode_s15fixed16_number(data, value[2])


def encode_s15fixed16_array(data: bytearray, values: list[float]) -> None:
    data.extend(b"sf32")
    data.extend(b"\x00\x00\x00\x00")
    for value in values:
        encode_s15fixed16_number(data, value)


def encode_xyz(data: bytearray, values: list[tuple[float, float, float]]) -> None:
    data.extend(b"XYZ ")
    data.extend(b"\x00\x00\x00\x00")
    for value in values:
        encode_xyz_number(data, value)
