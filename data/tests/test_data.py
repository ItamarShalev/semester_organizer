import os
import shutil
from copy import copy

import pytest

import utils
from collector.gui.gui import MessageType
from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.case_insensitive_dict import CaseInsensitiveDict, TextCaseInsensitiveDict
from data.degree import Degree
from data.flow import Flow
from data.language import Language
from data.meeting import Meeting
from data.course import Course
from data.day import Day
from data.schedule import Schedule
from data.semester import Semester
from data.settings import Settings
from data.type import Type
from data.course_choice import CourseChoice
from data import translation
from data.translation import _


class TestData:

    def test_meetings(self):
        meeting = Meeting(Day.MONDAY, "09:00", "11:00")
        meeting2 = Meeting(Day.MONDAY, "09:00", "10:00")
        meeting3 = Meeting(Day.MONDAY, "09:10", "10:00")
        meeting4 = Meeting(Day.MONDAY, "09:10", "20:00")
        meeting5 = Meeting(Day.MONDAY, "11:00", "20:00")
        meetings = [meeting2, meeting3, meeting4]

        assert meeting.get_string_start_time() == "09:00"
        assert meeting.get_string_end_time() == "11:00"
        assert all(meeting.is_crash_with_meeting(meeting_item) for meeting_item in meetings)
        assert not meeting5.is_crash_with_meeting(meeting)

        with pytest.raises(Exception):
            Meeting(Day.MONDAY, "11:00", "10:00")

        with pytest.raises(Exception):
            Meeting(Day.MONDAY, "11:00", "11:00")

        assert repr(meeting) == "09:00 - 11:00"

        assert [meeting.meeting_id, Day.MONDAY.value, "09:00", "11:00"] == [*meeting]

    def test_course(self):
        course = Course("", 0, 0, set(Semester), set(Degree))
        course2 = Course("", 0, 0, Semester.ANNUAL, Degree.SOFTWARE_ENGINEERING)
        assert course == course2
        course3 = Course("", 0, 0, Semester.ANNUAL, Degree.SOFTWARE_ENGINEERING)
        course3.add_degrees(Degree.COMPUTER_SCIENCE)
        course3.add_degrees({Degree.SOFTWARE_ENGINEERING, Degree.COMPUTER_SCIENCE})
        assert len(course3.degrees) == 2

        course.set_attendance_required(Type.LAB, True)
        course.set_attendance_required(Type.LECTURE, False)
        assert course.is_attendance_required(Type.LAB)
        assert not course.is_attendance_required(Type.LECTURE)

        course.name = "name"
        assert repr(course) == "name"
        assert repr(Semester.SUMMER) == "Summer"
        assert repr(Day.MONDAY) == "Monday"

        course.add_semesters({Semester.SUMMER})
        course.add_semesters(Semester.ANNUAL)
        assert course.semesters == {Semester.SUMMER, Semester.ANNUAL, Semester.SPRING, Semester.FALL}

    def test_activity(self):
        activity = Activity("", Type.LAB, False)
        activity.add_slot(Meeting(Day.MONDAY, "09:00", "11:00"))
        with pytest.raises(Exception):
            activity.add_slot(Meeting(Day.MONDAY, "09:00", "10:00"))
        assert activity.is_free_slot(Meeting(Day.MONDAY, "11:00", "12:00"))
        meetings = [Meeting(Day.MONDAY, "16:00", "18:00"), Meeting(Day.MONDAY, "18:00", "19:00")]
        activity.add_slots(meetings)
        assert not activity.is_crash_with_activities([])

        activity1 = Activity("", Type.LAB, True)
        assert not activity.is_crash_with_activity(activity1)

        assert activity1.no_meetings()

        activity.name = "name"
        assert repr(activity) == "name"

    def test_academic_activity(self):
        activity = AcademicActivity("name", activity_type=Type.LAB, course_number=10, parent_course_number=20)
        hash_attributes = (activity.name, activity.course_number, activity.parent_course_number, activity.activity_id)
        assert hash(activity) == hash(tuple([*hash_attributes]))
        course = Course("name", 10, 20, set(Semester), set(Degree))
        assert activity.same_as_course(course)
        activities = [activity]

        AcademicActivity.union_courses(activities, [course])
        assert repr(activity) == "name"

    def test_type(self):
        typ = Type.LAB
        assert typ == Type.LAB
        assert typ.is_exercise()
        assert repr(typ) == "Lab"

        typ = Type.PERSONAL
        assert typ == Type.PERSONAL
        assert typ.is_personal()

    def test_course_choices(self):
        course_choice = CourseChoice("A", [], [])
        assert course_choice.name == "A"
        assert hash(course_choice) == hash("A")

    def test_schedule(self):
        standby_time_in_minutes = 0

        meeting = Meeting(Day.MONDAY, "09:00", "11:00")
        meeting3 = Meeting(Day.MONDAY, "11:10", "12:00")
        meeting2 = Meeting(Day.MONDAY, "18:00", "20:00")
        standby_time_in_minutes += 6 * 60
        meeting4 = Meeting(Day.FRIDAY, "09:10", "20:00")
        meeting5 = Meeting(Day.SUNDAY, "11:00", "20:00")
        meeting7 = Meeting(Day.THURSDAY, "19:00", "20:20")
        meetings = [meeting, meeting2, meeting3, meeting4, meeting5, meeting7]
        activity = Activity("name", Type.LAB, False)
        activity.add_slots(meetings)

        activity2 = Activity("name2", Type.LAB, False)
        meeting6 = Meeting(Day.THURSDAY, "21:00", "22:00")
        standby_time_in_minutes += 40
        activity2.add_slot(meeting6)
        meetings.append(meeting6)

        schedule = Schedule("name", "file_name", "description", [activity, activity2])

        assert schedule.get_all_academic_meetings() == meetings
        assert schedule.get_all_meetings_by_day(Day.MONDAY) == {meeting, meeting3, meeting2}
        assert schedule.get_learning_days() == {Day.SUNDAY, Day.MONDAY, Day.THURSDAY, Day.FRIDAY}
        assert schedule.get_standby_in_minutes() == standby_time_in_minutes
        assert repr(schedule) == "name"

        copied_schedule = copy(schedule)
        assert copied_schedule == schedule

    def test_sort_meeting(self):
        meeting = Meeting(Day.MONDAY, "09:00", "11:00")
        meeting2 = Meeting(Day.MONDAY, "18:00", "20:00")
        meeting3 = Meeting(Day.MONDAY, "11:10", "12:00")
        meeting4 = Meeting(Day.FRIDAY, "09:10", "20:00")
        meeting5 = Meeting(Day.SUNDAY, "11:00", "20:00")
        meetings = [meeting, meeting2, meeting3, meeting4, meeting5]
        meetings.sort()
        assert meetings == [meeting5, meeting, meeting3, meeting2, meeting4]

    def test_language(self):
        language = Language.ENGLISH
        assert repr(language) == "english"
        assert language.short_name() == "en"

        translation.config_language_text(Language.ENGLISH)
        assert _("Test") == "Test"

        translation.config_language_text(Language.HEBREW)
        assert _("Test") == "בדיקה"

        assert translation.translate("Test") == translation._("Test")

        translation.config_language_text(None)
        assert Language.get_current() == Language.HEBREW

        assert repr(Language.ENGLISH) == "english"
        assert Language.contains("EnglISh")
        assert not Language.contains("France")

        assert Language.from_str("engLISH") is Language.ENGLISH
        assert Language.from_str("1") is Language.ENGLISH
        assert Language.from_str("en") is Language.ENGLISH
        with pytest.raises(ValueError):
            Language.from_str("France")

    def test_case_insensitive_dict(self):
        case_insensitive_dict = CaseInsensitiveDict()
        case_insensitive_dict["A"] = 1
        assert case_insensitive_dict["a"] == 1
        assert case_insensitive_dict["A"] == 1
        assert case_insensitive_dict.get("A") == 1
        with pytest.raises(KeyError):
            _var = case_insensitive_dict["b"]
        assert case_insensitive_dict.get("B") is None
        assert case_insensitive_dict.get("B", 2) == 2
        assert "A" in case_insensitive_dict
        assert "B" not in case_insensitive_dict
        assert len(case_insensitive_dict) == 1
        del case_insensitive_dict["A"]
        assert len(case_insensitive_dict) == 0
        case_insensitive_dict["A"] = 1
        case_insensitive_dict.pop("A")
        assert len(case_insensitive_dict) == 0
        case_insensitive_dict["A"] = 1
        case_insensitive_dict.popitem()
        assert len(case_insensitive_dict) == 0
        case_insensitive_dict["A"] = 1
        case_insensitive_dict.clear()
        assert len(case_insensitive_dict) == 0
        case_insensitive_dict["A"] = 1
        case_insensitive_dict.setdefault("A", 2)
        assert case_insensitive_dict["A"] == 1
        case_insensitive_dict.update({"A": 2})
        assert case_insensitive_dict["A"] == 2

        case_insensitive_dict = TextCaseInsensitiveDict({"? ASA,=   - ?": 1, 2: 3})
        assert case_insensitive_dict["AsA"] == 1
        assert case_insensitive_dict[2] == 3

    def test_utils(self):
        assert utils.get_logging()
        assert utils.get_custom_software_name() == "semester_organizer_lev"
        assert utils.get_course_data_test().parent_course_number == 318
        assert utils.windows_path_to_unix("C:\\path\\to") == "/c/path/to"
        test_folder = os.path.join(utils.get_database_path(), "test_folder")
        test_file = os.path.join(test_folder, "test_file.txt")
        shutil.rmtree(test_folder, ignore_errors=True)
        os.mkdir(test_folder)
        assert utils.get_last_modified_by_days(test_folder) == 0
        with open(test_file, "w") as file:
            file.write("test")
        assert utils.count_files_and_directory(test_folder) == (1, 0)
        shutil.rmtree(test_folder, ignore_errors=True)
        assert utils.get_last_modified_by_days(test_folder) == 0

    def test_degree(self):
        degrees = set()
        degrees.add(Degree.COMPUTER_SCIENCE)
        degrees.add(Degree.SOFTWARE_ENGINEERING)
        assert repr(Degree.COMPUTER_SCIENCE) == "Computer Science"
        assert len(Degree.get_defaults()) == 2
        assert set(Degree) == {Degree.COMPUTER_SCIENCE, Degree.SOFTWARE_ENGINEERING}
        assert ["COMPUTER_SCIENCE", 20] == [*Degree.COMPUTER_SCIENCE]
        assert Degree.COMPUTER_SCIENCE == Degree["COMPUTER_SCIENCE"]

    def test_flow_enum(self):
        flow = Flow.GUI
        assert flow is Flow.GUI
        assert str(flow) == "gui"
        assert flow.from_str("guI") is Flow.GUI
        assert flow.from_str("1") is Flow.GUI
        assert flow.from_str(1) is Flow.GUI
        with pytest.raises(ValueError):
            flow.from_str("18")

    def test_settings(self):
        # pylint: disable=no-member
        excepted_settings = Settings()
        excepted_settings.degrees = Degree.get_defaults()
        json_settings = Settings().to_json()
        settings = Settings.from_json(json_settings)
        assert settings == Settings()
        assert settings.degrees == Degree.get_defaults()

    def test_others(self):
        message = MessageType.ERROR
        assert repr(message) == "Error"
        assert str(message) == _("Error")
