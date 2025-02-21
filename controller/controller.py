import os
import sys
import shutil
import subprocess
import time
from collections import defaultdict
from operator import itemgetter
from typing import List, Dict, Literal, Optional, Any, Set
from pathlib import Path

import utils
from algorithms.csp import CSP, Status
from algorithms.constraint_courses import ConstraintCourses
from collector.network.network import NetworkHttp, InvalidSemesterTimeRequestException
from collector.db.db import Database
from convertor.convertor import Convertor
from data import translation
from data.academic_activity import AcademicActivity
from data.course_choice import CourseChoice
from data.degree import Degree
from data.language import Language
from data.schedule import Schedule
from data.settings import Settings
from data.message_type import MessageType
from data.day import Day
from data.semester import Semester
from data.output_format import OutputFormat
from data.translation import _
from data.user import User

Lecture = str


class Controller:
    def __init__(self, verbose: bool = False):
        self.database = Database()
        self.convertor = Convertor()
        self.csp = CSP()
        self.network = NetworkHttp()
        self.logger = utils.get_logging()
        self.delay_time = 0.12
        self.max_output = 20
        self.verbose = verbose
        self._clear_command = None

    def _clear_screen(self):
        if not self.verbose:
            if not self._clear_command:
                self._clear_command = "clear"
                return_code = os.system(self._clear_command)
                if return_code != 0:
                    self._clear_command = "cls"
            os.system(self._clear_command)

    def _print(self, text: str, *args, **kwargs):
        print(text, *args, **kwargs, flush=True)

    def run_console_flow(self):
        """
        Run the console flow of the program, only for academic activities.
        Console flow will use the default settings.
        and without database nor GUI.
        """
        self.logger.info("Starting console flow")
        self._clear_screen()
        self.database.init_personal_database_tables()
        language = Language.get_current()
        settings = self.database.load_settings() or Settings()
        language = language or settings.language
        settings.language = language
        settings.year = utils.convert_year(settings.year, language)
        translation.config_language_text(language)

        if settings.campus_name:
            campus_name = self.database.translate_campus_name(settings.campus_name)
            settings.campus_name = campus_name

        self.database.save_settings(settings)
        Language.set_current(language)

        self._validate_database('console')

        is_yes = self._console_ask_yes_or_no("Do you want to print the current settings and see their meaning?")
        self._clear_screen()
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

        self._console_ask_for_courses_already_done_if_needed(settings, language)

        campus_name = settings.campus_name
        user = self.database.load_user_data()
        self.network.set_user(user)

        self._console_alert_if_missing_user_data_and_need_to_login(settings, user)

        activities_ids_groups = self._console_get_activities_ids_can_enroll(settings, user)

        courses_choices = self._console_ask_courses_choices(campus_name, settings, activities_ids_groups)

        if not courses_choices:
            self._print(_("No courses were found, please try again with different settings."))
            return

        self._clear_screen()
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

        self._clear_screen()
        self._print(_("Generating schedules..."))

        all_courses_parent_numbers = {course_choice.parent_course_number for course_choice in courses_choices.values()}

        selected_activities = self.database.load_activities_by_parent_courses_numbers(all_courses_parent_numbers,
                                                                                      campus_name, language,
                                                                                      settings.degrees)
        AcademicActivity.union_attendance_required(selected_activities, courses_choices)

        courses_degrees = self.database.load_degrees_courses()

        schedules = self.csp.extract_schedules(selected_activities, courses_choices, settings, activities_ids_groups,
                                               courses_degrees)

        status = self.csp.get_status()

        self._console_print_status_results(status)

        self._console_save_schedules(settings, schedules)

    def run_main_gui_flow(self):
        # Support users who don't have tkinter.
        # pylint: disable=import-outside-toplevel
        translation.config_language_text(Language.ENGLISH)
        from collector.gui.gui import Gui, UserClickExitException
        gui = Gui()
        try:

            self.logger.info("Start the main gui flow")

            self._validate_database('gui')

            # Initialize the language for first time.
            # Currently, only English supported.
            # self._initial_language_if_first_time(gui)

            # user = self.gui.open_login_window(self.network.check_connection)
            # self.network.set_user(user)

            settings = self.database.load_settings() or Settings()

            # Override the settings with the default settings.
            settings.language = Language.ENGLISH

            campus_names = self.database.load_campus_names(settings.language)

            # years = self.database.load_years()

            settings = gui.open_settings_window(settings, campus_names, {utils.get_current_hebrew_year(): "2013"})

            # language = self.database.get_language()

            # if language and language != settings.language:
            #    translation.config_language_text(settings.language)

            self.database.save_settings(settings)

            language = settings.language

            campus_name = settings.campus_name

            ask_attendance = not settings.attendance_required_all_courses

            self.logger.info("Loading courses data...")

            courses = self.database.load_active_courses(campus_name, language)

            if not courses:
                message = _("There are no courses in the system, "
                            "please try again with another campus update your database from the server.")
                gui.open_notification_window(message, MessageType.ERROR)
                return

            courses_choices = self.database.load_courses_choices(campus_name, language, settings.degrees, courses)

            courses_choices = gui.open_academic_activities_window(ask_attendance, courses_choices)

            user_courses = []

            for course in courses:
                if course.name in courses_choices:
                    course_choice = courses_choices[course.name]
                    if ask_attendance:
                        course.attendance_required_for_lecture = course_choice.attendance_required_for_lecture
                        course.attendance_required_for_exercise = course_choice.attendance_required_for_practice
                    user_courses.append(course)

            activities = self.database.load_activities_by_courses_choices(courses_choices, campus_name, language)

            AcademicActivity.union_courses(activities, user_courses)

            activities += gui.open_personal_activities_window()

            schedules = self.csp.extract_schedules(activities, courses_choices, settings)

            if not schedules:
                gui.open_notification_window(_("No schedule were found"))
            else:
                results_path = utils.get_results_path()
                Controller.save_schedules(schedules, settings, results_path, self.max_output, self.convertor)
                self._open_results_folder(results_path)
                message = _("The schedules were saved in the directory: ") + results_path
                gui.open_notification_window(message)

        except UserClickExitException:
            self.logger.info("User clicked exit button")

        except Exception as error:
            message = "The system encountered an error, please contact the engineers."
            self.logger.error("The system encountered an error: %s", str(error))
            gui.open_notification_window(_(message), MessageType.ERROR)

    def _console_print_status_results(self, status: Status):
        if status is Status.FAILED:
            self._print(_("No schedules were found"))
            first_name, second_name = self.csp.get_last_activities_crashed()
            if first_name and second_name:
                self._print(_("The last activities that were crashed were: (you may want to give up one of them)"))
                self._print(_("The activity: {} And {}").format(first_name, second_name))
        elif status is Status.SUCCESS_WITH_ONE_FAVORITE_LECTURER:
            self._print(_("No schedules were found with all favorite lecturers, but found with some of them"))
        elif status is Status.SUCCESS_WITHOUT_FAVORITE_LECTURERS:
            self._print(_("No schedules were found with favorite lecturers"))

    def _initial_language_if_first_time(self, gui):
        settings = self.database.load_settings()
        if not settings:
            message = _("Welcome to the semester organizer!\nPlease choose a language\nThe current language is: ")
            message += _(str(Language.get_current()))
            language = gui.open_notification_window(message, MessageType.INFO, list(map(str, Language)))
            if language and Language.contains(language):
                language = Language[language.upper()]
                translation.config_language_text(language)
                if self.database.get_language() != language:
                    self.database.save_language(language)

    @staticmethod
    def save_schedules(all_schedules: List[Schedule], settings: Settings, results_path: Path, max_output: int = 20,
                       convertor: Convertor = Convertor()):
        # Save the most spread days and least spread days
        most_spread_days = defaultdict(list)
        least_spread_days = defaultdict(list)
        schedules_by_learning_days = defaultdict(list)
        schedules_by_standby_time = defaultdict(list)
        output_formats = settings.output_formats

        for schedule in all_schedules:
            standby_in_minutes = schedule.get_standby_in_minutes()
            learning_days = schedule.get_learning_days()
            schedule.file_name = \
                f"{schedule.file_name}_" + \
                _("with_{}_learning_days_and_{}_minutes_study_time").format(len(learning_days), standby_in_minutes)
            schedules_by_learning_days[len(learning_days)].append(schedule)
            schedules_by_standby_time[standby_in_minutes].append(schedule)

        schedules_by_learning_days = dict(sorted(schedules_by_learning_days.items(), key=itemgetter(0)))
        schedules_by_standby_time = dict(sorted(schedules_by_standby_time.items(), key=itemgetter(0)))

        if len(schedules_by_learning_days.keys()) > 1:
            most_spread_days = schedules_by_learning_days[max(schedules_by_learning_days.keys())]
            least_spread_days = schedules_by_learning_days[min(schedules_by_learning_days.keys())]

        # Get the lowest standby time
        if len(schedules_by_standby_time.keys()) > 1:
            schedules_by_standby_time = schedules_by_standby_time[min(schedules_by_standby_time.keys())]
        else:
            schedules_by_standby_time = None

        all_schedules_path = results_path / _("all_schedules")
        most_spread_days_path = results_path / _("most_spread_days")
        least_spread_days_path = results_path / _("least_spread_days")
        least_standby_time_path = results_path / _("least_standby_time")

        shutil.rmtree(results_path, ignore_errors=True)

        if len(all_schedules) > max_output:
            all_schedules = all_schedules[:max_output]
        convertor.convert_activities(all_schedules, all_schedules_path, output_formats)
        if most_spread_days and least_spread_days:
            if len(most_spread_days) > max_output:
                most_spread_days = most_spread_days[:max_output]
            if len(least_spread_days) > max_output:
                least_spread_days = least_spread_days[:max_output]
            convertor.convert_activities(most_spread_days, most_spread_days_path, output_formats)
            convertor.convert_activities(least_spread_days, least_spread_days_path, output_formats)
        if schedules_by_standby_time:
            if len(schedules_by_standby_time) > max_output:
                schedules_by_standby_time = schedules_by_standby_time[:max_output]
            convertor.convert_activities(schedules_by_standby_time, least_standby_time_path, output_formats)

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

    def _open_results_folder(self, results_path: Path):
        subprocess.call(f"explorer {results_path}", shell=True)

    def _validate_database(self, output_type: Literal['gui', 'console']):
        if not self.database.are_shared_tables_exists():
            self.logger.error("ERROR: Missing database, can't continue.")
            msg = _("Missing database, can't continue, please download the database file from the github server "
                    "and import the database by running :")
            msg += "'python __main__.py -- database_path {path_to_database.db}'"
            if output_type == 'gui':
                pass
                # self.gui.open_notification_window(msg, MessageType.ERROR)
            elif output_type == 'console':
                self._print(msg)
            sys.exit(0)

    def _console_ask_campus_name(self):
        self._clear_screen()
        self._print(_("Select the campus by enter their index:"))
        available_campuses = self.database.get_common_campuses_names()
        for index, name in enumerate(available_campuses, 1):
            self._print(f"{index}. {name}")
        campus_index = input(_("Enter the campus index: "))
        campus_name = available_campuses[int(campus_index) - 1]
        self._print("\n\n")
        return campus_name

    def _console_ask_courses_choices(self, campus_name: str, settings: Settings,
                                     activities_ids_can_enroll: Dict[str, Set[int]]) -> Dict[str, CourseChoice]:
        courses_choices = self._get_courses_choices_to_ask(campus_name, settings, activities_ids_can_enroll)
        self._print(_("Select the courses by enter their index:"))
        time.sleep(self.delay_time)
        last_choices_parent_courses_numbers = self.database.load_courses_console_choose() or []
        last_choices = [course_choice.name for course_choice in courses_choices.values()
                        if str(course_choice.parent_course_number) in last_choices_parent_courses_numbers]
        if last_choices:
            self._print(" 0.", _("Choose your previous selection:"), ", ".join(last_choices))
        last_choices_in_indexes = []
        for index, course_name in enumerate(courses_choices.keys(), 1):
            time.sleep(self.delay_time)
            self._print(f"{str(index).rjust(2)}.", _("Course:"), f"{course_name}")
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
            choices = [str(list(courses_choices.values())[index - 1].parent_course_number) for index in courses_indexes]
            self.database.save_courses_console_choose(choices)
        selected_courses_choices = {}
        for index, (course_name, course_choice) in enumerate(courses_choices.items(), 1):
            if index in courses_indexes:
                self.logger.debug("%d. '%s'", index, course_name)
                selected_courses_choices[course_name] = course_choice

        self._print("\n\n")
        return selected_courses_choices

    def _console_ask_yes_or_no(self, text: str):
        options = [_("Yes"), _("No")]
        self._print(_(text))
        for index, option in enumerate(options, 1):
            time.sleep(self.delay_time)
            self._print(f"{index}. {option}")
        yes_or_no = input(_("Enter the option index: "))
        self._validate_is_number_in_range(yes_or_no, 2, 1)
        yes_no_option = options[int(yes_or_no) - 1]
        self.logger.debug("Selected option: %s", yes_no_option)
        self._print("\n\n")
        return yes_no_option == _("Yes")

    def _console_save_schedules(self, settings: Settings, schedules: Optional[List[Schedule]]):
        if not schedules:
            return
        self._print(_("Found {} possible schedules").format(len(schedules)))
        if len(schedules) > self.max_output:
            self._print(_("Saving only the best {} schedules").format(self.max_output))
        self._print(_("Saving the schedules, it can take few seconds..."))

        results_path = utils.get_results_path()
        for try_number in range(1, 4):
            try:
                Controller.save_schedules(schedules, settings, results_path, self.max_output, self.convertor)
                self._print(_("Done successfully !"))
                self._print(_("The schedules were saved in the directory:"), results_path)
                self._open_results_folder(results_path)
                break
            except FileExistsError:
                text = _("ERROR: can't save the schedules, maybe the file is open? failed to save in: ")
                text += str(results_path)
                self._print(text)
                results_path = utils.get_results_path() / f"_{try_number}"
                self._print(_("Try to save in directory:"), results_path)

    def _console_ask_favorite_lecturers(self, course_name: str, lecture_type: str, lectures_list: List[Lecture]):
        selected_teachers = []
        if len(lectures_list) == 0:
            selected_teachers = []
        elif len(lectures_list) == 1:
            text = _("There is only one lecture for this the course {} which is {}, automatic select it.")
            text = text.format(course_name, lectures_list[0])
            self._print(text)
            selected_teachers = lectures_list
        else:
            self._print(_(f"Select the favorite teachers for {lecture_type} for the course: ") + f"'{course_name}'")
            for index, teacher in enumerate(lectures_list, 1):
                time.sleep(self.delay_time)
                self._print(f"{index}. {teacher}")
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

    def _console_ask_for_favorite_lecturers_all_courses(self, courses_choices: Dict[str, CourseChoice]) \
            -> Dict[str, CourseChoice]:
        selected_courses_choices = {}
        for course_name, course_choice in courses_choices.items():
            self._clear_screen()
            lectures_lists = [course_choice.available_teachers_for_lecture,
                              course_choice.available_teachers_for_practice]
            lectures_lists = [sorted(lectures_list) for lectures_list in lectures_lists]
            for lecture_type, lectures_list in zip(["lecture", "lab / exercise"], lectures_lists):
                if lecture_type == "lab / exercise":
                    self._print("\n\n")
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
        self._clear_screen()
        enter_sentence_format = "\n" + len(_("Explain: ")) * " "
        end_line = "\n\n"

        self._print(_("Current settings:"))
        self._print("")
        self._print(_("Attendance required all courses:"), self._yes_no(settings.attendance_required_all_courses))
        self._print(_("Explain: Count all the courses as attendance is mandatory"), end=enter_sentence_format)
        self._print(_("and there is no possibility of collision with other courses."), end=enter_sentence_format)
        self._print(_("If is set to no, you will ask for each course if you will want to be present."), end=end_line)

        campus_name = settings.campus_name or _("Not set")
        self._print(_("Campus name:"), campus_name)
        self._print(_("Explain: The name of the campus that you want to search for the courses."), end=end_line)

        user = self.database.load_user_data()
        text_exists = _("Exists in the system") if user else _("Not exists in the system")
        self._print(_("User details:"), text_exists)
        self._print(_("Explain: The user name and password that you used to login to Levnet."),
                    end=enter_sentence_format)
        self._print(_("Used to check which courses you can actually register in the Levnet website."), end=end_line)

        self._print(_("Show only classes can enroll in:"), self._yes_no(settings.show_only_classes_can_enroll))
        self._print(_("Explain: Show only the classes that you can enroll in Levnet."), end=enter_sentence_format)
        self._print(_("This setting must use connection to levnet, and therefore need your username and password"),
                    end=enter_sentence_format)
        self._print(_("Don't worry, the details will save only in your computer and will use only in Levnet."),
                    end=end_line)

        yes_no = self._yes_no(settings.show_only_courses_with_prerequisite_done)
        self._print(_("Show only courses with prerequisite done:"), yes_no)
        self._print(_("Explain: Show only courses that you can take because you have already passed the prerequisite."),
                    end=enter_sentence_format)
        self._print(_("If no data about the prerequisite exists in the system, the course will be shown anyway."),
                    end=enter_sentence_format)
        self._print(_("Courses whose prerequisites can be taken in parallel will be shown in any case."), end=end_line)

        self._print(_("Year of study:"), settings.year)
        self._print(_("Explain: The year of the courses to be selected and collect from the college."), end=end_line)

        self._print(_("Semester of study:"), _(str(settings.semester)))
        self._print(_("Explain: The semester of the courses to be selected and collect from the college."),
                    end=end_line)

        self._print(_("Degree you are studying:"), _(str(settings.degree)))
        self._print(_("Explain: The degree that you are currently studying."), end=end_line)
        self._print(_("This settings is used to show courses even if you can't enroll in them."), end=end_line)

        self._print(_("Degrees:"), ", ".join([_(str(degree)) for degree in settings.degrees]))
        self._print(_("Explain: The degrees of the courses to be selected and collect from the college."),
                    end=enter_sentence_format)
        text = _("You can select several degrees if you want, for example computer science and software engineering.")
        self._print(text, end=end_line)

        self._print(_("Show hertzog and yeshiva:"), self._yes_no(settings.show_hertzog_and_yeshiva))
        self._print(_("Explain: Show or don't show the courses for hertzog and yeshiva."), end=end_line)

        self._print(_("Show english courses of ESP:"), self._yes_no(settings.show_english_speaker_courses))
        self._print(_("Explain: Show or don't show the courses for English Speaker Program."), end=end_line)

        self._print(_("Show only courses with free places:"), self._yes_no(settings.show_only_courses_with_free_places))
        self._print(_("Explain: Show or don't show the courses that have free places to register."), end=end_line)

        yes_no = self._yes_no(settings.show_only_courses_with_the_same_actual_number)
        self._print(_("Show only courses with the same actual number:"), yes_no)
        self._print(_("Explain: Show or don't show the courses that have the same actual number and related."),
                    end=enter_sentence_format)
        self._print(_("there is no guarantee you will get course that have lecture and exercise you can register."),
                    end=enter_sentence_format)
        self._print(_("for example course that have lecture for english speaker and exercise for hebrew speaker."),
                    end=end_line)

        days_text = self._days_to_text(settings.show_only_classes_in_days)

        self._print(_("Show only classes in days:"), days_text)
        self._print(_("Explain: Show only the courses that have classes in the days you selected."), end=end_line)

        def output_formats_str(output_formats):
            return ", ".join([str(output_format) for output_format in output_formats])

        self._print(_("Output formats: "), output_formats_str(settings.output_formats))
        self._print(_("Explain: The output formats the schedules will be saved in."), end=enter_sentence_format)
        self._print(_("Possible formats: "), output_formats_str(list(OutputFormat)), end="\n\n")

        self._print(_("Don't show courses already done:"), self._yes_no(settings.dont_show_courses_already_done))
        self._print(_("Explain: Don't show the courses that you already done in the past."), end=end_line)

        courses_already_done = self.database.load_courses_already_done(Language.get_current())
        if courses_already_done:
            is_yes = self._console_ask_yes_or_no("Do you want to show all courses already done list?")
            self._clear_screen()
            if is_yes:
                names_already_done = [course.name for course in courses_already_done]
                self._print(_("Courses already done:"))
                for index, name in enumerate(names_already_done, 1):
                    self._print(f"{str(index).rjust(2)}. {name}")
            self._print(end_line)

    def _validate_is_number_in_range(self, number: Any, max_number: int, min_number: int = 0):
        try:
            number = int(number)
        except ValueError as error:
            raise ValueError(_("The value '{}' is not a number !").format(number)) from error
        if number < min_number or number > max_number:
            raise ValueError(_("The number must be between {} to {}").format(min_number, max_number))

    def _validate_is_numbers_in_range(self, numbers: List[Any], max_number: int, min_number: int = 0):
        for number in numbers:
            self._validate_is_number_in_range(number, max_number, min_number)

    def _console_ask_default_yes_no(self, text: Optional[str] = ""):
        self._print(_(text))
        default_yes_no_options = [_("Default"), _("Yes"), _("No")]
        return_values = [None, True, False]
        for index, option in enumerate(default_yes_no_options):
            self._print(f"{index}. {option}")
        selected_option = input(_("Enter the option index: "))
        self._validate_is_number_in_range(selected_option, len(default_yes_no_options) - 1)
        self.logger.debug("Selected option: %s", default_yes_no_options[int(selected_option)])
        default_yes_no_option = return_values[int(selected_option)]
        return default_yes_no_option

    def _console_ask_for_settings(self, settings: Settings):
        # pylint: disable=too-many-branches
        self._clear_screen()
        self._print(_("Campus name:"))
        self._print(_("Default value:"), settings.campus_name or _("Not set"))
        is_yes = self._console_ask_yes_or_no("Do you want to change the campus name?")
        if is_yes:
            campus_name = self._console_ask_campus_name()
            settings.campus_name = campus_name
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Show only classes can enroll in:"))
        self._print(_("Default value:"), self._yes_no(settings.show_only_classes_can_enroll))
        default_yes_no = self._console_ask_default_yes_no("Do you want to show only the courses you can enroll in?")
        if default_yes_no is not None:
            settings.show_only_classes_can_enroll = default_yes_no
        self._print("\n\n")
        self._clear_screen()

        exists_text = _("Exists in the system") if self.database.load_user_data() else _("Not exists in the system")
        self._print(_("User details:"))
        self._print(exists_text)
        is_yes = self._console_ask_yes_or_no("Do you want to set the user details?")
        if is_yes:
            user = self._console_ask_user_details()
            self.database.save_user_data(user)
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Show only courses with prerequisites done:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), self._yes_no(settings.show_only_courses_with_prerequisite_done))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.show_only_courses_with_prerequisite_done = default_yes_no
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Attendance required all courses:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), self._yes_no(settings.attendance_required_all_courses))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.attendance_required_all_courses = default_yes_no
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Year of study:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), settings.year)
        options = [_("Default")] + [str(year) for year in range(5780, 5788)]
        for index, year in enumerate(options):
            self._print(f"{index}.", _("Year :"), year)
        selected_option = input(_("Enter the option index: "))
        self._validate_is_number_in_range(selected_option, len(options) - 1)
        self.logger.debug("Selected option: %s", options[int(selected_option)])
        if int(selected_option) != 0:
            settings.year = int(options[int(selected_option)])

        self._print("\n\n")
        self._clear_screen()

        self._print(_("Semester of study:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), _(str(settings.semester)))
        # For now only Fall and Spring semesters supported
        options = [_("Default")] + [_(str(Semester.FALL)), _(str(Semester.SPRING))]
        return_options = [settings.semester, Semester.FALL, Semester.SPRING]
        for index, semester in enumerate(options):
            self._print(f"{index}. {semester}")

        selected_option = input(_("Enter the option index: "))
        self._validate_is_number_in_range(selected_option, len(options) - 1)
        self.logger.debug("Selected option: %s", options[int(selected_option)])
        settings.semester = return_options[int(selected_option)]
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Degree you are studying:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), _(str(settings.degree)))
        options = [_("Default")] + [_(str(degree)) for degree in Degree]
        return_options = [settings.degree] + list(Degree)
        for index, degree in enumerate(options):
            self._print(f"{index}. {degree}")

        selected_option = input(_("Enter the option index: "))
        self._validate_is_number_in_range(selected_option, len(options) - 1)
        self.logger.debug("Selected option: %s", options[int(selected_option)])
        settings.degree = return_options[int(selected_option)]
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Degrees:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), ", ".join([_(str(degree)) for degree in settings.degrees]))
        options = [_("Default")] + [_(str(degree)) for degree in Degree]
        return_options = list(Degree)
        for index, degree in enumerate(options):
            self._print(f"{index}. {degree}")

        selected_options = input(_("Enter indexes separated by comma (for example 1,2,3):"))
        selected_options = selected_options.split(",")
        self._validate_is_numbers_in_range(selected_options, len(options) - 1)
        if "0" in selected_options:
            self.logger.debug("Selected default.")
        else:
            settings.degrees = [return_options[int(selected_option) - 1] for selected_option in selected_options]
            self.logger.debug("Selected options: %s", ", ".join([str(degree) for degree in settings.degrees]))
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Show hertzog and yeshiva:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), self._yes_no(settings.show_hertzog_and_yeshiva))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.show_hertzog_and_yeshiva = default_yes_no

        self._print("\n\n")
        self._clear_screen()

        self._print(_("Show English speaker courses:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), self._yes_no(settings.show_english_speaker_courses))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.show_english_speaker_courses = default_yes_no

        self._print("\n\n")
        self._clear_screen()

        self._print(_("Show only courses with free places:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), self._yes_no(settings.show_only_courses_with_free_places))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.show_only_courses_with_free_places = default_yes_no
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Show only courses with the same actual number"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), self._yes_no(settings.show_only_courses_with_the_same_actual_number))
        default_yes_no = self._console_ask_default_yes_no()
        if default_yes_no is not None:
            settings.show_only_courses_active_classes = default_yes_no
        self._print("\n\n")
        self._clear_screen()

        days_text = self._days_to_text(settings.show_only_classes_in_days)

        self._print(_("Show only classes in days :"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), days_text)
        options = [_("Default")] + [_(str(day)) for day in Day]
        for index, day in enumerate(options):
            self._print(f"{index}. {day}")
        selected_options = input(_("Enter indexes separated by comma (for example 1,2,3):"))
        selected_options = [int(option) for option in selected_options.split(",")]
        self._validate_is_numbers_in_range(selected_options, len(options) - 1)
        if 0 not in selected_options:
            settings.show_only_classes_in_days = [Day(day) for day in selected_options]

        self._print("\n\n")
        self._clear_screen()

        self._print(_("Output formats:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), ", ".join([str(output_format) for output_format in settings.output_formats]))
        # For now only csv supported
        options = [_("Default")] + list(OutputFormat)
        for index, output_format in enumerate(options):
            self._print(f"{index}.", _("format"), str(output_format))

        selected_options = input(_("Enter indexes separated by comma (for example 1,2,3):"))
        selected_options = [int(option) for option in selected_options.split(",")]
        self._validate_is_numbers_in_range(selected_options, len(options) - 1)
        if 0 not in selected_options:
            settings.output_formats = [options[index] for index in selected_options]
        self._print("\n\n")
        self._clear_screen()

        self._print(_("Don't show courses already done:"))
        self._print(_("Select 0 to use the default settings."))
        self._print(_("Default value:"), self._yes_no(settings.dont_show_courses_already_done))
        default_yes_no = self._console_ask_default_yes_no("Do you want to hide courses already done?")
        if default_yes_no is not None:
            settings.dont_show_courses_already_done = default_yes_no
            if default_yes_no:
                is_yes = self._console_ask_yes_or_no("Do you want to edit the courses already done list?")
                if is_yes:
                    self._console_edit_courses_already_done(settings)

        return settings

    def _console_ask_for_attendance_required_all_courses(self, courses_choices: Dict[str, CourseChoice]) \
            -> Dict[str, CourseChoice]:
        selected_courses_choices = {}
        self._clear_screen()
        message = "Would you like to be present and consider the {} of course with mandatory attendance?"
        for course_name, course_choice in courses_choices.items():
            self._print(course_name + ":")
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

    def _days_to_text(self, days: List[Day]) -> str:
        all_days = set(Day)
        if all_days == set(days):
            days_text = _("All week days")
        else:
            days.sort(key=lambda day: day.value)
            days_text = ", ".join([_(str(day)) for day in days])
        return days_text

    def _console_ask_user_details(self):
        self._clear_screen()
        user = None
        while not user:
            self._print(_("Please enter your user details:"))
            username = input(_("Username:"))
            password = input(_("Password:"))
            user = User(username, password)
            if not user:
                self._print(_("User details can't be empty, please try again."))
                continue
            self._print(_("Connecting to the server..."))
            if self.network.check_connection(user):
                self._print(_("Your user details are correct and can continue."))
            else:
                self._print(_("Your user details are incorrect, please try again."))
                user = None
        return user

    def _console_alert_if_missing_user_data_and_need_to_login(self, settings: Settings, user: User):
        self._clear_screen()
        if settings.show_only_classes_can_enroll and not user:
            self._print(_("Show only courses you can enroll, courses or teacher that you can't enroll will no shown."))
            self._print(_("Anyway you can set this setting to 'No' and see all the courses and teachers."))
            self._print(_("And then ask from the student secretariat to enroll in the course."))
            self._print(_("Can't guarantee that they will enroll you or it will be fast."))
            self._print(_("Need to login to Levnet to use this feature."))
            is_yes = self._console_ask_yes_or_no("Do you want to set your username and password (if not - pass)?")
            if is_yes:
                user = self._console_ask_user_details()
                self.database.save_user_data(user)
                self.network.set_user(user)
            else:
                settings.show_only_classes_can_enroll = False
                self.database.save_settings(settings)
            self._print("\n\n")

    def _console_get_activities_ids_can_enroll(self, settings: Settings, user: User):
        self._clear_screen()
        activities_ids_groups = {}
        if settings.show_only_classes_can_enroll and user:
            activities_ids_groups = self.database.load_activities_ids_groups_can_enroll_in()
            use_last_data = True
            if activities_ids_groups:
                message = "Do you want to reset the activities list you can enroll in and extract from the Levnet?"
                use_last_data = self._console_ask_yes_or_no(message)
            if use_last_data:
                try:
                    if settings.dont_show_courses_already_done:
                        courses_already_did = self.database.load_courses_already_done(Language.get_current())
                        parent_courses_already_done = [course.parent_course_number for course in courses_already_did]
                    else:
                        parent_courses_already_done = []
                    max_tries = 5
                    message = "Fail in try number {}/{}, Will try again, Levnet is too slow now."
                    for number_try in range(1, max_tries + 1):
                        try:
                            self._print(_("Extracting activities list you can enroll in from Levnet..."))
                            activities_ids_groups = \
                                self.network.extract_all_activities_ids_can_enroll_in(settings,
                                                                                      parent_courses_already_done)
                            self._print(_("Extract all activities can enroll successfully."))
                            break
                        except InvalidSemesterTimeRequestException:
                            self._print(_("Registration isn't available, it's not the registration period."))
                            activities_ids_groups = {}
                            break
                        except Exception as error:
                            self._print(_(message).format(number_try, max_tries))
                            error_message = message.format(number_try, max_tries) + "ERROR: " + str(error)
                            self.logger.warning(error_message)

                    self.database.save_activities_ids_groups_can_enroll_in(activities_ids_groups)
                except Exception as error:
                    self.logger.error("ERROR: While try to extract all activities ids can enroll in, error: %s", error)
                    self._print(_("Error occurred while trying to extract the courses you can enroll in."))
                    text = _("Check connection and try again, will use the last data or will not filter the courses.")
                    self._print(text)
        return activities_ids_groups

    def _console_edit_courses_already_done(self, settings: Settings):
        self._clear_screen()
        courses_already_done = self.database.load_courses_already_done(Language.get_current())
        all_courses = self.database.load_courses(Language.get_current(), settings.degrees)
        finish_successfully = False
        message = "Do you want to add all courses from the start? (otherwise add to the exists list)"
        if courses_already_done:
            is_yes = self._console_ask_yes_or_no(message)
            if is_yes:
                self.database.clear_courses_already_done()
                courses_already_done = []

        text = _("We can help you to extract part of the courses you already done by extract them from the Levnet.")
        self._print(text)
        self._print(_("But you need to login to Levnet to use this feature."))
        self._print(_("Anyway, courses you do now or didn't pass will not be added."))
        is_yes = self._console_ask_yes_or_no("Do you want to extract the data from the Levnet?")
        if is_yes:
            user = self.database.load_user_data()
            if not user:
                user = self._console_ask_user_details()
                self.database.save_user_data(user)
            self.network.set_user(user)
            courses = self.network.extract_courses_already_did()
            courses_already_done = {course for course in all_courses for course_name, course_number in courses
                                    if course_number == course.course_number}
            self.database.save_courses_already_done(courses_already_done)

        courses_already_done = self.database.load_courses_already_done(Language.get_current())
        courses = [course for course in all_courses if course not in courses_already_done]
        courses.sort(key=lambda course: course.name)
        while not finish_successfully:
            for index, course in enumerate(courses, 1):
                self._print(f"{str(index).rjust(2)}.", _("Course:"), course.name)

            courses_indexes_input = input(_("Enter the courses you did indexes separated by comma (example: 1,2,20): "))
            self.logger.debug("Selected courses indexes: %s which they are: ", courses_indexes_input)
            courses_indexes = [int(index) for index in courses_indexes_input.strip().split(",")]
            self._validate_is_numbers_in_range(courses_indexes, len(courses), 1)
            choices = [courses[index - 1] for index in courses_indexes]
            self._print(_("The selected courses:"))
            for index, choice in enumerate(choices, 1):
                self._print(f"{str(index).rjust(2)}.", _("Course:"), choice.name)

            finish_successfully = self._console_ask_yes_or_no("Are you sure you want to add these courses to the list?")
            if finish_successfully:
                self.database.save_courses_already_done(set(choices))
                self._print(_("Courses already done list updated successfully."))
                self._print("\n\n")

    def _console_ask_for_courses_already_done_if_needed(self, settings: Settings, language: Language):
        courses_already_done = self.database.load_courses_already_done(language) or []
        self._clear_screen()
        if not courses_already_done and settings.dont_show_courses_already_done:
            self._print(_("Setting 'don't show courses already done is on', but there are no courses already done."))
            is_yes = self._console_ask_yes_or_no("Do you want to add the courses you already done?")
            if is_yes:
                self._console_edit_courses_already_done(settings)
            else:
                settings.dont_show_courses_already_done = False
                self.database.save_settings(settings)

    def _get_courses_choices_to_ask(self, campus_name: str, settings: Settings,
                                    activities_ids: Dict[str, Set[int]]) -> Dict[str, CourseChoice]:
        language = Language.get_current()
        courses_already_done = self.database.load_courses_already_done(language)
        degrees = settings.degrees
        ids = list(activities_ids.keys())
        courses_choices = self.database.load_courses_choices(campus_name, language, degrees, None, ids, True, settings)
        for course in courses_already_done:
            if course.name in courses_choices:
                courses_choices.pop(course.name)

        if settings.show_only_courses_with_prerequisite_done and courses_already_done:
            constraint_courses = ConstraintCourses()
            courses_cant_do = constraint_courses.get_courses_cant_do()
            for _course_name, course_parent_number in courses_cant_do:
                for course_choice in courses_choices.values():
                    if course_choice.parent_course_number == course_parent_number:
                        courses_choices.pop(course_choice.name)
                        break

        courses_choices = utils.sort_dict_by_key(courses_choices)
        return courses_choices
