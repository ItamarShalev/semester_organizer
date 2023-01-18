import pytest

from collector.gui.gui import Gui
from collector.gui import gui
from data import translation
from data.activity import Activity
from data.course_choice import CourseChoice
from data.day import Day
from data.language import Language
from data.meeting import Meeting
from data.output_format import OutputFormat
from data.semester import Semester
from data.settings import Settings
from data.type import Type


class TestGui:

    def test_translation(self):
        translation.config_language_text(Language.ENGLISH)
        assert gui._("test") == "test"
        translation.config_language_text(Language.HEBREW)
        assert gui._("Machon Lev") == "לב מכון"

    @pytest.mark.skip(reason="GUI cant run in CI")
    def test_personal_activities(self):
        translation.config_language_text(Language.HEBREW)
        gui_object = Gui()
        activity1 = Activity("MyName1", Type.PERSONAL, True)
        activity2 = Activity("MyName2", Type.PERSONAL, True)
        excepted_activities = [activity1, activity2]
        activity1.add_slot(Meeting(Day.MONDAY, "10:00", "12:00"))
        activity2.add_slot(Meeting(Day.SUNDAY, "10:00", "22:00"))
        activity2.add_slot(Meeting(Day.MONDAY, "13:00", "22:00"))
        tested_activities = gui_object.open_personal_activities_window()
        assert len(tested_activities) == len(excepted_activities)
        assert set(tested_activities) == set(excepted_activities)

    @pytest.mark.skip(reason="GUI cant run in CI")
    def test_settings(self):
        translation.config_language_text(Language.ENGLISH)
        gui_object = Gui()
        test_settings = Settings()
        test_settings.year = 5783
        test_settings.semester = Semester.SPRING
        test_settings.language = Language.ENGLISH
        test_settings.attendance_required_all_courses = False
        test_settings.campus_name = "לב"
        test_settings.show_hertzog_and_yeshiva = True
        test_settings.show_only_courses_with_free_places = True
        test_settings.show_only_courses_active_classes = False
        test_settings.show_only_courses_with_the_same_actual_number = False
        test_settings.show_only_classes_in_days = [Day.MONDAY, Day.TUESDAY]
        test_settings.dont_show_courses_already_done = False
        test_settings.show_only_courses_with_prerequisite_done = False
        test_settings.show_only_classes_can_enroll = True
        test_settings.output_formats = [OutputFormat.CSV]
        excepted_settings = gui_object.open_settings_window(Settings(), ["לב", "טל"], {5782: "תשפב", 5783: "תשפג"})
        assert test_settings == excepted_settings

    @pytest.mark.skip(reason="GUI cant run in CI")
    def test_academic_activities(self):
        translation.config_language_text(Language.ENGLISH)
        gui_object = Gui()

        course_choice_dict = {
            "MyName1": CourseChoice("MyName1", 1, ["Teacher1", "Techer2"], ["Teacher3", "Techer4"], True, False),
            "MyName2": CourseChoice("MyName2", 2, ["Teacher1", "Techer2"], ["Teacher3", "Techer4"], True, True),
            "MyName3": CourseChoice("MyName3", 3, ["Teacher1", "Techer2"], ["Teacher3", "Techer4"], True, True)}

        excepted_course_choices = {
            "MyName1": CourseChoice("MyName1", 1, ["Teacher1", "Techer2"], ["Teacher3", "Techer4"], True, False),
            "MyName3": CourseChoice("MyName3", 3, ["Teacher1"], ["Teacher3"], True, True)
        }

        # dictionary for the list above , the key is the course name
        actual_course_choices = gui_object.open_academic_activities_window(False, course_choice_dict)
        assert actual_course_choices == excepted_course_choices
