from typing import List, Dict

from unittest.mock import MagicMock
import pytest

import utils
from collector.db.db import Database
from collector.gui.gui import MessageType
from collector.network.network import NetworkHttp
from controller.controller import Controller
from convertor.convertor import Convertor
from csp.csp import CSP
from data.course_choice import CourseChoice
from data.settings import Settings


@pytest.mark.network()
@pytest.mark.network_http()
class TestController:

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
        user = Database().load_hard_coded_user_data()
        assert user, "Don't have user data to check."
        gui_mock = MagicMock()
        gui_mock.open_login_window = MagicMock(return_value=user)
        gui_mock.open_academic_activities_window = MagicMock(
            side_effect=TestController._open_academic_activities_window_mock)
        gui_mock.open_personal_activities_window = MagicMock(return_value=[])
        gui_mock.open_notification_window = MagicMock(side_effect=TestController._open_notification_window_mock)
        gui_mock.open_settings_window = MagicMock(side_effect=TestController._open_settings_window_mock)
        return gui_mock

    def test_run_main_gui_flow(self):
        gui_mock = TestController._get_gui_mock()
        controller = Controller()
        convertor = Convertor()
        convertor_mock = MagicMock()
        convertor_mock.convert_activities = MagicMock(convertor.convert_activities)
        controller.gui = gui_mock
        controller.convertor = convertor_mock
        controller.run_main_gui_flow()
        controller.convertor.convert_activities.assert_called_once()

    def test_flow_without_gui_without_database(self):
        csp = CSP()
        campus_name = utils.get_campus_name_test()
        user = Database().load_hard_coded_user_data()
        network = NetworkHttp(user)
        assert user, "Don't have user data to check."

        assert network.check_connection(), "Can't connect to the server."

        campus_names = network.extract_campus_names()
        assert campus_names, "Can't extract campus names from the server."

        assert campus_name in campus_names, "Some campus names are missing."

        courses = network.extract_all_courses(campus_name)
        assert courses, "Can't extract courses from the server."

        course = utils.get_course_data_test()
        assert course in courses, "Some courses are missing."

        academic_activities, missing_courses_names = network.extract_academic_activities_data(campus_name, [course])
        missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)
        assert not missing_courses_names, "The following courses don't have activities: " + ", ".join(
            missing_courses_names)

        assert not missing_meetings_data, "Can't extract academic activities from the server."
        schedules = csp.extract_schedules(academic_activities)
        assert schedules, "At least one schedule should be extracted."

    def test_flow_without_gui_with_database(self):
        csp = CSP()
        database = Database()
        campus_name = "מכון לב"
        user = database.load_hard_coded_user_data()
        network = NetworkHttp(user)
        assert user, "Don't have user data to check."

        assert network.check_connection(), "Can't connect to the server."

        campus_names = database.load_campus_names()
        if not campus_names:
            campus_names = network.extract_campus_names()
            assert campus_names, "Can't extract campus names from the server."
            assert campus_name in campus_names, "Some campus names are missing."
            database.save_campus_names(campus_names)

        courses = database.load_courses_data()
        course = utils.get_course_data_test()
        campus_name = utils.get_campus_name_test()
        if not courses:
            courses = network.extract_all_courses(campus_name)

            assert courses, "Can't extract courses from the server."
            assert course in courses, "Some courses are missing."
            database.save_courses_data(courses)

        academic_activities = database.load_academic_activities_data(campus_name, [course])

        if not academic_activities:
            academic_activities, missings = network.extract_academic_activities_data(campus_name, [course])
            assert not missings, "The following courses don't have activities: " + ", ".join(missings)

        missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)
        assert not missing_meetings_data, "Can't extract academic activities from the server."

        schedules = csp.extract_schedules(academic_activities)
        assert schedules, "At least one schedule should be extracted."

        assert campus_names, "Don't have campus names to check."

        assert campus_name in campus_names, "Some campus names are missing."
