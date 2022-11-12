from data.type import Type
from data.day import Day


class Activity:

    def __init__(self, name: str, activity_type: Type, is_must: bool):
        self.name = name
        self.type = activity_type
        self.is_must = is_must
        self.days = {day: [] for day in Day}

    def add_slot(self, meeting):
        if meeting.is_crash_with_meeting(self.days[meeting.day]):
            raise Exception("Meeting is crash with other meeting")
        self.days[meeting.day].append(meeting)

    def is_free_slot(self, meeting):
        return not meeting.is_crash_with_meeting(self.days[meeting.day])

    def add_slots(self, meetings):
        for meeting in meetings:
            self.add_slot(meeting)
