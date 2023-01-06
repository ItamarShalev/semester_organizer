import os
import shutil

from typing import List, Dict
from collections import defaultdict
from operator import itemgetter
from copy import copy


import utils
from collector.db.db import Database
from collector.gui.gui import Gui, MessageType, UserClickExitException
from collector.network.network import NetworkHttp, WeakNetworkConnectionException
from convertor.convertor import Convertor
from data import translation
from data.academic_activity import AcademicActivity
from data.settings import Settings
from data.course_choice import CourseChoice
from data.translation import _
from data.language import Language
from data.schedule import Schedule
from csp.csp import CSP


class Controller:

    def __init__(self):
        self.database = Database()
        self.network = NetworkHttp()
        self.gui = Gui()
        self.convertor = Convertor()
        self.csp = CSP()
        self.logger = utils.get_logging()

    def _get_courses_choices(self, all_academic_activities: List[AcademicActivity]) -> Dict[str, CourseChoice]:
        # key = course name, first value list of lectures, second value list of exercises
        dict_data = defaultdict(lambda: (set(), set()))
        for activity in all_academic_activities:
            index = 0 if activity.type.is_lecture() else 1
            dict_data[activity.name][index].add(activity.lecturer_name)

        courses_choices = {}
        for course_name, (lecturers, exercises) in dict_data.items():
            courses_choices[course_name] = CourseChoice(course_name, available_teachers_for_lecture=list(lecturers),
                                                        available_teachers_for_practice=list(exercises))
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

    def _initial_language_if_first_time(self):
        settings = self.database.load_settings()
        if not settings:
            message = _("Welcome to the semester organizer!\nPlease choose a language\nThe current language is: ")
            message += _(str(translation.get_current_language()))
            language = self.gui.open_notification_window(message, MessageType.INFO, list(map(str, Language)))
            if language and Language.contains(language):
                translation.config_language_text(Language[language.upper()])
                if self.database.get_language() != language:
                    self.database.clear_all_data()
                    self.database.save_language(language)
                    self.gui.set_language(language)
                    self.convertor.set_language(language)

    def _save_schedule(self, all_schedules: List[Schedule], settings: Settings):
        # Save the most spread days and least spread days
        most_spread_days = defaultdict(list)
        least_spread_days = defaultdict(list)
        schedules_by_learning_days = defaultdict(list)
        schedules_by_standby_time = defaultdict(list)
        results_path = utils.get_results_path()
        output_formats = settings.output_formats

        for schedule in all_schedules:
            standby_in_minutes = schedule.get_standby_in_minutes()
            learning_days = schedule.get_learning_days()
            copied_schedule = copy(schedule)
            copied_schedule.file_name = \
                f"{schedule.file_name}_" + \
                _("with_{}_learning_days_and_{}_minutes_study_time").format(len(learning_days), standby_in_minutes)
            schedules_by_learning_days[len(learning_days)].append(copied_schedule)
            schedules_by_standby_time[standby_in_minutes].append(copied_schedule)

        schedules_by_learning_days = dict(sorted(schedules_by_learning_days.items(), key=itemgetter(0)))
        schedules_by_standby_time = dict(sorted(schedules_by_standby_time.items(), key=itemgetter(0)))

        if len(schedules_by_learning_days.keys()) > 1:
            most_spread_days = schedules_by_learning_days[max(schedules_by_learning_days.keys())]
            least_spread_days = schedules_by_learning_days[min(schedules_by_learning_days.keys())]

        # Get the lowest standby time and the second lowest standby time
        if len(schedules_by_standby_time.keys()) > 2:
            lowest = schedules_by_standby_time[min(schedules_by_standby_time.keys())]
            del schedules_by_standby_time[min(schedules_by_standby_time.keys())]
            lowest += schedules_by_standby_time[min(schedules_by_standby_time.keys())]
            schedules_by_standby_time = lowest
        else:
            schedules_by_standby_time = None

        all_schedules_path = os.path.join(results_path, _("all_schedules"))
        most_spread_days_path = os.path.join(results_path, _("most_spread_days"))
        least_spread_days_path = os.path.join(results_path, _("least_spread_days"))
        least_standby_time_path = os.path.join(results_path, _("least_standby_time"))

        shutil.rmtree(results_path, ignore_errors=True)

        self.convertor.convert_activities(all_schedules, all_schedules_path, output_formats)
        if most_spread_days and least_spread_days:
            self.convertor.convert_activities(most_spread_days, most_spread_days_path, output_formats)
            self.convertor.convert_activities(least_spread_days, least_spread_days_path, output_formats)
        if schedules_by_standby_time:
            self.convertor.convert_activities(schedules_by_standby_time, least_standby_time_path, output_formats)

        message = _("The schedules were saved in the directory: ") + results_path
        self.gui.open_notification_window(message)

    def run_main_gui_flow(self):
        try:
            self.logger.info("Start the main gui flow")

            # Initialize the language for first time.
            self._initial_language_if_first_time()

            user = self.gui.open_login_window(self.network.check_connection)
            self.network.set_user(user)

            self.database.clear_data_old_than(days=1)

            settings = self.database.load_settings() or Settings()

            campus_names = self.database.load_campus_names() or self.network.extract_campus_names()
            self.database.save_campus_names(campus_names)

            years = self.database.load_years() or self.network.extract_years()
            self.database.save_years(years)

            settings = self.gui.open_settings_window(settings, campus_names, years)

            language = self.database.get_language()

            self.network.set_settings(settings)

            if settings.force_update_data:
                self.database.clear_all_data()

            if language and language != settings.language:
                self.database.clear_all_data()
                self.gui.set_language(settings.language)
                self.convertor.set_language(settings.language)

            self.database.save_settings(settings)
            campus_name = settings.campus_name

            ask_attendance = not settings.attendance_required_all_courses

            self.logger.info("Loading courses data...")

            courses = self.database.load_courses_data() or self.network.extract_all_courses(campus_name)

            if not courses:
                message = _("There are no courses in the system, please try again with another campus or year.")
                self.gui.open_notification_window(message, MessageType.ERROR)
                return

            all_academic_activities, _unused = self.network.extract_academic_activities_data(campus_name, courses)

            courses_choices = self._get_courses_choices(all_academic_activities)

            courses_choices = self.gui.open_academic_activities_window(ask_attendance, courses_choices)

            user_courses = []

            for course in courses:
                if course.name in courses_choices.keys():
                    course_choise = courses_choices[course.name]
                    if ask_attendance:
                        course.attendance_required_for_lecture = course_choise.attendance_required_for_lecture
                        course.attendance_required_for_exercise = course_choise.attendance_required_for_exercise
                    user_courses.append(course)

            activities = list(filter(lambda activity: activity.name in courses_choices.keys(), all_academic_activities))

            AcademicActivity.union_courses(activities, user_courses)

            activities += self.gui.open_personal_activities_window()

            schedules = self.csp.extract_schedules(activities, courses_choices, settings)

            if not schedules:
                self.gui.open_notification_window(_("No schedule were found"))
            else:
                self._save_schedule(schedules, settings)

        except UserClickExitException:
            self.logger.info("User clicked exit button")

        except WeakNetworkConnectionException as error:
            message = str(error)
            self.logger.error(message)
            self.gui.open_notification_window(_(message), MessageType.ERROR)

        except Exception as error:
            message = "The system encountered an error, please contanct the engeniers."
            self.logger.error("The system encountered an error: %s", str(error))
            self.gui.open_notification_window(_(message), MessageType.ERROR)

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
