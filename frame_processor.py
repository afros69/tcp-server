import select
import subprocess
import numpy as np


class FrameProcessor:
    def __init__(self, width=720, height=1280):
        self.width = width
        self.height = height
        # Initialize the FFmpeg process once
        self.process = subprocess.Popen(
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
            stderr=subprocess.PIPE,
            bufsize=10 ** 6  # Set buffer size to handle high data rate
        )

    def nal_units_to_cv2_frame(self, frame_data):
        try:
            # Write frame data to FFmpeg process stdin
            self.process.stdin.write(frame_data)

            # Read one frame from FFmpeg's stdout
            in_bytes = self.process.stdout.read(self.width * self.height * 3)
            if not in_bytes:
                return None  # No data received, possibly end of stream or error

            # Convert to numpy array and reshape for OpenCV
            frame = np.frombuffer(in_bytes, np.uint8).reshape([self.height, self.width, 3])
            return frame

        except Exception as e:
            print(f"Error in processing frame: {e}")
            return None

    def close(self):
        # Close FFmpeg process streams
        self.process.stdout.close()
        self.process.wait()
