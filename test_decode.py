import tempfile
from io import BytesIO

import av
import cv2
import ffmpeg
import numpy as np

from an_data import test_byte_array
from builder import frame_data_builder
from h264_unit import H264Unit
from nalu_parser import NALUParser


class FrameDecoder:
    def decode(self, data, approach):
        if approach == 1:
            return self.decode_tempfile(data)
        elif approach == 2:
            return self.decode_av(data)
        elif approach == 3:
            return self.decode_ffmpeg(data)
        elif approach == 4:
            return self.decode_h264_with_pyav(data)

    def decode_tempfile(self, frame_data):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".h264") as tmpfile:
                tmpfile.write(frame_data)
                h264_filename = tmpfile.name

            cap = cv2.VideoCapture(h264_filename)

            if cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    return None
                return frame
        except Exception as e:
            print(f"Failed to decode frame: {e}")
            return None

    def decode_av(self, frame_data):
        print("AV decode")
        # Create an `av` CodecContext for H.264 decoding
        codec = av.codec.CodecContext.create('h264', 'r')

        # Feed SPS, PPS, and I-frame data into the CodecContext
        packet_data = frame_data
        packet = av.Packet(packet_data)

        # Decode packet to get frames
        frames = []
        for frame in codec.decode(packet):
            # Convert AVFrame to a NumPy array in BGR format for OpenCV
            img = frame.to_ndarray(format='bgr24')
            frames.append(img)

        # Return the first frame (assuming a single frame packet)
        return frames[0] if frames else None

    def decode_h264_with_pyav(self, frame_data):
        # Use BytesIO to create a stream from the byte data
        stream = BytesIO(frame_data)

        # Create a PyAV input container from the byte stream
        container = av.open(stream, format='h264')

        # Decode frames
        frames = []
        for frame in container.decode(video=0):
            width, height = frame.width, frame.height
            img = frame.to_rgb().to_ndarray()

            # Confirm shape matches the frame's properties
            img = img.reshape(height, width, 3)
            frames.append(img)

        print(f"{len(frames)} frames were decoded")
        return frames[-1]  # Return a list of decoded frames

    def decode_ffmpeg(self, frame_date):
        # Combine SPS, PPS, and I-frame to form a complete NAL unit stream
        h264_data = frame_date

        # Decode using ffmpeg to raw frames and pipe to stdout
        out, _ = (
            ffmpeg
            .input('pipe:', format='h264')  # Input is a raw H.264 stream
            .output('pipe:', format='rawvideo', pix_fmt='bgr24')  # Output is raw video in BGR format
            .run(input=h264_data, capture_stdout=True, capture_stderr=True)
        )

        # Convert bytes to a NumPy array
        width, height = 720, 1280  # Use your frame's actual resolution
        frame = np.frombuffer(out, np.uint8).reshape([height, width, 3])

        return frame


def test():
    decoder = FrameDecoder()

    def test_unit_handler(unit: H264Unit, count):
        print(f"unit: type - {unit.type} [{unit.type_number}], length - {unit.byte_length}")
        build_data = frame_data_builder.build(unit)
        if build_data is None:
            return

        for i in [4]:
            frame = decoder.decode(build_data, i)
            if frame is not None:
                print("Frame is here!!!")
                cv2.imwrite(f"frames/frame{i}.png", frame)
            else:
                print("Frame is not here (")

    parser = NALUParser()
    parser.h264_unit_handler = test_unit_handler
    parser.enqueue(test_byte_array, 1)


if __name__ == '__main__':
    test()