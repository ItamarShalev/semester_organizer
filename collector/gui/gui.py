from enum import Enum, auto
from typing import List, Tuple, Dict, Optional

from data.activity import Activity
from data.course import Course
from data.user import User
from data.settings import Settings


class MessageType(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


class UserClickExitException(Exception):
    def __init__(self):
        super().__init__("User clicked exit button in the GUI.")


class Gui:

    def open_login_window(self) -> User:
        """
        This function will open the login window.
        :return: the user that was logged in.
        :raises: UserClickExitException if the user clicked exit button.
        """

    def close_login_window(self):
        """
        This function will close the login window.
        """

    def open_academic_activities_window(self, campuses: List[str], courses: List[Course],
                                        available_teachers: Dict[int, List[str]]) -> \
            Tuple[List[Course], Dict[int, List[str]]]:
        """
        This function will open the academic activities window.
        :param campuses: all the campus names that the user can choose from.
        :param courses: all the courses that the user can choose from.
        :param available_teachers: dict that will contain the available teachers for each course
               the key is the parent_course_number.
        :return: tuple of courses and available teachers for each course by the parent_course_number.
        :raises: UserClickExitException if the user clicked exit button.
        """

    def open_custom_activities_window(self) -> List[Activity]:
        """
        This function will open a window to ask the user for his custom activities.
        for example, job, army, etc.
        :return: list of custom activities, or empty list.
        """

    def open_notification_window(self, message: str, message_type: MessageType = MessageType.INFO,
                                 buttons: List[str] = None) -> Optional[str]:
        """
        This function will open a notification window.
        :param message: the message that will be shown in the window.
        :param message_type: the type of the message. it will be shown in the window.
        :param buttons: the buttons that will be shown in the window.
        :return: Which button was clicked. None if no button was clicked or the exit button was clicked.
        """

    def open_loading_window(self, message: str):
        """
        This function will open a loading window.
        :param message: the message that will be shown in the window.
        """

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
        :return: new object of Settings, if the user click exit button, it will return the old settings.
        """
