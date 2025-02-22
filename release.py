#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK


import argparse
import logging
import os
import platform
import subprocess
from enum import Enum
from typing import Optional

import argcomplete
import utils
from collector.db.db import Database


class OS(Enum):
    WINDOWS = ".exe"
    UBUNTU = ""
    MAC = ".dmg"

    def __str__(self):
        return self.name.capitalize()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--build", help="Create executable file", default=False, action="store_true")
    parser.add_argument("-t", "--title", help="Print the title of this build", default=False, action="store_true")
    parser.add_argument("-p", "--path", help="Print the executable path result", default=False, action="store_true")
    argcomplete.autocomplete(parser)
    arguments = parser.parse_args()
    return arguments


def get_os_type() -> Optional[OS]:
    system_type = platform.system()
    if system_type == "Windows":
        return OS.WINDOWS

    if system_type == "Linux":
        return OS.UBUNTU

    if system_type == "Darwin":
        return OS.MAC

    return None


def build(os_build_type: OS):
    database_file_path = Database().shared_database_path
    main_path = utils.ROOT_PATH / "__main__.py"
    separator = ';'
    if os_build_type in [OS.UBUNTU, OS.MAC]:
        separator = ':'

    print(f"Building executable file for {os_build_type} OS")
    print(f"Main script path: {main_path}")

    pyinstaller_cmd = f"pyinstaller --onefile " \
                      f"--add-binary {database_file_path}{separator}database " \
                      f"--name SemesterOrganizer{os_build_type.value} __main__.py"

    print("Running pyinstaller command: ", pyinstaller_cmd)
    return_code = subprocess.call(pyinstaller_cmd.split(" "))
    assert return_code == 0, "Pyinstaller command failed"

    print("Build finished successfully")


def main():
    utils.init_project()
    utils.config_logging_level(logging.DEBUG)
    os_type = get_os_type()
    args = get_args()
    args_count = sum([args.build, args.title, args.path])
    error_message = "Need exactly one argument from the following: build, title, path."

    assert args_count == 1, error_message
    assert os_type, f"{os.name} OS is not supported."

    if args.title:
        print(f"Executable File for {os_type} OS")

    elif args.path:
        file_path = os.path.join("dist", f"SemesterOrganizer{os_type.value}")
        print(file_path)

    elif args.build:
        build(os_type)


if __name__ == "__main__":
    main()
