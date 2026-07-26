"""ICC profile reader and writer."""

_DEFAULT_VERSION = (4, 4, 0)

_NULL_SIGNATURE = b"\x00\x00\x00\x00"

_NULL_ID = (
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)


def _get_uint16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], byteorder="big")


def _get_uint32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], byteorder="big")


def _get_uint64(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 8], byteorder="big")

def _get_s15fixed16_number(data: bytes, offset: int) -> float:
    v = int.from_bytes(data[offset : offset + 4], byteorder="big", signed=True)
    return v / 65536.0

def _get_u15fixed16_number(data: bytes, offset: int) -> float:
    return _get_uint32(data, offset) / 65536.0

def _get_xyz_number(data: bytes, offset: int) -> tuple[float, float, float]:
    return (
        _get_s15fixed16_number(data, offset),
        _get_s15fixed16_number(data, offset + 4),
        _get_s15fixed16_number(data, offset + 8),
    )

def _get_signature(data: bytes, offset: int) -> bytes:
    return data[offset : offset + 4]

def _decode_s15fixed16_array(data: bytes) -> list[float]:
    if len(data) < 8 or len(data) % 4 != 0:
        raise ValueError("Invalid length")
    signature = _get_signature(data, 0)
    if signature != b"sf32":
        raise ValueError("Invalid signature")
    reserved = data[4:8]
    if reserved != b"\x00\x00\x00\x00":
        raise ValueError("Reserved field must be 0")
    offset = 8
    count = (len(data) - offset) // 4
    values = []
    for _ in range(count):
        values.append(_get_s15fixed16_number(data, offset))
        offset += 4
    return values

def _decode_xyz(data: bytes) -> list[tuple[float, float, float]]:
    if len(data) < 8 or len(data) % 4 != 0:
        raise ValueError("Invalid length")
    signature = _get_signature(data, 0)
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
        values.append(_get_xyz_number(data, offset))
        offset += 12
    return values



def _append_uint32(data: bytearray, value: int) -> None:
    data.extend(value.to_bytes(4, byteorder="big"))


def _append_uint64(data: bytearray, value: int) -> None:
    data.extend(value.to_bytes(8, byteorder="big"))

def _append_s15fixed16_number(data: bytearray, value: float) -> None:
    int_value = int(value * 65535)
    data.extend(int_value.to_bytes(4, byteorder="big"))

def _append_xyz_number(data: bytearray, value: tuple[float, float, float]) -> None:
    _append_s15fixed16_number(data, value[0])
    _append_s15fixed16_number(data, value[1])
    _append_s15fixed16_number(data, value[2])

def _encode_s15fixed16_array(data: bytearray, values: list[float]) -> None:
    data.extend(b"sf32")
    data.extend(b"\x00\x00\x00\x00")
    for value in values:
        _append_s15fixed16_number(data, value)

