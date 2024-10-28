
from h264_unit import H264Unit


class NALUParser:

    def __init__(self):
        self.data_stream = bytearray()
        self.search_index = 0
        self.h264_unit_handler = None  # Callback for parsed H264 units

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
                    unit = H264Unit(unit_data)
                    units.append(unit)
                    self.data_stream = self.data_stream[self.search_index:]
                    self.search_index = 0
                else:
                    self.search_index += 4
            else:
                self.search_index += 1

        if self.h264_unit_handler:
            # print(f"{len(units)} units parsed")
            for unit in units:
                if unit.type is not None:
                    self.h264_unit_handler(unit, count)
