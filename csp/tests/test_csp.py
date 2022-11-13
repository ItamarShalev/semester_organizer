from csp import csp
from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.day import Day
from data.meeting import Meeting
from data.type import Type


def _format_str(string):
    return Meeting.str_to_time(string)


def test_one_from_one_option():
    activities = []
    academic_activity = AcademicActivity("a", Type.LECTURE, True, "a", 1, 1, "a")
    academic_activity.add_slot(Meeting(Day.SUNDAY, _format_str("10:00"), _format_str("11:00")))
    activities.append(academic_activity)

    academic_activity = AcademicActivity("b", Type.LAB, True, "b", 1, 1, "b")
    academic_activity.add_slot(Meeting(Day.SUNDAY, _format_str("12:00"), _format_str("14:30")))
    activities.append(academic_activity)

    activity = Activity("c", Type.PERSONAL, True)
    activity.add_slot(Meeting(Day.MONDAY, _format_str("12:00"), _format_str("14:30")))
    activities.append(activity)

    schedules = csp.extract_schedules(activities)
    assert len(schedules) == 1
    assert any(schedule.contains(activities) for schedule in schedules)


def test_two_from_two_options():
    activities_option_1 = []
    activities_option_2 = []

    activities = []
    academic_activity = AcademicActivity("a", Type.LECTURE, True, "a", 1, 1, "a")
    academic_activity.add_slot(Meeting(Day.SUNDAY, _format_str("10:00"), _format_str("11:00")))
    activities.append(academic_activity)
    activities_option_1.append(academic_activity)

    academic_activity = AcademicActivity("a", Type.LECTURE, True, "a", 2, 2, "a")
    academic_activity.add_slot(Meeting(Day.SUNDAY, _format_str("12:00"), _format_str("14:30")))
    activities.append(academic_activity)
    activities_option_2.append(academic_activity)

    activity = Activity("c", Type.PERSONAL, True)
    activity.add_slot(Meeting(Day.MONDAY, _format_str("12:00"), _format_str("14:30")))
    activities.append(activity)
    activities_option_1.append(activity)
    activities_option_2.append(activity)

    schedules = csp.extract_schedules(activities)
    assert len(schedules) == 2
    assert any(schedule.contains(activities_option_1) for schedule in schedules)
    assert any(schedule.contains(activities_option_2) for schedule in schedules)


def test_one_from_two_options():
    activities_option_1 = []

    activities = []
    academic_activity = AcademicActivity("a", Type.LECTURE, True, "a", 1, 1, "a")
    academic_activity.add_slot(Meeting(Day.SUNDAY, _format_str("10:00"), _format_str("11:00")))
    activities.append(academic_activity)
    activities_option_1.append(academic_activity)

    academic_activity = AcademicActivity("a", Type.PRACTICE, True, "a", 2, 2, "a")
    academic_activity.add_slot(Meeting(Day.SUNDAY, _format_str("12:00"), _format_str("14:30")))
    activities.append(academic_activity)
    activities_option_1.append(academic_activity)

    academic_activity = AcademicActivity("a", Type.PRACTICE, True, "a", 2, 2, "a")
    academic_activity.add_slot(Meeting(Day.MONDAY, _format_str("13:00"), _format_str("13:30")))
    activities.append(academic_activity)

    activity = Activity("c", Type.PERSONAL, True)
    activity.add_slot(Meeting(Day.MONDAY, _format_str("12:00"), _format_str("14:30")))
    activities.append(activity)
    activities_option_1.append(activity)

    schedules = csp.extract_schedules(activities)
    assert len(schedules) == 1
    assert any(schedule.contains(activities_option_1) for schedule in schedules)


def test_no_option():
    activities = []
    academic_activity = AcademicActivity("a", Type.LECTURE, True, "a", 1, 1, "a")
    academic_activity.add_slot(Meeting(Day.SUNDAY, _format_str("10:00"), _format_str("11:00")))
    activities.append(academic_activity)

    academic_activity = AcademicActivity("a", Type.LAB, True, "a", 2, 2, "a")
    academic_activity.add_slot(Meeting(Day.MONDAY, _format_str("12:00"), _format_str("13:30")))
    activities.append(academic_activity)

    activity = Activity("c", Type.PERSONAL, True)
    activity.add_slot(Meeting(Day.MONDAY, _format_str("12:00"), _format_str("14:30")))
    activities.append(activity)

    schedules = csp.extract_schedules(activities)
    assert len(schedules) == 0
