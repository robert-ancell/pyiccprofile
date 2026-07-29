"""ICC profile reader and writer."""

from __future__ import annotations

from pyiccprofile.atob0 import ICCAToB0
from pyiccprofile.atob1 import ICCAToB1
from pyiccprofile.atob2 import ICCAToB2
from pyiccprofile.blue_matrix_column import ICCBlueMatrixColumn
from pyiccprofile.btoa0 import ICCBToA0
from pyiccprofile.btoa1 import ICCBToA1
from pyiccprofile.btoa2 import ICCBToA2
from pyiccprofile.chromatic_adaptation import ICCChromaticAdaptation
from pyiccprofile.codec import (
    ICCDateTime,
    decode_signature,
    decode_uint32,
    decode_uint64,
    encode_signature,
    encode_uint32,
    encode_uint64,
)
from pyiccprofile.copyright import ICCCopyright
from pyiccprofile.element import ICCTaggedElement, ICCUnknownTaggedElement
from pyiccprofile.green_matrix_column import ICCGreenMatrixColumn
from pyiccprofile.media_white_point import ICCMediaWhitePoint
from pyiccprofile.perceptual_rendering_intent_gamut import (
    ICCPerceptualRenderingIntentGamut,
)
from pyiccprofile.profile_description import ICCProfileDescription
from pyiccprofile.red_matrix_column import ICCRedMatrixColumn
from pyiccprofile.technology import ICCTechnology

_DEFAULT_VERSION = (4, 4, 0)

_NULL_SIGNATURE = b"\x00\x00\x00\x00"

_NULL_ID = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


class ICCProfileClass:
    INPUT = b"scnr"
    DISPLAY = b"mntr"
    OUTPUT = b"prtr"
    DEVICE_LINK = b"link"
    COLOR_SPACE = b"spac"
    ABSTRACT = b"abst"
    NAMED_COLOR = b"nmcl"


class ICCColorSpace:
    XYZ = b"XYZ "
    LAB = b"Lab "
    CIE_LUV = b"Luv "
    YCBCR = b"YCbr"
    CIE_YXY = b"Yxy "
    RGB = b"RGB "
    GRAY = b"GRAY"
    HSV = b"HSV "
    HSL = b"HSL "
    CMYK = b"CMYK"
    CMY = b"CMY "
    TWO_COLOR = b"2CLR"
    THREE_COLOR = b"3CLR"
    FOUR_COLOR = b"4CLR"
    FIVE_COLOR = b"5CLR"
    SIX_COLOR = b"6CLR"
    SEVEN_COLOR = b"7CLR"
    EIGHT_COLOR = b"8CLR"
    NINE_COLOR = b"9CLR"
    TEN_COLOR = b"10CLR"
    ELEVEN_COLOR = b"11CLR"
    TWELVE_COLOR = b"12CLR"
    THIRTEEN_COLOR = b"13CLR"
    FOURTEEN_COLOR = b"14CLR"
    FIFTEEN_COLOR = b"15CLR"


class ICCRenderingIntent:
    PERCEPTUAL = 0
    MEDIA_RELATIVE_COLORIMETRIC = 1
    SATURATION = 2
    ICC_ABSOLUTE_COLORMETRIC = 3


class ICCPrimaryPlatform:
    APPLE_COMPUTER_INC = b"APPL"
    MICROSOFT_CORPORATION = b"MSFT"
    SILICON_GRAPHICS_INC = b"SGI "
    SUN_MICROSYSTEMS = b"SUNW"


def _get_signature_name(signature_class: type, signature: bytes) -> str:
    for name, value in signature_class.__dict__.items():
        if value == signature:
            return signature_class.__name__ + "." + name
    return repr(signature)


def _get_enum_name(enum_class: type, value: int) -> str:
    for name, enum_value in enum_class.__dict__.items():
        if enum_value == value:
            return enum_class.__name__ + "." + name
    return repr(value)


