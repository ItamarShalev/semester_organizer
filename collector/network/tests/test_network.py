import pytest
import utils
from collector.db.db import Database
from collector.network.network import Network


@pytest.mark.network
class TestNetwork:

    run_in_background = True
    user = None

    def test_check_setup(self):
        user = Database().load_hard_coded_user_data()
        assert user, "Can't load user data."
        network = Network(user, run_in_background=TestNetwork.run_in_background)
        assert network.check_connection(), "Can't connect to the server."
        TestNetwork.user = user

    @pytest.mark.skipif("not TestNetwork.user", reason="There is no user data to check.")
    def test_connect_disconnect(self):
        network = Network(TestNetwork.user, run_in_background=TestNetwork.run_in_background)
        network.connect()
        network.disconnect()

    @pytest.mark.skip(reason="Not implemented yet.")
    @pytest.mark.skipif("not TestNetwork.user", reason="There is no user data to check.")
    def test_extract_all_courses(self):
        network = Network(TestNetwork.user, run_in_background=TestNetwork.run_in_background)
        campus_name = utils.get_campus_name_test()
        assert network.check_connection(), "Can't connect to the server."

        courses = network.extract_all_courses(campus_name)
        assert courses, "Can't extract courses from the server."

    @pytest.mark.skipif("not TestNetwork.user", reason="There is no user data to check.")
    def test_extract_campus_names(self):
        database = Database()
        network = Network(TestNetwork.user, run_in_background=TestNetwork.run_in_background)
        campus_names = network.extract_campus_names()
        assert campus_names, "Can't extract campus names from the server."
        assert all(
            campus_name for campus_name in database.get_common_campuses_names()), "Some campuses names are missing."

    @pytest.mark.skip(reason="Not implemented yet.")
    @pytest.mark.skipif("not TestNetwork.user", reason="There is no user data to check.")
    def test_fill_academic_activities_data(self):
        network = Network(TestNetwork.user, run_in_background=TestNetwork.run_in_background)

        course = utils.get_course_data_test()
        campus_name = utils.get_campus_name_test()

        academic_activities, missings = network.extract_academic_activities_data(campus_name, [course])
        missing_meetings_data = any(activity.no_meetings() for activity in academic_activities)

        assert not missings, "The following courses don't have activities: " + ", ".join(missings)
        assert not missing_meetings_data and academic_activities, "Can't extract academic activities from the server."
