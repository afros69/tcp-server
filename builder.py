from h264_unit import H264Unit


class FrameDataBuilder:
    def __init__(self):
        self.key_frame = None
        self.sps = None
        self.pps = None
        self.description = None

    def parse_sps(self, sps):
        # Extract information from SPS data based on H.264 specification
        try:
            # Convert bytes to a bit string for easier parsing
            bit_string = ''.join(f'{byte:08b}' for byte in sps)

            # Parse width and height from SPS based on known positions
            width_in_mbs_minus1 = int(bit_string[32:44], 2)
            height_in_map_units_minus1 = int(bit_string[44:56], 2)

            # Calculate width and height in pixels
            width = (width_in_mbs_minus1 + 1) * 16
            height = (height_in_map_units_minus1 + 1) * 16

            return width, height
        except Exception as e:
            print("Error parsing SPS:", e)
            return None, None

    def create_description(self, sps: bytes, pps: bytes):
        self.description = sps + pps

    def create_sample_buffer(self, block_buffer, is_key_frame):
        if not self.description:
            print("Missing SPS/PPS")
            return None

        frame_data = self.description + block_buffer
        if not is_key_frame:
            frame_data = self.description + self.key_frame + block_buffer

        return frame_data

    def build(self, h264_unit: H264Unit):
        is_key_frame = False

        if h264_unit.type == 'sps':
            self.sps = h264_unit.data
            w, h = self.parse_sps(self.sps)
            print(w, h)
            return None
        elif h264_unit.type == 'pps':
            self.pps = h264_unit.data

            if self.sps and self.pps:
                self.create_description(self.sps, self.pps)
            return None

        if h264_unit.type == 'ifr':
            self.key_frame = h264_unit.data
            is_key_frame = True

        return self.create_sample_buffer(h264_unit.data, is_key_frame)


frame_data_builder = FrameDataBuilder()
