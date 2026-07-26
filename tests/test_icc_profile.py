import pyicc


def test_icc_profile():
    profile = pyicc.ICCProfile.decode(b"")
    assert profile.version == (4, 2, 0)
