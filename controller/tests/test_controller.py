import os.path
import shutil
from typing import List, Dict, Callable
from unittest.mock import MagicMock, patch

import pytest
from pytest import fixture

import utils
from collector.db.db import Database
from collector.gui.gui import MessageType, Gui
from controller.controller import Controller
from convertor.convertor import Convertor
from data import translation
from data.activity import Activity
from data.course_choice import CourseChoice
from data.language import Language
from data.settings import Settings
from data.user import User


@patch('utils.get_results_path', return_value=utils.get_results_test_path())
@patch('time.sleep', return_value=None)
class TestController:

    @pytest.mark.parametrize("language", list(Language))
    def test_run_main_gui_flow(self, _time_sleep_mock, _results_path_mock, controller_mock, language: Language):
        translation.config_language_text(language)
        controller_mock.database.save_language(language)
        controller_mock.run_main_gui_flow()
        controller_mock.convertor.convert_activities.assert_called()

    @pytest.mark.parametrize("language", list(Language))
    def test_flow_console(self, _time_sleep_mock, results_path_mock, controller_mock, language: Language):
        translation.config_language_text(language)
        controller_mock.database.save_language(language)
        test_input = iter([str(item) for item in [1, 2, "1, 3", 2]])

        def input_next(*args):
            try:
                return next(test_input)
            except StopIteration as error:
                text = ' '.join([str(item) for item in args])
                raise ValueError(f"FAIL: input args: {text}") from error

        results = results_path_mock()
        shutil.rmtree(results, ignore_errors=True)
        with patch('builtins.input', side_effect=input_next) as _input_mock:
            controller_mock.run_console_flow()
        # Check that the results file was created.
        assert os.path.exists(results)
        files_count, _dirs = utils.count_files_and_directory(results)
        assert files_count >= 1

    @fixture
    def gui_mock(self):
        class GuiMock(Gui):
            def open_personal_activities_window(self) -> List[Activity]:
                self.logger.debug("open_personal_activities_window was called")
                return []

            def open_academic_activities_window(self, ask_attendance_required: bool,
                                                course_choices: Dict[str, CourseChoice]) -> Dict[str, CourseChoice]:
                message = f"open_academic_activities_window_mock was called. with {ask_attendance_required} and " \
                          f"{course_choices.keys()}"
                self.logger.debug(message)
                name = utils.get_course_data_test().name
                return {name: CourseChoice(name, [], [])}

            def open_notification_window(self, message: str, message_type: MessageType = MessageType.INFO,
                                         buttons: List[str] = None):
                msg = f"open_notification_window_mock was called. with {message} and {message_type} and {buttons}"
                self.logger.debug(msg)

            def open_settings_window(self, settings: Settings, campuses: List[str], years: Dict[int, str]) -> Settings:
                msg = f"open_settings_window was called. with {settings} and {campuses} and {years}"
                self.logger.debug(msg)
                return settings

            def open_login_window(self, is_valid_user_function: Callable) -> User:
                self.logger.debug("open_login_window was called")
                return User("test", "test")

        return GuiMock()

    @fixture
    def convertor_mock(self):
        convertor = Convertor()
        convertor_mock = MagicMock()
        convertor_mock.convert_activities = MagicMock(side_effect=convertor.convert_activities)
        return convertor_mock

    @fixture
    def database_mock(self):
        class DatabaseMock(Database):

            def __init__(self):
                self.settings = Settings()
                self.settings.campus_name = utils.get_campus_name_test()
                super().__init__()

            def save_language(self, language: Language):
                self.logger.info("save_language was called with %s", language.name)
                self.settings.language = language

            def load_language(self):
                self.logger.info("load_language was called")
                return self.settings.language

            def save_settings(self, _settings: Settings):
                self.logger.info("save_settings was called")

            def save_courses_console_choose(self, _course_choices: Dict[str, CourseChoice]):
                self.logger.info("save_courses_console_choose was called")

            def load_settings(self):
                self.logger.info("load_settings was called")
                return self.settings

        return DatabaseMock()

    @fixture
    def controller_mock(self, database_mock, convertor_mock, gui_mock):
        # pylint: disable=protected-access
        controller = Controller()
        controller.gui = gui_mock
        controller.convertor = convertor_mock
        controller.database = database_mock
        controller._open_results_folder = MagicMock()
        return controller
