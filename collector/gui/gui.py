from typing import List, Tuple

from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.course import Course
from data.user import User
from data.output_format import OutputFormat


def open_login_window() -> User:
    pass


def open_academic_activities_window(campuses: List[str], courses: List[Course]) -> Tuple[str, List[AcademicActivity]]:
    """
    :return: campus name and academic activities
    """


def open_custom_activities_windows() -> List[Activity]:
    pass


def open_notification_windows(message: str):
    pass


def open_choose_format_window() -> List[OutputFormat]:
    pass
