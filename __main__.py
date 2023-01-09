#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import logging
import pathlib

import argcomplete

import utils
from collector.db.db import Database
from controller.controller import Controller
from data import translation
from data.language import Language
from data.user import User
from data.flow import Flow
from data.translation import _


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--flow", help="Run the program with flow, can be gui or console.",
                        default=Flow.GUI, choices=list(Flow), type=Flow.from_str)
    parser.add_argument("-u", "--username", help="The username user in the server", default=None, type=str)
    parser.add_argument("-p", "--password", help="The password user in the server", default=None, type=str)
    parser.add_argument("-l", "--language", help="Set the language of the program", choices=list(Language),
                        type=Language.from_str, default=Language.get_default())
    parser.add_argument("--database_path", default="", type=pathlib.Path,
                        help="Path to database file (.db) Update database by given .db file, "
                             "that can be downaloaded from the server (currently the gitub)")
    argcomplete.autocomplete(parser)
    return parser.parse_args()


def main():
    utils.init_project()
    utils.config_logging_level(logging.ERROR)
    args = get_args()
    translation.config_language_text(args.language)
    database = Database()

    if args.username and args.password:
        database.save_user_data(User(args.username, args.password))

    elif args.flow is Flow.CONSOLE:
        Controller().run_console_flow()

    elif args.flow is Flow.GUI:
        Controller().run_main_gui_flow()

    elif args.flow is Flow.UPDATE_DATABASE:
        message = _("Database path is not a file or doesn't exists, the path given is: ")
        assert args.database_path.is_file(), message + str(args.database_path)
        database.update_database(args.database_path)


if __name__ == '__main__':
    main()
