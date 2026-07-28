from pyiccprofile.codec import (
    decode_s15fixed16_number,
    decode_signature,
    decode_uint16,
    encode_s15fixed16_number,
    encode_signature,
    encode_uint16,
)


def _get_n_clut_grid_points(
    input_tables: list[list[int]], clut: list[list[int]]
) -> int:
    n_clut_grid_points = 1
    while True:
        n_clut_entries = n_clut_grid_points ** len(input_tables)
        if n_clut_entries == len(clut):
            return n_clut_grid_points
        if n_clut_entries > len(clut):
            raise ValueError("Invalid CLUT length")
        n_clut_grid_points += 1


class ICCLut16:
    SIGNATURE = b"mft2"

    def __init__(
        self,
        e1: float,
        e2: float,
        e3: float,
        e4: float,
        e5: float,
        e6: float,
        e7: float,
        e8: float,
        e9: float,
        input_tables: list[list[int]],
        clut: list[list[int]],
        output_tables: list[list[int]],
    ):
        if len(input_tables) > 255:
            raise ValueError("Too many input tables")
        input_table_length = len(input_tables[0]) if input_tables else 0
        for table in input_tables:
            if len(table) != input_table_length:
                raise ValueError("All input tables must have the same length")

        _get_n_clut_grid_points(input_tables, clut)
        for entry in clut:
            if len(entry) != len(output_tables):
                raise ValueError("CLUT entry must have n_output_channels values")

        if len(output_tables) > 255:
            raise ValueError("Too many output tables")
        output_table_length = len(output_tables[0]) if output_tables else 0
        for table in output_tables:
            if len(table) != output_table_length:
                raise ValueError("All output tables must have the same length")

        self.e1 = e1
        self.e2 = e2
        self.e3 = e3
        self.e4 = e4
        self.e5 = e5
        self.e6 = e6
        self.e7 = e7
        self.e8 = e8
        self.e9 = e9
        self.input_tables = input_tables
        self.clut = clut
        self.output_tables = output_tables

    @classmethod
    def decode(cls, data: bytes) -> "ICCLut16":
        if len(data) < 52:
            raise ValueError("Insufficient data")
        signature = decode_signature(data, 0)
        if signature != ICCLut16.SIGNATURE:
            raise ValueError(f"Invalid signature: {signature!r}")
        if data[4:8] != b"\x00\x00\x00\x00":
            raise ValueError("Invalid reserved bytes")
        n_input_channels = data[8]
        n_output_channels = data[9]
        n_clut_grid_points = data[10]
        if data[11] != 0:
            raise ValueError("Reserved byte must be 0")
        e1 = decode_s15fixed16_number(data, 12)
        e2 = decode_s15fixed16_number(data, 16)
        e3 = decode_s15fixed16_number(data, 20)
        e4 = decode_s15fixed16_number(data, 24)
        e5 = decode_s15fixed16_number(data, 28)
        e6 = decode_s15fixed16_number(data, 32)
        e7 = decode_s15fixed16_number(data, 36)
        e8 = decode_s15fixed16_number(data, 40)
        e9 = decode_s15fixed16_number(data, 44)
        n_input_table_entries = decode_uint16(data, 48)
        n_output_table_entries = decode_uint16(data, 50)

        offset = 52

        input_tables = []
        for _ in range(n_input_channels):
            table = []
            for _ in range(n_input_table_entries):
                end = offset + 2
                if end > len(data):
                    raise ValueError("Insufficient data for input table")
                table.append(decode_uint16(data, offset))
                offset = end
            input_tables.append(table)

        n_clut_entries = n_clut_grid_points**n_input_channels
        clut = []
        for _ in range(n_clut_entries):
            entry = []
            for _ in range(n_output_channels):
                end = offset + 2
                if end > len(data):
                    raise ValueError("Insufficient data for CLUT")
                entry.append(decode_uint16(data, offset))
                offset = end
            clut.append(entry)

        output_tables = []
        for _ in range(n_output_channels):
            table = []
            for _ in range(n_output_table_entries):
                end = offset + 2
                if end > len(data):
                    raise ValueError("Insufficient data for output table")
                table.append(decode_uint16(data, offset))
                offset = end
            output_tables.append(table)

        if offset != len(data):
            raise ValueError("Unexpected trailing data in lut16Type")

        return cls(
            e1,
            e2,
            e3,
            e4,
            e5,
            e6,
            e7,
            e8,
            e9,
            input_tables=input_tables,
            clut=clut,
            output_tables=output_tables,
        )

    def encode(self, data: bytearray) -> None:
        n_input_channels = len(self.input_tables)
        n_output_channels = len(self.output_tables)
        n_clut_grid_points = (
            _get_n_clut_grid_points(self.input_tables, self.clut)
            if n_input_channels
            else 0
        )
        n_input_table_entries = len(self.input_tables[0]) if self.input_tables else 0
        n_output_table_entries = len(self.output_tables[0]) if self.output_tables else 0

        encode_signature(data, ICCLut16.SIGNATURE)
        data.extend(b"\x00\x00\x00\x00")
        data.append(n_input_channels)
        data.append(n_output_channels)
        data.append(n_clut_grid_points)
        data.append(0)
        encode_s15fixed16_number(data, self.e1)
        encode_s15fixed16_number(data, self.e2)
        encode_s15fixed16_number(data, self.e3)
        encode_s15fixed16_number(data, self.e4)
        encode_s15fixed16_number(data, self.e5)
        encode_s15fixed16_number(data, self.e6)
        encode_s15fixed16_number(data, self.e7)
        encode_s15fixed16_number(data, self.e8)
        encode_s15fixed16_number(data, self.e9)
        encode_uint16(data, n_input_table_entries)
        encode_uint16(data, n_output_table_entries)
        for table in self.input_tables:
            for value in table:
                encode_uint16(data, value)
        for entry in self.clut:
            for value in entry:
                encode_uint16(data, value)
        for table in self.output_tables:
            for value in table:
                encode_uint16(data, value)

    def __repr__(self) -> str:
        args = [
            f"{self.e1}",
            f"{self.e2}",
            f"{self.e3}",
            f"{self.e4}",
            f"{self.e5}",
            f"{self.e6}",
            f"{self.e7}",
            f"{self.e8}",
            f"{self.e9}",
        ]
        return f"ICCLut16({', '.join(args)})"
