import argparse
import logging
import pathlib

import utils
from collector.db.db import Database
from controller.controller import Controller
from data import translation
from data.language import Language
from data.user import User


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--gui", help="Run the program with GUI.", action="store_true")
    parser.add_argument("-c", "--console", help="Run the program with console.", default=None, action="store_true")
    parser.add_argument("-u", "--username", help="The username user in the server", default=None, type=str)
    parser.add_argument("-p", "--password", help="The password user in the server", default=None, type=str)
    parser.add_argument("-l", "--language", help="Set the language of the program", choices=list(Language),
                        type=Language.from_str, default=Language.get_default())
    parser.add_argument("--update_database", default="", type=pathlib.Path,
                        help="Path to database file (.db) Update database by given .db file, "
                             "that can be downaloaded from the server (currently the gitub)")
    return parser.parse_args()


if __name__ == '__main__':
    utils.init_project()
    utils.config_logging_level(logging.INFO)
    args = get_args()
    translation.config_language_text(args.language)
    database = Database()

    if args.username and args.password:
        database.save_user_data(User(args.username, args.password))
    if args.update_database.is_file():
        database.update_database(args.update_database)
    elif args.console:
        Controller().run_console_flow()
    else:
        Controller().run_main_gui_flow()