def _encode_xyz(data: bytearray, values: list[tuple[float, float, float]]) -> None:
    data.extend(b"XYZ ")
    data.extend(b"\x00\x00\x00\x00")
    for value in values:
        _append_xyz_number(data, value)


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
    def __init__(self, records: list[ICCMultiLocalizedUnicodeTypeRecord]):
        self.records = records

    @classmethod
    def decode(cls, data: bytes) -> "ICCMultiLocalizedUnicodeType":
        if len(data) < 16:
            raise ValueError("Invalid length multi-localized unicode type")

        signature = _get_signature(data, 0)
        if signature != b"mluc":
            raise ValueError("Invalid signature for multi-localized unicode type")
        reserved = _get_uint32(data, 4)
        if reserved != 0:
            raise ValueError("Reserved field must be 0")
        n_records = _get_uint32(data, 8)
        record_length = _get_uint32(data, 12)
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
            string_length = _get_uint32(data, record_offset + 4)
            string_offset = _get_uint32(data, record_offset + 8)
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
        data.extend(b"mluc")
        data.extend(b"\x00\x00\x00\x00")
        _append_uint32(data, len(self.records))
        _append_uint32(data, 12)
        string_offset = 16 + len(self.records) * 12
        for record in self.records:
            data.extend(record.language_code.encode("ascii"))
            data.extend(record.country_code.encode("ascii"))
            string_length = len(record.string.encode("utf-16-be"))
            _append_uint32(data, string_length)
            _append_uint32(data, string_offset)
            string_offset += string_length
        for record in self.records:
            data.extend(record.string.encode("utf-16-be"))

    def __repr__(self) -> str:
        return f"ICCMultiLocalizedUnicodeType({self.records})"

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
            raise ValueError(f"Invalid signature: {signature}")
        if data[4:8] != b"\x00\x00\x00\x00":
            raise ValueError("Invalid reserved bytes")
        n_input_channels = data[8]
        n_output_channels = data[9]
        n_clut_grid_points = data[10]
        if data[11] != 0:
            raise ValueError("Reserved byte must be 0")
        e1 = _get_s15fixed16_number(data, 12)
        e2 = _get_s15fixed16_number(data, 16)
        e3 = _get_s15fixed16_number(data, 20)
        e4 = _get_s15fixed16_number(data, 24)
        e5 = _get_s15fixed16_number(data, 28)
        e6 = _get_s15fixed16_number(data, 32)
        e7 = _get_s15fixed16_number(data, 36)
        e8 = _get_s15fixed16_number(data, 40)
        e9 = _get_s15fixed16_number(data, 44)
        # FIXME

        return cls(e1, e2, e3, e4, e5, e6, e7, e8, e9)

    def encode(self, data: bytearray) -> None:
        data.extend(b"mft1")
        data.extend(b"\x00\x00\x00\x00")
        data.append(0)# n_input_channels
        data.append(0)# n_output_channels
        data.append(0)# n_clut_grid_points
        data.append(0)
        _append_s15fixed16_number(data, self.e1)
        _append_s15fixed16_number(data, self.e2)
        _append_s15fixed16_number(data, self.e3)
        _append_s15fixed16_number(data, self.e4)
        _append_s15fixed16_number(data, self.e5)
        _append_s15fixed16_number(data, self.e6)
        _append_s15fixed16_number(data, self.e7)
        _append_s15fixed16_number(data, self.e8)
        _append_s15fixed16_number(data, self.e9)
        # FIXME

class ICCLut16:
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
    def decode(cls, data: bytes) -> "ICCLut16":
        if len(data) < 48:
            raise ValueError("Insufficient data")
        signature = data[:4]
        if signature != b"mft2":
            raise ValueError(f"Invalid signature: {signature}")
        if data[4:8] != b"\x00\x00\x00\x00":
            raise ValueError("Invalid reserved bytes")
        n_input_channels = data[8]
        n_output_channels = data[9]
        n_clut_grid_points = data[10]
        if data[11] != 0:
            raise ValueError("Reserved byte must be 0")
        e1 = _get_s15fixed16_number(data, 12)
        e2 = _get_s15fixed16_number(data, 16)
        e3 = _get_s15fixed16_number(data, 20)
        e4 = _get_s15fixed16_number(data, 24)
        e5 = _get_s15fixed16_number(data, 28)
        e6 = _get_s15fixed16_number(data, 32)
        e7 = _get_s15fixed16_number(data, 36)
        e8 = _get_s15fixed16_number(data, 40)
        e9 = _get_s15fixed16_number(data, 44)
        # FIXME

        return cls(e1, e2, e3, e4, e5, e6, e7, e8, e9)

    def encode(self, data: bytearray) -> None:
        data.extend(b"mft2")
        data.extend(b"\x00\x00\x00\x00")
        data.append(0)# n_input_channels
        data.append(0)# n_output_channels
        data.append(0)# n_clut_grid_points
        data.append(0)
        _append_s15fixed16_number(data, self.e1)
        _append_s15fixed16_number(data, self.e2)
        _append_s15fixed16_number(data, self.e3)
        _append_s15fixed16_number(data, self.e4)
        _append_s15fixed16_number(data, self.e5)
        _append_s15fixed16_number(data, self.e6)
        _append_s15fixed16_number(data, self.e7)
        _append_s15fixed16_number(data, self.e8)
        _append_s15fixed16_number(data, self.e9)
        # FIXME

