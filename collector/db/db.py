import os
import sqlite3 as database
from typing import List, Optional

import utils
from data.academic_activity import AcademicActivity
from data.course import Course
from data.user import User
from data.type import Type
from data.day import Day
from data.meeting import Meeting


class Database:
    USER_NAME_FILE_PATH = os.path.join(utils.get_database_path(), "user_data.txt")
    CAMPUS_NAMES_FILE_PATH = os.path.join(utils.get_database_path(), "campus_names.txt")
    COURSES_DATA_FILE_PATH = os.path.join(utils.get_database_path(), "courses_data.txt")
    ACTIVITIES_DATA_DATABASE_PATH = os.path.join(utils.get_database_path(), "activities_data.db")

    def save_courses_data(self, courses: List[Course]):
        courses_set = set(courses)
        courses_set.update(set(self.load_courses_data()))
        with open(Database.COURSES_DATA_FILE_PATH, "w") as file:
            for course in courses_set:
                file.write(f"{course.name};{course.course_number};{course.parent_course_number}\n")

    def save_academic_activities_data(self, campus_name: str, academic_activities: List[AcademicActivity]):
        activities_names = {activity.name: activity for activity in academic_activities}
        was_exists = os.path.exists(Database.ACTIVITIES_DATA_DATABASE_PATH)
        with database.connect(Database.ACTIVITIES_DATA_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            # Create the table if not exists.
            if not was_exists:
                cursor.execute("CREATE TABLE activities (activity_id TEXT PRIMARY KEY, campus_name TEXT, "
                               "activity_name TEXT, type INTEGER ,course_number INTEGER, lecturer TEXT, "
                               "parent_course_number INTEGER, location TEXT);")
                cursor.execute("CREATE TABLE meetings (day INTEGER, start_time TEXT, end_time TEXT, activity_id TEXT, "
                               "FOREIGN KEY(activity_id) REFERENCES activities(activity_id) ON DELETE CASCADE);")

            # Delete all the activities that inside with the same name, to avoid old data.
            for activity_name in activities_names:
                cursor.execute("DELETE FROM activities WHERE campus_name = (?) AND activity_name = (?);",
                               (campus_name, activity_name))

            # Insert the new data.
            for activity in academic_activities:
                cursor.execute("INSERT INTO activities VALUES (?, ?, ?, ?, ?, ?, ?, ?);", (
                    activity.activity_id, campus_name, activity.name, activity.type.value, activity.course_number,
                    activity.lecturer_name, activity.parent_course_number, activity.location))
                for meeting in activity.get_meetings():
                    cursor.execute("INSERT INTO meetings VALUES (?, ?, ?, ?);", (
                        meeting.day.value, meeting.get_string_start_time(), meeting.get_string_end_time(),
                        activity.activity_id))
            connection.commit()
            cursor.close()

    def save_campus_names(self, names: List[str]):
        with open(Database.CAMPUS_NAMES_FILE_PATH, "w") as file:
            file.write("\n".join(names))

    def load_courses_data(self) -> List[Course]:
        if not os.path.isfile(Database.COURSES_DATA_FILE_PATH):
            return []
        with open(Database.COURSES_DATA_FILE_PATH, "r") as file:
            courses = []
            for line in file:
                line = line.strip()
                if line == "":
                    continue
                course_name, course_number, parent_course_number = line.split(";")
                course = Course(course_name, int(course_number), int(parent_course_number))
                courses.append(course)
            return courses

    def clear_courses_data(self):
        if os.path.exists(Database.COURSES_DATA_FILE_PATH):
            os.remove(Database.COURSES_DATA_FILE_PATH)

    def clear_academic_activities_data(self, campus_name: Optional[str] = None):
        """
        The function clears the academic activities data.
        :param campus_name: if None, the function will clear all the academic activities data.
        :return:
        """
        # If the database not exists, there is nothing to clear.
        if not os.path.isfile(Database.ACTIVITIES_DATA_DATABASE_PATH):
            return
        if campus_name is None:
            with database.connect(Database.ACTIVITIES_DATA_DATABASE_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM meetings;")
                cursor.execute("DELETE FROM activities;")
                connection.commit()
                cursor.close()
        else:
            with database.connect(Database.ACTIVITIES_DATA_DATABASE_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM activities WHERE campus_name = (?);", (campus_name,))
                connection.commit()
                cursor.close()

    def clear_campus_names(self):
        if os.path.exists(Database.CAMPUS_NAMES_FILE_PATH):
            os.remove(Database.CAMPUS_NAMES_FILE_PATH)

    def check_if_courses_data_exists(self, campus_name: str, courses: List[Course]) -> bool:
        return bool(self.load_academic_activities_data(campus_name, courses))

    def load_academic_activities_data(self, campus_name: str, courses: List[Course]) -> List[AcademicActivity]:
        """
        The function loads the academic activities data from the database.
        if the database does not exist, the function will return an empty list.
        if courses is empty, the function will return all the academic activities data by campus name.
        else the function will return the academic activities data by the campus name and the courses' names.
        """

        # If the database does not exist, return an empty list.
        if not os.path.exists(Database.ACTIVITIES_DATA_DATABASE_PATH):
            return []
        activities = []
        with database.connect(Database.ACTIVITIES_DATA_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            # If courses is empty, return all the academic activities data by campus name.
            if not courses:
                cursor.execute("SELECT * FROM activities WHERE campus_name = (?);", campus_name)
            else:
                # Else, return the academic activities data by the campus name and the courses' names.
                courses_names = [course.name for course in courses]
                sql = f"SELECT * FROM activities WHERE campus_name = (?) AND activity_name IN " \
                      f"({','.join(['?'] * len(courses_names))});"
                cursor.execute(sql, (campus_name, *courses_names))

            # Parse the data.
            activities_data = cursor.fetchall()

            for activity_data in activities_data:
                activity_id, __, name, activity_type, course_number, lecturer, p_course_number, location = activity_data
                activity = AcademicActivity(name, Type(activity_type), True, lecturer, course_number, p_course_number,
                                            location, activity_id)
                cursor.execute("SELECT * FROM meetings WHERE activity_id = (?);", (activity_id,))
                meetings_data = cursor.fetchall()
                # Parse the meetings data.
                for meeting_data in meetings_data:
                    day, start_time, end_time, activity_id = meeting_data
                    if activity_id == activity.activity_id:
                        meeting = Meeting(Day(day), Meeting.str_to_time(start_time), Meeting.str_to_time(end_time))
                        activity.add_slot(meeting)
                activities.append(activity)
            cursor.close()
        return activities

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
