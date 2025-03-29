import ssl
from datetime import datetime

import pytest
from pytest import fixture

from src import utils
from src.collector.db import Database
from src.collector.network import Network, WeakNetworkConnectionException, InvalidServerRequestException
from src.collector.network import InvalidSemesterTimeRequestException, TLSAdapter
from src.data.course import Course
from src.data.language import Language
from src.data.settings import Settings
from src.data.translation import _
from src.data.user import User


@pytest.mark.network
class TestPublicNetwork:

    already_fail_once = False

    @fixture
    def user(self):
        user_data = ""
        try:
            user_data = Database().load_user_data()
            assert user_data, "Can't load user data."
            network = Network(user_data)
            assert network.check_connection(), "Can't connect to the server."
        except Exception as error:
            if not TestPublicNetwork.already_fail_once:
                TestPublicNetwork.already_fail_once = True
                raise error
            pytest.skip(str(error))
        return user_data

    def test_fail_connection(self):
        network = Network(User("123456789", "123456789"))
        with pytest.raises(RuntimeError):
            network.connect()

    def test_connect_disconnect(self, user):
        network = Network(user)
        network.connect()
        network.disconnect()

    def test_extract_all_activities_ids_can_enroll_in(self, user):
        network = Network(user)
        settings = Settings()
        activities_ids_can_enroll_in = []

        try:
            activities_ids_can_enroll_in = network.extract_all_activities_ids_can_enroll_in(settings, [])
        except InvalidSemesterTimeRequestException:
            return
        assert "120131.04.5783.01" in activities_ids_can_enroll_in, "Can't extract activities ids can enroll in."

    def test_check_setup(self, user):
        network = Network()
        network.set_user(user)
        assert network.check_connection(), "Can't connect to the server."

    def test_extract_courses_already_did(self, user):
        network = Network(user)
        courses = network.extract_courses_already_did()
        assert courses, "Can't extract courses already did."
        assert any(course for course in courses if course[1] == 120701)

    def test_for_coverage(self):
        network = Network()
        network.set_settings(Settings())
        network.change_language(Language.ENGLISH)
        with pytest.raises(WeakNetworkConnectionException):
            raise WeakNetworkConnectionException()

    @pytest.mark.parametrize("language", list(Language))
    def test_extract_campus_names(self, user, language: Language):
        Language.set_current(language)
        database = Database()
        network = Network(user)
        network.change_language(language)
        campus_names = network.extract_campus_names()
        assert campus_names, "Can't extract campus names from the server."
        all_campuses_found = all(campus_name in campus_names for campus_name in database.get_common_campuses_names())
        assert all_campuses_found, "Some campuses names are missing."

    def test_extract_extra_course_info(self, user):
        network = Network(user)
        result = network.extract_extra_course_info(utils.get_course_data_test())
        assert result

    @pytest.mark.parametrize("language", list(Language))
    def test_extract_years(self, user, language: Language):
        network = Network(user)
        network.change_language(language)
        years = network.extract_years()
        current_year = datetime.now().year
        current_hebrew_year = utils.get_current_hebrew_year()
        hebrew_year_data = (current_hebrew_year, utils.get_current_hebrew_name())
        english_year_data = (current_hebrew_year, f"{current_year - 1}-{current_year}")
        test_year = hebrew_year_data if language is Language.HEBREW else english_year_data
        assert years, "Can't extract years from the server."
        assert test_year in years.items(), f"The year {current_hebrew_year} is missing."

    @pytest.mark.parametrize("language", list(Language))
    def test_extract_all_courses(self, user, language: Language):
        network = Network(user)
        network.change_language(language)
        campus_name = utils.get_campus_name_test()

        courses = network.extract_all_courses(campus_name)
        assert courses, "Can't extract courses from the server."
        with pytest.raises(RuntimeError):
            network.extract_all_courses("Not a campus name")

    @pytest.mark.parametrize("language", list(Language))
    def test_extract_academic_activities_data(self, user, language: Language):
        network = Network(user)
        network.change_language(language)
        course = utils.get_course_data_test()
        campus_name = utils.get_campus_name_test()

        academic_activities, missings = network.extract_academic_activities_data(campus_name, [course])
        missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)

        if missings:
            print("WARNING: The following courses don't have activities: " + ", ".join(missings))
        if not academic_activities:
            print("WARNING: Fail to extract the activities, skip it since it can be delay of the college.")
        assert not missing_meetings_data, "Can't extract academic activities from the server."

        not_found_course = Course("name", -10, -30)
        loaded_academic_activities = network.extract_academic_activities_data(campus_name, [not_found_course])
        assert loaded_academic_activities == ([], ["name"])

    @pytest.mark.parametrize("language", list(Language))
    def test_change_language_campuses(self, user, language: Language):
        network = Network(user)
        network.change_language(language)
        campuses = network.extract_campuses()
        # Campus ID of Machon lev is 1
        assert campuses[1] == _("Machon Lev")

    def test_coverage(self, user):
        with pytest.raises(WeakNetworkConnectionException):
            raise WeakNetworkConnectionException()

        with pytest.raises(InvalidServerRequestException):
            try:
                raise InvalidServerRequestException("url_request", {}, None)
            except InvalidServerRequestException as error:
                assert not error.has_json()
                raise

        TLSAdapter.session(ssl.OP_NO_TLSv1_2)
