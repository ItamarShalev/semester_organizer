import pathlib
from sqlite3 import IntegrityError

import pytest
from pytest import fixture

import utils
from collector.db.db import Database
from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.course import Course
from data.course_choice import CourseChoice
from data.day import Day
from data.degree import Degree
from data.language import Language
from data.meeting import Meeting
from data.semester import Semester
from data.settings import Settings
from data.translation import _
from data.type import Type
from data.user import User
from data.output_format import OutputFormat


class TestDatabase:

    TEST_DATABASE_FOLDER = "test_database"

    def test_not_empty(self, database_mock):
        assert database_mock.are_shared_tables_exists()

    def test_load_current_versions(self, database_mock):
        assert database_mock.load_current_versions() == (None, None)
        database_mock.save_current_versions("1.0", "2.0.0")
        assert database_mock.load_current_versions() == ("1.0", "2.0.0")

    def test_not_exists(self, database_mock):
        database_mock.clear_all_data()
        database_mock.shared_database_path.unlink(missing_ok=True)
        assert database_mock.get_common_campuses_names()
        assert not database_mock.load_semesters()
        assert not database_mock.get_language()
        assert not database_mock.load_years()
        assert not database_mock.load_settings()
        assert not database_mock.load_degrees()
        assert not database_mock.load_courses_already_done(Language.ENGLISH)
        assert not database_mock.load_activities_ids_groups_can_enroll_in()
        assert not database_mock.load_user_data()
        assert not database_mock.load_campus_names()
        assert not database_mock.load_personal_activities()
        assert not database_mock.load_courses(Language.ENGLISH, None)
        assert not database_mock.load_active_courses("", Language.ENGLISH)
        assert not database_mock.load_activities_by_parent_courses_numbers(set(), "", Language.ENGLISH)
        assert not database_mock.load_activities_by_courses_choices({}, "", Language.ENGLISH)
        assert not database_mock.load_academic_activities("", Language.ENGLISH, [])
        assert not database_mock.load_campuses()
        assert not database_mock.are_shared_tables_exists()

    def test_campuses(self, database_mock):

        campuses = {
            1: ("A", "א"),
            2: ("B", "ב"),
            3: ("C", "ג"),
        }
        database_mock.save_campuses(campuses)
        assert database_mock.load_campuses() == campuses
        assert database_mock.load_campus_names(Language.HEBREW) == ["א", "ב", "ג"]
        assert database_mock.load_campus_names(Language.ENGLISH) == ["A", "B", "C"]

    def test_language(self, database_mock):
        assert not database_mock.get_language()
        database_mock.save_language(Language.ENGLISH)
        assert database_mock.get_language() == Language.ENGLISH

    def test_semesters(self, database_mock):
        semesters = list(Semester)
        database_mock.save_semesters(semesters)

        assert set(semesters) == set(database_mock.load_semesters())

    def test_common_campuses_names(self, database_mock):
        assert len(database_mock.get_common_campuses_names()) == 5
        assert _("Machon Lev") in database_mock.get_common_campuses_names()

    def test_update_database(self, database_mock):
        database_mock.clear_shared_database()
        database_mock.init_database_tables()
        assert not database_mock.load_degrees()
        database_path = utils.get_database_path() / TestDatabase.TEST_DATABASE_FOLDER
        new_database_path = database_path / "new_database.db"
        old_database_path = database_mock.shared_database_path
        database_mock.shared_database_path = new_database_path
        database_mock.init_database_tables()
        database_mock.save_degrees(list(Degree))
        assert database_mock.load_degrees()
        database_mock.shared_database_path = old_database_path
        assert not database_mock.load_degrees()
        database_mock.update_database(pathlib.Path(new_database_path))
        assert database_mock.load_degrees()
        new_database_path.unlink(missing_ok=True)

    def test_load_activities_by_parent_courses_numbers(self, database_mock, campuses):
        campus_name = campuses[1][0]
        activity = AcademicActivity("activity", Type.LECTURE, True, "lecturer_", 0, 2, "", "1.0", "")
        activity1 = AcademicActivity("activity", Type.LECTURE, True, "lecturer_", 0, 2, "", "1.0", "")
        activity.add_slot(Meeting(Day.MONDAY, "10:00", "12:00"))
        database_mock.save_courses([Course("course", 1221, 2, set(Semester), set(Degree))], Language.ENGLISH)
        database_mock.save_academic_activities([activity], campus_name, Language.ENGLISH)
        database_mock.save_academic_activities([activity1], campus_name, Language.HEBREW)
        activities_loaded = database_mock.load_activities_by_parent_courses_numbers({2}, campus_name, Language.ENGLISH)
        assert activities_loaded == [activity]
        assert database_mock.load_activities_by_parent_courses_numbers({1}, campus_name, Language.ENGLISH) == []

    def test_degrees(self, database_mock):
        degrees = [Degree.SOFTWARE_ENGINEERING]
        database_mock.save_degrees(degrees)

        assert set(degrees) == set(database_mock.load_degrees())
        database_mock.clear_all_data()
        database_mock.init_database_tables()
        database_mock.save_degrees([("SOFTWARE_ENGINEERING", 30)])
        with pytest.raises(ValueError):
            database_mock.load_degrees()

    def test_courses_already_done(self, database_mock):
        assert not database_mock.load_courses_already_done(Language.ENGLISH)
        course1 = Course("course1", 1234, 2, set(Semester), set(Degree))
        course2 = Course("course2", 1235, 3, set(Semester), set(Degree))
        database_mock.save_courses([course1, course2], Language.ENGLISH)
        assert database_mock.load_courses(Language.ENGLISH) == [course1, course2]
        database_mock.save_courses_already_done({course1})
        assert database_mock.load_courses_already_done(Language.ENGLISH) == {course1}
        database_mock.clear_courses_already_done()
        assert not database_mock.load_courses_already_done(Language.ENGLISH)

    def test_is_active_credits_courses(self, database_mock):
        course = Course("name", 10, 20, is_active=True, credits_count=2.3)
        course.degrees = set(Degree)
        database_mock.save_courses([course], Language.ENGLISH)
        courses = database_mock.load_courses(Language.ENGLISH, set(Degree))
        assert len(courses) == 1
        assert courses[0].is_active is True
        assert courses[0].credits_count == 2.3

    def test_courses(self, database_mock):
        hebrew_courses = [Course(f"קורס {i}", i, i + 1000, set(Semester), set(Degree)) for i in range(10)]
        database_mock.save_courses(hebrew_courses, Language.HEBREW)

        english_courses = [Course(f"course {i}", i, i + 1000, set(Semester), set(Degree)) for i in range(10)]
        database_mock.save_courses(english_courses, Language.ENGLISH)

        assert set(hebrew_courses) == set(database_mock.load_courses(Language.HEBREW))
        assert set(english_courses) == set(database_mock.load_courses(Language.ENGLISH))

    def test_personal_activities(self, database_mock):
        activity = Activity("my activity")
        activity.add_slot(Meeting(Day.MONDAY, "10:00", "12:00"))
        database_mock.save_personal_activities([activity])
        loaded = database_mock.load_personal_activities()
        assert loaded == [activity]
        assert loaded[0].meetings == [Meeting(Day.MONDAY, "10:00", "12:00")]
        assert database_mock.are_personal_tables_exists()
        with pytest.raises(IntegrityError):
            database_mock.save_personal_activities([activity])

    def test_activities(self, database_mock, campuses):
        campus_name = "A"
        academic_activity = AcademicActivity("name", Type.LECTURE, True, "meir", 12, 232, "", "12.23", "", 0, 100, 1213)
        academic_activity.add_slot(Meeting(Day.MONDAY, "10:00", "12:00"))
        database_mock.save_academic_activities([academic_activity], campus_name, Language.ENGLISH)
        loaded = database_mock.load_academic_activities(campus_name, Language.ENGLISH,
                                                        [Course("name", 12, 232, set(Semester), set(Degree))])
        assert loaded == [academic_activity]
        assert loaded[0].meetings == [Meeting(Day.MONDAY, "10:00", "12:00")]

    def test_activities_can_enroll_in(self, database_mock):
        all_activities_can_enroll_in = {
            "12.1.1": {103},
            "10.10.1": {103, 104},
        }
        database_mock.clear_activities_ids_tracks_can_enroll()
        assert not database_mock.load_activities_ids_groups_can_enroll_in()
        database_mock.save_activities_ids_groups_can_enroll_in(all_activities_can_enroll_in)
        loaded_activities_ids = database_mock.load_activities_ids_groups_can_enroll_in()
        assert len(loaded_activities_ids) == 2
        assert loaded_activities_ids["12.1.1"] == {103}
        assert loaded_activities_ids["10.10.1"] == {103, 104}

    def test_mandatory_degrees(self, database_mock):
        course = Course("course", 10, 20, Semester.FALL,
                        {Degree.SOFTWARE_ENGINEERING, Degree.COMPUTER_SCIENCE}, Degree.COMPUTER_SCIENCE)
        database_mock.save_courses([course], Language.ENGLISH)
        courses = database_mock.load_courses(Language.ENGLISH, {Degree.SOFTWARE_ENGINEERING})
        assert len(courses) == 1, "ERROR: Entered one course."
        assert courses[0].mandatory_degrees == {Degree.COMPUTER_SCIENCE}
        assert courses[0].optional_degrees == {Degree.SOFTWARE_ENGINEERING}

    def test_course_choices(self, database_mock, campuses):
        campus_name = "A"
        courses = [Course(f"Course {i}", i, i + 1000, set(Semester), set(Degree)) for i in range(10)]
        database_mock.save_courses(courses, Language.ENGLISH)
        activities = [AcademicActivity(f"Course {i}", Type.LECTURE, True, "meir", i, i + 1000, "", f"3{i}", "", 0, 1, 0)
                      for i in range(10)]
        database_mock.save_academic_activities(activities, campus_name, Language.ENGLISH)
        loaded_courses_choices = database_mock.load_courses_choices(campus_name, Language.ENGLISH, set(Degree))
        excepted_courses_choices = [CourseChoice(f"Course {i}", i, {"meir"}, set()) for i in range(10)]
        assert set(loaded_courses_choices.values()) == set(excepted_courses_choices)

    def test_load_activities_by_courses_choices(self, database_mock, campuses):
        campus_name = "A"
        language = Language.ENGLISH
        courses = [Course(f"Cor {i}", i, i + 10, set(Semester), set(Degree)) for i in range(10)]
        database_mock.save_courses(courses, language)

        def create_activity(i):
            return AcademicActivity(f"Cor {i}", Type.LECTURE, True, f"meir{i}", i, i + 10, "", f"12.23{i}", "", 0, 1, 0)

        activities = [create_activity(i) for i in range(10)]

        courses_choices_excepted = {"Cor 5": CourseChoice("Cor 5", 5, {"meir5"}, set())}
        courses_choices = {"Cor 1": CourseChoice("Cor 1", 1, {"meir0"}, set())}
        courses_choices.update(courses_choices_excepted)

        database_mock.save_academic_activities(activities, campus_name, language)
        loaded_choices = database_mock.load_activities_by_courses_choices(courses_choices, campus_name, language)
        assert loaded_choices == [create_activity(5)]

    def test_user_data(self, database_mock):
        user = User("username", "password")

        database_mock.save_user_data(user)

        loaded_user = database_mock.load_user_data()
        assert user == loaded_user

        database_mock.user_name_file_path.unlink(missing_ok=True)
        assert database_mock.load_user_data() is None

    def test_settings(self, database_mock):
        database_mock.clear_settings()
        assert database_mock.load_settings() is None

        settings = Settings()
        settings.campus_name = "בדיקה"
        settings.year = 2020
        settings.output_formats = [OutputFormat.EXCEL]
        database_mock.save_settings(settings)
        assert database_mock.load_settings() == settings

        database_mock.clear_settings()
        assert database_mock.load_settings() is None

    def test_years(self, database_mock):
        database_mock.clear_years()
        assert not database_mock.load_years()

        years = {30: "אאא"}
        database_mock.save_years(years)

        assert years == database_mock.load_years()

        database_mock.clear_years()
        assert not database_mock.load_years()

    def test_last_courses_choices(self, database_mock):
        names = ["a", "b", "c"]
        database_mock.save_courses_console_choose(names)
        assert database_mock.load_courses_console_choose() == names
        database_mock.clear_last_courses_choose_input()
        assert not database_mock.load_courses_console_choose()

    def test_load_courses_choices(self, database_mock, campuses):
        campus_name = campuses[1][0]
        activity1 = AcademicActivity("name1", Type.LECTURE, True, "meir", 124, 34, "", "124.01", "", 0, 100, 1213)
        activity2 = AcademicActivity("name2", Type.LAB, True, "meir2", 125, 35, "", "125.02", "", 0, 100, 1213)
        activity3 = AcademicActivity("name3", Type.LECTURE, True, "meir", 126, 36, "", "126.03", "", 0, 100, 1213)
        activity1.add_slot(Meeting(Day.MONDAY, "10:00", "12:00"))
        activity2.add_slot(Meeting(Day.SUNDAY, "10:00", "12:00"))
        activity3.add_slot(Meeting(Day.WEDNESDAY, "10:00", "12:00"))
        activities = [activity1, activity2, activity3]
        courses = [Course("name1", 124, 34, set(Semester), set(Degree)),
                   Course("name2", 125, 35, set(Semester), set(Degree)),
                   Course("name3", 126, 36, set(Semester), set(Degree))]
        database_mock.save_degrees(list(Degree))
        database_mock.save_semesters(list(Semester))
        database_mock.save_courses(courses, Language.ENGLISH)
        database_mock.save_academic_activities(activities, campus_name, Language.ENGLISH)
        excepted_courses_choices = {
            "name1": CourseChoice("name1", 124, {"meir"}, set()),
            "name2": CourseChoice("name2", 125, set(), {"meir2"}),
        }
        courses_choices = database_mock.load_courses_choices(campus_name, Language.ENGLISH, set(Degree), courses,
                                                             ["124.01", "125.02"])
        assert len(courses_choices) == 2
        assert courses_choices == excepted_courses_choices

    def test_clear_all(self, database_mock):
        database_mock.clear_all_data()
        database_mock.shared_database_path.unlink(missing_ok=True)
        database_mock.personal_database_path.unlink(missing_ok=True)

    @fixture
    def database_mock(self):
        class DatabaseMock(Database):

            def __init__(self):
                super().__init__(TestDatabase.TEST_DATABASE_FOLDER)
                database_path = utils.get_database_path() / TestDatabase.TEST_DATABASE_FOLDER
                self.shared_database_path = database_path / "database.db"
                self.user_name_file_path.unlink(missing_ok=True)

        database = DatabaseMock()
        database.clear_all_data()
        database.clear_personal_database()
        database.clear_shared_database()
        database.init_database_tables()

        return database

    @fixture
    def campuses(self, database_mock):
        campuses = {
            1: ("A", "א"),
            2: ("B", "ב"),
            3: ("C", "ג"),
        }
        database_mock.save_campuses(campuses)
        return campuses
