import os
from typing import List, Optional

import utils
from data.academic_activity import AcademicActivity
from data.course import Course
from data.user import User

USER_NAME_FILE_PATH = os.path.join(utils.get_database_path(), "username_data")


def save_courses_data(courses: List[Course]):
    pass


def save_academic_activities_data(academic_activities: List[AcademicActivity]):
    pass


def save_campus_names(names: List[str]):
    pass


def load_courses_data() -> List[Course]:
    pass


def clear_courses_data():
    pass


def clear_academic_activities_data():
    pass


def clear_campus_names():
    pass


def check_if_courses_data_exists(courses: List[Course]) -> bool:
    pass


def load_academic_activities_data(courses: List[Course]) -> List[AcademicActivity]:
    pass


def load_campus_names() -> List[str]:
    pass


def load_hard_coded_user_data() -> Optional[User]:
    """
    This function is used to load the user data from the hard coded file.
    The user data is for testing purposes only.
    The user data will not save in the database.
    It will read from username_data.txt file that locate in the above.
    The format of the file is:
    username
    password
    :return: The user data or None if not found.
    """
    if not os.path.exists(USER_NAME_FILE_PATH):
        return None
    with open(USER_NAME_FILE_PATH, "r") as file:
        user_name = file.readline().strip()
        password = file.readline().strip()
        return User(user_name, password)
