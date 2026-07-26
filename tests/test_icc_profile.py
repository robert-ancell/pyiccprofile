import pyicc


def test_icc_profile():
    profile = pyicc.ICCProfile(
        preferred_cmm_type=0,
        profile_class=pyicc.ICCProfileClass.INPUT,
        data_color_space=pyicc.ICCDataColorSpace.CIELAB,
        pcs=pyicc.ICCDataColorSpace.CIELAB,
        creation_time=pyicc.ICCDateTime(2026, 7, 26, 16, 18, 42),
        rendering_intent=0,
        tagged_elements=[],
    )
    encoded_profile = profile.encode()

    out_profile = pyicc.ICCProfile.decode(encoded_profile)
    assert out_profile.version == (4, 4, 0)
