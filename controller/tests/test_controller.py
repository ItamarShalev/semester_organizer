import os.path
from typing import List, Dict, Tuple

from unittest.mock import MagicMock
import pytest

import utils
from collector.gui.gui import MessageType
from controller.controller import Controller
from convertor.convertor import Convertor
from data.course_choice import CourseChoice
from data.language import Language
from data.settings import Settings
from data import translation
from data.user import User


@pytest.mark.network()
@pytest.mark.network_http()
class TestController:

    @staticmethod
    def _get_count_files_and_directory(directory: str) -> Tuple[int, int]:
        files = dirs = 0

        for _unused, dirs_name, files_names in os.walk(directory):
            # ^ this idiom means "we won't be using this value"
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

    def test_run_main_gui_flow(self):
        translation.config_language_text(Language.HEBREW)
        gui_mock = TestController._get_gui_mock()
        controller = Controller()
        convertor = Convertor()
        convertor_mock = MagicMock()
        convertor_mock.convert_activities = MagicMock(side_effect=convertor.convert_activities)
        controller.gui = gui_mock
        controller.convertor = convertor_mock
        controller.run_main_gui_flow()
        controller.convertor.convert_activities.assert_called()

    def test_flow_console(self):
        translation.config_language_text(Language.ENGLISH)
        controller = Controller()
        controller.run_console_flow(1, "2, 8, 11, 14, 15, 35", 1, 2, 3, 1, 1, 1)
        results = utils.get_results_path()
        # Check that the results file was created.
        # And contains only one file.
        assert os.path.exists(results)
        files_count, _dirs = TestController._get_count_files_and_directory(results)
        assert files_count == 1
