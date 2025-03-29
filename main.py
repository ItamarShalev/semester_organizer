#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import logging
import pathlib
from argparse import ArgumentParser

import argcomplete

from src import utils
from src.collector.db import Database
from src.controller.controller import Controller
from src.algorithms.constraint_courses import ConstraintCourses
from src.data.language import Language
from src.data.user import User
from src.data.flow import Flow
from src.data.translation import _


def get_args():
    parser = ArgumentParser()
    parser.add_argument("-f", "--flow", help="Run the program with flow, can be gui or console.",
                        default=Flow.CONSOLE, choices=list(Flow), type=Flow.from_str)
    parser.add_argument("-u", "--username", help="The username user in the server", default=None, type=str)
    parser.add_argument("-p", "--password", help="The password user in the server", default=None, type=str)
    parser.add_argument("-l", "--language", help="Set the language of the program", choices=list(Language),
                        type=Language.from_str, default=Language.get_default())
    parser.add_argument("-v", "--verbose", help="Print more debug logs", default=False, action="store_true")
    parser.add_argument("--database_path", default="", type=pathlib.Path,
                        help="Path to database file (.db) Update database by given .db file, "
                             "that can be downloaded from the server (currently the github)")
    argcomplete.autocomplete(parser)
    return parser.parse_args()


def main():
    utils.init_project()
    args = get_args()
    utils.config_logging_level(logging.DEBUG if args.verbose else logging.ERROR)
    Language.set_current(args.language)
    database = Database()

    if args.username and args.password:
        database.save_user_data(User(args.username, args.password))

    if args.flow is Flow.CONSOLE:
        Controller(verbose=args.verbose).run_console_flow()

    elif args.flow is Flow.UPDATE_DATABASE:
        message = _("Database path is not a file or doesn't exists, the path given is: ")
        assert args.database_path.is_file(), message + str(args.database_path)
        database.update_database(args.database_path)

    elif args.flow is Flow.UPDATE_GENERATED_JSON_DATA:
        ConstraintCourses().export_generated_json_data()


if __name__ == '__main__':
    main()
