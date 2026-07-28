from pyiccprofile.element import ICCTaggedElement


class ICCPerceptualRenderingIntentGamut(ICCTaggedElement):
    SIGNATURE = b"rig0"

    def __init__(
        self,
    ):
        pass

    @classmethod
    def decode(cls, data: bytes) -> "ICCPerceptualRenderingIntentGamut":
        return cls()

    def __repr__(self) -> str:
        return "ICCPerceptualRenderingIntentGamut(...)"
