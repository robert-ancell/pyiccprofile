from pyiccprofile.codec import decode_signature_type, encode_signature_type
from pyiccprofile.element import ICCTaggedElement


class ICCTechnologyType:
    FILM_SCANNER = b"fscn"
    DIGITAL_CAMERA = b"dcam"
    REFLECTIVE_SCANNER = b"rscn"
    INK_JET_PRINTER = b"ijet"
    THERMAL_WAX_PRINTER = b"twax"
    ELECTROPHOTOGRAPHIC_PRINTER = b"epho"
    ELECTROSTATIC_PRINTER = b"esta"
    DYE_SUBLIMATION_PRINTER = b"dsub"
    PHOTOGRAPHIC_PAPER_PRINTER = b"rpho"
    FILM_WRITER = b"fprn"
    VIDEO_MONITOR = b"vidm"
    VIDEO_CAMERA = b"vidc"
    PROJECTION_TELEVISION = b"pjtv"
    CATHODE_RAY_TUBE_DISPLAY = b"CRT "
    PASSIVE_MATRIX_DISPLAY = b"PMD "
    ACTIVE_MATRIX_DISPLAY = b"AMD "
    LIQUID_CRYSTAL_DISPLAY = b"LCD "
    ORGANIC_LED_DISPLAY = b"OLED"
    PHOTO_CD = b"KPCD"
    PHOTOGRAPHIC_IMAGE_SETTER = b"imgs"
    GRAVURE = b"grav"
    OFFSET_LITHOGRAPHY = b"offs"
    SILKSCREEN = b"silk"
    FLEXOGRAPHY = b"flex"
    MOTION_PICTURE_FILM_SCANNER = b"mpfs"
    MOTION_PICTURE_FILM_RECORDER = b"mpfr"
    DIGITAL_MOTION_PICTURE_CAMERA = b"dmpc"
    DIGITAL_CINEMA_PROJECTOR = b"dcpj"


class ICCTechnology(ICCTaggedElement):
    SIGNATURE = b"tech"

    def __init__(self, technology: bytes):
        self.technology = technology

    @classmethod
    def decode(cls, data: bytes) -> "ICCTechnology":
        technology = decode_signature_type(data)
        return cls(technology)

    def encode(self, data: bytearray) -> None:
        encode_signature_type(data, self.technology)

    def __eq__(self, other):
        return isinstance(other, ICCTechnology) and other.technology == self.technology

    def __repr__(self) -> str:
        return f"ICCTechnology({self.technology!r})"
