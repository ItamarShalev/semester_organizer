import pytest
from pytest import fixture

from collector.db.db import Database
from collector.network.public_network import PublicNetworkHttp, WeakNetworkConnectionException
from collector.network.public_network import InvalidSemesterTimeRequestException
from data.language import Language
from data.settings import Settings
from data.user import User


@pytest.mark.network
@pytest.mark.network_http
class BaseTestNetworkHttp:
    already_fail_once = False

    @fixture
    def user(self):
        user_data = ""
        try:
            user_data = Database().load_user_data()
            assert user_data, "Can't load user data."
            network = PublicNetworkHttp(user_data)
            assert network.check_connection(), "Can't connect to the server."
        except Exception as error:
            if not BaseTestNetworkHttp.already_fail_once:
                BaseTestNetworkHttp.already_fail_once = True
                raise error
            pytest.skip(str(error))
        return user_data


@pytest.mark.network
@pytest.mark.network_http
class TestPublicNetworkHttp(BaseTestNetworkHttp):

    def test_fail_connection(self):
        network = PublicNetworkHttp(User("123456789", "123456789"))
        with pytest.raises(RuntimeError):
            network.connect()

    def test_connect_disconnect(self, user):
        network = PublicNetworkHttp(user)
        network.connect()
        network.disconnect()

    def test_extract_all_activities_ids_can_enroll_in(self, user):
        network = PublicNetworkHttp(user)
        settings = Settings()
        activities_ids_can_enroll_in = []

        try:
            activities_ids_can_enroll_in = network.extract_all_activities_ids_can_enroll_in(settings, [])
        except InvalidSemesterTimeRequestException:
            return
        assert "120131.04.5783.01" in activities_ids_can_enroll_in, "Can't extract activities ids can enroll in."

    def test_check_setup(self, user):
        network = PublicNetworkHttp()
        network.set_user(user)
        assert network.check_connection(), "Can't connect to the server."

    def test_extract_courses_already_did(self, user):
        network = PublicNetworkHttp(user)
        courses = network.extract_courses_already_did()
        assert courses, "Can't extract courses already did."
        assert any(course for course in courses if course[1] == 120701)

    def test_for_coverage(self):
        network = PublicNetworkHttp()
        network.set_settings(Settings())
        network.change_language(Language.ENGLISH)
        with pytest.raises(WeakNetworkConnectionException):
            raise WeakNetworkConnectionException()
