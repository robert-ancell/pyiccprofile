"""ICC profile reader and writer."""

from __future__ import annotations

from pyiccprofile.a2b0 import ICCA2B0
from pyiccprofile.a2b1 import ICCA2B1
from pyiccprofile.a2b2 import ICCA2B2
from pyiccprofile.b2a0 import ICCB2A0
from pyiccprofile.b2a1 import ICCB2A1
from pyiccprofile.b2a2 import ICCB2A2
from pyiccprofile.chromatic_adaptation import ICCChromaticAdaptation
from pyiccprofile.codec import (
    ICCDateTime,
    decode_signature,
    decode_uint32,
    decode_uint64,
    encode_uint32,
    encode_uint64,
)
from pyiccprofile.copyright import ICCCopyright
from pyiccprofile.element import ICCTaggedElement, ICCUnknownTaggedElement
from pyiccprofile.media_white_point import ICCMediaWhitePoint
from pyiccprofile.perceptual_rendering_intent_gamut import (
    ICCPerceptualRenderingIntentGamut,
)
from pyiccprofile.profile_description import ICCProfileDescription

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


class ICCDataColorSpace:
    NCIEXYZ = b"XYZ "
    CIELAB = b"LAB "


class ICCRenderingIntent:
    PERCEPTUAL = 0
    MEDIA_RELATIVE_COLORIMETRIC = 1
    SATURATION = 2
    ICC_ABSOLUTE_COLORMETRIC = 3


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
    def decode(cls, data: bytes) -> ICCProfile:
        if len(data) < 132:
            raise ValueError("ICC profile data is too short")

        profile_size = decode_uint32(data, 0)
        if profile_size != len(data):
            raise ValueError("ICC profile size does not match")
        preferred_cmm_type = decode_uint32(data, 4)
        version = (data[8], data[9] >> 4, data[9] & 0xF)
        if (data[10], data[11]) != (0, 0):
            raise ValueError("ICC profile reserved bytes are not zero")
        profile_class = decode_signature(data, 12)
        if profile_class not in ICCProfileClass.__dict__.values():
            raise ValueError("ICC profile class is not valid")
        data_color_space = decode_signature(data, 16)
        pcs = decode_signature(data, 20)
        creation_time = ICCDateTime.decode(data[24:36])
        signature = data[36:40]
        if signature != b"acsp":
            raise ValueError("ICC profile signature is not valid")
        primary_platform = data[40:44]
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
                ICCChromaticAdaptation.SIGNATURE: ICCChromaticAdaptation,
                ICCMediaWhitePoint.SIGNATURE: ICCMediaWhitePoint,
                ICCPerceptualRenderingIntentGamut.SIGNATURE: ICCPerceptualRenderingIntentGamut,
                ICCA2B0.SIGNATURE: ICCA2B0,
                ICCA2B1.SIGNATURE: ICCA2B1,
                ICCA2B2.SIGNATURE: ICCA2B2,
                ICCB2A0.SIGNATURE: ICCB2A0,
                ICCB2A1.SIGNATURE: ICCB2A1,
                ICCB2A2.SIGNATURE: ICCB2A2,
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
        encode_uint32(data, 132)  # FIXME: profile size
        encode_uint32(data, self.preferred_cmm_type)
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
        encode_uint32(data, self.flags)
        data.extend(self.device_manufacturer)
        data.extend(self.device_model)
        encode_uint64(data, self.device_attributes)
        encode_uint32(data, self.rendering_intent)
        # FIXME nCIEXYZ values
        for _ in range(12):
            data.append(0)
        data.extend(self.creator)
        data.extend(self.id)
        for _ in range(28):
            data.append(0)
        # FIXME: tags
        encode_uint32(data, 0)
        return bytes(data)

    def __repr__(self) -> str:
        args = []
        args.append(f"preferred_cmm_type={self.preferred_cmm_type}")
        if self.version != _DEFAULT_VERSION:
            args.append(f"version={self.version}")
        profile_class_str = {
            ICCProfileClass.INPUT: "INPUT",
            ICCProfileClass.DISPLAY: "DISPLAY",
            ICCProfileClass.OUTPUT: "OUTPUT",
            ICCProfileClass.DEVICE_LINK: "DEVICE_LINK",
            ICCProfileClass.COLOR_SPACE: "COLOR_SPACE",
            ICCProfileClass.ABSTRACT: "ABSTRACT",
            ICCProfileClass.NAMED_COLOR: "NAMED_COLOR",
        }.get(self.profile_class, None)
        if profile_class_str is None:
            profile_class_str = repr(self.profile_class)
        else:
            profile_class_str = f"ICCProfileClass.{profile_class_str}"
        args.append(f"profile_class={profile_class_str}")
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
        rendering_intent_str = {
            ICCRenderingIntent.PERCEPTUAL: "PERCEPTUAL",
            ICCRenderingIntent.MEDIA_RELATIVE_COLORIMETRIC: "MEDIA_RELATIVE_COLORIMETRIC",
            ICCRenderingIntent.SATURATION: "SATURATION",
            ICCRenderingIntent.ICC_ABSOLUTE_COLORMETRIC: "ICC_ABSOLUTE_COLORMETRIC",
        }.get(self.rendering_intent, None)
        if rendering_intent_str is None:
            rendering_intent_str = repr(self.rendering_intent)
        else:
            rendering_intent_str = f"ICCRenderingIntent.{rendering_intent_str}"
        args.append(f"rendering_intent={rendering_intent_str}")
        args.append(f"tagged_elements={self.tagged_elements}")
        return f"ICCProfile({', '.join(args)})"
