import pyiccprofile
from pyiccprofile.profile import ICCRenderingIntent


def test_icc_profile():
    profile = pyiccprofile.ICCProfile(
        profile_class=pyiccprofile.ICCProfileClass.INPUT,
        data_color_space=pyiccprofile.ICCColorSpace.LAB,
        pcs=pyiccprofile.ICCColorSpace.LAB,
        creation_time=pyiccprofile.ICCDateTime(2026, 7, 26, 16, 18, 42),
        rendering_intent=ICCRenderingIntent.PERCEPTUAL,
        tagged_elements=[],
    )
    encoded_profile = profile.encode()

    out_profile = pyiccprofile.ICCProfile.decode(encoded_profile)
    assert out_profile.version == (4, 4, 0)
