import subprocess
import tempfile
from io import BytesIO

# import av
import cv2
import ffmpeg
import numpy as np


class FrameDecoder:
    def decode(self, data, approach):
        if approach == 1:
            return self.decode_tempfile(data)
        # elif approach == 2:
        #     return self.decode_av(data)
        elif approach == 3:
            return self.decode_ffmpeg(data)
        elif approach == 4:
            return self.decode_h264_with_pyav(data)
        elif approach == 5:
            return self.nal_units_to_cv2_frames(data)

    def decode_tempfile(self, frame_data):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".h264") as tmpfile:
                tmpfile.write(frame_data)
                h264_filename = tmpfile.name

            cap = cv2.VideoCapture(h264_filename)
            new_frame = None
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                new_frame = frame
            cap.release()
            return new_frame
        except Exception as e:
            print(f"Failed to decode frame: {e}")
            return None

    # def decode_av(self, frame_data):
    #     import av
    #     print("AV decode")
    #     # Create an `av` CodecContext for H.264 decoding
    #     codec = av.codec.CodecContext.create('h264', 'r')
    #
    #     # Feed SPS, PPS, and I-frame data into the CodecContext
    #     packet_data = frame_data
    #     packet = av.Packet(packet_data)
    #
    #     # Decode packet to get frames
    #     frames = []
    #     for frame in codec.decode(packet):
    #         # Convert AVFrame to a NumPy array in BGR format for OpenCV
    #         img = frame.to_ndarray(format='bgr24')
    #         frames.append(img)
    #
    #     # Return the first frame (assuming a single frame packet)
    #     return frames[0] if frames else None
    #
    def decode_h264_with_pyav(self, frame_data):
        import av
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

    def decode_ffmpeg(self, frame_data):
        # Combine SPS, PPS, and I-frame to form a complete NAL unit stream
        h264_data = frame_data

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

    def nal_units_to_cv2_frames(self, frame_data, width = 720, height = 1280):
        # Start FFmpeg process to read H.264 frames from stdin and output raw video to stdout
        process = subprocess.Popen(
            [
                'ffmpeg',
                '-f', 'h264',  # Specify raw H.264 input format
                '-i', 'pipe:0',  # Read from standard input
                '-pix_fmt', 'bgr24',  # Pixel format for OpenCV compatibility
                '-f', 'rawvideo',  # Output as raw video
                'pipe:1'  # Output to standard output
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        process.stdin.write(frame_data)

        # Close stdin to signal FFmpeg that input is done
        process.stdin.close()
        result_frame = None
        # Read frames from FFmpeg stdout and display using OpenCV
        while True:
            # Read one frame (width * height * 3 bytes for BGR24 format)
            in_bytes = process.stdout.read(width * height * 3)
            if not in_bytes:
                break
            # Convert bytes to numpy array and reshape for OpenCV
            frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])

            if frame is not None:
                result_frame = frame

        # Clean up
        process.stdout.close()
        process.wait()
        return result_frame
