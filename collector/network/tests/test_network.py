import pytest
import utils
from collector.db.db import Database
from collector.network.network import NetworkDriver
from collector.network.network import NetworkHttp
from data.user import User


@pytest.mark.network
@pytest.mark.network_http
class TestNetworkHttp:
    user = None

    def test_fail_connection(self):
        network = NetworkHttp(User("123456789", "123456789"))
        with pytest.raises(RuntimeError):
            network.connect()

    def test_check_setup(self):
        user = Database().load_hard_coded_user_data()
        assert user, "Can't load user data."
        network = NetworkHttp()
        network.set_user(user)
        assert network.check_connection(), "Can't connect to the server."
        TestNetworkHttp.user = user

    @pytest.mark.skipif("not TestNetworkHttp.user", reason="There is no user data to check.")
    def test_connect_disconnect(self):
        network = NetworkHttp(TestNetworkHttp.user)
        network.connect()
        network.disconnect()

    @pytest.mark.skipif("not TestNetworkHttp.user", reason="There is no user data to check.")
    def test_extract_campus_names(self):
        database = Database()
        network = NetworkHttp(TestNetworkHttp.user)
        campus_names = network.extract_campus_names()
        assert campus_names, "Can't extract campus names from the server."
        assert all(
            campus_name for campus_name in database.get_common_campuses_names()), "Some campuses names are missing."

    @pytest.mark.skipif("not TestNetworkHttp.user", reason="There is no user data to check.")
    def test_extract_years(self):
        network = NetworkHttp(TestNetworkHttp.user)
        years = network.extract_years()
        assert years, "Can't extract years from the server."
        assert len(years) == 7, "The number of years is not 10."
        assert (5783, 'תשפ"ג') in years.items(), "The year 5783 is missing."

    @pytest.mark.skipif("not TestNetworkHttp.user", reason="There is no user data to check.")
    def test_extract_all_courses(self):
        network = NetworkHttp(TestNetworkHttp.user)
        campus_name = utils.get_campus_name_test()
        assert network.check_connection(), "Can't connect to the server."

        courses = network.extract_all_courses(campus_name)
        assert courses, "Can't extract courses from the server."

    @pytest.mark.skipif("not TestNetworkHttp.user", reason="There is no user data to check.")
    def test_extract_academic_activities_data(self):
        network = NetworkHttp(TestNetworkHttp.user)

        course = utils.get_course_data_test()
        campus_name = utils.get_campus_name_test()

        academic_activities, missings = network.extract_academic_activities_data(campus_name, [course])
        missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)

        assert not missings, "The following courses don't have activities: " + ", ".join(missings)
        assert not missing_meetings_data and academic_activities, "Can't extract academic activities from the server."


@pytest.mark.network
@pytest.mark.network_driver
class TestNetworkDriver:
    run_in_background = True
    user = None

    def test_check_setup(self):
        user = Database().load_hard_coded_user_data()
        assert user, "Can't load user data."
        network = NetworkDriver(user, run_in_background=TestNetworkDriver.run_in_background)
        assert network.check_connection(), "Can't connect to the server."
        TestNetworkDriver.user = user

    @pytest.mark.skipif("not TestNetworkDriver.user", reason="There is no user data to check.")
    def test_connect_disconnect(self):
        network = NetworkDriver(TestNetworkDriver.user, run_in_background=TestNetworkDriver.run_in_background)
        network.connect()
        network.disconnect()

    @pytest.mark.skip(reason="Not implemented yet.")
    @pytest.mark.skipif("not TestNetworkDriver.user", reason="There is no user data to check.")
    def test_extract_all_courses(self):
        network = NetworkDriver(TestNetworkDriver.user, run_in_background=TestNetworkDriver.run_in_background)
        campus_name = utils.get_campus_name_test()
        assert network.check_connection(), "Can't connect to the server."

        courses = network.extract_all_courses(campus_name)
        assert courses, "Can't extract courses from the server."

    @pytest.mark.skipif("not TestNetworkDriver.user", reason="There is no user data to check.")
    def test_extract_campus_names(self):
        database = Database()
        network = NetworkDriver(TestNetworkDriver.user, run_in_background=TestNetworkDriver.run_in_background)
        campus_names = network.extract_campus_names()
        assert campus_names, "Can't extract campus names from the server."
        assert all(
            campus_name for campus_name in database.get_common_campuses_names()), "Some campuses names are missing."

    @pytest.mark.skip(reason="Not implemented yet.")
    @pytest.mark.skipif("not TestNetworkDriver.user", reason="There is no user data to check.")
    def test_extract_academic_activities_data(self):
        network = NetworkDriver(TestNetworkDriver.user, run_in_background=TestNetworkDriver.run_in_background)

        course = utils.get_course_data_test()
        campus_name = utils.get_campus_name_test()

        academic_activities, missings = network.extract_academic_activities_data(campus_name, [course])
        missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)

        assert not missings, "The following courses don't have activities: " + ", ".join(missings)
        assert not missing_meetings_data and academic_activities, "Can't extract academic activities from the server."
