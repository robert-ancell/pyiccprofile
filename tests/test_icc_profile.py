import pyiccprofile


def test_icc_profile():
    profile = pyiccprofile.ICCProfile(
        preferred_cmm_type=0,
        profile_class=pyiccprofile.ICCProfileClass.INPUT,
        data_color_space=pyiccprofile.ICCDataColorSpace.CIELAB,
        pcs=pyiccprofile.ICCDataColorSpace.CIELAB,
        creation_time=pyiccprofile.ICCDateTime(2026, 7, 26, 16, 18, 42),
        rendering_intent=0,
        tagged_elements=[],
    )
    encoded_profile = profile.encode()

    out_profile = pyiccprofile.ICCProfile.decode(encoded_profile)
    assert out_profile.version == (4, 4, 0)
