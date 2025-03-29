from collections import defaultdict
from typing import Dict, List
from itertools import count

from src.data.type import Type


class Activity:
    _ids = count(0)

    def __init__(self, name: str = None, activity_type: Type = None, attendance_required: bool = None):
        self.activity_id = next(self._ids)
        self.name = name
        self.type = activity_type or Type.PERSONAL
        self.attendance_required = attendance_required if attendance_required is not None else True
        self.meetings = []

    @staticmethod
    def create_personal_from_database(activity_id: int, name: str):
        activity = Activity()
        activity.activity_id = activity_id
        activity.name = name
        activity.type = Type.PERSONAL
        activity.attendance_required = True
        return activity

    def add_slot(self, meeting):
        if meeting.is_crash_with_meetings(self.meetings):
            raise RuntimeError("Meeting is crash with other meeting")
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

    def __hash__(self):
        return hash(self.name)

    @staticmethod
    def get_activities_by_name(activities) -> Dict[str, List]:
        result = defaultdict(list)
        for activity in activities:
            result[activity.name].append(activity)
        return dict(result)

    @staticmethod
    def extract_flat_activities_by_type(activities: List["Activity"]) -> List[List["Activity"]]:
        result = {activity_type: [] for activity_type in Type}
        for activity in activities:
            result[activity.type].append(activity)
        return [item for item in result.values() if item]

    @staticmethod
    def extract_all_options_of_activity(activities_list: List[List["Activity"]]) -> List[List["Activity"]]:
        if not activities_list:
            return [[]]
        all_options = []
        options = Activity.extract_all_options_of_activity(activities_list[1:])
        for activity in activities_list[0]:
            for option in options:
                all_options.append([activity] + option)
        return all_options

    def __eq__(self, other):
        is_equals = self.name == other.name and self.type == other.type
        is_equals = is_equals and self.attendance_required == other.attendance_required
        is_equals = is_equals and len(self.meetings) == len(other.meetings)
        is_equals = is_equals and all(meeting in other.meetings for meeting in self.meetings)
        return is_equals

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)
