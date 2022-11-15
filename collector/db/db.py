import os
from typing import List, Optional

import utils
from data.academic_activity import AcademicActivity
from data.course import Course
from data.user import User


class Database:
    USER_NAME_FILE_PATH = os.path.join(utils.get_database_path(), "user_data.txt")
    CAMPUS_NAMES_FILE_PATH = os.path.join(utils.get_database_path(), "campus_names.txt")

    def save_courses_data(self, courses: List[Course]):
        pass

    def save_academic_activities_data(self, campus_name: str, academic_activities: List[AcademicActivity]):
        pass

    def save_campus_names(self, names: List[str]):
        with open(Database.CAMPUS_NAMES_FILE_PATH, "w") as file:
            file.write("\n".join(names))

    def load_courses_data(self) -> List[Course]:
        pass

    def clear_courses_data(self):
        pass

    def clear_academic_activities_data(self, campus_name: Optional[str] = None):
        """
        The function clears the academic activities data.
        :param campus_name: if None, the function will clear all the academic activities data.
        :return:
        """

    def clear_campus_names(self):
        if os.path.exists(Database.CAMPUS_NAMES_FILE_PATH):
            os.remove(Database.CAMPUS_NAMES_FILE_PATH)

    def check_if_courses_data_exists(self, courses: List[Course]) -> bool:
        pass

    def load_academic_activities_data(self, campus_name: str, courses: List[Course]) -> List[AcademicActivity]:
        pass

    def load_campus_names(self) -> List[str]:
        if not os.path.exists(Database.CAMPUS_NAMES_FILE_PATH):
            return []
        with open(Database.CAMPUS_NAMES_FILE_PATH, "r") as file:
            return file.read().splitlines()

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

    def get_common_campuses_names(self) -> List[str]:
        campus_names = []
        campus_names.append("מכון לב")
        campus_names.append("מכון טל")
        campus_names.append("מכון לוסטיג")
        campus_names.append("""מח"ר-טל תבונה""")
        campus_names.append("""מבח"ר בנים""")
        return campus_names
