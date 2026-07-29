import pytest

from pyiccprofile.codec import decode_signature_type, encode_signature_type
from pyiccprofile.perceptual_rendering_intent_gamut import (
    ICCPerceptualRenderingIntentGamut,
    ICCPerceptualRenderingIntentGamutType,
)


def test_signature_type_round_trip():
    data = bytearray()
    encode_signature_type(data, b"prmg")
    assert bytes(data) == b"sig " + b"\x00\x00\x00\x00" + b"prmg"
    assert decode_signature_type(bytes(data)) == b"prmg"


def test_signature_type_decode_invalid_type_signature_raises():
    data = b"XXXX" + b"\x00\x00\x00\x00" + b"prmg"
    with pytest.raises(ValueError):
        decode_signature_type(data)


def test_signature_type_decode_invalid_reserved_bytes_raises():
    data = b"sig " + b"\x01\x00\x00\x00" + b"prmg"
    with pytest.raises(ValueError):
        decode_signature_type(data)


def test_signature_type_decode_wrong_length_raises():
    with pytest.raises(ValueError):
        decode_signature_type(b"sig " + b"\x00\x00\x00\x00" + b"prm")  # 1 short
    with pytest.raises(ValueError):
        decode_signature_type(b"sig " + b"\x00\x00\x00\x00" + b"prmgX")  # 1 long


def test_perceptual_rendering_intent_gamut_round_trip():
    tag = ICCPerceptualRenderingIntentGamut(
        ICCPerceptualRenderingIntentGamutType.MEDIUM
    )
    data = bytearray()
    tag.encode(data)
    assert bytes(data) == b"sig \x00\x00\x00\x00prmg"

    decoded = ICCPerceptualRenderingIntentGamut.decode(bytes(data))
    assert decoded.gamut == ICCPerceptualRenderingIntentGamutType.MEDIUM

    re_encoded = bytearray()
    decoded.encode(re_encoded)
    assert bytes(re_encoded) == bytes(data)


def test_perceptual_rendering_intent_gamut_decode_invalid_signature_raises():
    data = b"XXXX" + b"\x00\x00\x00\x00" + b"prmg"
    with pytest.raises(ValueError):
        ICCPerceptualRenderingIntentGamut.decode(data)


def test_perceptual_rendering_intent_gamut_constructor_rejects_wrong_length():
    with pytest.raises(ValueError):
        ICCPerceptualRenderingIntentGamut(b"abc")
    with pytest.raises(ValueError):
        ICCPerceptualRenderingIntentGamut(b"abcde")


def test_perceptual_rendering_intent_gamut_repr_does_not_raise():
    tag = ICCPerceptualRenderingIntentGamut(
        ICCPerceptualRenderingIntentGamutType.MEDIUM
    )
    assert "ICCPerceptualRenderingIntentGamut(" in repr(tag)
