import os
from typing import List, Optional

import utils
from data.academic_activity import AcademicActivity
from data.course import Course
from data.user import User


class Database:
    USER_NAME_FILE_PATH = os.path.join(utils.get_database_path(), "user_data.txt")

    def save_courses_data(self, courses: List[Course]):
        pass

    def save_academic_activities_data(self, academic_activities: List[AcademicActivity]):
        pass

    def save_campus_names(self, names: List[str]):
        pass

    def load_courses_data(self) -> List[Course]:
        pass

    def clear_courses_data(self):
        pass

    def clear_academic_activities_data(self):
        pass

    def clear_campus_names(self):
        pass

    def check_if_courses_data_exists(self, courses: List[Course]) -> bool:
        pass

    def load_academic_activities_data(self, courses: List[Course]) -> List[AcademicActivity]:
        pass

    def load_campus_names(self) -> List[str]:
        pass

    def load_hard_coded_user_data(self) -> Optional[User]:
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
        if not os.path.exists(Database.USER_NAME_FILE_PATH):
            return None
        with open(Database.USER_NAME_FILE_PATH, "r") as file:
            user_name = file.readline().strip()
            password = file.readline().strip()
            return User(user_name, password)

    def clear_all_data(self):
        self.clear_courses_data()
        self.clear_academic_activities_data()
        self.clear_campus_names()
