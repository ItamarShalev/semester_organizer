from time import struct_time
from day import Day


class Meeting:

    def __init__(self, day: Day, start_time: struct_time, end_time: struct_time):
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
