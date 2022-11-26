import logging
import os
import sys
from data.course import Course


def init_project():
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
    logging.getLogger("WDM").setLevel(logging.WARNING)


def set_logging_to_file(level=logging.DEBUG):
    format_logging = "%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(message)s"
    logging.basicConfig(filemode="a", filename=os.path.join(get_root_path(), "log.txt"), datefmt="%H:%M:%S",
                        level=level, format=format_logging)


def get_root_path():
    return os.path.dirname(os.path.abspath(__file__))


def get_current_hebrew_year():
    return 5783


def get_database_path():
    if not os.path.exists(os.path.join(get_root_path(), "database")):
        os.makedirs(os.path.join(get_root_path(), "database"))
    return os.path.join(get_root_path(), "database")


def get_results_path():
    return os.path.join(get_root_path(), "results")


def config_logging_level(level=logging.DEBUG):
    format_logging = "%(asctime)s %(name)s.%(funcName)s +%(lineno)s: %(message)s"
    logging.basicConfig(stream=sys.stdout, datefmt="%H:%M:%S", level=level, format=format_logging)


def get_logging():
    return logging.getLogger(get_custom_software_name())


def get_custom_software_name():
    return "semester_organizer_lev"


def get_campus_name_test():
    return "מכון לב"


def get_course_data_test():
    return Course("חשבון אינפני' להנדסה 1", 120131, 318)
