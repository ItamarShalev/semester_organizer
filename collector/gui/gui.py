from enum import Enum, auto
from typing import List, Dict, Optional

import utils
from data.activity import Activity
from data.course_choice import CourseChoice
from data.user import User
from data.settings import Settings


class MessageType(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


class UserClickExitException(Exception):
    def __init__(self):
        super().__init__("ERROR: Can't click exit button without choose from the options.")


class Gui:

    def __init__(self):
        self.logger = utils.get_logging()

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

    def open_academic_activities_window(self, ask_attendance_required: bool, course_choice: List[CourseChoice]) -> \
            List[CourseChoice]:
        """
        This function will open the academic activities window.
        :param: ask_attendance_required: if the user should choose if the activity is attendance required.
        :param: course_choice: the courses that the user can choose from.
        :return: the courses that the user chose.
        :raises: UserClickExitException if the user clicked exit button.
        """

    def open_personal_activities_window(self) -> List[Activity]:
        """
        This function will open a window to ask the user for his custom activities.
        for example, job, army, etc.
        :return: list of custom activities, or empty list.
        """

    def open_notification_window(self, message: str, message_type: MessageType = MessageType.INFO,
                                 buttons: List[str] = None) -> Optional[str]:
        """
        This function will open a notification window.
        :param: message: the message that will be shown in the window.
        :param: message_type: the type of the message. it will be shown in the window.
        :param: buttons: the buttons that will be shown in the window.
        :return: Which button was clicked. None if no button was clicked or the exit button was clicked.
        """

    def open_loading_window(self, message: str):
        """
        This function will open a loading window.
        :param: message: the message that will be shown in the window.
        """

    def close_loading_window(self):
        """
        This function will open a loading window.
        :param: message: the message that will be shown in the window.
        """

    def open_settings_window(self, settings: Settings, campuses: List[str], years: Dict[str, int]) -> Settings:
        """
        This function will open the settings window.
        it will show all the campus names that the user can choose from.
        years will be dict that will contain the years in format [hebrew_year: value_of_year]
        for example: {"תשפ"ג"
        : 5783}
        :param: settings: the settings that will be shown in the window. the function will return the new settings.
        :param: campuses: all the campus names that the user can choose from.
        :param: years: all the years that the user can choose from.
        :return: new object of Settings, if the user click exit button, it will return the old settings.
        """
