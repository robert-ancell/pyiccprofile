from pyiccprofile.codec import decode_signature, decode_uint32, encode_uint32


class ICCMultiLocalizedUnicodeTypeRecord:
    def __init__(self, language_code: str, country_code: str, string: str):
        if len(language_code) != 2:
            raise ValueError("Language code must be exactly 2 characters")
        if len(country_code) != 2:
            raise ValueError("Country code must be exactly 2 characters")
        self.language_code = language_code
        self.country_code = country_code
        self.string = string

    def __repr__(self) -> str:
        return f"ICCMultiLocalizedUnicodeTypeRecord({self.language_code!r}, {self.country_code!r}, {self.string!r})"


class ICCMultiLocalizedUnicodeType:
    SIGNATURE = b"mluc"

    def __init__(self, records: list[ICCMultiLocalizedUnicodeTypeRecord]):
        self.records = records

    @classmethod
    def decode(cls, data: bytes) -> "ICCMultiLocalizedUnicodeType":
        if len(data) < 16:
            raise ValueError("Invalid length multi-localized unicode type")

        signature = decode_signature(data, 0)
        if signature != ICCMultiLocalizedUnicodeType.SIGNATURE:
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
            if string_offset < character_start or string_offset + string_length > len(
                data
            ):
                raise ValueError("Invalid string offset")
            string = data[string_offset : string_offset + string_length].decode(
                "utf-16-be"
            )
            records.append(
                ICCMultiLocalizedUnicodeTypeRecord(language_code, country_code, string)
            )
            record_offset += record_length

        return cls(records)

    def encode(self, data: bytearray) -> None:
        data.extend(ICCMultiLocalizedUnicodeType.SIGNATURE)
        data.extend(b"\x00\x00\x00\x00")
        encode_uint32(data, len(self.records))
        encode_uint32(data, 12)
        string_offset = 16 + len(self.records) * 12
        for record in self.records:
            data.extend(record.language_code.encode("ascii"))
            data.extend(record.country_code.encode("ascii"))
            string_length = len(record.string.encode("utf-16-be"))
            encode_uint32(data, string_length)
            encode_uint32(data, string_offset)
            string_offset += string_length
        for record in self.records:
            data.extend(record.string.encode("utf-16-be"))

    def __repr__(self) -> str:
        return f"ICCMultiLocalizedUnicodeType({self.records})"
