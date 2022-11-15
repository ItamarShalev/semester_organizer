from typing import List, Optional, Tuple

from data.academic_activity import AcademicActivity
from data.course import Course
from data.user import User


class Network:

    def __init__(self, user: Optional[User] = None):
        self.user = user

    def check_username_and_password(self) -> bool:
        pass

    def extract_academic_activities_data(self, campus_name: str, courses: List[Course]) \
            -> Tuple[List[AcademicActivity], List[str]]:
        """
        The function fills the academic activities' data.
        The function will connect to the server and will extract the data from the server by the parent course number.
        :param user: the username and password
        :param campus_name: the campus name
        :param courses: all the courses to get
        :return: list of all academic activities by the courses, list of all the courses names that missing data
        """

    def extract_all_courses(self) -> List[Course]:
        pass

    def extract_campus_names(self) -> List[str]:
        pass

    def set_user(self, user: User):
        self.user = user
