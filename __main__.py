import argparse
import logging

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
    parser.add_argument("--update", help="Update the data from the server", default=None, action="store_true")
    return parser.parse_args()


if __name__ == '__main__':
    utils.init_project()
    utils.config_logging_level(logging.INFO)
    args = get_args()
    translation.config_language_text(args.language)
    if args.username and args.password:
        Database().save_hard_coded_user_data(User(args.username, args.password))
    if args.update:
        Controller().run_update_levnet_data_flow()
    elif args.console:
        Controller().run_console_flow()
    else:
        Controller().run_main_gui_flow()