class ICCProfile:
    def __init__(
        self,
        profile_class: bytes,
        data_color_space: bytes,
        pcs: bytes,
        creation_time: ICCDateTime,
        rendering_intent: int,
        tagged_elements: list[ICCTaggedElement],
        preferred_cmm_type: bytes = _NULL_SIGNATURE,
        version: tuple[int, int, int] = _DEFAULT_VERSION,
        primary_platform=_NULL_SIGNATURE,
        flags: int = 0,
        device_manufacturer: bytes = _NULL_SIGNATURE,
        device_model: bytes = _NULL_SIGNATURE,
        device_attributes: int = 0,
        creator: bytes = _NULL_SIGNATURE,
        id: bytes = _NULL_ID,
    ):
        if len(preferred_cmm_type) != 4:
            raise ValueError("preferred_cmm_type must be 4 bytes")
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
    def decode(cls, data: bytes) -> ICCProfile:
        if len(data) < 132:
            raise ValueError("ICC profile data is too short")

        profile_size = decode_uint32(data, 0)
        if profile_size != len(data):
            raise ValueError("ICC profile size does not match")
        preferred_cmm_type = decode_signature(data, 4)
        version = (data[8], data[9] >> 4, data[9] & 0xF)
        if (data[10], data[11]) != (0, 0):
            raise ValueError("ICC profile reserved bytes are not zero")
        profile_class = decode_signature(data, 12)
        if profile_class not in ICCProfileClass.__dict__.values():
            raise ValueError("ICC profile class is not valid")
        data_color_space = decode_signature(data, 16)
        pcs = decode_signature(data, 20)
        creation_time = ICCDateTime.decode(data[24:36])
        if decode_signature(data, 36) != b"acsp":
            raise ValueError("ICC profile signature is not valid")
        primary_platform = decode_signature(data, 40)
        flags = decode_uint32(data, 44)
        device_manufacturer = decode_signature(data, 48)
        device_model = decode_signature(data, 52)
        device_attributes = decode_uint64(data, 56)
        rendering_intent = decode_uint32(data, 64)
        if rendering_intent > ICCRenderingIntent.ICC_ABSOLUTE_COLORMETRIC:
            raise ValueError("ICC profile rendering intent is not valid")
        # FIXME nCIEXYZ values data[68:80]
        creator = decode_signature(data, 80)
        id = data[84:100]
        for d in data[100:128]:
            if d != 0:
                raise ValueError("ICC profile reserved bytes are not zero")

        tag_count = decode_uint32(data, 128)
        tag_table_length = 4 + 12 * tag_count
        data_start = 128 + tag_table_length
        if len(data) < data_start:
            raise ValueError("ICC profile data is too short")
        tag_start = 132
        tagged_elements = []
        for _ in range(tag_count):
            tag_signature = decode_signature(data, tag_start)
            offset = decode_uint32(data, tag_start + 4)
            if offset % 4 != 0:
                raise ValueError("ICC profile tag offset is not aligned")
            length = decode_uint32(data, tag_start + 8)
            if offset < data_start or offset + length > len(data):
                raise ValueError("ICC profile tag data is out of bounds")
            tag_class: type[ICCTaggedElement] | None = {
                ICCProfileDescription.SIGNATURE: ICCProfileDescription,
                ICCCopyright.SIGNATURE: ICCCopyright,
                ICCTechnology.SIGNATURE: ICCTechnology,
                ICCChromaticAdaptation.SIGNATURE: ICCChromaticAdaptation,
                ICCMediaWhitePoint.SIGNATURE: ICCMediaWhitePoint,
                ICCRedMatrixColumn.SIGNATURE: ICCRedMatrixColumn,
                ICCGreenMatrixColumn.SIGNATURE: ICCGreenMatrixColumn,
                ICCBlueMatrixColumn.SIGNATURE: ICCBlueMatrixColumn,
                ICCPerceptualRenderingIntentGamut.SIGNATURE: ICCPerceptualRenderingIntentGamut,
                ICCAToB0.SIGNATURE: ICCAToB0,
                ICCAToB1.SIGNATURE: ICCAToB1,
                ICCAToB2.SIGNATURE: ICCAToB2,
                ICCBToA0.SIGNATURE: ICCBToA0,
                ICCBToA1.SIGNATURE: ICCBToA1,
                ICCBToA2.SIGNATURE: ICCBToA2,
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
        tag_table_length = 4 + 12 * len(self.tagged_elements)
        data_start = 128 + tag_table_length

        tag_table = bytearray()
        encode_uint32(tag_table, len(self.tagged_elements))
        tag_data = bytearray()
        offset = data_start
        for element in self.tagged_elements:
            if isinstance(element, ICCUnknownTaggedElement):
                tag_signature = element.signature
            else:
                tag_signature = type(element).SIGNATURE
            body = bytearray()
            element.encode(body)
            length = len(body)
            encode_signature(tag_table, tag_signature)
            encode_uint32(tag_table, offset)
            encode_uint32(tag_table, length)
            tag_data.extend(body)
            padding = (-length) % 4
            tag_data.extend(b"\x00" * padding)
            offset += length + padding

        total_size = data_start + len(tag_data)

        data = bytearray()
        encode_uint32(data, total_size)
        encode_signature(data, self.preferred_cmm_type)
        data.append(self.version[0])
        data.append(self.version[1] << 4 | self.version[2])
        data.append(0)
        data.append(0)
        encode_signature(data, self.profile_class)
        encode_signature(data, self.data_color_space)
        encode_signature(data, self.pcs)
        self.creation_time.encode(data)
        encode_signature(data, b"acsp")
        encode_signature(data, self.primary_platform)
        encode_uint32(data, self.flags)
        encode_signature(data, self.device_manufacturer)
        encode_signature(data, self.device_model)
        encode_uint64(data, self.device_attributes)
        encode_uint32(data, self.rendering_intent)
        # FIXME nCIEXYZ values
        for _ in range(12):
            data.append(0)
        encode_signature(data, self.creator)
        data.extend(self.id)
        for _ in range(28):
            data.append(0)
        data.extend(tag_table)
        data.extend(tag_data)
        return bytes(data)

    def __repr__(self) -> str:
        args = []
        if self.preferred_cmm_type != _NULL_SIGNATURE:
            args.append(f"preferred_cmm_type={self.preferred_cmm_type!r}")
        if self.version != _DEFAULT_VERSION:
            args.append(f"version={self.version}")
        args.append(
            f"profile_class={_get_signature_name(ICCProfileClass, self.profile_class)}"
        )
        args.append(
            f"data_color_space={_get_signature_name(ICCColorSpace, self.data_color_space)}"
        )
        args.append(f"pcs={_get_signature_name(ICCColorSpace, self.pcs)}")
        args.append(f"creation_time={self.creation_time}")
        if self.flags != 0:
            args.append(f"flags={self.flags}")
        if self.primary_platform != _NULL_SIGNATURE:
            args.append(
                f"primary_platform={_get_signature_name(ICCPrimaryPlatform, self.primary_platform)}"
            )
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
            f"rendering_intent={_get_enum_name(ICCRenderingIntent, self.rendering_intent)}"
        )
        args.append(f"tagged_elements={self.tagged_elements}")
        return f"ICCProfile({', '.join(args)})"
