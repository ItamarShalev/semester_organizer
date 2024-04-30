import json
import sys
from argparse import Namespace, ArgumentParser
from pathlib import Path
from typing import List, Optional, Any, Dict

main_project_dir = Path(__file__).parent.parent.parent
sys.path.append(str(main_project_dir))

import utils
from collector.db.db import Database
from collector.network.network import NetworkHttp
from data.course_choice import CourseChoice
from data.language import Language
from data import translation
from data.settings import Settings
from data.user import User
from data.output_format import OutputFormat
from data.schedule import Schedule
from data.translation import _
from utils import ConsoleApi
from algorithms.csp import CSP, Status
from controller.controller import Controller


class GetCampuses(ConsoleApi):

    def _args_parse(self, parser: ArgumentParser):
        parser.add_argument("--output_file", type=Path, default="result.json",
                            help="Output file to write results to.")
        parser.add_argument("--only_common", action="store_true", default=False,
                            help="Load only common campuses.")

    def _initialize_and_validate(self, args: Optional[Namespace] = None):
        args.output_file = args.output_file.resolve()
        self.write_result_file(args.output_file, status=False)
        translation.config_language_text(Language.HEBREW)

    def _invoke(self, args: Optional[Namespace] = None) -> Any:
        database = Database()
        campuses = database.load_campuses()
        if args.only_common:
            filter_campuses = database.get_common_campuses_names()
            campuses = {campus_id: (english_name, hebrew_name) for campus_id, (english_name, hebrew_name)
                        in campuses.items()
                        if english_name in filter_campuses or hebrew_name in filter_campuses}
        self.logger.info("Campuses loaded")
        list_campuses = []
        for campus_id, (english_name, hebrew_name) in campuses.items():
            list_campuses.append({
                "id": campus_id,
                "english_name": english_name,
                "hebrew_name": hebrew_name,
            })
        self.logger.info(f"Write results to '{args.output_file}'")
        self.write_result_file(args.output_file, result=list_campuses, status=True)

    def help_examples(self) -> List[str]:
        return [
            "--output_file result.json",
            "--output_file result.json --only_common",
        ]

    def help_long(self) -> str:
        return self.help_short()

    def help_short(self) -> str:
        return "Get all campuses names and their ids."


class GetCourses(ConsoleApi):

    def _args_parse(self, parser: ArgumentParser):
        parser.add_argument("--output_file", type=Path, default="result.json",
                            help="Output file to write results to.")
        parser.add_argument("--id", type=str, required=True,
                            help="Load database data for specific user.")
        parser.add_argument("--campus_id", type=int, required=True,
                            help="Load the for that campus.")
        parser.add_argument("--user_name", type=str,
                            help="Will help to extract the suit lectures for that student.")
        parser.add_argument("--password", type=str,
                            help="The password for the user name.")
        parser.add_argument("--only_classes_can_enroll", action="store_true", default=False,
                            help="Will extract only lectures can enroll.\n"
                                 "User name and password are required.")

    def _initialize_and_validate(self, args: Optional[Namespace] = None):
        args.output_file = args.output_file.resolve()
        self.write_result_file(args.output_file, status=False)
        if args.only_classes_can_enroll and not (args.user_name and args.password):
            raise RuntimeError("ERROR: Missing username and password when ask to download data from the server.")
        if bool(args.user_name) ^ bool(args.password):
            raise RuntimeError("ERROR: Must given both username and password or none of them.")
        self.logger.debug("Init database and settings for the user.")
        translation.config_language_text(Language.HEBREW)
        database = Database(args.id)
        database.clear_personal_database()
        database.clear_settings()
        database.init_personal_database_tables()
        settings = Settings()
        settings.output_formats = [OutputFormat.IMAGE]
        settings.show_only_courses_with_prerequisite_done = False
        settings.show_only_courses_with_free_places = False
        settings.show_english_speaker_courses = False
        self.logger.info("Load campuses info.")
        all_campuses = database.load_campuses()
        if args.campus_id not in all_campuses:
            raise RuntimeError("ERROR: No such campus id.")
        hebrew_index = 1
        settings.campus_name = all_campuses[args.campus_id][hebrew_index]
        settings.show_only_classes_can_enroll = args.only_classes_can_enroll
        if args.user_name and args.password:
            database.save_user_data(User(args.user_name, args.password))
        database.save_settings(settings)

    def _invoke(self, args: Optional[Namespace] = None) -> Any:
        database = Database(args.id)
        settings = database.load_settings()
        activities_ids = None

        if args.only_classes_can_enroll:
            self.logger.info("Extract all activities ids can enroll in.")
            network = NetworkHttp(User(args.user_name, args.password))
            activities_ids_can_enroll = network.extract_all_activities_ids_can_enroll_in(settings)
            database.save_activities_ids_groups_can_enroll_in(activities_ids_can_enroll)
            activities_ids = list(set(activities_ids_can_enroll))

        self.logger.info("Extract courses choices.")
        courses_choices: Dict[str, CourseChoice] = database.load_courses_choices(
            campus_name=settings.campus_name,
            language=Language.get_current(),
            degrees=settings.degrees,
            activities_ids=activities_ids,
            extract_unrelated_degrees=True,
            settings=settings,
        )
        courses_choices = utils.sort_dict_by_key(courses_choices)
        self.logger.info("Courses choices were loaded.")
        choices = [course_choice.to_json() for course_choice in courses_choices.values()]

        self.logger.info(f"Write results to '{args.output_file}'.")
        self.write_result_file(args.output_file, result=choices, status=True)

    def help_examples(self) -> List[str]:
        return [
            "--id 121 --campus_id 1",
            "# Show only options the student can enroll in the levnet.",
            "--id 121 --campus_id 1 --only_classes_can_enroll --user_name user --password password"
        ]

    def help_long(self) -> str:
        return self.help_short()

    def help_short(self) -> str:
        return "Get all courses names and their ids that available."


