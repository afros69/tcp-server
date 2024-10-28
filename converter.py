import tempfile

import av
import cv2

from h264_unit import H264Unit


class MyConverter:
    def __init__(self):
        self.sps = None
        self.pps = None
        self.description = None
        self.sample_buffer_callback = None

    def add_nal_start_code(self, data):
        return b'\x00\x00\x00\x01' + data

    def create_description(self, sps: bytes, pps: bytes):
        """Set up the extradata (concatenated SPS and PPS) for the codec."""
        if sps and pps:
            if sps.startswith(b'\x00\x00\x00\x01'):
                sps = sps[4:]
            if pps.startswith(b'\x00\x00\x00\x01'):
                pps = pps[4:]

            self.description = self.add_nal_start_code(sps) + self.add_nal_start_code(pps)

    def create_block_buffer(self, h264_unit: H264Unit):
        """Create a properly formatted frame with a start code if needed."""
        # Add start code if missing
        if not h264_unit.data.startswith(b'\x00\x00\x00\x01'):
            return b'\x00\x00\x00\x01' + h264_unit.data
        return h264_unit.data

    def create_sample_buffer(self, block_buffer):
        """Decode the frame from block_buffer."""
        if not self.description:
            print("No description available - missing SPS/PPS")
            return None

        try:
            print(f"sps: {self.sps}, pps: {self.pps}, description: {self.description},  block: {block_buffer[:20]}")
            frame_data = self.description + block_buffer
            # print(frame_data)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".h264") as tmpfile:
                tmpfile.write(frame_data)
                h264_filename = tmpfile.name

            # Now use cv2.VideoCapture to read frames from the temporary file
            cap = cv2.VideoCapture(h264_filename)

            # Reading frames from the H.264 stream
            if cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    return None
                return frame

        except Exception as e:
            print(f"Failed to decode frame: {e}")
            return None

    def convert(self, h264_unit: H264Unit):
        """Convert H264Unit to a decoded frame, handling SPS and PPS initialization."""
        if h264_unit.type == 'sps':
            self.sps = h264_unit.data
            return None
        elif h264_unit.type == 'pps':
            self.pps = h264_unit.data
            # Initialize the codec context if both SPS and PPS are set
            if self.sps and self.pps:
                self.create_description(self.sps, self.pps)
            return None

        # For frame NAL units, add a start code if necessary and decode
        block_buffer = self.create_block_buffer(h264_unit)
        return self.create_sample_buffer(block_buffer)


# Example usage
def frame_callback(frame):
    """This callback function will handle the decoded frame display."""
    img = frame.to_ndarray(format='bgr24')
    cv2.imshow('Decoded Frame', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return


# Initialize converter and assign callback
converter = MyConverter()
converter.sample_buffer_callback = frame_callback