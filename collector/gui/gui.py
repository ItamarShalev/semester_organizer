from typing import List, Tuple

from data.activity import Activity
from data.course import Course
from data.output_format import OutputFormat
from data.user import User


class Gui:

    def open_login_window(self) -> User:
        pass

    def open_academic_activities_window(self, campuses: List[str], courses: List[Course]) -> Tuple[str, List[Course]]:
        """
        :return: campus names and courses
        """

    def open_custom_activities_windows(self) -> List[Activity]:
        pass

    def open_notification_windows(self, message: str):
        pass

    def open_choose_format_window(self) -> List[OutputFormat]:
        pass
