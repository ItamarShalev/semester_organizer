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
from data.day import Day
from data.meeting import Meeting
from data.output_format import OutputFormat


class TestDatabase:

    @fixture
    def database(self):
        Database.YEARS_FILE_PATH = os.path.join(utils.get_database_path(), "test_years_data.txt")
        Database.VERSIONS_PATH = os.path.join(utils.get_database_path(), "test_versions.txt")
        Database.SETTINGS_FILE_PATH = os.path.join(utils.get_database_path(), "test_settings_data.txt")
        Database.CAMPUS_NAMES_FILE_PATH = os.path.join(utils.get_database_path(), "test_campus_names.txt")
        Database.COURSES_DATA_FILE_PATH = os.path.join(utils.get_database_path(), "test_courses_data.txt")
        Database.ACTIVITIES_DATA_DATABASE_PATH = os.path.join(utils.get_database_path(), "test_activities_data.db")
        Database.DATABASE_PATH = os.path.join(utils.get_database_path(), "test_database.db")

        with suppress(Exception):
            os.remove(Database.DATABASE_PATH)

        with suppress(Exception):
            os.remove(Database.ACTIVITIES_DATA_DATABASE_PATH)

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

    def test_load_active_courses(self, database, campuses):
        campus_name = "A"
        active_courses = [Course(f"course {i}", i, i + 1000) for i in range(10)]
        non_active_courses = [Course(f"course {i}", i, i + 1000) for i in range(20, 30)]
        all_courses = active_courses + non_active_courses
        database.save_courses(all_courses, Language.ENGLISH)
        database.save_active_courses(active_courses, campus_name, Language.ENGLISH)

        assert set(active_courses) == set(database.load_active_courses(campus_name, Language.ENGLISH))

    def test_course_choices(self, database, campuses):
        campus_name = "A"
        courses = [Course(f"Course {i}", i, i + 1000) for i in range(10)]
        database.save_courses(courses, Language.ENGLISH)
        database.save_active_courses(courses, campus_name, Language.ENGLISH)
        activities = [AcademicActivity(f"Course {i}", Type.LECTURE, True, "meir", i, i + 1000, "", "12.23", "", 0, 1, 0)
                      for i in range(10)]
        database.save_academic_activities(activities, campus_name, Language.ENGLISH)
        loaded_courses_choices = database.load_courses_choices(campus_name, Language.ENGLISH)
        excepted_courses_choices = [CourseChoice(f"Course {i}", ["meir"], []) for i in range(10)]
        assert set(loaded_courses_choices.values()) == set(excepted_courses_choices)

    def test_all(self):
        database = Database()
        database.clear_all_data()
        database.init_database_tables()
        assert not database.load_settings()
        assert not database.load_campus_names(Language.ENGLISH)
        assert not database.load_courses_data()
        assert not database.load_academic_activities_data(utils.get_campus_name_test(), [])

    def test_courses_data(self):
        database = Database()
        courses = [Course(f"Course {i}", i, i + 1000) for i in range(10)]
        database.clear_courses_data()
        database.save_courses_data(courses)
        loaded_courses = database.load_courses_data()
        assert set(courses) == set(loaded_courses)

        database.clear_courses_data()
        assert not database.load_courses_data()

    def test_academic_activities(self):
        database = Database()
        academic_activities = []
        campus_name = utils.get_campus_name_test()
        for i in range(10):
            academic_activity = AcademicActivity(f"name{i}", Type.LECTURE, True, campus_name, i, i + 1000, "a", str(i))
            academic_activities.append(academic_activity)
        academic_activities[0].add_slot(Meeting(Day.MONDAY, "10:00", "12:00"))
        courses = AcademicActivity.extract_courses_data(academic_activities)
        database.clear_academic_activities_data()
        database.save_academic_activities_data(campus_name, academic_activities)
        assert database.check_if_courses_data_exists(campus_name, courses)

        loaded_academic_activities = database.load_academic_activities_data(campus_name, courses)
        assert set(academic_activities).issubset(set(loaded_academic_activities))

        database.clear_campus_names()
        assert not database.load_campus_names()

        database.save_academic_activities_data(campus_name, academic_activities)
        academic_activities[0].type = Type.LAB
        academic_activities.append(
            AcademicActivity(f"Course {30}", Type.LECTURE, True, f"A {30}", 30, 30 + 1000, "", activity_id=f"{30}"))
        database.save_academic_activities_data(campus_name, academic_activities)
        courses.clear()
        courses.append(Course(f"Course {30}", 30, 30 + 1000))
        courses.append(Course(f"Course {0}", 0, 0 + 1000))
        assert database.check_if_courses_data_exists(campus_name, courses)

        loaded_academic_activities = database.load_academic_activities_data(campus_name, courses)
        assert set(loaded_academic_activities).issubset(set(academic_activities))

        loaded_academic_activities = database.load_academic_activities_data(campus_name, [])
        assert loaded_academic_activities

        assert utils.get_campus_name_test() in database.get_common_campuses_names()

        database.clear_academic_activities_data(campus_name)
        database.clear_data_old_than(0)
        assert not database.load_academic_activities_data(campus_name, courses)

    def test_load_hard_coded_user_data(self, database):
        user = User("username", "password")

        database.save_hard_coded_user_data(user)

        loaded_user = database.load_hard_coded_user_data()
        assert user == loaded_user

        os.remove(Database.USER_NAME_FILE_PATH)
        assert database.load_hard_coded_user_data() is None

    def test_settings(self):
        database = Database()
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

    def test_years(self):
        database = Database()
        database.clear_years()
        assert not database.load_years()

        years = {30: "אאא"}
        database.save_years(years)

        assert years == database.load_years()

        database.clear_years()
        assert not database.load_years()
