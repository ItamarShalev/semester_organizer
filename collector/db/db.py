import json
import os
import pathlib
import shutil
import sqlite3 as database
import time
from collections import defaultdict
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
    DATABASE_PATH = os.path.join(utils.get_database_path(), "database.db")
    COURSES_CHOOSE_PATH = os.path.join(utils.get_database_path(), "course_choose_user_input.txt")

    def __init__(self):
        self.logger = utils.get_logging()
        self._all_sql_tables = ["degrees",
                                "campuses",
                                "degrees_courses",
                                "lecturers",
                                "courses_lecturers",
                                "semesters_courses",
                                "courses",
                                "semesters",
                                "personal_activities_meetings",
                                "personal_activities",
                                "activities_meetings",
                                "activities",
                                "meetings"]

    def init_database_tables(self):
        with database.connect(self.DATABASE_PATH) as connection:
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

            cursor.execute("CREATE TABLE IF NOT EXISTS personal_activities "
                           "(id INTEGER PRIMARY KEY, name TEXT UNIQUE);")

            cursor.execute("CREATE TABLE IF NOT EXISTS meetings "
                           "(id INTEGER PRIMARY KEY, day INTEGER, start_time TEXT, end_time TEXT);")

            cursor.execute("CREATE TABLE IF NOT EXISTS personal_activities_meetings "
                           "(acitivity_id INTEGER, meeting_id INTEGER, "
                           "FOREIGN KEY(acitivity_id) REFERENCES personal_activities(id), "
                           "FOREIGN KEY(meeting_id) REFERENCES meetings(id));")

            cursor.execute("CREATE TABLE IF NOT EXISTS activities "
                           "(name TEXT, activity_type INTEGER, attendance_required BOOLEAN, lecturer_name TEXT, "
                           "course_number INTEGER, parent_course_number INTEGER, location TEXT, "
                           "activity_id TEXT, description TEXT, current_capacity INTEGER, "
                           "max_capacity INTEGER, actual_course_number INTEGER, campus_id INTEGER, "
                           "language_value CHARACTER(2),"
                           "FOREIGN KEY(campus_id) REFERENCES campuses(id), "
                           "FOREIGN KEY(lecturer_name) REFERENCES lecturers(name),"
                           "PRIMARY KEY(activity_id, campus_id, language_value));")

            cursor.execute("CREATE TABLE IF NOT EXISTS activities_meetings "
                           "(activity_id TEXT, meeting_id INTEGER, campus_id INTEGER, language_value CHARACTER(2), "
                           "FOREIGN KEY(activity_id) REFERENCES activities(activity_id), "
                           "FOREIGN KEY(meeting_id) REFERENCES meetings(id), "
                           "PRIMARY KEY(activity_id, meeting_id, campus_id, language_value));")

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

    def load_campus_id(self, campus_name: str):
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM campuses WHERE english_name = ? or hebrew_name = ?;",
                           (campus_name, campus_name))
            campus_id = cursor.fetchone()[0]
            return campus_id

    def save_semesters(self, semesters: List[Semester]):
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for semester in semesters:
                cursor.execute("INSERT OR IGNORE INTO semesters VALUES (?, ?);", (*semester, ))
            connection.commit()
            cursor.close()

    def save_degrees(self, degrees: List[Degree]):
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for degree in degrees:
                cursor.execute("INSERT OR IGNORE INTO degrees VALUES (?, ?);", (*degree, ))
            connection.commit()
            cursor.close()

    def load_semesters(self) -> List[Semester]:
        if not os.path.exists(self.DATABASE_PATH):
            return []
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM semesters;")
            semesters = [Semester[semester_name.upper()] for (semester_name,) in cursor.fetchall()]
            cursor.close()
            return semesters

    def save_personal_activities(self, activities: List[Activity]):
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for activity in activities:
                cursor.execute("INSERT OR IGNORE INTO personal_activities VALUES (?, ?);",
                               (activity.activity_id, activity.name))
                for meeting in activity.meetings:
                    cursor.execute("INSERT OR IGNORE INTO meetings VALUES (?, ?, ?, ?);", (*meeting, ))
                    cursor.execute("INSERT OR IGNORE INTO personal_activities_meetings VALUES (?, ?);",
                                   (activity.activity_id, meeting.meeting_id))
            connection.commit()
            cursor.close()

    def load_courses_choices(self, campus_name: str,
                             language: Language, courses: List[Course] = None,
                             degrees: Set[Degree] = None) -> Dict[str, CourseChoice]:
        """
        If courses is None - load all active courses
        If degrees is None - load default degrees
        """
        degrees = degrees or Degree.get_defaults()
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            courses = courses or self.load_active_courses(campus_name, language)
            courses_choices_data = defaultdict(lambda: (set(), set()))
            lecture_index = 0
            practice_index = 1
            degrees_text = f"({', '.join(['?'] * len(degrees))})"

            for course in courses:
                cursor.execute("SELECT lecturer_name, is_lecture_rule FROM courses_lecturers "
                               "INNER JOIN degrees_courses "
                               "ON courses_lecturers.parent_course_number = degrees_courses.parent_course_number "
                               "WHERE courses_lecturers.course_number = ? "
                               "AND courses_lecturers.parent_course_number = ? "
                               "AND courses_lecturers.campus_id = ? "
                               "AND courses_lecturers.language_value = ? "
                               f"AND degrees_courses.degree_name IN {degrees_text} ;",
                               (course.course_number, course.parent_course_number, campus_id, language.short_name(),
                                *[degree.name for degree in degrees]))

                for lecturer_name, is_lecture_rule in cursor.fetchall():
                    index = lecture_index if is_lecture_rule else practice_index
                    courses_choices_data[course.name][index].add(lecturer_name)

            courses_choices = {course_name: CourseChoice(course_name, list(lectures), list(practices))
                               for course_name, (lectures, practices) in courses_choices_data.items()}
            cursor.close()
            return courses_choices

    def load_personal_activities(self) -> List[Activity]:
        if not os.path.exists(self.DATABASE_PATH):
            return []
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, name FROM personal_activities;")
            activities = [Activity.create_personal_from_database(activity_id, activity_name)
                          for activity_id, activity_name in cursor.fetchall()]

            for activity in activities:
                cursor.execute("SELECT meetings.* FROM meetings "
                               "INNER JOIN personal_activities_meetings "
                               "ON meetings.id = personal_activities_meetings.meeting_id "
                               "WHERE personal_activities_meetings.acitivity_id = ?;", (activity.activity_id,))
                meetings = [Meeting.create_meeting_from_database(*data_line) for data_line in cursor.fetchall()]
                activity.meetings = meetings
            cursor.close()
            return activities

    def save_courses(self, courses: List[Course], language: Language):
        with database.connect(self.DATABASE_PATH) as connection:
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
        if not os.path.exists(self.DATABASE_PATH):
            return []
        with database.connect(self.DATABASE_PATH) as connection:
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
        if not os.path.exists(self.DATABASE_PATH):
            return []
        with database.connect(self.DATABASE_PATH) as connection:
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

    def load_activities_by_courses_choices(self, courses_choices: Dict[str, CourseChoice], campus_name: str,
                                           language: Language) -> List[AcademicActivity]:
        if not os.path.exists(self.DATABASE_PATH):
            return []
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            activities_result = []
            lecture_types = [Type.LECTURE, Type.SEMINAR]
            practice_types = [Type.PRACTICE, Type.LAB]
            for course_name, course_choice in courses_choices.items():
                lectures = course_choice.available_teachers_for_lecture
                practices = course_choice.available_teachers_for_practice
                hold_place_lectures = ",".join(["?"] * len(course_choice.available_teachers_for_lecture))
                hold_place_practices = ",".join(["?"] * len(course_choice.available_teachers_for_practice))
                is_not_null = "lecturer_name IS NOT NULL"

                text_hold_place_lectures = f"lecturer_name IN ({hold_place_lectures})" if lectures else is_not_null

                text_hold_place_practices = f"lecturer_name IN ({hold_place_practices})" if practices else is_not_null

                cursor.execute("SELECT * FROM activities "
                               "WHERE name = ? AND language_value = ? AND campus_id = ? AND "
                               f"((activity_type in (?, ?) AND {text_hold_place_lectures}) "
                               "OR "
                               f"(activity_type in (?, ?) AND {text_hold_place_practices}));",
                               (course_name, language.short_name(), campus_id,
                                *lecture_types, *lectures,
                                *practice_types, *practices))

                activities = [AcademicActivity(*data_line) for *data_line, _campus_id, _language in cursor.fetchall()]

                for activity in activities:
                    if activity.type.is_lecture():
                        activity.attendance_required = course_choice.attendance_required_for_lecture
                    else:
                        activity.attendance_required = course_choice.attendance_required_for_practice
                    cursor.execute("SELECT meetings.* FROM meetings "
                                   "INNER JOIN activities_meetings "
                                   "ON meetings.id = activities_meetings.meeting_id "
                                   "WHERE activities_meetings.activity_id = ? AND "
                                   "activities_meetings.campus_id = ? AND "
                                   "activities_meetings.language_value = ?;",
                                   (activity.activity_id, campus_id, language.short_name()))
                    meetings = [Meeting.create_meeting_from_database(*data_line) for data_line in cursor.fetchall()]
                    activity.meetings = meetings

                activities_result.extend(activities)
            cursor.close()
            return activities_result

    def save_academic_activities(self, activities: List[AcademicActivity], campus_name: str, language: Language):
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            for activity in activities:
                cursor.execute("INSERT OR IGNORE INTO lecturers VALUES (?);", (activity.lecturer_name,))
                cursor.execute("INSERT OR IGNORE INTO activities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                               (*activity, campus_id, language.short_name()))
                cursor.execute("INSERT OR IGNORE INTO courses_lecturers VALUES (?, ?, ?, ?, ?, ?);",
                               (activity.course_number, activity.parent_course_number, activity.lecturer_name,
                                activity.type.is_lecture(), campus_id, language.short_name()))
                for meeting in activity.meetings:
                    cursor.execute("INSERT OR IGNORE INTO meetings VALUES (?, ?, ?, ?);", (*meeting,))
                    cursor.execute("INSERT OR IGNORE INTO activities_meetings VALUES (?, ?, ?,  ?);",
                                   (activity.activity_id, meeting.meeting_id, campus_id, language.short_name()))
            connection.commit()
            cursor.close()

    def load_academic_activities(self, campus_name: str, language: Language,
                                 courses: List[Course]) -> List[AcademicActivity]:
        if not os.path.exists(self.DATABASE_PATH):
            return []
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            campus_id = self.load_campus_id(campus_name)
            courses_parent_numbers = [str(course.parent_course_number) for course in courses]
            cursor.execute("SELECT * FROM activities "
                           "WHERE campus_id = ? AND language_value = ? AND "
                           f"parent_course_number IN ({','.join(courses_parent_numbers)});",
                           (campus_id, language.short_name()))

            activities = [AcademicActivity(*data_line) for *data_line, _campus_id, _language in cursor.fetchall()]

            for activity in activities:
                cursor.execute("SELECT meetings.* FROM meetings "
                               "INNER JOIN activities_meetings "
                               "ON meetings.id = activities_meetings.meeting_id "
                               "WHERE activities_meetings.activity_id = ? AND "
                               "activities_meetings.campus_id = ? AND "
                               "activities_meetings.language_value = ?;",
                               (activity.activity_id, campus_id, language.short_name()))
                meetings = [Meeting.create_meeting_from_database(*data_line) for data_line in cursor.fetchall()]
                activity.meetings = meetings
            cursor.close()
            return activities

    def save_campuses(self, campuses: Dict[int, Tuple[EnglishName, HebrewName]]):
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for campus_id, (english_name, hebrew_name) in campuses.items():
                cursor.execute("INSERT OR IGNORE INTO campuses VALUES (?, ?, ?);",
                               (campus_id, english_name, hebrew_name))
            connection.commit()
            cursor.close()

    def load_campus_names(self, language: Language = None) -> List[str]:
        if not os.path.exists(self.DATABASE_PATH):
            return []
        with database.connect(self.DATABASE_PATH) as connection:
            language = language or Language.get_current()
            cursor = connection.cursor()
            name_column = "english_name" if language is Language.ENGLISH else "hebrew_name"
            cursor.execute(f"SELECT {name_column} FROM campuses;")
            campus_names = [name[0] for name in cursor.fetchall()]
            cursor.close()
            return campus_names

    def load_campuses(self) -> Dict[int, Tuple[EnglishName, HebrewName]]:
        if not os.path.exists(self.DATABASE_PATH):
            return {}
        with database.connect(self.DATABASE_PATH) as connection:
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

    def load_courses_console_choose(self) -> Optional[list[str]]:
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

    def clear_all_data(self):
        self.clear_settings()
        self.clear_years()
        self.clear_database()
        self.clear_last_courses_choose_input()

    def save_settings(self, settings: Settings):
        with open(self.SETTINGS_FILE_PATH, "w", encoding=utils.ENCODING) as file:
            file.write(settings.to_json())

    def load_settings(self) -> Optional[Settings]:
        if not os.path.exists(self.SETTINGS_FILE_PATH):
            return None
        with open(self.SETTINGS_FILE_PATH, "r", encoding=utils.ENCODING) as file:
            # pylint: disable=no-member
            return Settings.from_json(file.read())

    def _get_last_modified_by_days(self, file_path: str) -> int:
        if not os.path.exists(file_path):
            return 0
        last_modified = os.path.getmtime(file_path)
        return int((time.time() - last_modified) / 60 / 60 / 24)

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
        with database.connect(self.DATABASE_PATH) as connection:
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
        self.clear_database()
        self.init_database_tables()
        shutil.copy2(database_path, self.DATABASE_PATH)

    def is_all_tables_exists(self):
        if not os.path.exists(self.DATABASE_PATH):
            return False
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            all_exists = True
            for table_name in self._all_sql_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name= ?;", (table_name,))
                all_exists = all_exists and bool(cursor.fetchone())
            cursor.close()
            return all_exists

    def clear_database(self):
        if not os.path.exists(self.DATABASE_PATH):
            return
        with database.connect(self.DATABASE_PATH) as connection:
            cursor = connection.cursor()
            for table_name in self._all_sql_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            cursor.close()

    def clear_last_courses_choose_input(self):
        if os.path.exists(self.COURSES_CHOOSE_PATH):
            os.remove(self.COURSES_CHOOSE_PATH)
