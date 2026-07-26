import pyicc


def test_icc_profile():
    profile = pyicc.ICCProfile.decode(b"")
