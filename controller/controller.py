from typing import List
from collections import defaultdict
import time

import utils
from collector.db.db import Database
from collector.gui.gui import Gui, MessageType, UserClickExitException
from collector.network.network import NetworkHttp, WeakNetworkConnectionException
from convertor.convertor import Convertor
from data.academic_activity import AcademicActivity
from data.settings import Settings
from data.type import Type
from data.course_choice import CourseChoice
from csp import csp


class Controller:
    SLEEP_TIME_AFTER_ERROR = 10

    def __init__(self):
        self.database = Database()
        self.network = NetworkHttp()
        self.gui = Gui()
        self.convertor = Convertor()
        self.logger = utils.get_logging()

    def _get_courses_choices(self, all_academic_activities: List[AcademicActivity]) -> List[CourseChoice]:
        # key = course name, first value list of lectures, second value list of exercises
        dict_data = defaultdict(lambda: (set(), set()))
        for activity in all_academic_activities:
            index = 1 if activity.type in [Type.LECTURE, Type.SEMINAR] else 0
            dict_data[activity.name][index].add(activity.lecturer_name)

        courses_choices = []
        for course_name, (lecturers, exercises) in dict_data.items():
            courses_choices.append(CourseChoice(course_name, available_teachers_for_lecture=list(lecturers),
                                                available_teachers_for_practice=list(exercises)))
        return courses_choices

    def _get_academic_activities_data(self, campus_name, courses):
        activities = []

        if self.database.check_if_courses_data_exists(campus_name, courses):
            activities = self.database.load_academic_activities_data(campus_name, courses)
        else:
            activities, names_missing_activities = self.network.extract_academic_activities_data(campus_name, courses)

            if names_missing_activities:
                message = "The following courses don't have activities: " + ", ".join(names_missing_activities)
                self.gui.open_notification_window(message)

            self.database.save_academic_activities_data(campus_name, activities)
        return activities

    def run_main_gui_flow(self):
        try:
            user = None
            while not user:
                user = self.gui.open_login_window()
                if not user:
                    self.gui.open_notification_window("The username or password is incorrect.")
            self.gui.close_login_window()
            self.network.set_user(user)

            settings = self.database.load_settings() or Settings()

            campus_names = self.network.extract_campus_names()

            settings = self.gui.open_settings_window(settings, campus_names, utils.get_years_list())
            self.database.save_settings(settings)

            ask_attendance = not settings.attendance_required_all_courses

            self.gui.open_loading_window("Loading courses data...")

            courses = self.database.load_courses_data() or self.network.extract_all_courses(settings.campus_name)

            if not courses:
                self.gui.close_loading_window()
                message = "There are no courses in the system, please try again with another campus or year."
                self.gui.open_notification_window(message, MessageType.ERROR)
                time.sleep(Controller.SLEEP_TIME_AFTER_ERROR)
                return

            all_academic_activities, _ = self.network.extract_academic_activities_data(settings.campus_name, courses)

            self.gui.close_loading_window()

            courses_choices = self._get_courses_choices(all_academic_activities)

            courses_choices = self.gui.open_academic_activities_window(ask_attendance, courses_choices)

            courses_names = [course.name for course in courses_choices]
            user_courses = []

            for course in courses:
                if course.name in courses_names:
                    course_choise = courses_choices[courses_names.index(course.name)]
                    if ask_attendance:
                        course.attendance_required_for_lecture = course_choise.attendance_required_for_lecture
                        course.attendance_required_for_exercise = course_choise.attendance_required_for_exercise
                    user_courses.append(course)

            activities = list(filter(lambda activity: activity.name in courses_names, all_academic_activities))

            AcademicActivity.union_courses(activities, user_courses)

            activities += self.gui.open_personal_activities_window()

            schedules = csp.extract_schedules(activities, courses_choices)

            if not schedules:
                self.gui.open_notification_window("No schedules were found")
            else:
                self.convertor.convert_activities(schedules, "results", settings.output_formats)

            self.gui.open_notification_window("The schedules were saved in the 'results' folder")

        except (WeakNetworkConnectionException, UserClickExitException) as error:
            message = str(error)
            self.gui.open_notification_window(message, MessageType.ERROR)
            self.logger.error(message)
            time.sleep(Controller.SLEEP_TIME_AFTER_ERROR)

    def run_update_levnet_data_flow(self):
        self.network = NetworkHttp()

        self.logger.debug("Start updating the levnet data")
        user = self.database.load_hard_coded_user_data()
        assert user, "There is no user data, can't access the levnet website."
        self.logger.debug("User data was loaded successfully")

        self.network.set_user(user)
        assert self.network.check_connection(), "ERROR: Can't connect to the levnet website"
        self.logger.debug("The username and password are valid")

        self.database.clear_all_data()
        self.logger.debug("The database was cleared successfully")

        campus_names = self.network.extract_campus_names()
        self.logger.debug("The campus names were extracted successfully")
        self.logger.debug("The campus names are: %s", ", ".join(campus_names))

        self.database.save_campus_names(campus_names)

        courses = self.network.extract_all_courses(utils.get_campus_name_test())
        self.logger.debug("The courses were extracted successfully")
        self.logger.debug("The courses are: %s", ", ".join([course.name for course in courses]))

        self.database.save_courses_data(courses)

        common_campuses_names = self.database.get_common_campuses_names()

        for campus_name in common_campuses_names:
            self.logger.debug("Start extracting the academic activities data for the campus: %s", campus_name)
            activities, missings = self.network.extract_academic_activities_data(campus_name, courses)
            if activities and not missings:
                self.logger.debug("The academic activities data were extracted successfully")
            else:
                self.logger.debug("The academic activities data were extracted with errors")
                self.logger.debug("The missing courses are: %s", ', '.join(missings))

            self.database.save_academic_activities_data(campus_name, activities)
