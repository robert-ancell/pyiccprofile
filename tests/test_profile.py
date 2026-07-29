from pyiccprofile.chromatic_adaptation import ICCChromaticAdaptation
from pyiccprofile.codec import ICCDateTime
from pyiccprofile.copyright import ICCCopyright
from pyiccprofile.element import ICCTaggedElement, ICCUnknownTaggedElement
from pyiccprofile.profile import ICCColorSpace, ICCProfile, ICCProfileClass
from pyiccprofile.profile_description import ICCProfileDescription


def _base_profile(tagged_elements: list[ICCTaggedElement]):
    return ICCProfile(
        profile_class=ICCProfileClass.DISPLAY,
        data_color_space=ICCColorSpace.RGB,
        pcs=ICCColorSpace.XYZ,
        creation_time=ICCDateTime(2026, 7, 26, 16, 18, 42),
        rendering_intent=0,
        tagged_elements=tagged_elements,
    )


def _description(text: str):
    return ICCProfileDescription([("en", "US", text)])


def _copyright(copyright: str):
    return ICCCopyright([("en", "US", copyright)])


def test_profile_no_tags_round_trip():
    profile = _base_profile([])
    encoded = profile.encode()
    decoded = ICCProfile.decode(encoded)
    assert decoded.tagged_elements == []
    assert len(encoded) == 132


def test_profile_single_tag_round_trip():
    profile = _base_profile([_description("Hello ICC")])
    encoded = profile.encode()
    decoded = ICCProfile.decode(encoded)
    assert len(decoded.tagged_elements) == 1
    tag = decoded.tagged_elements[0]
    assert isinstance(tag, ICCProfileDescription)
    assert tag.description.records[0].string == "Hello ICC"


def test_profile_multiple_tags_round_trip():
    tags = [
        _description("A display profile"),
        _copyright("Copyright 2026"),
        ICCChromaticAdaptation([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]),
    ]
    profile = _base_profile(tags)
    encoded = profile.encode()
    decoded = ICCProfile.decode(encoded)

    assert decoded.tagged_elements == tags


def test_profile_unknown_tag_round_trips_verbatim():
    unknown = ICCUnknownTaggedElement(b"zzzz", b"\x01\x02\x03\x04\x05")
    profile = _base_profile([unknown])
    encoded = profile.encode()
    decoded = ICCProfile.decode(encoded)

    assert len(decoded.tagged_elements) == 1
    tag = decoded.tagged_elements[0]
    assert isinstance(tag, ICCUnknownTaggedElement)
    assert tag.signature == b"zzzz"
    assert tag.data == b"\x01\x02\x03\x04\x05"


def test_profile_round_trip_twice_is_stable():
    # encode -> decode -> encode should be byte-identical (idempotent).
    profile = _base_profile([_description("stability check")])
    once = profile.encode()
    decoded = ICCProfile.decode(once)
    twice = decoded.encode()
    assert once == twice
