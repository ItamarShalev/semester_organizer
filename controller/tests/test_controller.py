import shutil
from contextlib import suppress
from typing import Dict, Set
from unittest.mock import MagicMock, patch
import pytest
from pytest import fixture

import utils
from collector.db.db import Database
from collector.network.network import NetworkHttp
from controller.controller import Controller
from convertor.convertor import Convertor
from data import translation
from data.course_choice import CourseChoice
from data.language import Language
from data.settings import Settings


@patch('utils.get_results_path', return_value=utils.get_results_test_path())
@patch('time.sleep', return_value=None)
class TestController:

    @pytest.mark.parametrize("language", list(Language))
    def test_flow_console(self, _time_sleep_mock, results_path_mock, controller_mock, language):
        translation.config_language_text(language)
        controller_mock.database.save_language(language)
        inputs = []
        # show settings menu
        inputs.append("1")
        # don't change settings
        inputs.append("2")
        # don't add courses already done
        inputs.append("2")
        # don't show only courses can enroll in since tests always run with the same user details
        # inputs.append("2")
        # choose courses indexes
        inputs.append("1")
        # don't select lectures
        inputs.append("2")

        test_input = iter([str(item) for item in inputs])

        def input_next(*_unused_args):
            with suppress(StopIteration):
                return next(test_input)

        results = results_path_mock()
        shutil.rmtree(results, ignore_errors=True)
        with patch('builtins.input', side_effect=input_next) as _input_mock:
            controller_mock.run_console_flow()
        # Check that the results file was created.
        assert results.exists()
        files_count, _dirs = utils.count_files_and_directory(results)
        assert files_count >= 1

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
                super().__init__("test_database")
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
    def network_mock(self):
        class NetworkMock(NetworkHttp):
            def extract_all_activities_ids_can_enroll_in(self, *_unused_args) -> Dict[str, Set[int]]:
                self.logger.info("extract_all_activities_ids_can_enroll_in was called")
                return {}

        return NetworkMock()

    @fixture
    def controller_mock(self, database_mock, convertor_mock, network_mock):
        # pylint: disable=protected-access
        controller = Controller(verbose=True)
        controller.max_output = 1
        controller.convertor = convertor_mock
        controller.database = database_mock
        controller.network = network_mock
        controller._open_results_folder = MagicMock()
        return controller