class ICCLutAToB:
    def __init__(self):
        pass

    @classmethod
    def decode(cls, data: bytes) -> "IccLutAToB":
        signature = data[:4]
        if signature != b"mAB ":
            raise ValueError(f"Invalid signature: {signature}")
        if data[4:8] != b"\x00\x00\x00\x00":
            raise ValueError("Invalid reserved bytes")
        n_input_channels = data[8]
        n_output_channels = data[9]
        if data[10] != 0 or data[11] != 0:
            raise ValueError("Invalid reserved bytes")
        return cls()

    def encode(self, data: bytearray) -> None:
        data.extend(b"mAB ")
        data.extend(b"\x00\x00\x00\x00")
        # FIXME

    def __repr__(self) -> str:
        return f"ICCLutAToB()"

class ICCLutBToA:
    def __init__(self):
        pass

    @classmethod
    def decode(cls, data: bytes) -> "IccLutBToA":
        signature = data[:4]
        if signature != b"mBA ":
            raise ValueError(f"Invalid signature: {signature}")
        if data[4:8] != b"\x00\x00\x00\x00":
            raise ValueError("Invalid reserved bytes")
        n_input_channels = data[8]
        n_output_channels = data[9]
        if data[10] != 0 or data[11] != 0:
            raise ValueError("Invalid reserved bytes")
        return cls()

    def encode(self, data: bytearray) -> None:
        data.extend(b"mBA ")
        data.extend(b"\x00\x00\x00\x00")
        # FIXME

    def __repr__(self) -> str:
        return f"ICCLutBToA()"

class ICCProfileClass:
    INPUT = b"scnr"
    DISPLAY = b"mntr"
    OUTPUT = b"prtr"
    DEVICE_LINK = b"link"
    COLOR_SPACE = b"spac"
    ABSTRACT = b"abst"
    NAMED_COLOR = b"nmcl"


class ICCDataColorSpace:
    NCIEXYZ = b"XYZ "
    CIELAB = b"LAB "


class ICCRenderingIntent:
    PERCEPTUAL = 0
    MEDIA_RELATIVE_COLORIMETRIC = 1
    SATURATION = 2
    ICC_ABSOLUTE_COLORMETRIC = 3


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
        year = _get_uint16(data, 0)
        month = _get_uint16(data, 2)
        if month < 1 or month > 12:
            raise ValueError("Invalid month")
        day = _get_uint16(data, 4)
        if day < 1 or day > 31:
            raise ValueError("Invalid day")
        hours = _get_uint16(data, 6)
        if hours > 23:
            raise ValueError("Invalid hours")
        minutes = _get_uint16(data, 8)
        if minutes > 59:
            raise ValueError("Invalid minutes")
        seconds = _get_uint16(data, 10)
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


class ICCTaggedElement:
    @classmethod
    def decode(cls, data: bytes) -> "ICCTaggedElement":
        raise NotImplementedError()


class ICCProfileDescription(ICCTaggedElement):
    def __init__(self, description: ICCMultiLocalizedUnicodeType):
        self.description = description

    @classmethod
    def decode(cls, data: bytes) -> "ICCProfileDescription":
        description = ICCMultiLocalizedUnicodeType.decode(data)
        return cls(description)

    def encode(self, data: bytearray) -> None:
        self.description.encode(data)

    def __repr__(self) -> str:
        return f"ICCProfileDescription({self.description})"


