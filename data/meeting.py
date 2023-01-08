from typing import Union
from itertools import count
from time import struct_time, strptime
import time
import functools
from data.day import Day


@functools.total_ordering
class Meeting:
    _ids = count(0)

    def __init__(self, day: Day, start_time: Union[struct_time, str], end_time: Union[struct_time, str]):
        self.meeting_id = next(Meeting._ids)
        self.day = day
        if isinstance(start_time, str):
            self.start_time = Meeting.str_to_time(start_time)
        else:
            self.start_time = start_time

        if isinstance(end_time, str):
            self.end_time = Meeting.str_to_time(end_time)
        else:
            self.end_time = end_time

        if self.start_time >= self.end_time:
            raise Exception("Start time is after end time")

    def __str__(self):
        return f"{self.get_string_start_time()} - {self.get_string_end_time()}"

    def __repr__(self):
        return str(self)

    def is_crash_with_meeting(self, meeting):
        if self.day != meeting.day:
            return False
        meeting_crash = self.start_time <= meeting.start_time < self.end_time
        other_meeting_crash = meeting.start_time <= self.start_time < meeting.end_time
        return meeting_crash or other_meeting_crash

    def is_crash_with_meetings(self, meetings):
        if not meetings:
            return False
        return any(self.is_crash_with_meeting(meeting) for meeting in meetings)

    def get_string_start_time(self):
        return time.strftime("%H:%M", self.start_time)

    def get_string_end_time(self):
        return time.strftime("%H:%M", self.end_time)

    def __eq__(self, other):
        is_equals = self.day == other.day
        is_equals = is_equals and self.start_time == other.start_time
        is_equals = is_equals and self.end_time == other.end_time
        return is_equals

    def __lt__(self, other):
        return self.day < other.day or (self.day == other.day and self.end_time < other.start_time)

    def __hash__(self):
        return hash((self.day, self.start_time, self.end_time))

    @staticmethod
    def str_to_time(time_str):
        """
        :param time_str: time in format "HH:MM" for example: "13:00"
        :return: struct_time
        """
        return strptime(time_str, "%H:%M")