class SelectChoices(ConsoleApi):

    def _args_parse(self, parser: ArgumentParser):
        parser.add_argument("--choices_file", type=Path, required=True,
                            help="json file contain the choices of the user.")
        parser.add_argument("--output_file", type=Path, default="result.json",
                            help="Output file to write results to.")
        parser.add_argument("--id", type=str, required=True,
                            help="Load database data for specific user.")
        parser.add_argument("--max_output", type=int, default=20,
                            help="Max result of options to extract.")

    def _initialize_and_validate(self, args: Optional[Namespace] = None):
        args.output_file = args.output_file.resolve()
        self.write_result_file(args.output_file, status=False)
        if not args.choices_file.is_file():
            raise RuntimeError("ERROR: Missing choices file.")
        translation.config_language_text(Language.HEBREW)

    def _invoke(self, args: Optional[Namespace] = None) -> Any:
        csp = CSP()
        database = Database(args.id)
        settings = database.load_settings()
        if not settings:
            raise RuntimeError("ERROR: Must run get_courses command before.")
        self.logger.info("Extract courses choices from choices json file")
        courses_choices: Dict[str, CourseChoice] = self._extract_courses_choices(args.choices_file)
        self.logger.info("Courses choices were loaded.")
        all_courses_parent_numbers = {course_choice.parent_course_number for course_choice in courses_choices.values()}

        selected_activities = database.load_activities_by_parent_courses_numbers(
            parent_courses_numbers=all_courses_parent_numbers,
            campus_name=settings.campus_name,
            language=Language.get_current(),
            degrees=settings.degrees,
            settings=settings,
        )

        ids = database.load_activities_ids_groups_can_enroll_in()
        activities_ids_groups = ids if settings.show_only_classes_can_enroll else None

        schedules = csp.extract_schedules(
            activities=selected_activities,
            courses_choices=courses_choices,
            settings=settings,
            activities_ids_groups=activities_ids_groups,
            courses_degrees=database.load_degrees_courses(),
        )

        settings.output_formats = [OutputFormat.IMAGE]

        results_path = self._save_schedules(settings, schedules, args.max_output, args.id)
        all_schedules = results_path / _("all_schedules")
        all_schedules = str(all_schedules) if all_schedules.is_dir() else None
        most_spread_days = results_path / _("most_spread_days")
        most_spread_days = str(most_spread_days) if most_spread_days.is_dir() else None
        least_spread_days = results_path / _("least_spread_days")
        least_spread_days = str(least_spread_days) if least_spread_days.is_dir() else None
        least_standby_time = results_path / _("least_standby_time")
        least_standby_time = str(least_standby_time) if least_standby_time.is_dir() else None

        result = {
            "result_path": str(results_path),
            "details_paths": {
                "all_schedules_path": all_schedules,
                "most_spread_days_path": most_spread_days,
                "least_spread_days_path": least_spread_days,
                "least_standby_time_path": least_standby_time,
            }
        }

        self.logger.info(f"Write results to '{args.output_file}'.")
        self.write_result_file(
            file_path=args.output_file,
            result=result,
            status=bool(csp.status is not Status.FAILED),
            message_error=self._get_status_message(csp),
        )

    def _save_schedules(self, settings: Settings, schedules: Optional[List[Schedule]], max_output: int,
                        user_id: str) -> Optional[Path]:
        if not schedules:
            return None
        self.logger.info(f"Found {len(schedules)} possible schedules")
        if len(schedules) > max_output:
            self.logger.info(f"Saving only the best {max_output} schedules")
        self.logger.info("Saving the schedules, it can take few seconds...")

        results_path = utils.get_results_path() / user_id
        controller = Controller()
        controller.save_schedule(schedules, settings, results_path, max_output)
        self.logger.info("Done successfully !")
        self.logger.info(f"The schedules were saved in the directory: {results_path}")
        return results_path

    def _get_status_message(self, csp: CSP) -> str:
        message = None
        status = csp.get_status()
        if status is Status.FAILED:
            message = _("No schedules were found")
            first_name, second_name = csp.get_last_activities_crashed()
            if first_name and second_name:
                message += "\n" + _("The last activities that were crashed were: (you may want to give up one of them)")
                message += "\n" + _("The activity: {} And {}").format(first_name, second_name)
        elif status is Status.SUCCESS_WITH_ONE_FAVORITE_LECTURER:
            message = _("No schedules were found with all favorite lecturers, but found with some of them")
        elif status is Status.SUCCESS_WITHOUT_FAVORITE_LECTURERS:
            message = _("No schedules were found with favorite lecturers")
        return message

    def _extract_courses_choices(self, choices_file: Path) -> Dict[str, CourseChoice]:
        try:
            with open(choices_file, 'r', encoding='utf-8') as file:
                result = json.load(file)['result']
            courses_choices = [CourseChoice.from_json(item) for item in result]
            return {course_choice.name: course_choice for course_choice in courses_choices}
        except Exception as error:
            raise RuntimeError("ERROR: Choices file could not be extracted, invalid format.") from error

    def help_examples(self) -> List[str]:
        return [
            "--choices_file input.json --id 121",
            "# Limit the output count to reduce runtime",
            "--choices_file input.json --id 121 --max_output 10",
        ]

    def help_long(self) -> str:
        return f"{self.help_short()}\nNOTICE: get_courses command must run before."

    def help_short(self) -> str:
        return "Select choices and generate schedules."


def main():
    commands = [GetCampuses, GetCourses, SelectChoices]
    description = "Console API to generate semester schedules."
    ConsoleApi.run(commands, description)


if __name__ == "__main__":
    main()
