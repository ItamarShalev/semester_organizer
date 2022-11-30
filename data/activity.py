from collections import defaultdict
from typing import Dict, List

from data.type import Type


class Activity:

    def __init__(self, name: str = None, activity_type: Type = None, attendance_required: bool = None):
        self.name = name
        self.type = activity_type
        self.attendance_required = attendance_required
        self.meetings = []

    def add_slot(self, meeting):
        if meeting.is_crash_with_meetings(self.meetings):
            raise Exception("Meeting is crash with other meeting")
        self.meetings.append(meeting)

    def is_free_slot(self, meeting):
        return not meeting.is_crash_with_meetings(self.meetings)

    def add_slots(self, meetings):
        for meeting in meetings:
            self.add_slot(meeting)

    def is_crash_with_activities(self, activities):
        if not activities:
            return False
        return any(self.is_crash_with_activity(activity) for activity in activities)

    def is_crash_with_activity(self, activity):
        if not self.attendance_required or not activity.attendance_required:
            return False
        return any(meeting.is_crash_with_meetings(activity.meetings) for meeting in self.meetings)

    def no_meetings(self):
        return not self.meetings

    @staticmethod
    def get_activities_by_name(activities) -> Dict[str, List]:
        result = defaultdict(list)
        for activity in activities:
            result[activity.name].append(activity)
        return dict(result)

    def __eq__(self, other):
        is_equals = self.name == other.name and self.type == other.type
        is_equals = is_equals and self.attendance_required == other.attendance_required
        is_equals = is_equals and len(self.meetings) == len(other.meetings)
        for meeting in self.meetings:
            is_equals = is_equals and meeting in other.meetings
        return is_equals

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)
