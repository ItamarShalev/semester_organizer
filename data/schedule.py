from typing import List

from data.activity import Activity


class Schedule:

    def __init__(self, name: str, file_name: str, description: str, activities: List[Activity]):
        self.name = name
        self.file_name = file_name
        self.description = description
        self.activities = activities

    def __str__(self):
        return f"{self.name} {self.description}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        is_equals = len(self.activities) == len(other.activities)
        return is_equals and all(activity in other.activities for activity in self.activities)

    def __contains__(self, activity):
        return activity in self.activities

    def contains(self, activities):
        return all(activity in self for activity in activities)
