import builtins
import os.path
from typing import List, Dict, Tuple

from unittest.mock import MagicMock

import pytest
from pytest import fixture

import utils
from collector.gui.gui import MessageType
from controller.controller import Controller
from convertor.convertor import Convertor
from data.course_choice import CourseChoice
from data.language import Language
from data.settings import Settings
from data import translation
from data.user import User


class TestController:

    @staticmethod
    def _get_count_files_and_directory(directory: str) -> Tuple[int, int]:
        files = dirs = 0

        for _unused, dirs_name, files_names in os.walk(directory):
            files += len(files_names)
            dirs += len(dirs_name)
        return files, dirs

    @staticmethod
    def _open_academic_activities_window_mock(ask_attendance_required: bool,
                                              course_choices: Dict[str, CourseChoice]) -> Dict[str, CourseChoice]:
        message = f"open_academic_activities_window_mock was called. with {ask_attendance_required} and " \
                  f"{course_choices.keys()}"
        utils.get_logging().debug(message)
        name = utils.get_course_data_test().name
        return {name: CourseChoice(name, [], [])}

    @staticmethod
    def _open_notification_window_mock(message: str, message_type: MessageType = MessageType.INFO,
                                       buttons: List[str] = None):
        msg = f"open_notification_window_mock was called. with {message} and {message_type} and {buttons}"
        utils.get_logging().debug(msg)

    @staticmethod
    def _open_settings_window_mock(settings: Settings, campuses: List[str], years: Dict[int, str]) -> Settings:
        msg = f"open_settings_window was called. with {settings} and {campuses} and {years}"
        utils.get_logging().debug(msg)
        return settings

    @staticmethod
    def _get_gui_mock():
        gui_mock = MagicMock()
        gui_mock.open_login_window = MagicMock(return_value=User("test", "test"))
        gui_mock.open_academic_activities_window = MagicMock(
            side_effect=TestController._open_academic_activities_window_mock)
        gui_mock.open_personal_activities_window = MagicMock(return_value=[])
        gui_mock.open_notification_window = MagicMock(side_effect=TestController._open_notification_window_mock)
        gui_mock.open_settings_window = MagicMock(side_effect=TestController._open_settings_window_mock)
        return gui_mock

    @fixture
    def controller(self):
        # pylint: disable=protected-access
        gui_mock = TestController._get_gui_mock()
        controller = Controller()
        convertor = Convertor()
        convertor_mock = MagicMock()
        convertor_mock.convert_activities = MagicMock(side_effect=convertor.convert_activities)
        controller.gui = gui_mock
        controller.convertor = convertor_mock
        controller.database.SETTINGS_FILE_PATH = os.path.join(utils.get_database_path(), "test_settings_data.txt")
        controller.database.COURSES_CHOOSE_PATH = os.path.join(utils.get_database_path(),
                                                               "test_course_choose_user_input.txt")
        settings = Settings()
        settings.campus_name = utils.get_campus_name_test()
        controller.database.save_settings(settings)
        controller._open_results_folder = MagicMock()
        return controller

    @pytest.mark.parametrize("language", list(Language))
    def test_run_main_gui_flow(self, controller, language: Language):
        translation.config_language_text(language)
        controller.database.save_language(language)
        controller.run_main_gui_flow()
        controller.convertor.convert_activities.assert_called()

    @pytest.mark.parametrize("language", list(Language))
    def test_flow_console(self, controller, language: Language):
        translation.config_language_text(language)
        controller.database.save_language(language)
        test_input = iter([str(item) for item in [1, 2, "1, 3", 2]])

        def input_next(*args):
            try:
                return next(test_input)
            except StopIteration as error:
                text = ' '.join([str(item) for item in args])
                raise ValueError(f"FAIL: input args: {text}") from error

        builtins.input = input_next
        controller.run_console_flow()
        results = utils.get_results_path()
        # Check that the results file was created.
        # And contains only one file.
        assert os.path.exists(results)
        files_count, _dirs = TestController._get_count_files_and_directory(results)
        assert files_count >= 1
