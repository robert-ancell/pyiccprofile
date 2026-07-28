import pytest

from pyiccprofile.lut16 import ICCLut16

_MATRIX = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def _build_lut16_data(
    n_input_channels: int,
    n_output_channels: int,
    n_clut_grid_points: int,
    n_input_table_entries: int = 4,
    n_output_table_entries: int = 4,
) -> bytes:
    """Build a well-formed lut16Type ('mft2') tag payload for testing."""
    data = bytearray()
    data.extend(b"mft2")
    data.extend(b"\x00\x00\x00\x00")
    data.append(n_input_channels)
    data.append(n_output_channels)
    data.append(n_clut_grid_points)
    data.append(0)
    for value in _MATRIX:
        data.extend(int(value * 65536).to_bytes(4, byteorder="big", signed=True))
    data.extend(n_input_table_entries.to_bytes(2, byteorder="big"))
    data.extend(n_output_table_entries.to_bytes(2, byteorder="big"))
    for channel in range(n_input_channels):
        for i in range(n_input_table_entries):
            data.extend(((i + channel) % 65536).to_bytes(2, byteorder="big"))
    n_clut_entries = n_clut_grid_points**n_input_channels
    for entry in range(n_clut_entries):
        for o in range(n_output_channels):
            data.extend(((entry + o) % 65536).to_bytes(2, byteorder="big"))
    for channel in range(n_output_channels):
        for i in range(n_output_table_entries):
            data.extend(((65535 - i - channel) % 65536).to_bytes(2, byteorder="big"))
    return bytes(data)


@pytest.mark.parametrize(
    "n_input_channels,n_output_channels,n_clut_grid_points,"
    "n_input_table_entries,n_output_table_entries",
    [
        (2, 3, 3, 4, 4),  # grid points not a divisor of channel count
        (3, 4, 9, 2, 2),  # minimal 2-entry tables
        (1, 1, 17, 8, 8),  # prime grid size
        (4, 4, 2, 16, 16),
        (1, 3, 1, 4, 4),  # minimal single-entry CLUT
        (5, 2, 1, 2, 2),  # grid_points=1 with several input channels
        (2, 2, 4, 4096, 4096),  # large table entry counts, still fits uint16
    ],
)
def test_lut16_round_trip(
    n_input_channels,
    n_output_channels,
    n_clut_grid_points,
    n_input_table_entries,
    n_output_table_entries,
):
    data = _build_lut16_data(
        n_input_channels,
        n_output_channels,
        n_clut_grid_points,
        n_input_table_entries,
        n_output_table_entries,
    )

    lut = ICCLut16.decode(data)

    assert len(lut.input_tables) == n_input_channels
    assert all(len(table) == n_input_table_entries for table in lut.input_tables)
    assert len(lut.clut) == n_clut_grid_points**n_input_channels
    assert all(len(entry) == n_output_channels for entry in lut.clut)
    assert len(lut.output_tables) == n_output_channels
    assert all(len(table) == n_output_table_entries for table in lut.output_tables)
    assert lut.e1 == pytest.approx(_MATRIX[0])
    assert lut.e5 == pytest.approx(_MATRIX[4])
    assert lut.e9 == pytest.approx(_MATRIX[8])

    encoded = bytearray()
    lut.encode(encoded)
    assert bytes(encoded) == data


def test_lut16_decode_invalid_signature():
    data = bytearray(_build_lut16_data(1, 1, 2))
    data[0:4] = b"XXXX"
    with pytest.raises(ValueError):
        ICCLut16.decode(bytes(data))


def test_lut16_decode_invalid_reserved_header_bytes():
    data = bytearray(_build_lut16_data(1, 1, 2))
    data[4:8] = b"\x01\x00\x00\x00"
    with pytest.raises(ValueError):
        ICCLut16.decode(bytes(data))


def test_lut16_decode_invalid_reserved_byte_after_grid_points():
    data = bytearray(_build_lut16_data(1, 1, 2))
    data[11] = 1
    with pytest.raises(ValueError):
        ICCLut16.decode(bytes(data))


def test_lut16_decode_truncated_data_raises():
    data = _build_lut16_data(2, 3, 3)
    with pytest.raises(ValueError):
        ICCLut16.decode(data[:-1])


def test_lut16_decode_truncated_before_table_counts_raises():
    # Header + matrix only, missing the 4-byte table entry count fields.
    data = _build_lut16_data(1, 1, 2)
    with pytest.raises(ValueError):
        ICCLut16.decode(data[:50])


def test_lut16_decode_trailing_data_raises():
    data = _build_lut16_data(1, 1, 2) + b"\x00"
    with pytest.raises(ValueError):
        ICCLut16.decode(data)


def test_lut16_decode_insufficient_data_for_header_raises():
    with pytest.raises(ValueError):
        ICCLut16.decode(b"mft2" + b"\x00" * 20)


def test_lut16_constructor_rejects_inconsistent_input_table_lengths():
    with pytest.raises(ValueError):
        ICCLut16(
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            input_tables=[[0, 0, 0, 0], [0, 0]],  # inconsistent lengths
            clut=[[0]],
            output_tables=[[0, 0]],
        )


def test_lut16_constructor_rejects_inconsistent_output_table_lengths():
    with pytest.raises(ValueError):
        ICCLut16(
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            input_tables=[[0, 0]],
            clut=[[0]],
            output_tables=[[0, 0, 0], [0]],  # inconsistent lengths
        )


def test_lut16_constructor_rejects_clut_entry_wrong_width():
    with pytest.raises(ValueError):
        ICCLut16(
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            input_tables=[[0, 0]],
            clut=[[0, 0]],  # should have 1 value (1 output channel)
            output_tables=[[0, 0]],
        )


def test_lut16_constructor_rejects_clut_length_not_a_perfect_power():
    # 2 input channels means len(clut) must be a perfect square; 5 is not.
    with pytest.raises(ValueError):
        ICCLut16(
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            input_tables=[[0, 0], [0, 0]],
            clut=[[0, 0, 0]] * 5,
            output_tables=[[0, 0], [0, 0], [0, 0]],
        )


def test_lut16_repr_does_not_raise():
    data = _build_lut16_data(1, 1, 2)
    lut = ICCLut16.decode(data)
    assert "ICCLut16(" in repr(lut)
