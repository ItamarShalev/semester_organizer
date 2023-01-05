import pytest

from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.language import Language
from data.meeting import Meeting
from data.course import Course
from data.day import Day
from data.schedule import Schedule
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

    def test_course(self):
        course = Course("", 0, 0, "0.0.1", None)
        course2 = Course("", 1, 2, "0.0.1", None)
        assert course == course2

        course.set_attendance_required(Type.LAB, True)
        course.set_attendance_required(Type.LECTURE, False)
        assert course.is_attendance_required(Type.LAB)
        assert not course.is_attendance_required(Type.LECTURE)

        course.name = "name"
        assert repr(course) == "name"

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
        course = Course("name", 10, 20, "0.0.1", None)
        assert activity.same_as_course(course)
        activities = [activity]

        AcademicActivity.union_courses(activities, [course])
        assert activity.activity_id == course.activity_id

        assert repr(activity) == "name"

    def test_type(self):
        typ = Type.LAB
        assert typ == Type.LAB
        assert typ.is_exercise()
        assert repr(typ) == "Lab"
        assert str(typ) == "Lab"

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
