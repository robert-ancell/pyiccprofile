import pytest

from pyiccprofile.lut8 import ICCLut8

_MATRIX = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def _build_lut8_data(
    n_input_channels: int, n_output_channels: int, n_clut_grid_points: int
) -> bytes:
    """Build a well-formed lut8Type ('mft1') tag payload for testing."""
    data = bytearray()
    data.extend(b"mft1")
    data.extend(b"\x00\x00\x00\x00")
    data.append(n_input_channels)
    data.append(n_output_channels)
    data.append(n_clut_grid_points)
    data.append(0)
    for value in _MATRIX:
        data.extend(int(value * 65536).to_bytes(4, byteorder="big", signed=True))
    for channel in range(n_input_channels):
        data.extend(bytes([(i + channel) % 256 for i in range(256)]))
    n_clut_entries = n_clut_grid_points**n_input_channels
    for entry in range(n_clut_entries):
        data.extend(bytes([(entry + o) % 256 for o in range(n_output_channels)]))
    for channel in range(n_output_channels):
        data.extend(bytes([(255 - i - channel) % 256 for i in range(256)]))
    return bytes(data)


@pytest.mark.parametrize(
    "n_input_channels,n_output_channels,n_clut_grid_points",
    [
        (2, 3, 3),  # grid points not a divisor of channel count
        (3, 4, 9),
        (1, 1, 17),  # prime grid size
        (4, 4, 2),
        (1, 3, 1),  # minimal single-entry CLUT
        (5, 2, 1),  # grid_points=1 with several input channels
    ],
)
def test_lut8_round_trip(n_input_channels, n_output_channels, n_clut_grid_points):
    data = _build_lut8_data(
        n_input_channels, n_output_channels, n_clut_grid_points
    )

    lut = ICCLut8.decode(data)

    assert len(lut.input_tables) == n_input_channels
    assert all(len(table) == 256 for table in lut.input_tables)
    assert len(lut.clut) == n_clut_grid_points**n_input_channels
    assert all(len(entry) == n_output_channels for entry in lut.clut)
    assert len(lut.output_tables) == n_output_channels
    assert all(len(table) == 256 for table in lut.output_tables)
    assert lut.e1 == pytest.approx(_MATRIX[0])
    assert lut.e5 == pytest.approx(_MATRIX[4])
    assert lut.e9 == pytest.approx(_MATRIX[8])

    encoded = bytearray()
    lut.encode(encoded)
    assert bytes(encoded) == data


def test_lut8_decode_invalid_signature():
    data = bytearray(_build_lut8_data(1, 1, 2))
    data[0:4] = b"XXXX"
    with pytest.raises(ValueError):
        ICCLut8.decode(bytes(data))


def test_lut8_decode_invalid_reserved_header_bytes():
    data = bytearray(_build_lut8_data(1, 1, 2))
    data[4:8] = b"\x01\x00\x00\x00"
    with pytest.raises(ValueError):
        ICCLut8.decode(bytes(data))


def test_lut8_decode_invalid_reserved_byte_after_grid_points():
    data = bytearray(_build_lut8_data(1, 1, 2))
    data[11] = 1
    with pytest.raises(ValueError):
        ICCLut8.decode(bytes(data))


def test_lut8_decode_truncated_data_raises():
    data = _build_lut8_data(2, 3, 3)
    with pytest.raises(ValueError):
        ICCLut8.decode(data[:-1])


def test_lut8_decode_trailing_data_raises():
    data = _build_lut8_data(1, 1, 2) + b"\x00"
    with pytest.raises(ValueError):
        ICCLut8.decode(data)


def test_lut8_decode_insufficient_data_for_header_raises():
    with pytest.raises(ValueError):
        ICCLut8.decode(b"mft1" + b"\x00" * 10)


def test_lut8_constructor_rejects_wrong_input_table_length():
    with pytest.raises(ValueError):
        ICCLut8(
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            input_tables=[[0] * 255],  # should be 256 entries
            clut=[[0]],
            output_tables=[[0] * 256],
        )


def test_lut8_constructor_rejects_wrong_output_table_length():
    with pytest.raises(ValueError):
        ICCLut8(
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            input_tables=[[0] * 256],
            clut=[[0]],
            output_tables=[[0] * 255],  # should be 256 entries
        )


def test_lut8_constructor_rejects_clut_entry_wrong_width():
    with pytest.raises(ValueError):
        ICCLut8(
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            input_tables=[[0] * 256],
            clut=[[0, 0]],  # should have 1 value (1 output channel)
            output_tables=[[0] * 256],
        )


def test_lut8_constructor_rejects_clut_length_not_a_perfect_power():
    # 2 input channels means len(clut) must be a perfect square; 5 is not.
    with pytest.raises(ValueError):
        ICCLut8(
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            input_tables=[[0] * 256, [0] * 256],
            clut=[[0, 0, 0]] * 5,
            output_tables=[[0] * 256, [0] * 256, [0] * 256],
        )


def test_lut8_repr_does_not_raise():
    data = _build_lut8_data(1, 1, 2)
    lut = ICCLut8.decode(data)
    assert "ICCLut8(" in repr(lut)
