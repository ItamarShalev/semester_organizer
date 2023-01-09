import os
import sys
import shutil
import subprocess
import time
from collections import defaultdict
from copy import copy
from operator import itemgetter
from typing import List, Dict, Literal

import utils
from collector.db.db import Database
from collector.gui.gui import Gui, MessageType, UserClickExitException
from convertor.convertor import Convertor
from csp.csp import CSP
from data import translation
from data.academic_activity import AcademicActivity
from data.course_choice import CourseChoice
from data.language import Language
from data.schedule import Schedule
from data.settings import Settings
from data.translation import _


class Controller:

    def __init__(self):
        self.database = Database()
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

    def _initial_language_if_first_time(self):
        settings = self.database.load_settings()
        if not settings:
            message = _("Welcome to the semester organizer!\nPlease choose a language\nThe current language is: ")
            message += _(str(Language.get_current()))
            language = self.gui.open_notification_window(message, MessageType.INFO, list(map(str, Language)))
            if language and Language.contains(language):
                translation.config_language_text(Language[language.upper()])
                if self.database.get_language() != language:
                    self.database.save_language(language)

    def _save_schedule(self, all_schedules: List[Schedule], settings: Settings, results_path: str):
        # Save the most spread days and least spread days
        most_spread_days = defaultdict(list)
        least_spread_days = defaultdict(list)
        schedules_by_learning_days = defaultdict(list)
        schedules_by_standby_time = defaultdict(list)
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

    def _delete_data_if_new_version(self):
        language = self.database.get_language()
        software_version, database_version = self.database.load_current_versions()
        new_software_version, new_database_version = utils.SOFTWARE_VERSION, utils.DATA_SOFTWARE_VERSION
        if software_version != new_software_version or database_version != new_database_version:
            self.database.clear_all_data()
            self.database.clear_settings()
            if language:
                self.database.save_language(language)
            self.database.save_current_versions(new_software_version, new_database_version)

    def _open_results_folder(self, results_path: str):
        subprocess.call(f"explorer {results_path}", shell=True)

    def _validate_database(self, output_type: Literal['gui', 'console']):
        if not self.database.is_all_tables_exists():
            self.logger.error("ERROR: Missing database, can't continue.")
            msg = _("Missing database, can't continue, please download the database file from the github server "
                    "and import the database by running :")
            msg += "'python __main__.py -- update_dabase {path_to_database.db}'"
            if output_type == 'gui':
                self.gui.open_notification_window(msg, MessageType.ERROR)
            elif output_type == 'console':
                print(msg)
            sys.exit(1)

    def run_console_flow(self):
        """
        Run the console flow of the program, only for academic activities.
        Console flow will use the default settings.
        and without database nor GUI.
        """
        # pylint: disable=too-many-branches
        # For testing purposes
        self.logger.info("Starting console flow")
        delay_time = 0.12

        self._validate_database('console')

        language = Language.get_current()
        print(_("Select the campus by enter their index:"))
        available_campuses = self.database.get_common_campuses_names()
        for index, name in enumerate(available_campuses, 1):
            time.sleep(delay_time)
            print(f"{index}. {name}")
        campus_index = input(_("Enter the campus index: "))
        campus_name = available_campuses[int(campus_index) - 1]
        print("\n\n")

        courses_choices = self.database.load_courses_choices(campus_name, language)
        courses_choices = dict(sorted(courses_choices.items(), key=itemgetter(0)))

        print(_("Select the courses by enter their index:"))
        for index, course_name in enumerate(courses_choices.keys(), 1):
            time.sleep(delay_time)
            print(f"{index}. {course_name}")
        input_help = _("Enter the courses indexes separated by comma (example: 1,2,20): ")
        courses_indexes = input(input_help)
        self.logger.debug("Selected courses indexes: %s which they are: ", courses_indexes)
        courses_indexes = [int(index) for index in courses_indexes.strip().split(",")]
        selected_courses_choices = {}
        for index, (course_name, course_choice) in enumerate(courses_choices.items(), 1):
            if index in courses_indexes:
                self.logger.debug("%d. '%s'", index, course_name)
                selected_courses_choices[course_name] = course_choice

        print("\n\n")
        options = [_("Yes"), _("No")]
        print(_("Do you want to select favorite lecturers?"))
        for index, option in enumerate(options, 1):
            time.sleep(delay_time)
            print(f"{index}. {option}")
        favorite_lecturers_option = input(_("Enter the option index: "))
        yes_no_option = options[int(favorite_lecturers_option) - 1]
        self.logger.debug("Selected option: %s", yes_no_option)
        if yes_no_option == _("Yes"):
            for course_name, (course_name, course_choice) in enumerate(selected_courses_choices.items(), 1):
                lectures_lists = [course_choice.available_teachers_for_lecture,
                                  course_choice.available_teachers_for_practice]
                selected_teachers_lists = []
                lectures_lists = [sorted(lectures_list) for lectures_list in lectures_lists]
                for lecture_type, lectures_list in zip(["lecture", "lab / exercise"], lectures_lists):
                    if len(lectures_list) == 0:
                        selected_teachers_lists.append(lectures_list)
                        continue
                    if len(lectures_list) == 1:
                        text = _("There is only one lecture for this the course %s which is %s, automatic select it.")
                        text = text.format(course_name, lectures_list[0])
                        print(text)
                        selected_teachers_lists.append(lectures_list)
                        continue
                    print("\n\n")
                    print(_(f"Select the favorite teachers for {lecture_type} for the course: ") + f"'{course_name}'")
                    for index, teacher in enumerate(lectures_list, 1):
                        time.sleep(delay_time)
                        print(f"{index}. {teacher}")
                    input_help = \
                        _("Enter the teachers indexes separated by comma (example: 1,2,20) or 0 to select all: ")

                    teachers_indexes = input(input_help)
                    self.logger.debug("Selected teachers indexes: %s which they are: ", teachers_indexes)
                    teachers_indexes = [int(index) for index in teachers_indexes.strip().split(",")]
                    selected_teachers = []
                    if 0 in teachers_indexes:
                        selected_teachers = lectures_list
                        self.logger.debug("All the available teachers are: %s", ', '.join(selected_teachers))
                        teachers_indexes = []
                    for index, teacher in enumerate(lectures_list, 1):
                        if index in teachers_indexes:
                            self.logger.debug("%d. '%s'", index, teacher)
                            selected_teachers.append(teacher)
                    selected_teachers_lists.append(selected_teachers)
                course_choice.available_teachers_for_lecture = selected_teachers_lists[0]
                course_choice.available_teachers_for_practice = selected_teachers_lists[1]
                selected_courses_choices[course_name] = course_choice

        print("\n\n")
        print(_("Generating schedules..."))

        selected_activities = self.database.load_activities_by_courses_choices(selected_courses_choices,
                                                                               campus_name, language)

        settings = Settings()
        settings.language = language

        schedules = self.csp.extract_schedules(selected_activities, selected_courses_choices, settings)

        if not schedules:
            print(_("No schedules were found"))
        else:
            print(_("Done successfully !"))
            print(_("Found %d possible schedules").format(len(schedules)))

            results_path = utils.get_results_path()
            self._save_schedule(schedules, settings, results_path)
            print(_("The schedules were saved in the directory: ") + results_path)
            self._open_results_folder(results_path)

    def run_main_gui_flow(self):
        try:
            self.logger.info("Start the main gui flow")

            self._validate_database('gui')

            # Initialize the language for first time.
            self._initial_language_if_first_time()

            # user = self.gui.open_login_window(self.network.check_connection)
            # self.network.set_user(user)

            settings = self.database.load_settings() or Settings()

            campus_names = self.database.load_campus_names(settings.language)

            years = self.database.load_years()

            settings = self.gui.open_settings_window(settings, campus_names, years)

            language = self.database.get_language()

            if (language and language != settings.language):
                translation.config_language_text(settings.language)

            self.database.save_settings(settings)

            language = settings.language

            campus_name = settings.campus_name

            ask_attendance = not settings.attendance_required_all_courses

            self.logger.info("Loading courses data...")

            courses = self.database.load_active_courses(campus_name, language)

            if not courses:
                message = _("There are no courses in the system, "
                            "please try again with another campus update your database from the server.")
                self.gui.open_notification_window(message, MessageType.ERROR)
                return

            courses_choices = self.database.load_courses_choices(campus_name, language, courses)

            courses_choices = self.gui.open_academic_activities_window(ask_attendance, courses_choices)

            user_courses = []

            for course in courses:
                if course.name in courses_choices.keys():
                    course_choise = courses_choices[course.name]
                    if ask_attendance:
                        course.attendance_required_for_lecture = course_choise.attendance_required_for_lecture
                        course.attendance_required_for_exercise = course_choise.attendance_required_for_exercise
                    user_courses.append(course)

            activities = self.database.load_activities_by_courses_choices(courses_choices, campus_name, language)

            AcademicActivity.union_courses(activities, user_courses)

            activities += self.gui.open_personal_activities_window()

            schedules = self.csp.extract_schedules(activities, courses_choices, settings)

            if not schedules:
                self.gui.open_notification_window(_("No schedule were found"))
            else:
                results_path = utils.get_results_path()
                self._save_schedule(schedules, settings, results_path)
                message = _("The schedules were saved in the directory: ") + results_path
                self.gui.open_notification_window(message)
                self._open_results_folder(results_path)

        except UserClickExitException:
            self.logger.info("User clicked exit button")

        except Exception as error:
            message = "The system encountered an error, please contanct the engeniers."
            self.logger.error("The system encountered an error: %s", str(error))
            self.gui.open_notification_window(_(message), MessageType.ERROR)
