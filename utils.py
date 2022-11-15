import logging
import os
import sys
from data.course import Course


def set_logging_to_file():
    get_logging().setFileHandler(logging.FileHandler(os.path.join(get_root_path(), "log.txt")))


def get_root_path():
    return os.path.dirname(os.path.abspath(__file__))


def get_database_path():
    if not os.path.exists(os.path.join(get_root_path(), "database")):
        os.makedirs(os.path.join(get_root_path(), "database"))
    return os.path.join(get_root_path(), "database")


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
