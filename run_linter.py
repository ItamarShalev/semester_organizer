#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK


import argparse
import logging
import os
import shutil
import subprocess
import sys
from contextlib import suppress

import argcomplete

import utils
from data.user import User


def get_all_python_files(test_files=False):
    files_result = []
    blocked_dirs = ["venv", ".idea", "results", "database", "logs", ".github", ".pytest_cache", "__pycache__", ".git"]
    for root, dirs, files in os.walk(utils.ROOT_PATH):
        dirs[:] = [d for d in dirs if d not in blocked_dirs]
        for file in files:
            if file.endswith(".py") and (not test_files or file.startswith("test_")):
                files_result.append(os.path.join(root, file))
    return files_result


def pip_install(*arguments):
    return_code = subprocess.call([sys.executable, "-m", "pip", "install", *arguments])
    assert return_code == 0, "ERROR: pip failed to install, check your network connection"


def clear_project():
    folders_to_clear = [".pytest_cache", "__pycache__"]
    files_to_clear = ["coverage.xml", ".coverage"]
    for folder in folders_to_clear:
        folder_path = os.path.join(utils.ROOT_PATH, folder)
        shutil.rmtree(folder_path, ignore_errors=True)

    for file in files_to_clear:
        file_path = os.path.join(utils.ROOT_PATH, file)
        with suppress(FileNotFoundError):
            os.remove(file_path)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="The username user in the server", default=None)
    parser.add_argument("-p", "--password", help="The password user in the server", default=None)
    parser.add_argument("-i", "--install", help="Install all the needed packages", default=False, action="store_true")
    parser.add_argument("-c", "--coverage", help="Run coverage", default=False, action="store_true")
    parser.add_argument("-n", "--network", help="Run network_http pytest mark", default=False, action="store_true")
    parser.add_argument("-a", "--all", help="Run all tests", default=False, action="store_true")
    parser.add_argument("-v", "--verbose", help="Print more debug logs", default=False, action="store_true")
    argcomplete.autocomplete(parser)
    arguments = parser.parse_args()
    return arguments


def update_pip():
    pip_install("--upgrade", "pip")


def install_requirements():
    pip_install("-r", "requirements.txt")


def install_development_requirements():
    pip_install("-r", "development_requirements.txt")


def get_user_data(argument_args):
    # pylint: disable=import-outside-toplevel
    # in case the user still not installed the requirements
    # it will import everything only after installing the requirements
    from collector.db.db import Database
    if not argument_args.username or not argument_args.password:
        user_data = Database().load_user_data()
    else:
        user_data = User(argument_args.username, argument_args.password)
        Database().save_user_data(user_data)

    return user_data


def _build_pytest_command(arguments):
    coveragerc_ci_cd = os.path.join(utils.ROOT_PATH, ".coveragerc_ci_cd")
    if arguments.coverage:
        if arguments.network:
            pytest_cmd = "coverage run -m pytest".split(" ")
        else:
            pytest_cmd = f"coverage run --rcfile={coveragerc_ci_cd} -m pytest".split(" ")
    else:
        pytest_cmd = ["pytest"]

    pytest_arguments = ['-m', 'not network']
    if arguments.all:
        pytest_arguments = ['--reruns', '2', '--reruns-delay', '5']
    elif arguments.network:
        pytest_arguments = ['-m', 'not network_driver', '--reruns', '2', '--reruns-delay', '5']
    if arguments.verbose:
        pytest_arguments += ['-v']

    return pytest_cmd, pytest_arguments


def _build_coverage_command(arguments):
    if arguments.network:
        coverage_cmd = "coverage report -m --fail-under=95"
    else:
        coveragerc_ci_cd = os.path.join(utils.ROOT_PATH, ".coveragerc_ci_cd")
        public_network_path = os.path.join(utils.ROOT_PATH, "collector", "network", "public_network.py")
        private_network_path = os.path.join(utils.ROOT_PATH, "semester_organizer_private", "network", "network.py")
        coverage_cmd = f"coverage report --rcfile={coveragerc_ci_cd} -m " \
                       f"--omit='{public_network_path},{private_network_path}' --fail-under=95"

    return coverage_cmd.split(" ")


def run_linter_and_tests(arguments):
    pytest_cmd, pytest_arguments = _build_pytest_command(arguments)

    return_code = subprocess.call(["pycodestyle", *get_all_python_files()])

    return_code += subprocess.call(["pylint", *get_all_python_files()])

    return_code += subprocess.call([*pytest_cmd, *get_all_python_files(test_files=True), *pytest_arguments])

    if arguments.coverage:
        coverage_cmd = _build_coverage_command(arguments)
        return_code += subprocess.call([*coverage_cmd])
    assert return_code == 0, "ERROR: Linter failed, check the log file"


def main():
    utils.init_project()
    clear_project()
    args = get_args()
    if args.install:
        update_pip()
        install_requirements()
        install_development_requirements()
    utils.config_logging_level(logging.DEBUG if args.verbose else logging.INFO)
    get_user_data(args)
    run_linter_and_tests(args)


if __name__ == '__main__':
    main()
