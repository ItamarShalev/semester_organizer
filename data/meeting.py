from time import struct_time, time

from day import Day


class Meeting:

    def __init__(self, day: Day, start_time: struct_time, end_time: struct_time):
        self.day = day
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        start_time_str = time.strftime("%H:%M", self.start_time)
        end_time_str = time.strftime("%H:%M", self.end_time)
        return f"{start_time_str} - {end_time_str}"

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

    @staticmethod
    def format_string_time_to_struct_time(time_str):
        """
        :param time_str: time in format "HH:MM" for example: "13:00"
        :return: struct_time
        """
        return time.strptime(time_str, "%H:%M")