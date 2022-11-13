from typing import List

from data.activity import Activity


class Schedule:

    def __init__(self, name: str, file_name: str, description: str, activities: List[Activity]):
        self.name = name
        self.file_name = file_name
        self.description = description
        self.activities = activities

    def __eq__(self, other):
        is_equals = len(self.activities) == len(other.activities)
        for activity in self.activities:
            is_equals = is_equals and activity in other.activities
        return is_equals

    def __contains__(self, activity):
        return activity in self.activities
