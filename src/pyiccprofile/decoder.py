def decode_uint16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], byteorder="big")


def decode_uint32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], byteorder="big")


def decode_uint64(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 8], byteorder="big")


def decode_s15fixed16_number(data: bytes, offset: int) -> float:
    v = int.from_bytes(data[offset : offset + 4], byteorder="big", signed=True)
    return v / 65536.0


def decode_u15fixed16_number(data: bytes, offset: int) -> float:
    return decode_uint32(data, offset) / 65536.0


def decode_xyz_number(data: bytes, offset: int) -> tuple[float, float, float]:
    return (
        decode_s15fixed16_number(data, offset),
        decode_s15fixed16_number(data, offset + 4),
        decode_s15fixed16_number(data, offset + 8),
    )


def decode_signature(data: bytes, offset: int) -> bytes:
    return data[offset : offset + 4]


def decode_s15fixed16_array(data: bytes) -> list[float]:
    if len(data) < 8 or len(data) % 4 != 0:
        raise ValueError("Invalid length")
    signature = decode_signature(data, 0)
    if signature != b"sf32":
        raise ValueError("Invalid signature")
    reserved = data[4:8]
    if reserved != b"\x00\x00\x00\x00":
        raise ValueError("Reserved field must be 0")
    offset = 8
    count = (len(data) - offset) // 4
    values = []
    for _ in range(count):
        values.append(decode_s15fixed16_number(data, offset))
        offset += 4
    return values


def decode_xyz(data: bytes) -> list[tuple[float, float, float]]:
    if len(data) < 8 or len(data) % 4 != 0:
        raise ValueError("Invalid length")
    signature = decode_signature(data, 0)
    if signature != b"XYZ ":
        raise ValueError("Invalid signature")
    reserved = data[4:8]
    if reserved != b"\x00\x00\x00\x00":
        raise ValueError("Reserved field must be 0")
    offset = 8
    count = (len(data) - offset) // 4
    if count % 3 != 0:
        raise ValueError("Invalid count")
    values = []
    for _ in range(0, count, 3):
        values.append(decode_xyz_number(data, offset))
        offset += 12
    return values
