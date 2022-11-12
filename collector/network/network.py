from typing import List

from data.academic_activity import AcademicActivity
from data.course import Course
from data.user import User


def check_username_and_password(user: User) -> bool:
    pass


def extract_academic_activities_data(user: User, parents_numbers: List[int]) -> List[AcademicActivity]:
    pass


def extract_all_courses(user: User) -> List[Course]:
    pass


def extract_campus_names(user: User) -> List[str]:
    pass
