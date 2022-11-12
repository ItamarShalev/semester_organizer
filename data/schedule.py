from typing import List

from data.activity import Activity


class Schedule:

    def __init__(self, name: str, file_name: str, description: str, activities: List[Activity]):
        self.name = name
        self.file_name = file_name
        self.description = description
        self.activities = activities
