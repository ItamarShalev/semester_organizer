#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK


import argparse
import logging
from datetime import timedelta
from timeit import default_timer as timer

import argcomplete

import utils
from collector.db.db import Database
from collector.network.network import Network
from data.degree import Degree
from data.language import Language
from data.user import User


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--campus", default=None, type=str,
                        help="Download data to specific campus, default is for all the campuses")
    parser.add_argument("-l", "--language", default=None, type=str,
                        help="Download data to specific language, default is for all the languages")
    parser.add_argument("-u", "--username", help="The username user in the server", default=None, type=str)
    parser.add_argument("-p", "--password", help="The password user in the server", default=None, type=str)
    argcomplete.autocomplete(parser)
    return parser.parse_args()


def run_update_levnet_data_flow():
    start = timer()
    network = Network()
    database = Database()
    logger = utils.get_logging()

    args = get_args()
    if args.username and args.password:
        database.save_user_data(User(args.username, args.password))

    logger.debug("Start updating the levnet data")
    user = database.load_user_data()
    assert user, "There is no user data, can't access the levnet website."
    logger.debug("User data was loaded successfully")

    network.set_user(user)
    assert network.check_connection(), "ERROR: Can't connect to the levnet website"
    logger.debug("The username and password are valid")

    database.clear_all_data()
    database.init_database_tables()
    logger.debug("The database was cleared successfully")

    network.change_language(Language.ENGLISH)
    english_campuses = network.extract_campuses()
    logger.debug("The english campus were extracted successfully")
    logger.debug("The english campus are: %s", ", ".join(english_campuses.values()))

    network.change_language(Language.HEBREW)
    hebrew_campuses = network.extract_campuses()
    logger.debug("The hebrew campus were extracted successfully")
    logger.debug("The hebrew campus are: %s", ", ".join(hebrew_campuses.values()))

    campuses = {key: (english_campuses[key], hebrew_campuses[key]) for key in english_campuses.keys()}

    database.save_campuses(campuses)
    database.save_degrees(list(Degree))
    languages = [Language[args.language.upper()]] if args.language else list(Language)

    for language in languages:
        Language.set_current(language)
        network.change_language(language)
        logger.debug("The language was changed to %s", language)
        all_degrees = set(Degree)
        for degree in all_degrees:

            common_campuses_names = database.get_common_campuses_names()
            campuses = [args.campus] if args.campus else common_campuses_names

            for campus_name in campuses:

                courses = network.extract_all_courses(campus_name, degree)

                logger.debug("The courses were extracted successfully")
                logger.debug("The courses are: %s", ", ".join([course.name for course in courses]))

                database.save_courses(courses, language)

                logger.debug("Extracting data for campus: %s in language %s", campus_name, language.name)
                logger.debug("Start extracting the academic activities data for the campus: %s", campus_name)
                activities, missings = network.extract_academic_activities_data(campus_name, courses)
                if activities and not missings:
                    logger.debug("The academic activities data were extracted successfully")
                else:
                    logger.debug("The academic activities data were extracted with errors")
                    logger.debug("The missing courses are: %s", ', '.join(missings))

                database.save_academic_activities(activities, campus_name, language)
    end = timer()
    logger.debug("The levnet data was updated successfully in %s time", str(timedelta(seconds=end - start)))


def main():
    Language.set_current(Language.ENGLISH)
    utils.init_project()
    utils.config_logging_level(logging.DEBUG)
    run_update_levnet_data_flow()


if __name__ == '__main__':
    main()
