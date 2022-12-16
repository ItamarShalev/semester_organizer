from typing import List
from collections import defaultdict

import utils
from collector.db.db import Database
from collector.gui.gui import Gui, MessageType, UserClickExitException
from collector.network.network import NetworkHttp, WeakNetworkConnectionException
from convertor.convertor import Convertor
from data.academic_activity import AcademicActivity
from data.settings import Settings
from data.course_choice import CourseChoice
from csp.csp import CSP


class Controller:

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
            index = 1 if activity.type.is_lecture() else 0
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
            self.logger.info("Start the main gui flow")
            csp = CSP()
            user = self.gui.open_login_window(self.network.check_connection)
            self.network.set_user(user)

            self.database.clear_data_old_than(days=1)

            settings = self.database.load_settings() or Settings()

            campus_names = self.network.extract_campus_names()

            years = self.database.load_years()
            if not years:
                years = self.network.extract_years()
                self.database.save_years(years)

            settings = self.gui.open_settings_window(settings, campus_names, years)

            self.network.set_settings(settings)

            if settings.force_update_data:
                self.database.clear_all_data()

            self.database.save_settings(settings)

            ask_attendance = not settings.attendance_required_all_courses

            self.logger.info("Loading courses data...")

            courses = self.database.load_courses_data() or self.network.extract_all_courses(settings.campus_name)

            if not courses:
                message = "There are no courses in the system, please try again with another campus or year."
                self.gui.open_notification_window(message, MessageType.ERROR)
                return

            all_academic_activities, _ = self.network.extract_academic_activities_data(settings.campus_name, courses)

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

            schedules = csp.extract_schedules(activities, courses_choices, settings)

            results_dir = utils.get_results_path()

            if not schedules:
                self.gui.open_notification_window("No schedules were found")
            else:
                self.convertor.convert_activities(schedules, results_dir, settings.output_formats)
                self.gui.open_notification_window(f"The schedules were saved in the {results_dir} folder")

        except (WeakNetworkConnectionException, UserClickExitException) as error:
            message = str(error)
            self.logger.error(message)
            self.gui.open_notification_window(message, MessageType.ERROR)

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
