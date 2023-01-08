import os
from contextlib import suppress

from pytest import fixture

import utils
from collector.db.db import Database
from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.course import Course
from data.course_choice import CourseChoice
from data.language import Language
from data.semester import Semester
from data.settings import Settings
from data.type import Type
from data.user import User
from data.output_format import OutputFormat


class TestDatabase:

    @fixture
    def database(self):
        Database.USER_NAME_FILE_PATH = os.path.join(utils.get_database_path(), "test_user_data.txt")
        Database.YEARS_FILE_PATH = os.path.join(utils.get_database_path(), "test_years_data.txt")
        Database.VERSIONS_PATH = os.path.join(utils.get_database_path(), "test_versions.txt")
        Database.SETTINGS_FILE_PATH = os.path.join(utils.get_database_path(), "test_settings_data.txt")
        Database.DATABASE_PATH = os.path.join(utils.get_database_path(), "test_database.db")

        with suppress(Exception):
            os.remove(Database.DATABASE_PATH)

        with suppress(Exception):
            os.remove(Database.USER_NAME_FILE_PATH)

        database = Database()
        database.clear_all_data()
        database.init_database_tables()
        return database

    @fixture
    def campuses(self, database):
        campuses = {
            1: ("A", "א"),
            2: ("B", "ב"),
            3: ("C", "ג"),
        }
        database.save_campuses(campuses)
        return campuses

    def test_campuses(self, database):

        campuses = {
            1: ("A", "א"),
            2: ("B", "ב"),
            3: ("C", "ג"),
        }
        database.save_campuses(campuses)
        assert database.load_campus_names(Language.HEBREW) == ["א", "ב", "ג"]
        assert database.load_campus_names(Language.ENGLISH) == ["A", "B", "C"]

    def test_semesters(self, database):
        semesters = list(Semester)
        database.save_semesters(semesters)

        assert set(semesters) == set(database.load_semesters())

    def test_courses(self, database):
        hebrew_courses = [Course(f"קורס {i}", i, i + 1000, semesters=Semester.ANNUAL) for i in range(10)]
        database.save_courses(hebrew_courses, Language.HEBREW)

        english_courses = [Course(f"course {i}", i, i + 1000) for i in range(10)]
        database.save_courses(english_courses, Language.ENGLISH)

        assert set(hebrew_courses) == set(database.load_courses(Language.HEBREW))
        assert set(english_courses) == set(database.load_courses(Language.ENGLISH))

    def test_personal_activities(self, database):
        activity = Activity("my activity")
        database.save_personal_activities([activity])
        loaded = database.load_personal_activities()
        assert loaded == [activity]

    def test_activities(self, database, campuses):
        campus_name = "A"
        academic_activity = AcademicActivity("name", Type.LECTURE, True, "meir", 12, 232, "", "12.23", "", 0, 100, 1213)
        database.save_academic_activities([academic_activity], campus_name, Language.ENGLISH)
        loaded = database.load_academic_activities(campus_name, Language.ENGLISH, [Course("name", 12, 232)])
        assert loaded == [academic_activity]

    def test_course_choices(self, database, campuses):
        campus_name = "A"
        courses = [Course(f"Course {i}", i, i + 1000) for i in range(10)]
        database.save_courses(courses, Language.ENGLISH)
        activities = [AcademicActivity(f"Course {i}", Type.LECTURE, True, "meir", i, i + 1000, "", f"3{i}", "", 0, 1, 0)
                      for i in range(10)]
        database.save_academic_activities(activities, campus_name, Language.ENGLISH)
        loaded_courses_choices = database.load_courses_choices(campus_name, Language.ENGLISH)
        excepted_courses_choices = [CourseChoice(f"Course {i}", ["meir"], []) for i in range(10)]
        assert set(loaded_courses_choices.values()) == set(excepted_courses_choices)

    def test_load_activities_by_courses_choices(self, database, campuses):
        campus_name = "A"
        language = Language.ENGLISH
        courses = [Course(f"Cor {i}", i, i + 10) for i in range(10)]
        database.save_courses(courses, language)

        def create_activity(i):
            return AcademicActivity(f"Cor {i}", Type.LECTURE, True, f"meir{i}", i, i + 10, "", f"12.23{i}", "", 0, 1, 0)

        activities = [create_activity(i) for i in range(10)]

        courses_choices_excepted = {"Cor 5": CourseChoice("Cor 5", ["meir5"], [])}
        courses_choices = {"Cor 1": CourseChoice("Cor 1", ["meir0"], [])}
        courses_choices.update(courses_choices_excepted)

        database.save_academic_activities(activities, campus_name, language)
        loaded_courses_choices = database.load_activities_by_courses_choices(courses_choices, campus_name, language)
        assert loaded_courses_choices == [create_activity(5)]

    def test_all(self, database):
        database.clear_all_data()
        database.init_database_tables()
        assert not database.load_settings()
        assert not database.load_campus_names(Language.ENGLISH)

    def test_user_data(self, database):
        user = User("username", "password")

        database.save_user_data(user)

        loaded_user = database.load_user_data()
        assert user == loaded_user

        os.remove(Database.USER_NAME_FILE_PATH)
        assert database.load_user_data() is None

    def test_settings(self, database):
        database.clear_settings()
        assert database.load_settings() is None

        settings = Settings()
        settings.campus_name = "בדיקה"
        settings.year = 2020
        settings.output_formats = [OutputFormat.EXCEL]
        database.save_settings(settings)
        assert database.load_settings() == settings

        database.clear_settings()
        assert database.load_settings() is None

    def test_years(self, database):
        database.clear_years()
        assert not database.load_years()

        years = {30: "אאא"}
        database.save_years(years)

        assert years == database.load_years()

        database.clear_years()
        assert not database.load_years()
