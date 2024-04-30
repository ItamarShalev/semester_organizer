import logging
import os
import shutil
import sys
import time
import json
from argparse import ArgumentParser, RawTextHelpFormatter, Namespace
from pathlib import Path
from contextlib import suppress
from datetime import datetime
from operator import itemgetter
from typing import Tuple, Dict, Any, List, Type, Optional
from abc import ABC, abstractmethod

import urllib3
from urllib3.exceptions import InsecureRequestWarning

from data.course import Course
from data.degree import Degree
from data.semester import Semester
from data.language import Language
from data.translation import _

ENCODING = "utf-8-sig"
ROOT_PATH = Path(__file__).parent.resolve()
LOG_FILE_HANDLER = logging.FileHandler(filename=ROOT_PATH / "log.txt", encoding=ENCODING, mode='w')
DATA_SOFTWARE_VERSION = "1.0"
SOFTWARE_VERSION = "1.0"


class ConsoleApi(ABC):

    def write_result_file(self, file_path: Path, result: Optional[Any] = None, status: bool = True,
                          message_error: Optional[str] = None) -> None:
        file_path.unlink(missing_ok=True)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        json_data = {
            "status": status,
            "message_error": message_error,
            "result": result,
        }
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, sort_keys=False, indent=4, ensure_ascii=False)

    @staticmethod
    def run(obj_commands: List[Type['ConsoleApi']], description: Optional[str] = None):
        args = sys.argv[1:] or ['--help']
        parser = ArgumentParser(formatter_class=RawTextHelpFormatter, description=description)
        commands_parser = parser.add_subparsers(
            metavar="command",
            help="Choose command from the list (Try <command> --help for more details)"
        )

        for obj_command in obj_commands:
            command = obj_command()

            sub_parser = commands_parser.add_parser(
                name=command.snake_case_name(),
                formatter_class=RawTextHelpFormatter,
                description=command.help_full(),
                help=command.help_short()
            )

            sub_parser.set_defaults(invoke_func=command.invoke)
            command.args_parse(sub_parser)

        namespace: Namespace = parser.parse_args(args)
        namespace.invoke_func(namespace)

    def __init__(self):
        self.logger = logging.getLogger(__package__)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def snake_case_name(self):
        result = ""
        for char in self.name:
            if char.isupper() and result:
                result += "_" + char.lower()
            else:
                result += char.lower()
        return result

    def args_parse(self, parser: ArgumentParser):
        self._args_parse(parser)

    def initialize_and_validate(self, args: Optional[Namespace] = None):
        config_logging_level(level=logging.INFO, class_name=self.name)
        self._initialize_and_validate(args)

    def invoke(self, args: Optional[Namespace] = None) -> Any:
        self.initialize_and_validate(args)
        return self._invoke(args)

    def help_full(self) -> str:
        example_lines = []
        for example in self.help_examples():
            if example.startswith('#'):
                example_lines.append(example)
            else:
                file_name = Path(sys.modules[self.__module__].__file__).name
                example_lines.append(f"python {file_name} {self} {example}")
        help_full = self.help_long() + "\n\nExamples usage:\n\t" + "\n\t".join(example_lines)
        return help_full

    @abstractmethod
    def _args_parse(self, parser: ArgumentParser):
        pass

    @abstractmethod
    def _initialize_and_validate(self, args: Optional[Namespace] = None):
        pass

    @abstractmethod
    def _invoke(self, args: Optional[Namespace] = None) -> Any:
        pass

    @abstractmethod
    def help_examples(self) -> List[str]:
        pass

    @abstractmethod
    def help_long(self) -> str:
        pass

    @abstractmethod
    def help_short(self) -> str:
        pass

    def __repr__(self) -> str:
        return self.snake_case_name()

    def __str__(self) -> str:
        return self.snake_case_name()


def sort_dict_by_key(dictionary: Dict[Any, Any]) -> Dict[Any, Any]:
    return dict(sorted(dictionary.items(), key=itemgetter(0)))


def disable_logger_third_party_warnings():
    urllib3.disable_warnings(InsecureRequestWarning)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
    logging.getLogger("WDM").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def windows_path_to_unix(path):
    drive, rest = path.split(":", 1)
    unix_path = rest.replace("\\", "/")
    unix_path = f"/{drive.lower()}{unix_path}"
    return unix_path


