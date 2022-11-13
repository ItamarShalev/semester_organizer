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

    def is_crash_with_activities(self, activities):
        if not activities:
            return False
        return any(self.is_crash_with_activity(activity) for activity in activities)

    def is_crash_with_activity(self, activity):
        if not self.is_must or not activity.is_must:
            return False
        for day in Day:
            all_meetings = [meeting for meetings in self.days.values() for meeting in meetings]
            for meeting in activity.days[day]:
                if meeting.is_crash_with_meetings(all_meetings):
                    return True
        return False

    def __eq__(self, other):
        is_equals = self.name == other.name and self.type == other.type and self.is_must == other.is_must
        for day, meetings in self.days.items():
            is_equals = is_equals and len(meetings) == len(other.days[day])
            for meeting in meetings:
                is_equals = is_equals and meeting in other.days[day]
        return is_equals
