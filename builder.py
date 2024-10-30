from h264_unit import H264Unit


class FrameDataBuilder:
    def __init__(self):
        self.key_frame = None
        self.sps = None
        self.pps = None
        self.description = None

    def create_description(self, sps: bytes, pps: bytes):
        self.description = sps + pps

    def create_sample_buffer(self, block_buffer, is_key_frame):
        if not self.description:
            print("Missing SPS/PPS")
            return None

        data = block_buffer
        if not is_key_frame:
            data = self.key_frame + block_buffer
        frame_data = self.description + data
        self.key_frame = data

        return frame_data

    def build(self, h264_unit: H264Unit):
        is_key_frame = False

        if h264_unit.type == 'sps':
            self.sps = h264_unit.data
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
