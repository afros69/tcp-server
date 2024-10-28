from an_data import test_byte_array
from h264_unit import H264Unit


class NALUParser:

    def __init__(self):
        self.data_stream = bytearray()
        self.search_index = 0
        self.h264_unit_handler = None  # Callback for parsed H264 units

    def validate_nalu(self, nalu_data):
        # Check for Annex B start code and strip it
        if nalu_data.startswith(b'\x00\x00\x01'):
            nalu_data = nalu_data[3:]
        elif nalu_data.startswith(b'\x00\x00\x00\x01'):
            nalu_data = nalu_data[4:]

        # Extract the NAL unit header
        header_byte = nalu_data[0]
        forbidden_zero_bit = (header_byte >> 7) & 0x1
        nri = (header_byte >> 5) & 0x3
        nal_type = header_byte & 0x1F

        # # Display parsed information
        # print("Forbidden Zero Bit:", forbidden_zero_bit)
        # print("NRI:", nri)
        # print("NAL Type:", nal_type)

        # Remove emulation prevention bytes
        parsed_payload = bytearray()
        i = 1  # Start after header
        while i < len(nalu_data):
            if i + 2 < len(nalu_data) and nalu_data[i:i + 3] == b'\x00\x00\x03':
                parsed_payload.extend(nalu_data[i:i + 2])
                i += 3
            else:
                parsed_payload.append(nalu_data[i])
                i += 1

        return parsed_payload

    def enqueue(self, data, count):
        self.data_stream.extend(data)
        units = []
        while self.search_index < len(self.data_stream) - 3:
            if (self.data_stream[self.search_index] == 0 and
                    self.data_stream[self.search_index + 1] == 0 and
                    self.data_stream[self.search_index + 2] == 0 and
                    self.data_stream[self.search_index + 3] == 1):
                if self.search_index > 0:
                    unit_data = self.data_stream[:self.search_index]
                    # unit_data = self.validate_nalu(unit_data)
                    unit = H264Unit(unit_data)
                    units.append(unit)
                    self.data_stream = self.data_stream[self.search_index + 4:]
                    self.search_index = 0
                else:
                    self.search_index += 4
            else:
                self.search_index += 1

        if self.h264_unit_handler:
            # print(f"{len(units)} units parsed")
            for unit in units:
                self.h264_unit_handler(unit, count)


def test_nalu_parser():
    def test_unit_handler(unit, count):
        print(unit.data)
    parser = NALUParser()
    parser.h264_unit_handler = test_unit_handler
    parser.enqueue(test_byte_array, 1)

if __name__ == '__main__':
    test_nalu_parser()