from collector.db import db
from collector.gui import gui
from collector.network import network
from convertor import convert_helper
from csp import csp


def _get_campus_names(user):
    campus_names = db.load_campus_names()
    if not campus_names:
        campus_names = network.extract_campus_names(user)
        db.save_campus_names(campus_names)
    return campus_names


def _get_courses_data(user):
    courses = db.load_courses_data()
    if not courses:
        courses = network.extract_all_courses(user)
        db.save_courses_data(courses)
    return courses


def _get_academic_activities_data(user, campus_name, courses, academic_activities):
    activities = []

    if db.check_if_courses_data_exists(courses):
        activities = db.load_academic_activities_data(courses)
    else:
        network.fill_academic_activities_data(user, campus_name, academic_activities)
        names_of_courses_without_activities = network.fill_academic_activities_data(user, campus_name,
                                                                                    academic_activities)

        if names_of_courses_without_activities:
            message = "The following courses don't have activities: " + ", ".join(names_of_courses_without_activities)
            gui.open_notification_windows(message)
            activities = [activity for activity in activities if
                          activity.name not in names_of_courses_without_activities]
        else:
            activities = academic_activities

        db.save_academic_activities_data(activities)
    return activities


def main():
    user = gui.open_login_window()
    campus_names = _get_campus_names(user)
    courses = _get_courses_data(user)
    campus_name, academic_activities = gui.open_academic_activities_window(campus_names, courses)
    courses = [activity.convert_to_course_object() for activity in academic_activities]
    activities = _get_academic_activities_data(user, campus_name, courses, academic_activities)
    activities += gui.open_custom_activities_windows()
    formats = gui.open_choose_format_window()
    schedules = csp.extract_schedules(activities)
    if not schedules:
        gui.open_notification_windows("No schedules were found")
    else:
        convert_helper.convert_activities(schedules, "results", formats)

    gui.open_notification_windows("The schedules were saved in the 'results' folder")


if __name__ == '__main__':
    main()
