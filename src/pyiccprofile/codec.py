def encode_uint16(data: bytearray, value: int) -> None:
    data.extend(value.to_bytes(2, byteorder="big"))


def encode_uint32(data: bytearray, value: int) -> None:
    data.extend(value.to_bytes(4, byteorder="big"))


def encode_uint64(data: bytearray, value: int) -> None:
    data.extend(value.to_bytes(8, byteorder="big"))


def encode_u16fixed16_number(data: bytearray, value: float) -> None:
    encode_uint32(data, int(value * 65536))


def encode_s15fixed16_number(data: bytearray, value: float) -> None:
    int_value = int(value * 65536)
    data.extend(int_value.to_bytes(4, byteorder="big", signed=True))


def encode_xyz_number(data: bytearray, value: tuple[float, float, float]) -> None:
    encode_s15fixed16_number(data, value[0])
    encode_s15fixed16_number(data, value[1])
    encode_s15fixed16_number(data, value[2])


def encode_s15fixed16_array(data: bytearray, values: list[float]) -> None:
    encode_signature(data, b"sf32")
    data.extend(b"\x00\x00\x00\x00")
    for value in values:
        encode_s15fixed16_number(data, value)


def encode_xyz(data: bytearray, values: list[tuple[float, float, float]]) -> None:
    encode_signature(data, b"XYZ ")
    data.extend(b"\x00\x00\x00\x00")
    for value in values:
        encode_xyz_number(data, value)


def encode_signature(data: bytearray, signature: bytes) -> None:
    data.extend(signature)


def encode_signature_type(data: bytearray, value: bytes) -> None:
    encode_signature(data, b"sig ")
    data.extend(b"\x00\x00\x00\x00")
    encode_signature(data, value)


def encode_multi_localized_unicode_type(
    data: bytearray, value: list[tuple[str, str, str]]
) -> None:
    encode_signature(data, b"mluc")
    data.extend(b"\x00\x00\x00\x00")
    encode_uint32(data, len(value))
    encode_uint32(data, 12)
    string_offset = 16 + len(value) * 12
    for language_code, country_code, string in value:
        data.extend(language_code.encode("ascii"))
        data.extend(country_code.encode("ascii"))
        string_length = len(string.encode("utf-16-be"))
        encode_uint32(data, string_length)
        encode_uint32(data, string_offset)
        string_offset += string_length
    for _, _, string in value:
        data.extend(string.encode("utf-16-be"))


def decode_uint16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], byteorder="big")


def decode_uint32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], byteorder="big")


def decode_uint64(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 8], byteorder="big")


def decode_u16fixed16_number(data: bytes, offset: int) -> float:
    return decode_uint32(data, offset) / 65536.0


def decode_s15fixed16_number(data: bytes, offset: int) -> float:
    v = int.from_bytes(data[offset : offset + 4], byteorder="big", signed=True)
    return v / 65536.0


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
    if decode_signature(data, 0) != b"sf32":
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


def decode_signature_type(data: bytes) -> bytes:
    if len(data) != 12:
        raise ValueError("Invalid length")
    if decode_signature(data, 0) != b"sig ":
        raise ValueError("Invalid signature")
    if data[4:8] != b"\x00\x00\x00\x00":
        raise ValueError("Reserved field must be 0")
    return decode_signature(data, 8)


def decode_multi_localized_unicode_type(data: bytes) -> list[tuple[str, str, str]]:
    if len(data) < 16:
        raise ValueError("Invalid length multi-localized unicode type")

    signature = decode_signature(data, 0)
    if signature != b"mluc":
        raise ValueError("Invalid signature for multi-localized unicode type")
    reserved = decode_uint32(data, 4)
    if reserved != 0:
        raise ValueError("Reserved field must be 0")
    n_records = decode_uint32(data, 8)
    record_length = decode_uint32(data, 12)
    if record_length < 12:
        raise ValueError("Invalid record length")
    character_start = 16 + n_records * record_length
    if character_start > len(data):
        raise ValueError("Insufficient data for records")
    record_offset = 16
    records = []
    for _ in range(n_records):
        language_code = data[record_offset : record_offset + 2].decode("ascii")
        country_code = data[record_offset + 2 : record_offset + 4].decode("ascii")
        string_length = decode_uint32(data, record_offset + 4)
        string_offset = decode_uint32(data, record_offset + 8)
        if string_offset < character_start or string_offset + string_length > len(data):
            raise ValueError("Invalid string offset")
        string = data[string_offset : string_offset + string_length].decode("utf-16-be")
        records.append((language_code, country_code, string))
        record_offset += record_length

    return records


class ICCDateTime:
    def __init__(
        self, year: int, month: int, day: int, hours: int, minutes: int, seconds: int
    ):
        self.year = year
        self.month = month
        self.day = day
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    @classmethod
    def decode(cls, data: bytes) -> "ICCDateTime":
        if len(data) != 12:
            raise ValueError("Invalid ICCDateTime data")
        year = decode_uint16(data, 0)
        month = decode_uint16(data, 2)
        if month < 1 or month > 12:
            raise ValueError("Invalid month")
        day = decode_uint16(data, 4)
        if day < 1 or day > 31:
            raise ValueError("Invalid day")
        hours = decode_uint16(data, 6)
        if hours > 23:
            raise ValueError("Invalid hours")
        minutes = decode_uint16(data, 8)
        if minutes > 59:
            raise ValueError("Invalid minutes")
        seconds = decode_uint16(data, 10)
        if seconds > 59:
            raise ValueError("Invalid seconds")
        return cls(year, month, day, hours, minutes, seconds)

    def encode(self, data: bytearray) -> None:
        data.extend(
            self.year.to_bytes(2, "big")
            + self.month.to_bytes(2, "big")
            + self.day.to_bytes(2, "big")
            + self.hours.to_bytes(2, "big")
            + self.minutes.to_bytes(2, "big")
            + self.seconds.to_bytes(2, "big")
        )

    def __repr__(self) -> str:
        return f"ICCDateTime({self.year}, {self.month}, {self.day}, {self.hours}, {self.minutes}, {self.seconds})"
