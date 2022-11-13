from typing import List

from data.academic_activity import AcademicActivity
from data.course import Course
from data.user import User


def check_username_and_password(user: User) -> bool:
    pass


def fill_academic_activities_data(user: User, campus_name: str, academic_activities: List[AcademicActivity]) \
        -> List[str]:
    """
    The function fills the academic activities' data.
    The function will connect to the server and will extract the data from the server by the parent course number.
    :param user: the username and password
    :param campus_name: the campus name
    :param academic_activities: all the academic activities
    :return: list of all the courses names that don't have activities
    """


def extract_all_courses(user: User) -> List[Course]:
    pass


def extract_campus_names(user: User) -> List[str]:
    pass