class ICCCopyright(ICCTaggedElement):
    def __init__(self, copyright: ICCMultiLocalizedUnicodeType):
        self.copyright = copyright

    @classmethod
    def decode(cls, data: bytes) -> "ICCCopyright":
        copyright = ICCMultiLocalizedUnicodeType.decode(data)
        return cls(copyright)

    def encode(self, data: bytearray) -> None:
        self.copyright.encode(data)

    def __repr__(self) -> str:
        return f"ICCCopyright({self.copyright})"


class ICCChromaticAdaptation(ICCTaggedElement):
    def __init__(self, matrix: list[float]):
        self.matrix = matrix

    @classmethod
    def decode(cls, data: bytes) -> "ICCChromaticAdaptation":
        matrix = _decode_s15fixed16_array(data)
        if len(matrix) != 9:
            raise ValueError("Invalid matrix")
        return cls(matrix)

    def encode(self, data: bytearray) -> None:
        _encode_s15fixed16_array(data, self.matrix)

    def __repr__(self) -> str:
        return f"ICCChromaticAdaptation({self.matrix})"


class ICCMediaWhitePoint(ICCTaggedElement):
    def __init__(self, colors: list[tuple[float, float, float]]):
        self.colors = colors

    @classmethod
    def decode(cls, data: bytes) -> "ICCMediaWhitePoint":
        colors = _decode_xyz(data)
        # FIXME: Can this be more than one color?
        return cls(colors)

    def encode(self, data: bytearray) -> None:
        _encode_xyz(data, self.colors)

    def __repr__(self) -> str:
        return f"ICCMediaWhitePoint({self.colors})"

class ICCPerceptualRenderingIntentGamut(ICCTaggedElement):
    def __init__(self, ):
        pass

    @classmethod
    def decode(cls, data: bytes) -> "ICCPerceptualRenderingIntentGamut":
        return cls()

    def __repr__(self) -> str:
        return f"ICCPerceptualRenderingIntentGamut(...)"

class ICCA2B0(ICCTaggedElement):
    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutAToB):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> "ICCA2B0":
        transform = ICCLutAToB.decode(data)
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCA2B0({self.transform})"

class ICCA2B1(ICCTaggedElement):
    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutAToB):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> "ICCA2B1":
        transform = ICCLutAToB.decode(data)
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCA2B1({self.transform})"

class ICCA2B2(ICCTaggedElement):
    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutAToB):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> "ICCA2B2":
        transform = ICCLutAToB.decode(data)
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCA2B2({self.transform})"

class ICCB2A0(ICCTaggedElement):
    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutBToA):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> "ICCB2A0":
        transform = ICCLutBToA.decode(data)
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCB2A0({self.transform})"

class ICCB2A1(ICCTaggedElement):
    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutBToA):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> "ICCB2A1":
        transform = ICCLutBToA.decode(data)
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCB2A1({self.transform})"

class ICCB2A2(ICCTaggedElement):
    def __init__(self, transform: ICCLut8 | ICCLut16 | ICCLutBToA):
        self.transform = transform

    @classmethod
    def decode(cls, data: bytes) -> "ICCB2A2":
        transform = ICCLutBToA.decode(data)
        return cls(transform)

    def __repr__(self) -> str:
        return f"ICCB2A2({self.transform})"

class ICCUnknownTaggedElement(ICCTaggedElement):
    def __init__(self, signature: bytes, data: bytes):
        self.signature = signature
        self.data = data

    def __repr__(self) -> str:
        return f"ICCUnknownTaggedData({self.signature!r}, ...)"


