from typing import List, Tuple, Dict

from data.activity import Activity
from data.course import Course
from data.output_format import OutputFormat
from data.user import User
from data.settings import Settings


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

    def open_settings_window(self, settings: Settings, campuses: List[str], years: Dict[str, int]) -> Settings:
        """
        This function will open the settings window.
        it will show all the campus names that the user can choose from.
        years will be dict that will contain the years in format [hebrew_year: value_of_year]
        for example: {"תשפ"ג"
        : 5783}
        :param settings: the settings that will be shown in the window. the function will return the new settings.
        :param campuses: all the campus names that the user can choose from.
        :param years: all the years that the user can choose from.
        :return: new object of Settings.
        """
