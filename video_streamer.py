import subprocess
import cv2
import numpy as np

class VideoStreamer:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.frame_size = width * height * 3  # 3 bytes per pixel (BGR)
        self.min_data_chunk = 4096  # Increase minimum data to accumulate
        self.buffer = bytearray()  # Accumulated buffer

        # Updated FFmpeg command with debug loglevel
        self.process = subprocess.Popen(
            ['ffmpeg', '-loglevel', 'debug', '-f', 'h264', '-i', 'pipe:0', '-f', 'rawvideo', '-pix_fmt', 'bgr24', 'pipe:1'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**8
        )

    def stream_video(self, data_queue):
        print("Streaming video started.")
        while True:
            # Get data from queue
            if not data_queue.empty():
                data = data_queue.get()
                print("Data received:", len(data), "bytes")

                # Accumulate data until it reaches the minimum chunk size
                self.buffer.extend(data)
                if len(self.buffer) < self.min_data_chunk:
                    continue  # Wait until buffer accumulates enough data

                try:
                    # Write accumulated buffer to FFmpeg stdin
                    self.process.stdin.write(self.buffer)
                    self.buffer.clear()  # Clear buffer after writing to FFmpeg

                    # Read from FFmpeg's stdout in chunks
                    in_bytes = self.process.stdout.read(self.frame_size)
                    if in_bytes:
                        # Convert bytes to numpy array and reshape
                        frame = np.frombuffer(in_bytes, np.uint8).reshape([self.height, self.width, 3])
                        cv2.imshow('Video Stream', frame)

                        # Exit if 'q' is pressed
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print("Quit streaming.")
                            break
                    else:
                        print("No data read from FFmpeg.")
                except Exception as e:
                    print("Error in video stream:", e)
                    break

            # Print FFmpeg stderr output for diagnostic
            ffmpeg_errors = self.process.stderr.read(1000).decode('utf-8')
            if ffmpeg_errors:
                print("FFmpeg error output:", ffmpeg_errors)

    def close(self):
        self.process.stdin.close()
        self.process.wait()
