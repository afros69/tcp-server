import struct
import threading

import ffmpeg
import numpy as np


class H264Unit:
    class NALUType:
        SPS = 'sps'
        PPS = 'pps'
        IFR = 'ifr'
        PFR = 'pfr'

    def __init__(self, payload: bytes):
        self.payload = payload
        self.type_number = payload[4] & 0x1F
        self.length_data = None
        self.byte_length = None

        type_map = {
            7: H264Unit.NALUType.SPS,
            8: H264Unit.NALUType.PPS,
            5: H264Unit.NALUType.IFR,
            1: H264Unit.NALUType.PFR
        }
        self.type = type_map.get(self.type_number)

        if self.type == H264Unit.NALUType.IFR or self.type == H264Unit.NALUType.PFR:
            nalu_length = len(payload[4:])
            # Convert the length to a 4-byte big-endian format
            self.length_data = struct.pack('>I', nalu_length)
            self.byte_length = nalu_length

    @property
    def data(self):
        # if self.type == H264Unit.NALUType.VCL:
        #     return self.length_data + self.payload
        return self.payload


class H264Converter:
    def __init__(self):
        self.sps = None
        self.pps = None
        self.description = None
        self.sample_buffer_callback = None
        self.lock = threading.Lock()

    def create_description(self, h264_format: H264Unit):
        if h264_format.type == 'sps':
            self.sps = h264_format
        elif h264_format.type == 'pps':
            self.pps = h264_format

        if self.sps and self.pps:
            # Build a description from SPS and PPS
            # SPS and PPS are parameter sets used in H264; we would typically pass them to a decoder.
            self.description = (self.sps.data, self.pps.data)
            print("Description created with SPS and PPS.")

    def create_block_buffer(self, h264_format: H264Unit) -> bytes:
        """
        Allocates memory for the H264 frame data to simulate a block buffer.
        In Python, this can be handled with a simple copy of the data,
        but the purpose is to emulate the concept of a block buffer.
        """
        # Allocate a memory block and copy the data
        block_buffer = bytes(h264_format.data)  # Copy the data to ensure isolated block buffer
        return block_buffer

    def create_sample_buffer(self, block_buffer: bytes) -> np.ndarray:
        try:
            # Decode block buffer using ffmpeg-python, which wraps FFmpeg
            out, err = (
                ffmpeg
                .input('pipe:', format='h264')  # Input from raw H264 byte stream
                .output('pipe:', format='rawvideo', pix_fmt='rgb24')  # Convert to RGB frames
                .run(input=block_buffer, capture_stdout=True, capture_stderr=True)
            )

            # Convert to numpy array for the resulting frame
            video_frame = np.frombuffer(out, np.uint8).reshape([-1, 3])  # Adjust shape to frame dimensions if known
            return video_frame
        except ffmpeg.Error as e:
            print("Failed to create sample buffer:", e)
            return None

    def convert(self, h264_unit: H264Unit):
        # Run conversion in a separate thread (similar to DispatchQueue)
        threading.Thread(target=self._convert_async, args=(h264_unit,)).start()

    def _convert_async(self, h264_unit: H264Unit):
        with self.lock:
            if h264_unit.type in ['sps', 'pps']:
                self.description = None
                self.create_description(h264_unit)
                return
            else:
                self.sps = None
                self.pps = None

            block_buffer = self.create_block_buffer(h264_unit)
            sample_buffer = self.create_sample_buffer(block_buffer)

            if sample_buffer is not None and self.sample_buffer_callback:
                # Call the callback with the sample buffer (numpy array frame)
                self.sample_buffer_callback(sample_buffer)


# Example usage
def sample_buffer_callback(frame):
    print("Received frame with shape:", frame.shape)


h264_converter = H264Converter()