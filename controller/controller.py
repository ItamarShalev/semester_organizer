import os
import sys
import shutil
import subprocess
import time
from collections import defaultdict
from copy import copy
from operator import itemgetter
from typing import List, Dict, Literal, Optional, Any, Set

import utils
from collector.db.db import Database
from collector.gui.gui import Gui, MessageType, UserClickExitException
from convertor.convertor import Convertor
from csp.csp import CSP
from data import translation
from data.academic_activity import AcademicActivity
from data.course_choice import CourseChoice
from data.degree import Degree
from data.language import Language
from data.schedule import Schedule
from data.settings import Settings
from data.day import Day
from data.semester import Semester
from data.output_format import OutputFormat
from data.translation import _

Lecture = str


class Controller:

    def __init__(self):
        self.database = Database()
        self.gui = Gui()
        self.convertor = Convertor()
        self.csp = CSP()
        self.logger = utils.get_logging()
        self.delay_time = 0.12

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
                language = Language[language.upper()]
                translation.config_language_text(language)
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
            sys.exit(0)

    def _console_ask_campus_name(self):
        print(_("Select the campus by enter their index:"))
        available_campuses = self.database.get_common_campuses_names()
        for index, name in enumerate(available_campuses, 1):
            print(f"{index}. {name}")
        campus_index = input(_("Enter the campus index: "))
        campus_name = available_campuses[int(campus_index) - 1]
        print("\n\n")
        return campus_name

    def _console_ask_courses_choices(self, campus_name: str, degrees: Set[Degree]):
        language = Language.get_current()
        courses_choices = self.database.load_courses_choices(campus_name, language, degrees=degrees)
        courses_choices = dict(sorted(courses_choices.items(), key=itemgetter(0)))

        print(_("Select the courses by enter their index:"))
        time.sleep(self.delay_time)
        last_choices = self.database.load_courses_console_choose() or []
        if last_choices:
            print(" 0.", _("Choose your previous selection:"), ", ".join(last_choices))
        last_choices_in_indexes = []
        for index, course_name in enumerate(courses_choices.keys(), 1):
            time.sleep(self.delay_time)
            print(f"{str(index).rjust(2)}.", _("Course:"), f"{course_name}")
            if course_name in last_choices:
                last_choices_in_indexes.append(index)
        input_help = _("Enter the courses indexes separated by comma (example: 1,2,20): ")
        courses_indexes_input = input(input_help)
        self.logger.debug("Selected courses indexes: %s which they are: ", courses_indexes_input)
        courses_indexes = [int(index) for index in courses_indexes_input.strip().split(",")]
        self._validate_is_numbers_in_range(courses_indexes, len(courses_choices), 0 if last_choices else 1)
        if 0 in courses_indexes:
            courses_indexes = last_choices_in_indexes
        else:
            choices = [list(courses_choices.keys())[index - 1] for index in courses_indexes]
            self.database.save_courses_console_choose(choices)
        selected_courses_choices = {}
        for index, (course_name, course_choice) in enumerate(courses_choices.items(), 1):
            if index in courses_indexes:
                self.logger.debug("%d. '%s'", index, course_name)
                selected_courses_choices[course_name] = course_choice

        print("\n\n")
        return selected_courses_choices

    def _console_ask_yes_or_no(self, text: str):
        options = [_("Yes"), _("No")]
        print(_(text))
        for index, option in enumerate(options, 1):
            time.sleep(self.delay_time)
            print(f"{index}. {option}")
        yes_or_no = input(_("Enter the option index: "))
        self._validate_is_number_in_range(yes_or_no, 2, 1)
        yes_no_option = options[int(yes_or_no) - 1]
        self.logger.debug("Selected option: %s", yes_no_option)
        print("\n\n")
        return yes_no_option == _("Yes")

    def _console_save_schedules(self, settings: Settings, schedules: List[Schedule]):
        print(_("Done successfully !"))
        print(_("Found {} possible schedules").format(len(schedules)))

        results_path = utils.get_results_path()
        for try_number in range(1, 4):
            try:
                self._save_schedule(schedules, settings, results_path)
                print(_("The schedules were saved in the directory: ") + results_path)
                self._open_results_folder(results_path)
                break
            except FileExistsError:
                print(_("ERROR: can't save the schedules, maybe the file is open? failed to save in: ") + results_path)
                results_path = utils.get_results_path() + f"_{try_number}"
                print(_("Try to save in directory:"), results_path)

    def _console_ask_favorite_lecturers(self, course_name: str, lecture_type: str, lectures_list: List[Lecture]):
        selected_teachers = []
        if len(lectures_list) == 0:
            selected_teachers = []
        elif len(lectures_list) == 1:
            text = _("There is only one lecture for this the course {} which is {}, automatic select it.")
            text = text.format(course_name, lectures_list[0])
            print(text)
            selected_teachers = lectures_list
        else:
            print("\n\n")
            print(_(f"Select the favorite teachers for {lecture_type} for the course: ") + f"'{course_name}'")
            for index, teacher in enumerate(lectures_list, 1):
                time.sleep(self.delay_time)
                print(f"{index}. {teacher}")
            input_help = \
                _("Enter the teachers indexes separated by comma (example: 1,2,20) or 0 to select all: ")

            teachers_indexes = input(input_help)
            self.logger.debug("Selected teachers indexes: %s which they are: ", teachers_indexes)
            teachers_indexes = [int(index) for index in teachers_indexes.strip().split(",")]
            if 0 in teachers_indexes:
                selected_teachers = lectures_list
                self.logger.debug("All the available teachers are: %s", ', '.join(selected_teachers))
                teachers_indexes = []
            for index, teacher in enumerate(lectures_list, 1):
                if index in teachers_indexes:
                    self.logger.debug("%d. '%s'", index, teacher)
                    selected_teachers.append(teacher)

        return selected_teachers

    def _console_ask_for_favorite_lecturers_all_courses(self, courses_choices: Dict[str, List[CourseChoice]]):
        selected_courses_choices = {}
        for course_name, course_choice in courses_choices.items():
            lectures_lists = [course_choice.available_teachers_for_lecture,
                              course_choice.available_teachers_for_practice]
            lectures_lists = [sorted(lectures_list) for lectures_list in lectures_lists]
            for lecture_type, lectures_list in zip(["lecture", "lab / exercise"], lectures_lists):
                selected = self._console_ask_favorite_lecturers(course_name, lecture_type, lectures_list)
                if lecture_type == "lecture":
                    course_choice.available_teachers_for_lecture = selected
                else:
                    course_choice.available_teachers_for_practice = selected
            selected_courses_choices[course_name] = course_choice
        return selected_courses_choices

    def _yes_no(self, value: bool):
        return _("Yes") if value else _("No")

    def _print_current_settings(self, settings: Settings):
        enter_sentence_format = "\n" + len(_("Explain: ")) * " "
        end_line = "\n\n"

        print(_("Current settings:"))
        print()
        print(_("Attendance required all courses:"), self._yes_no(settings.attendance_required_all_courses))
        print(_("Explain: Count all the courses as attendance is mandatory"), end=enter_sentence_format)
        print(_("and there is no possibility of collision with other courses."), end=enter_sentence_format)
        print(_("If is set to no, you will ask for each course if you will want to be present."), end=end_line)

        campus_name = settings.campus_name or _("Not set")
        print(_("Campus name:"), campus_name)
        print(_("Explain: The name of the campus that you want to search for the courses."), end=end_line)

        print(_("Year of study:"), settings.year)
        print(_("Explain: The year of the courses to be selected and collect from the college."), end=end_line)

        print(_("Semester of study:"), _(str(settings.semester)))
        print(_("Explain: The semester of the courses to be selected and collect from the college."), end=end_line)

        print(_("Degrees:"), ", ".join([_(str(degree)) for degree in settings.degrees]))
        print(_("Explain: The degrees of the courses to be selected and collect from the college."),
              end=enter_sentence_format)
        print(_("You can select several degrees if you want, for example computer science and software engineering."),
              end=end_line)

        print(_("Show hertzog and yeshiva:"), self._yes_no(settings.show_hertzog_and_yeshiva))
        print(_("Explain: Show or don't show the courses for hertzog and yeshiva."), end=end_line)

        print(_("Show only courses with free places:"), self._yes_no(settings.show_only_courses_with_free_places))
        print(_("Explain: Show or don't show the courses that have free places to register."), end=end_line)

        yes_no = self._yes_no(settings.show_only_courses_with_the_same_actual_number)
        print(_("Show only courses with the same actual number:"), yes_no)
        print(_("Explain: Show or don't show the courses that have the same actual number and related."),
              end=enter_sentence_format)
        print(_("there is no guarantee you will get course that have lecture and exercise you can register."),
              end=enter_sentence_format)
        print(_("for example course that have lecture for english speaker and exercise for hebrew speaker."),
              end=end_line)

        days_text = self._days_to_text(settings.show_only_classes_in_days)

        print(_("Show only classes in days:"), days_text)
        print(_("Explain: Show only the courses that have classes in the days you selected."), end=end_line)

        def output_formats_str(output_formats):
            return ", ".join([str(output_format) for output_format in output_formats])

        print(_("Output formats: "), output_formats_str(settings.output_formats))
        print(_("Explain: The output formats the schedules will be saved in."), end=enter_sentence_format)
        print(_("Possible formats: "), output_formats_str(list(OutputFormat)), end="\n\n")

    def _validate_is_number_in_range(self, number: Any, max_number: int, min_number: int = 0):
        try:
            number = int(number)
        except ValueError as error:
            raise ValueError(_("The value '{}' is not a number !").format(number)) from error
        if number < min_number or number > max_number:
            raise ValueError(_("The number must be between {} to {}").format(min_number, max_number))

    def _validate_is_numbers_in_range(self, numbers: list[Any], max_number: int, min_number: int = 0):
        for number in numbers:
            self._validate_is_number_in_range(number, max_number, min_number)

    def _console_ask_default_yes_no(self, text: Optional[str] = None):
        if text:
            print(_(text))
        else:
            print()
        default_yes_no_options = [_("Default"), _("Yes"), _("No")]
        return_values = [None, True, False]
        for index, option in enumerate(default_yes_no_options):
            print(f"{index}. {option}")
        selected_option = input(_("Enter the option index: "))
        self._validate_is_number_in_range(selected_option, len(default_yes_no_options) - 1)
        self.logger.debug("Selected option: %s", default_yes_no_options[int(selected_option)])
        default_yes_no_option = return_values[int(selected_option)]
        return default_yes_no_option

    def _console_ask_for_settings(self, settings: Settings):
        # pylint: disable=too-many-branches
        print(_("Attendance required all courses:"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), self._yes_no(settings.attendance_required_all_courses))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.attendance_required_all_courses = default_yes_no
        print("\n\n")

        campus_name = settings.campus_name or _("Not set")
        print(_("Campus name:"))
        if campus_name != _("Not set"):
            print(_("Select 0 to use the default settings."))
        print(_("Default value:"), settings.campus_name or _("Not set"))
        is_yes = self._console_ask_yes_or_no("Do you want to change the campus name?")
        if is_yes:
            campus_name = self._console_ask_campus_name()
            settings.campus_name = campus_name
        print("\n\n")

        print(_("Year of study:"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), settings.year)
        options = [_("Default")] + [str(year) for year in range(5780, 5788)]
        for index, year in enumerate(options):
            print(f"{index}.", _("Year :"), year)
        selected_option = input(_("Enter the option index: "))
        self._validate_is_number_in_range(selected_option, len(options) - 1)
        self.logger.debug("Selected option: %s", options[int(selected_option)])
        if int(selected_option) != 0:
            settings.year = int(options[int(selected_option)])

        print("\n\n")

        print(_("Semester of study:"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), _(str(settings.semester)))
        # For now only Fall and Spring semesters supported
        options = [_("Default")] + [_(str(Semester.FALL)), _(str(Semester.SPRING))]
        return_options = [settings.semester, Semester.FALL, Semester.SPRING]
        for index, semester in enumerate(options):
            print(f"{index}. {semester}")

        selected_option = input(_("Enter the option index: "))
        self._validate_is_number_in_range(selected_option, len(options) - 1)
        self.logger.debug("Selected option: %s", options[int(selected_option)])
        settings.semester = return_options[int(selected_option)]
        print("\n\n")

        print(_("Degrees:"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), ", ".join([_(str(degree)) for degree in settings.degrees]))
        options = [_("Default")] + [_(str(degree)) for degree in Degree]
        return_options = list(Degree)
        for index, degree in enumerate(options):
            print(f"{index}. {degree}")

        selected_options = input(_("Enter indexes separated by comma (for example 1,2,3):"))
        selected_options = selected_options.split(",")
        self._validate_is_numbers_in_range(selected_options, len(options) - 1)
        self.logger.debug("Selected options: %s",
                          ", ".join([options[int(selected_option)] for selected_option in selected_options]))
        settings.degrees = [return_options[int(selected_option)] for selected_option in selected_options]
        print("\n\n")

        print(_("Show hertzog and yeshiva:"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), self._yes_no(settings.show_hertzog_and_yeshiva))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.show_hertzog_and_yeshiva = default_yes_no

        print("\n\n")

        print(_("Show only courses with free places:"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), self._yes_no(settings.show_only_courses_with_free_places))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.show_only_courses_with_free_places = default_yes_no
        print("\n\n")

        print(_("Show only courses with the same actual number"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), self._yes_no(settings.show_only_courses_with_the_same_actual_number))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.show_only_courses_active_classes = default_yes_no
        print("\n\n")

        days = settings.show_only_classes_in_days
        days_text = self._days_to_text(settings.show_only_classes_in_days)

        print(_("Show only classes in days :"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), days_text)
        options = [_("Default")] + [_(str(day)) for day in days]
        for index, day in enumerate(options):
            print(f"{index}. {day}")
        selected_options = input(_("Enter indexes separated by comma (for example 1,2,3):"))
        selected_options = [int(option) for option in selected_options.split(",")]
        self._validate_is_numbers_in_range(selected_options, len(options) - 1)
        if 0 not in selected_options:
            settings.show_only_classes_in_days = [Day(day) for day in selected_options]

        print("\n\n")

        print(_("Output formats:"))
        print(_("Select 0 to use the default settings."))
        print(_("Default value:"), ", ".join([str(output_format) for output_format in settings.output_formats]))
        # For now only csv supported
        options = [_("Default")] + [OutputFormat.CSV]
        for index, output_format in enumerate(options):
            print(f"{index}.", _("format"), str(output_format))

        selected_options = input(_("Enter indexes separated by comma (for example 1,2,3):"))
        selected_options = [int(option) for option in selected_options.split(",")]
        self._validate_is_numbers_in_range(selected_options, len(options) - 1)
        if 0 not in selected_options:
            settings.output_formats = [OutputFormat.CSV]
        print("\n\n")

        return settings

    def _console_ask_for_attendance_required_all_courses(self, courses_choices: Dict[str, List[CourseChoice]]):
        selected_courses_choices = {}
        message = "Would you like to be present and consider the {} of course with mandatory attendance?"
        for course_name, course_choice in courses_choices.items():
            print(course_name + ":")
            lectures_lists = [course_choice.available_teachers_for_lecture,
                              course_choice.available_teachers_for_practice]
            lectures_lists = [sorted(lectures_list) for lectures_list in lectures_lists]
            for lecture_type, lectures_list in zip(["lecture", "lab / exercise"], lectures_lists):
                is_yes = False
                if len(lectures_list) > 0:
                    is_yes = self._console_ask_yes_or_no(message.format(lecture_type))
                if lecture_type == "lecture":
                    course_choice.attendance_required_for_lecture = is_yes
                else:
                    course_choice.attendance_required_for_practice = is_yes
            selected_courses_choices[course_name] = course_choice
        return selected_courses_choices

    def run_console_flow(self):
        """
        Run the console flow of the program, only for academic activities.
        Console flow will use the default settings.
        and without database nor GUI.
        """
        # For testing purposes
        self.logger.info("Starting console flow")

        language = Language.get_current()
        settings = self.database.load_settings() or Settings()
        language = language or settings.language
        settings.language = language
        translation.config_language_text(language)

        if settings.campus_name:
            campus_name = self.database.translate_campus_name(settings.campus_name)
            settings.campus_name = campus_name

        self.database.save_settings(settings)
        Language.set_current(language)

        self._validate_database('console')

        is_yes = self._console_ask_yes_or_no("Do you want to print the current settings and see their meaning?")

        if is_yes:
            self._print_current_settings(settings)

        is_yes = self._console_ask_yes_or_no("Do you want to change the current settings?")

        if is_yes:
            settings = self._console_ask_for_settings(settings)
            self.database.save_settings(settings)
            language = settings.language

        if not settings.campus_name:
            campus_name = self._console_ask_campus_name()
            settings.campus_name = campus_name
            self.database.save_settings(settings)

        campus_name = settings.campus_name

        courses_choices = self._console_ask_courses_choices(campus_name, settings.degrees)

        is_yes = self._console_ask_yes_or_no("Do you want to select favorite lecturers?")

        if is_yes:
            courses_choices = self._console_ask_for_favorite_lecturers_all_courses(courses_choices)
        if not settings.attendance_required_all_courses:
            message = "Do you want to be present and consider all courses with mandatory attendance?"
            is_yes = self._console_ask_yes_or_no(message)
            if is_yes:
                settings.attendance_required_all_courses = True
                self.database.save_settings(settings)
            else:
                courses_choices = self._console_ask_for_attendance_required_all_courses(courses_choices)

        print("\n\n")
        print(_("Generating schedules..."))

        selected_activities = self.database.load_activities_by_courses_choices(courses_choices, campus_name, language)

        schedules = self.csp.extract_schedules(selected_activities, courses_choices, settings)

        if not schedules:
            print(_("No schedules were found"))
        else:
            self._console_save_schedules(settings, schedules)

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

            if language and language != settings.language:
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

    def _days_to_text(self, days: List[Day]) -> str:
        all_days = set(Day)
        if all_days == days:
            days_text = _("All week days")
        else:
            days.sort(key=lambda day: day.value)
            days_text = ", ".join([_(str(day)) for day in days])
        return days_text