def install_auto_complete_cli():
    argcomplete_path = os.path.abspath(os.path.join(os.path.expanduser("~"), "argcomplete_semester_organizer.sh"))
    if os.path.exists(argcomplete_path):
        return
    local_argcomplete_path = os.path.join(ROOT_PATH, "argcomplete_semester_organizer.sh")
    # copy file to home directory
    shutil.copyfile(local_argcomplete_path, argcomplete_path)
    bashrc_path = os.path.abspath(os.path.join(os.path.expanduser("~"), ".bashrc"))
    files = ["__main__.py", "release.py", "run_linter.py", "update_levnet_data.py"]
    text_to_copy = "\n\n# This part it is for the auto-complete of the semester_organizer project\n"
    text_to_copy += "export ARGCOMPLETE_USE_TEMPFILES=1\n"
    text_to_copy += f"source {windows_path_to_unix(argcomplete_path)}\n"
    for file in files:
        file_path = os.path.abspath(os.path.join(ROOT_PATH, file))
        file_path = windows_path_to_unix(file_path)
        text_to_copy += f'eval "$(register-python-argcomplete {file_path})"\n'
    text_to_copy += "# End of the autocomplete section"
    if not os.path.exists(bashrc_path):
        with open(bashrc_path, "w") as file:
            file.write(text_to_copy)
    else:
        with open(bashrc_path, "+a") as file:
            if text_to_copy not in file.read():
                file.write(text_to_copy)


def init_project():
    if sys.version_info < (3, 8):
        raise RuntimeError("To run this program you should have Python 3.8 or a more recent version.")
    with suppress(AttributeError):
        if os.name == "nt":
            sys.stdout.reconfigure(encoding="utf-8")
    disable_logger_third_party_warnings()
    try:
        install_auto_complete_cli()
    except Exception as error:
        get_logging().error(error)


def get_current_hebrew_year():
    return convert_year(datetime.now().year, Language.HEBREW)


def convert_year(year: int, language: Language) -> int:
    """
    Change year by the language.
    """
    result = year
    diff_hebrew_year = 3761
    if language is Language.HEBREW and year < diff_hebrew_year:
        result = year + diff_hebrew_year - 1
    elif language is Language.ENGLISH and year > diff_hebrew_year:
        result = year - diff_hebrew_year + 1
    return result


def get_current_hebrew_name():
    # This is temporal solution until
    # תשפ"ט
    additional_letter = chr(ord("א") + get_current_hebrew_year() - 5781)
    assert additional_letter != "י", "ERROR: Invalid calculation and should using different method."
    hebrew_name = 'תשפ"' + additional_letter
    return hebrew_name


def get_database_path() -> Path:
    database_path = ROOT_PATH / "database"
    database_path.mkdir(parents=True, exist_ok=True)
    return database_path


def get_results_path() -> Path:
    return Path.home() / "semester_organizer_results"


def get_results_test_path() -> Path:
    return get_database_path() / "results_test"


def count_files_and_directory(directory: str) -> Tuple[int, int]:
    files = dirs = 0
    for _unused, dirs_name, files_names in os.walk(directory):
        files += len(files_names)
        dirs += len(dirs_name)
    return files, dirs


def get_last_modified_by_days(file_path: str) -> int:
    if not os.path.exists(file_path):
        return 0
    last_modified = os.path.getmtime(file_path)
    return int((time.time() - last_modified) / 60 / 60 / 24)


def get_current_semester():
    current_month = datetime.now().month
    fall_months = [8, 9, 10, 11, 12, 1]
    return Semester.FALL if current_month in fall_months else Semester.SPRING


def config_logging_level(level=logging.DEBUG, class_name: str = "%(name)s"):
    format_logging = f"%(asctime)s {class_name}.%(funcName)s +%(lineno)s: %(message)s"
    handlers = [logging.StreamHandler()]
    if level == logging.DEBUG:
        handlers.append(LOG_FILE_HANDLER)
    logging.basicConfig(handlers=handlers, datefmt="%H:%M:%S", level=level, format=format_logging)


def get_logging():
    return logging.getLogger(get_custom_software_name())


def get_custom_software_name():
    return "semester_organizer_lev"


def get_campus_name_test():
    return _("Machon Lev")


def get_course_data_test():
    return Course(_("Infinitesimal Calculus 1"), 120131, 318, {Semester.SPRING, Semester.FALL}, set(Degree))