class ICCProfile:
    def __init__(
        self,
        preferred_cmm_type: int,
        profile_class: bytes,
        data_color_space: bytes,
        pcs: bytes,
        creation_time: ICCDateTime,
        rendering_intent: int,
        tagged_elements: list[ICCTaggedElement],
        version: tuple[int, int, int] = _DEFAULT_VERSION,
        primary_platform=_NULL_SIGNATURE,
        flags: int = 0,
        device_manufacturer: bytes = _NULL_SIGNATURE,
        device_model: bytes = _NULL_SIGNATURE,
        device_attributes: int = 0,
        creator: bytes = _NULL_SIGNATURE,
        id: bytes = _NULL_ID,
    ):
        if len(profile_class) != 4:
            raise ValueError("profile_class must be 4 bytes")
        if len(data_color_space) != 4:
            raise ValueError("data_color_space must be 4 bytes")
        if len(pcs) != 4:
            raise ValueError("pcs must be 4 bytes")
        if len(device_manufacturer) != 4:
            raise ValueError("device_manufacturer must be 4 bytes")
        if len(device_model) != 4:
            raise ValueError("device_model must be 4 bytes")
        if len(creator) != 4:
            raise ValueError("creator must be 4 bytes")
        if len(id) != 16:
            raise ValueError("id must be 16 bytes")
        self.preferred_cmm_type = preferred_cmm_type
        self.version = version
        self.profile_class = profile_class
        self.data_color_space = data_color_space
        self.pcs = pcs
        self.creation_time = creation_time
        self.primary_platform = primary_platform
        self.flags = flags
        self.device_manufacturer = device_manufacturer
        self.device_model = device_model
        self.device_attributes = device_attributes
        self.rendering_intent = rendering_intent
        self.creator = creator
        self.id = id
        self.tagged_elements = tagged_elements

    @classmethod
    def decode(cls, data: bytes) -> "ICCProfile":
        if len(data) < 132:
            raise ValueError("ICC profile data is too short")

        profile_size = _get_uint32(data, 0)
        if profile_size != len(data):
            raise ValueError("ICC profile size does not match")
        preferred_cmm_type = _get_uint32(data, 4)
        version = (data[8], data[9] >> 4, data[9] & 0xF)
        if (data[10], data[11]) != (0, 0):
            raise ValueError("ICC profile reserved bytes are not zero")
        profile_class = _get_signature(data, 12)
        if profile_class not in ICCProfileClass.__dict__.values():
            raise ValueError("ICC profile class is not valid")
        data_color_space = _get_signature(data, 16)
        pcs = _get_signature(data, 20)
        creation_time = ICCDateTime.decode(data[24:36])
        signature = data[36:40]
        if signature != b"acsp":
            raise ValueError("ICC profile signature is not valid")
        primary_platform = data[40:44]
        flags = _get_uint32(data, 44)
        device_manufacturer = _get_signature(data, 48)
        device_model = _get_signature(data, 52)
        device_attributes = _get_uint64(data, 56)
        rendering_intent = _get_uint32(data, 64)
        if rendering_intent > ICCRenderingIntent.ICC_ABSOLUTE_COLORMETRIC:
            raise ValueError("ICC profile rendering intent is not valid")
        # FIXME nCIEXYZ values data[68:80]
        creator = _get_signature(data, 80)
        id = data[84:100]
        for d in data[100:128]:
            if d != 0:
                raise ValueError("ICC profile reserved bytes are not zero")

        tag_count = _get_uint32(data, 128)
        tag_table_length = 4 + 12 * tag_count
        data_start = 128 + tag_table_length
        if len(data) < data_start:
            raise ValueError("ICC profile data is too short")
        tag_start = 132
        tagged_elements = []
        for _ in range(tag_count):
            tag_signature = _get_signature(data, tag_start)
            offset = _get_uint32(data, tag_start + 4)
            if offset % 4 != 0:
                raise ValueError("ICC profile tag offset is not aligned")
            length = _get_uint32(data, tag_start + 8)
            if offset < data_start or offset + length > len(data):
                raise ValueError("ICC profile tag data is out of bounds")
            tag_class: type[ICCTaggedElement]|None = {
                b"desc": ICCProfileDescription,
                b"cprt": ICCCopyright,
                b"chad": ICCChromaticAdaptation,
                b"wtpt": ICCMediaWhitePoint,
                b"rig0": ICCPerceptualRenderingIntentGamut,
                b"A2B0": ICCA2B0,
                b"A2B1": ICCA2B1,
                b"A2B2": ICCA2B2,
                b"B2A0": ICCB2A0,
                b"B2A1": ICCB2A1,
                b"B2A2": ICCB2A2,
            }.get(tag_signature, None)
            if tag_class is not None:
                element = tag_class.decode(data[offset : offset + length])
            else:
                element = ICCUnknownTaggedElement(
                    tag_signature, data[offset : offset + length]
                )
            tagged_elements.append(element)
            tag_start += 12

        return cls(
            preferred_cmm_type=preferred_cmm_type,
            version=version,
            profile_class=profile_class,
            data_color_space=data_color_space,
            pcs=pcs,
            creation_time=creation_time,
            primary_platform=primary_platform,
            flags=flags,
            device_manufacturer=device_manufacturer,
            device_model=device_model,
            device_attributes=device_attributes,
            rendering_intent=rendering_intent,
            creator=creator,
            id=id,
            tagged_elements=tagged_elements,
        )

    def encode(self) -> bytes:
        data = bytearray()
        _append_uint32(data, 132) # FIXME: profile size
        _append_uint32(data, self.preferred_cmm_type)
        data.append(self.version[0])
        data.append(self.version[1] << 4 | self.version[2])
        data.append(0)
        data.append(0)
        data.extend(self.profile_class)
        data.extend(self.data_color_space)
        data.extend(self.pcs)
        self.creation_time.encode(data)
        data.extend(b"acsp")
        data.extend(self.primary_platform)
        _append_uint32(data, self.flags)
        data.extend(self.device_manufacturer)
        data.extend(self.device_model)
        _append_uint64(data, self.device_attributes)
        _append_uint32(data, self.rendering_intent)
        # FIXME nCIEXYZ values
        for _ in range(12):
            data.append(0)
        data.extend(self.creator)
        data.extend(self.id)
        for _ in range(28):
            data.append(0)
        # FIXME: tags
        _append_uint32(data, 0)
        return bytes(data)

    def __repr__(self) -> str:
        rendering_intent_str = {
            ICCRenderingIntent.PERCEPTUAL: "PERCEPTUAL",
            ICCRenderingIntent.MEDIA_RELATIVE_COLORIMETRIC: "MEDIA_RELATIVE_COLORIMETRIC",
            ICCRenderingIntent.SATURATION: "SATURATION",
            ICCRenderingIntent.ICC_ABSOLUTE_COLORMETRIC: "ICC_ABSOLUTE_COLORMETRIC",
        }
        args = []
        args.append(f"preferred_cmm_type={self.preferred_cmm_type}")
        if self.version != _DEFAULT_VERSION:
            args.append(f"version={self.version}")
        args.append(f"profile_class={self.profile_class!r}")
        args.append(f"data_color_space={self.data_color_space!r}")
        args.append(f"pcs={self.pcs!r}")
        args.append(f"creation_time={self.creation_time}")
        if self.flags != 0:
            args.append(f"flags={self.flags}")
        if self.primary_platform != _NULL_SIGNATURE:
            args.append(f"primary_platform={self.primary_platform}")
        if self.device_manufacturer != _NULL_SIGNATURE:
            args.append(f"device_manufacturer={self.device_manufacturer!r}")
        if self.device_model != _NULL_SIGNATURE:
            args.append(f"device_model={self.device_model!r}")
        if self.device_attributes != 0:
            args.append(f"device_attributes={self.device_attributes!r}")
        if self.creator != _NULL_SIGNATURE:
            args.append(f"creator={self.creator!r}")
        if self.id != _NULL_ID:
            args.append(f"id={self.id!r}")
        args.append(
            f"rendering_intent=ICCRenderingIntent.{rendering_intent_str[self.rendering_intent]}"
        )
        args.append(f"tagged_elements={self.tagged_elements}")
        return f"ICCProfile({', '.join(args)})"
