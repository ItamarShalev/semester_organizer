import json
import os
import pathlib
import shutil
import sqlite3 as database
from collections import defaultdict
from contextlib import suppress
from sqlite3 import OperationalError
from typing import List, Optional, Dict, Tuple, Collection, Set

import utils
from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.course import Course
from data.course_choice import CourseChoice
from data.degree import Degree
from data.language import Language
from data.meeting import Meeting
from data.semester import Semester
from data.settings import Settings
from data.translation import _
from data.type import Type
from data.user import User

EnglishName = str
HebrewName = str


class Database:

    USER_NAME_FILE_PATH = os.path.join(utils.get_database_path(), "user_data.txt")
    YEARS_FILE_PATH = os.path.join(utils.get_database_path(), "years_data.txt")
    VERSIONS_PATH = os.path.join(utils.get_database_path(), "versions.txt")
    SETTINGS_FILE_PATH = os.path.join(utils.get_database_path(), "settings_data.txt")
    SHARED_DATABASE_PATH = os.path.join(utils.get_database_path(), "database.db")
    PERSONAL_DATABASE_PATH = os.path.join(utils.get_database_path(), "personal_database.db")
    COURSES_CHOOSE_PATH = os.path.join(utils.get_database_path(), "course_choose_user_input.txt")

    def __init__(self):
        self.logger = utils.get_logging()
        self._shared_sql_tables = [
            "degrees",
            "campuses",
            "degrees_courses",
            "lecturers",
            "courses_lecturers",
            "semesters_courses",
            "courses",
            "semesters",
            "activities",
        ]
        self._personal_sql_tables = [
            "personal_activities",
            "personal_meetings",
            "activities_can_enroll_in",
            "courses_already_done",
            "activities_tracks",
        ]

    def init_personal_database_tables(self):
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS personal_activities "
                           "(id INTEGER PRIMARY KEY, name TEXT UNIQUE);")

            cursor.execute("CREATE TABLE IF NOT EXISTS personal_meetings "
                           "(activity_id INTEGER, day INTEGER, start_time TEXT, end_time TEXT, "
                           "PRIMARY KEY (activity_id, day, start_time, end_time));")

            cursor.execute("CREATE TABLE IF NOT EXISTS activities_can_enroll_in "
                           "(activity_id TEXT PRIMARY KEY);")

            cursor.execute("CREATE TABLE IF NOT EXISTS courses_already_done "
                           "(parent_course_number INTEGER PRIMARY KEY);")

            cursor.execute("CREATE TABLE IF NOT EXISTS activities_tracks "
                           "(activity_id TEXT, track INTEGER, "
                           "PRIMARY KEY (activity_id, track));")

            connection.commit()
            cursor.close()

    def init_shared_database_tables(self):
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS campuses "
                           "(id INTEGER PRIMARY KEY, english_name TEXT, hebrew_name TEXT);")

            cursor.execute("CREATE TABLE IF NOT EXISTS semesters (id INTEGER PRIMARY KEY, name TEXT UNIQUE);")

            cursor.execute("CREATE TABLE IF NOT EXISTS semesters_courses "
                           "(semester_id INTEGER, course_id INTEGER, "
                           "FOREIGN KEY(course_id) REFERENCES courses(parent_course_number), "
                           "FOREIGN KEY(semester_id) REFERENCES semesters(id));")

            cursor.execute("CREATE TABLE IF NOT EXISTS courses "
                           "(name TEXT, course_number INTEGER, "
                           "parent_course_number INTEGER, language_value CHARACTER(2),"
                           "PRIMARY KEY(parent_course_number, language_value));")

            cursor.execute("CREATE TABLE IF NOT EXISTS meetings "
                           "(activity_id TEXT, day INTEGER, start_time TEXT, end_time TEXT, "
                           "language_value CHARACTER(2), "
                           "FOREIGN KEY(activity_id) REFERENCES activities(id), "
                           "PRIMARY KEY(activity_id, day, start_time, end_time, language_value));")

            cursor.execute("CREATE TABLE IF NOT EXISTS activities "
                           "(name TEXT, activity_type INTEGER, attendance_required BOOLEAN, lecturer_name TEXT, "
                           "course_number INTEGER, parent_course_number INTEGER, location TEXT, "
                           "activity_id TEXT, description TEXT, current_capacity INTEGER, "
                           "max_capacity INTEGER, actual_course_number INTEGER, campus_id INTEGER, "
                           "language_value CHARACTER(2),"
                           "FOREIGN KEY(campus_id) REFERENCES campuses(id), "
                           "FOREIGN KEY(lecturer_name) REFERENCES lecturers(name),"
                           "PRIMARY KEY(activity_id, campus_id, language_value));")

            cursor.execute("CREATE TABLE IF NOT EXISTS lecturers "
                           "(name TEXT PRIMARY KEY);")

            cursor.execute("CREATE TABLE IF NOT EXISTS courses_lecturers "
                           "(course_number INTEGER, parent_course_number INTEGER, lecturer_name TEXT, "
                           "is_lecture_rule BOOLEAN, campus_id INTEGER, language_value CHARACTER(2), "
                           "FOREIGN KEY(lecturer_name) REFERENCES lecturers(name), "
                           "FOREIGN KEY(campus_id) REFERENCES campuses(id), "
                           "PRIMARY KEY(course_number, parent_course_number, lecturer_name, "
                           "is_lecture_rule, campus_id, lecturer_name));")

            cursor.execute("CREATE TABLE IF NOT EXISTS degrees "
                           "(name TEXT PRIMARY KEY, department INTEGER);")

            cursor.execute("CREATE TABLE IF NOT EXISTS degrees_courses "
                           "(degree_name TEXT, parent_course_number INTEGER, "
                           "FOREIGN KEY(degree_name) REFERENCES degrees(name), "
                           "PRIMARY KEY(degree_name, parent_course_number));")

            connection.commit()
            cursor.close()

    def init_database_tables(self):
        self.init_shared_database_tables()
        self.init_personal_database_tables()

    def clear_activities_ids_tracks_can_enroll(self):
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM activities_can_enroll_in;")
            cursor.execute("DELETE FROM activities_tracks;")
            connection.commit()
            cursor.close()

    def load_degrees_courses(self) -> Dict[int, Set[Degree]]:
        degrees_courses = defaultdict(set)
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM degrees_courses;")
            for degree_name, course_number in cursor.fetchall():
                degrees_courses[course_number].add(Degree[degree_name])
            cursor.close()
        return degrees_courses

    def load_campus_id(self, campus_name: str):
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM campuses WHERE english_name = ? or hebrew_name = ?;",
                           (campus_name, campus_name))
            campus_id = cursor.fetchone()[0]
            return campus_id

    def save_semesters(self, semesters: List[Semester]):
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for semester in semesters:
                cursor.execute("INSERT OR IGNORE INTO semesters VALUES (?, ?);", (*semester, ))
            connection.commit()
            cursor.close()

    def save_activities_ids_groups_can_enroll_in(self, activities_can_enroll_in: Dict[str, Set[int]]):
        self.clear_activities_ids_tracks_can_enroll()
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for activity_id, tracks in activities_can_enroll_in.items():
                cursor.execute("INSERT INTO activities_can_enroll_in VALUES (?);", (activity_id, ))
                for track in tracks:
                    cursor.execute("INSERT INTO activities_tracks VALUES (?, ?);", (activity_id, track))
            connection.commit()
            cursor.close()

    def load_activities_ids_groups_can_enroll_in(self) -> Dict[str, Set[str]]:
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT activity_id FROM activities_can_enroll_in;")
            activities_can_enroll_in = {activity_id: set() for (activity_id,) in cursor.fetchall()}
            for activity_id, tracks in activities_can_enroll_in.items():
                cursor.execute("SELECT track FROM activities_tracks WHERE activity_id = ?;", (activity_id, ))
                tracks.update(track for (track,) in cursor.fetchall())
            cursor.close()
            return activities_can_enroll_in

    def save_degrees(self, degrees: List[Degree]):
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for degree in degrees:
                cursor.execute("INSERT OR IGNORE INTO degrees VALUES (?, ?);", (*degree, ))
            connection.commit()
            cursor.close()

    def load_degrees(self):
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM degrees;")
            degrees_values = cursor.fetchall()
            degrees = set()
            for name, department in degrees_values:
                degree = Degree[name]
                if degree.value != department:
                    raise ValueError("Degree department in database is different from the one in the code")
                degrees.add(degree)
            return degrees

    def load_semesters(self) -> List[Semester]:
        if not os.path.exists(self.SHARED_DATABASE_PATH):
            return []
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM semesters;")
            semesters = [Semester[semester_name.upper()] for (semester_name,) in cursor.fetchall()]
            cursor.close()
            return semesters

    def save_personal_activities(self, activities: List[Activity]):
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for activity in activities:
                cursor.execute("INSERT INTO personal_activities VALUES (?, ?);",
                               (activity.activity_id, activity.name))
                for meeting in activity.meetings:
                    cursor.execute("INSERT OR IGNORE INTO personal_meetings VALUES (?, ?, ?, ?);",
                                   (activity.activity_id, *meeting, ))
            connection.commit()
            cursor.close()

    def load_courses_choices(self, campus_name: str,
                             language: Language,
                             degrees: Set[Degree],
                             courses: List[Course] = None,
                             activities_ids: List[str] = None,
                             extract_unrelated_degrees: bool = False,
                             settings: Settings = None) -> Dict[str, CourseChoice]:
        """
        If courses is None - load all active courses
        If degrees is None - load default degrees
        """
        activities_ids = activities_ids or []
        assert extract_unrelated_degrees is bool(settings)
        assert degrees
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            courses = courses or self.load_active_courses(campus_name, language)
            courses_choices_data = defaultdict(lambda: (set(), set()))
            courses_choices = {}
            lecture_index = 0
            practice_index = 1
            degrees_text = f"({', '.join(['?'] * len(degrees))})"
            activities_ids_text = f"activities.activity_id IN ({', '.join(['?'] * len(activities_ids))})" \
                if activities_ids else "1"

            for course in courses:
                cursor.execute("SELECT degree_name FROM degrees_courses "
                               "WHERE parent_course_number = ?;", (course.parent_course_number,))
                courses_degrees = {Degree[degree_name] for (degree_name,) in cursor.fetchall()}

                unrelated_degrees_text = "0"
                if extract_unrelated_degrees:
                    if degrees - courses_degrees and not {settings.degree} & courses_degrees:
                        unrelated_degrees_text = "1"

                cursor.execute("SELECT courses_lecturers.lecturer_name, courses_lecturers.is_lecture_rule "
                               "FROM courses_lecturers "
                               "INNER JOIN degrees_courses "
                               "INNER JOIN activities "
                               "ON courses_lecturers.parent_course_number = degrees_courses.parent_course_number "
                               "AND courses_lecturers.parent_course_number = activities.parent_course_number "
                               "WHERE courses_lecturers.course_number = ? "
                               "AND courses_lecturers.parent_course_number = ? "
                               "AND courses_lecturers.campus_id = ? "
                               "AND courses_lecturers.language_value = ? "
                               f"AND degrees_courses.degree_name IN {degrees_text} "
                               f"AND (({activities_ids_text}) "
                               f"OR ({unrelated_degrees_text}));",
                               (course.course_number, course.parent_course_number, campus_id, language.short_name(),
                                *[degree.name for degree in degrees], *activities_ids))

                for lecturer_name, is_lecture_rule in cursor.fetchall():
                    index = lecture_index if is_lecture_rule else practice_index
                    courses_choices_data[course.name][index].add(lecturer_name)

                if course.name in courses_choices_data.keys():
                    courses_choices[course.name] = CourseChoice(course.name, course.parent_course_number,
                                                                *courses_choices_data[course.name])
            cursor.close()
            return courses_choices

    def load_personal_activities(self) -> List[Activity]:
        if not os.path.exists(self.PERSONAL_DATABASE_PATH):
            return []
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, name FROM personal_activities;")
            activities = [Activity.create_personal_from_database(activity_id, activity_name)
                          for activity_id, activity_name in cursor.fetchall()]

            for activity in activities:
                cursor.execute("SELECT * FROM personal_meetings "
                               "WHERE activity_id = ?;", (activity.activity_id, ))
                meetings = [Meeting(*data_line) for _activity_id, *data_line in cursor.fetchall()]
                activity.meetings = meetings
            cursor.close()
            return activities

    def save_courses(self, courses: List[Course], language: Language):
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for course in courses:
                cursor.execute("INSERT INTO courses VALUES (?, ?, ?, ?);", (*course, language.short_name()))
                for semester in course.semesters:
                    cursor.execute("INSERT INTO semesters_courses VALUES (?, ?);",
                                   (semester.value, course.parent_course_number))
                for degree in course.degrees:
                    cursor.execute("INSERT OR IGNORE INTO degrees_courses VALUES (?, ?);",
                                   (degree.name, course.parent_course_number))
            connection.commit()
            cursor.close()

    def load_courses(self, language: Language, degrees: Optional[Set[Degree]] = None) -> List[Course]:
        if not os.path.exists(self.SHARED_DATABASE_PATH):
            return []
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            degrees = degrees or Degree.get_defaults()
            degrees_text = f"({', '.join(['?'] * len(degrees))})"
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM courses "
                           "WHERE language_value = ?;", (language.short_name(),))
            courses = [Course(*data_line) for data_line in cursor.fetchall()]
            for course in courses:
                cursor.execute("SELECT name FROM semesters "
                               "INNER JOIN semesters_courses "
                               "INNER JOIN degrees_courses "
                               "ON semesters.id = semesters_courses.semester_id "
                               "AND semesters_courses.course_id = degrees_courses.parent_course_number "
                               "WHERE semesters_courses.course_id = ?"
                               f"AND degrees_courses.degree_name in {degrees_text};",
                               (course.parent_course_number, *[degree.name for degree in degrees]))
                course.semesters = [Semester[semester_name.upper()] for (semester_name,) in cursor.fetchall()]
            cursor.close()
            return courses

    def load_active_courses(self, campus_name: str, language: Language,
                            degrees: Collection[Degree] = None) -> List[Course]:
        if not os.path.exists(self.SHARED_DATABASE_PATH):
            return []
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            degrees = degrees or Degree.get_defaults()
            degrees_text = f"({', '.join(['?'] * len(degrees))})"
            cursor.execute("SELECT DISTINCT courses.* FROM courses "
                           "INNER JOIN activities "
                           "INNER JOIN degrees_courses "
                           "ON courses.parent_course_number = activities.parent_course_number "
                           "AND courses.course_number = activities.course_number AND "
                           "courses.language_value = activities.language_value "
                           "WHERE activities.campus_id = ? AND courses.language_value = ?"
                           f"AND degrees_courses.degree_name in {degrees_text};",
                           (campus_id, language.short_name(), *[degree.name for degree in degrees]))

            courses = [Course(*data_line) for data_line in cursor.fetchall()]
            cursor.close()
            return courses

    def load_activities_by_parent_courses_numbers(self, parent_courses_numbers: Set[int],
                                                  campus_name: str, language: Language,
                                                  degrees: Collection[Degree] = None) -> List[AcademicActivity]:
        if not os.path.exists(self.SHARED_DATABASE_PATH):
            return []
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            degrees = degrees or Degree.get_defaults()
            degrees_text = f"({', '.join(['?'] * len(degrees))})"
            parent_courses_numbers_text = f"({', '.join(['?'] * len(parent_courses_numbers))})"
            cursor.execute("SELECT DISTINCT activities.* FROM activities "
                           "INNER JOIN degrees_courses "
                           "ON activities.parent_course_number = degrees_courses.parent_course_number "
                           "WHERE activities.campus_id = ? AND activities.language_value = ? "
                           f"AND degrees_courses.degree_name in {degrees_text} "
                           f"AND activities.parent_course_number in {parent_courses_numbers_text};",
                           (campus_id, language.short_name(), *[degree.name for degree in degrees],
                            *parent_courses_numbers))
            activities = [AcademicActivity(*data_line) for *data_line, _campus_id, _language_value in cursor.fetchall()]
            for activity in activities:
                cursor.execute("SELECT * FROM meetings "
                               "WHERE activity_id = ? AND "
                               "language_value = ?;",
                               (activity.activity_id, language.short_name()))
                meetings = [Meeting(*data_line) for _activity_id, *data_line, _language_value in cursor.fetchall()]
                activity.meetings = meetings

            cursor.close()
            return activities

    def load_activities_by_courses_choices(self, courses_choices: Dict[str, CourseChoice],
                                           campus_name: str, language: Language,
                                           activities_ids: List[str] = None) -> List[AcademicActivity]:
        if not os.path.exists(self.SHARED_DATABASE_PATH):
            return []
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            activities_result = []
            activities_ids = activities_ids or []
            lecture_types = [Type.LECTURE, Type.SEMINAR]
            practice_types = [Type.PRACTICE, Type.LAB]
            activities_ids_text = f"activities.activity.id IN ({', '.join(['?'] * len(activities_ids))})" \
                if activities_ids else "1"
            for course_name, course_choice in courses_choices.items():
                lectures = course_choice.available_teachers_for_lecture
                practices = course_choice.available_teachers_for_practice
                hold_place_lectures = ",".join(["?"] * len(course_choice.available_teachers_for_lecture))
                hold_place_practices = ",".join(["?"] * len(course_choice.available_teachers_for_practice))
                is_not_null = "lecturer_name IS NOT NULL"

                text_hold_place_lectures = f"lecturer_name IN ({hold_place_lectures})" if lectures else is_not_null

                text_hold_place_practices = f"lecturer_name IN ({hold_place_practices})" if practices else is_not_null

                cursor.execute("SELECT * FROM activities "
                               f"WHERE name = ? AND {activities_ids_text} AND language_value = ? AND campus_id = ? AND "
                               f"((activity_type in (?, ?) AND {text_hold_place_lectures}) "
                               "OR "
                               f"(activity_type in (?, ?) AND {text_hold_place_practices}));",
                               (course_name, *activities_ids, language.short_name(), campus_id,
                                *lecture_types, *lectures,
                                *practice_types, *practices))

                activities = [AcademicActivity(*data_line) for *data_line, _campus_id, _language in cursor.fetchall()]

                for activity in activities:
                    if activity.type.is_lecture():
                        activity.attendance_required = course_choice.attendance_required_for_lecture
                    else:
                        activity.attendance_required = course_choice.attendance_required_for_practice
                    cursor.execute("SELECT * FROM meetings "
                                   "WHERE activity_id = ? AND language_value = ?;",
                                   (activity.activity_id, language.short_name()))
                    meetings = [Meeting(*data_line) for _activity_id, *data_line, _language_value in cursor.fetchall()]
                    activity.meetings = meetings

                activities_result.extend(activities)
            cursor.close()
            return activities_result

    def save_academic_activities(self, activities: List[AcademicActivity], campus_name: str, language: Language):
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            for activity in activities:
                cursor.execute("INSERT OR IGNORE INTO lecturers VALUES (?);", (activity.lecturer_name,))
                cursor.execute("INSERT INTO activities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                               (*activity, campus_id, language.short_name()))
                cursor.execute("INSERT OR IGNORE INTO courses_lecturers VALUES (?, ?, ?, ?, ?, ?);",
                               (activity.course_number, activity.parent_course_number, activity.lecturer_name,
                                activity.type.is_lecture(), campus_id, language.short_name()))
                for meeting in activity.meetings:
                    cursor.execute("INSERT OR IGNORE INTO meetings VALUES (?, ?, ?, ?, ?);",
                                   (activity.activity_id, *meeting, language.short_name()))

            connection.commit()
            cursor.close()

    def load_academic_activities(self, campus_name: str, language: Language,
                                 courses: List[Course], activities_ids: List[str] = None) -> List[AcademicActivity]:
        if not os.path.exists(self.SHARED_DATABASE_PATH):
            return []
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            activities_ids = activities_ids or []
            activities_ids_text = f"activities.activity.id IN ({', '.join(['?'] * len(activities_ids))})" \
                if activities_ids else "1"
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            courses_parent_numbers = [str(course.parent_course_number) for course in courses]
            cursor.execute("SELECT * FROM activities "
                           "WHERE campus_id = ? AND language_value = ? AND "
                           f"parent_course_number IN ({','.join(courses_parent_numbers)}) "
                           f"AND {activities_ids_text} ;",
                           (campus_id, language.short_name()))

            activities = [AcademicActivity(*data_line) for *data_line, _campus_id, _language in cursor.fetchall()]

            for activity in activities:
                cursor.execute("SELECT * FROM meetings "
                               "WHERE activity_id = ? AND "
                               "language_value = ?;",
                               (activity.activity_id, language.short_name()))
                meetings = [Meeting(*data_line) for _activity_id, *data_line, _language_value in cursor.fetchall()]
                activity.meetings = meetings
            cursor.close()
            return activities

    def save_campuses(self, campuses: Dict[int, Tuple[EnglishName, HebrewName]]):
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for campus_id, (english_name, hebrew_name) in campuses.items():
                cursor.execute("INSERT OR IGNORE INTO campuses VALUES (?, ?, ?);",
                               (campus_id, english_name, hebrew_name))
            connection.commit()
            cursor.close()

    def load_campus_names(self, language: Language = None) -> List[str]:
        if not os.path.exists(self.SHARED_DATABASE_PATH):
            return []
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            language = language or Language.get_current()
            cursor = connection.cursor()
            name_column = "english_name" if language is Language.ENGLISH else "hebrew_name"
            cursor.execute(f"SELECT {name_column} FROM campuses;")
            campus_names = [name[0] for name in cursor.fetchall()]
            cursor.close()
            return campus_names

    def load_campuses(self) -> Dict[int, Tuple[EnglishName, HebrewName]]:
        if not os.path.exists(self.SHARED_DATABASE_PATH):
            return {}
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM campuses;")
            campuses = {campus_id: (english_name, hebrew_name)
                        for campus_id, english_name, hebrew_name in cursor.fetchall()}
            cursor.close()
            return campuses

    def load_current_versions(self) -> Tuple[Optional[str], Optional[str]]:
        if not os.path.isfile(self.VERSIONS_PATH):
            return None, None
        with open(self.VERSIONS_PATH, "r", encoding=utils.ENCODING) as file:
            software_version, database_version = file.readlines()
            return software_version.strip(), database_version.strip()

    def save_current_versions(self, software_version: str, database_version: str):
        with open(self.VERSIONS_PATH, "w", encoding=utils.ENCODING) as file:
            file.write(f"{software_version}\n{database_version}")

    def get_language(self) -> Optional[Language]:
        settings = self.load_settings()
        return settings.language if settings else None

    def save_language(self, language: Language):
        settings = self.load_settings() or Settings()
        settings.language = language
        self.save_settings(settings)

    def save_courses_console_choose(self, courses_names: List[str]):
        with open(self.COURSES_CHOOSE_PATH, "w", encoding=utils.ENCODING) as file:
            file.write("\n".join(courses_names))

    def load_courses_console_choose(self) -> Optional[List[str]]:
        if not os.path.isfile(self.COURSES_CHOOSE_PATH):
            return None
        with open(self.COURSES_CHOOSE_PATH, "r", encoding=utils.ENCODING) as file:
            return [text.replace("\n", "") for text in file.readlines()]

    def load_user_data(self) -> Optional[User]:
        """
        This function is used to load the user data from the hard coded file.
        It will read from USER_NAME_FILE_PATH file that locate in the above.
        The format of the file is:
        username
        password
        :return: The user data or None if not found.
        """
        if not os.path.exists(self.USER_NAME_FILE_PATH):
            return None
        with open(self.USER_NAME_FILE_PATH, "r", encoding=utils.ENCODING) as file:
            return User(file.readline().strip(), file.readline().strip())

    def clear_versions(self):
        with suppress(Exception):
            os.remove(self.VERSIONS_PATH)

    def clear_all_data(self):
        self.clear_settings()
        self.clear_years()
        self.clear_shared_database()
        self.clear_last_courses_choose_input()
        self.clear_versions()

    def save_settings(self, settings: Settings):
        with open(self.SETTINGS_FILE_PATH, "w", encoding=utils.ENCODING) as file:
            file.write(settings.to_json())

    def load_settings(self) -> Optional[Settings]:
        if not os.path.exists(self.SETTINGS_FILE_PATH):
            return None
        with open(self.SETTINGS_FILE_PATH, "r", encoding=utils.ENCODING) as file:
            # pylint: disable=no-member
            return Settings.from_json(file.read())

    def clear_settings(self):
        if os.path.exists(self.SETTINGS_FILE_PATH):
            os.remove(self.SETTINGS_FILE_PATH)

    def get_common_campuses_names(self) -> List[str]:
        campus_names = []
        campus_names.append(_("Machon Lev"))
        campus_names.append(_("Machon Tal"))
        campus_names.append(_("Machon Lustig"))
        campus_names.append(_("Mahar-Tal"))
        campus_names.append(_("Mavchar- Men"))
        return campus_names

    def translate_campus_name(self, campus_name: str) -> str:
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT english_name, hebrew_name FROM campuses WHERE hebrew_name = ? or english_name = ?;",
                           (campus_name, campus_name))
            result = cursor.fetchone()
            if Language.get_current() is Language.HEBREW:
                campus_name = result[1]
            else:
                campus_name = result[0]
            cursor.close()
            return campus_name

    def save_years(self, years: Dict[int, str]):
        with open(self.YEARS_FILE_PATH, "w", encoding=utils.ENCODING) as file:
            file.write(json.dumps(years))

    def load_years(self):
        if not os.path.exists(self.YEARS_FILE_PATH):
            return {}
        with open(self.YEARS_FILE_PATH, "r", encoding=utils.ENCODING) as file:
            data = json.loads(file.read())
            return {int(key): value for key, value in data.items()}

    def clear_years(self):
        if os.path.exists(self.YEARS_FILE_PATH):
            os.remove(self.YEARS_FILE_PATH)

    def save_user_data(self, user_data: User):
        if user_data:
            with open(self.USER_NAME_FILE_PATH, "w", encoding=utils.ENCODING) as file:
                file.write(f"{user_data.username}\n{user_data.password}")

    def update_database(self, database_path: pathlib.Path):
        self.clear_shared_database()
        self.init_database_tables()
        shutil.copy2(database_path, self.SHARED_DATABASE_PATH)

    def _are_tables_exists(self, tables_names: List[str], database_path: str):
        if not os.path.exists(database_path):
            return False
        with database.connect(database_path) as connection:
            cursor = connection.cursor()
            all_exists = True
            for table_name in tables_names:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name= ?;", (table_name,))
                all_exists = all_exists and bool(cursor.fetchone())
            cursor.close()
            return all_exists

    def are_shared_tables_exists(self):
        return self._are_tables_exists(self._shared_sql_tables, self.SHARED_DATABASE_PATH)

    def are_personal_tables_exists(self):
        return self._are_tables_exists(self._personal_sql_tables, self.PERSONAL_DATABASE_PATH)

    def _clear_database(self, tables_names: List[str], database_path: str):
        if not os.path.exists(database_path):
            return
        with database.connect(database_path) as connection:
            cursor = connection.cursor()
            for table_name in tables_names:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            cursor.close()

    def clear_shared_database(self):
        self._clear_database(self._shared_sql_tables, self.SHARED_DATABASE_PATH)

    def clear_personal_database(self):
        self._clear_database(self._personal_sql_tables, self.PERSONAL_DATABASE_PATH)

    def clear_last_courses_choose_input(self):
        if os.path.exists(self.COURSES_CHOOSE_PATH):
            os.remove(self.COURSES_CHOOSE_PATH)

    def save_courses_already_done(self, courses: Set[Course]):
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for course in courses:
                cursor.execute("INSERT OR IGNORE INTO courses_already_done (parent_course_number) VALUES (?);",
                               (course.parent_course_number,))
            cursor.close()

    def load_courses_already_done(self, language: Language) -> Set[Course]:
        parent_courses_numbers = None
        courses = None
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT * FROM courses_already_done;")
            except OperationalError:
                return set()
            parent_courses_numbers = {parent_course_number for (parent_course_number,) in cursor.fetchall()}
            cursor.close()
        if not parent_courses_numbers:
            return set()
        with database.connect(self.SHARED_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM courses "
                           "WHERE language_value = ? "
                           "AND parent_course_number IN (" + ", ".join(["?"] * len(parent_courses_numbers)) + ");",
                           (language.short_name(), *parent_courses_numbers))
            courses = {Course(*course_data) for *course_data, _language_value in cursor.fetchall()}
            cursor.close()
            return courses

    def clear_courses_already_done(self):
        with database.connect(self.PERSONAL_DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM courses_already_done;")
            cursor.close()
