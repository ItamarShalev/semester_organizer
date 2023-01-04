from typing import List, Set
import time
from data.activity import Activity
from data.day import Day
from data.meeting import Meeting


class Schedule:

    def __init__(self, name: str, file_name: str, description: str, activities: List[Activity]):
        self.name = name
        self.file_name = file_name
        self.description = description
        self.activities = activities

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        is_equals = len(self.activities) == len(other.activities)
        return is_equals and all(activity in other.activities for activity in self.activities)

    def __contains__(self, activity):
        return activity in self.activities

    def contains(self, activities):
        return all(activity in self for activity in activities)

    def get_learning_days(self) -> Set[Day]:
        return {meeting.day for activity in self.activities for meeting in activity.meetings}

    def get_all_academic_meetings(self) -> List[Meeting]:
        return [meeting for activity in self.activities for meeting in activity.meetings
                if not activity.type.is_personal()]

    def get_standby_in_minutes(self) -> float:
        """
        Get standby hours for all academic activities in schedule in minutes.
        """
        result = 0
        meetings = self.get_all_academic_meetings()
        meetings.sort()

        def to_minutes(struct_time: time.struct_time):
            return struct_time.tm_hour * 60 + struct_time.tm_min

        for i in range(len(meetings) - 1):
            if meetings[i].day != meetings[i + 1].day:
                continue
            delta_time = to_minutes(meetings[i + 1].start_time) - to_minutes(meetings[i].end_time)
            # Don't calculate standby minutes for the break between classes
            if delta_time > 15:
                result += delta_time
        return result

    def get_all_meetings_by_day(self, day: Day) -> Set[Meeting]:
        return {meeting for meeting in self.get_all_academic_meetings() if meeting.day is day}
