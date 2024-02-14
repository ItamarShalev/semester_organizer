import logging
import os
import shutil
import sys
import time
from pathlib import Path
from contextlib import suppress
from datetime import datetime
from operator import itemgetter
from typing import Tuple, Dict, Any

import urllib3
from urllib3.exceptions import InsecureRequestWarning

from data.course import Course
from data.degree import Degree
from data.semester import Semester
from data.translation import _

ENCODING = "utf-8-sig"
ROOT_PATH = Path(__file__).parent.resolve()
LOG_FILE_HANDLER = logging.FileHandler(filename=ROOT_PATH / "log.txt", encoding=ENCODING, mode='w')
DATA_SOFTWARE_VERSION = "1.0"
SOFTWARE_VERSION = "1.0"


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
    if sys.version_info < (3, 7):
        raise RuntimeError("To run this program you should have Python 3.7 or a more recent version.")
    with suppress(AttributeError):
        if os.name == "nt":
            sys.stdout.reconfigure(encoding="utf-8")
    disable_logger_third_party_warnings()
    try:
        install_auto_complete_cli()
    except Exception as error:
        get_logging().error(error)


def get_current_hebrew_year():
    diff_hebrew_year = 3761
    return diff_hebrew_year + datetime.now().year - 1


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


def config_logging_level(level=logging.DEBUG):
    format_logging = "%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(message)s"
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
