import logging
import os
from data.course import Course
from data.semester import Semester

ENCODING = "utf-8"
LOG_FILE_HANDLER = logging.FileHandler(filename="log.txt", encoding=ENCODING, mode='w')


def init_project():
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
    logging.getLogger("WDM").setLevel(logging.WARNING)


def set_logging_to_file(level=logging.DEBUG):
    format_logging = "%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(message)s"

    logging.basicConfig(handlers=[LOG_FILE_HANDLER, logging.StreamHandler()],
                        datefmt="%H:%M:%S", level=level, format=format_logging)


def get_root_path():
    return os.path.dirname(os.path.abspath(__file__))


def get_current_hebrew_year():
    return 5783


def get_years_list():
    return [get_current_hebrew_year(), get_current_hebrew_year()]


def get_database_path():
    if not os.path.exists(os.path.join(get_root_path(), "database")):
        os.makedirs(os.path.join(get_root_path(), "database"))
    return os.path.join(get_root_path(), "database")


def get_results_path():
    return os.path.join(get_root_path(), "results")


def get_current_semester():
    return Semester.FALL


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
    return "מכון לב"


def get_course_data_test():
    return Course("חשבון אינפני' להנדסה 1", 120131, 318)
