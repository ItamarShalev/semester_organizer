import utils
from collector.db.db import Database
from collector.gui.gui import Gui
from collector.network.network import NetworkHttp
from convertor.convertor import Convertor
from data.academic_activity import AcademicActivity
from csp import csp


class Controller:

    def __init__(self):
        self.database = Database()
        self.network = NetworkHttp()
        self.gui = Gui()
        self.convertor = Convertor()
        self.logger = utils.get_logging()

    def _get_campus_names(self):
        campus_names = self.database.load_campus_names()
        if not campus_names:
            campus_names = self.network.extract_campus_names()
            self.database.save_campus_names(campus_names)
        return campus_names

    def _get_courses_data(self):
        courses = self.database.load_courses_data()
        if not courses:
            courses = self.network.extract_all_courses(utils.get_campus_name_test())
            self.database.save_courses_data(courses)
        return courses

    def _get_academic_activities_data(self, campus_name, courses):
        activities = []

        if self.database.check_if_courses_data_exists(campus_name, courses):
            activities = self.database.load_academic_activities_data(campus_name, courses)
        else:
            activities, names_missing_activities = self.network.extract_academic_activities_data(campus_name, courses)

            if names_missing_activities:
                message = "The following courses don't have activities: " + ", ".join(names_missing_activities)
                self.gui.open_notification_window(message)

            self.database.save_academic_activities_data(campus_name, activities)
        return activities

    def run_main_gui_flow(self):
        # pylint: disable = E, W, R, C
        # To complete : suit the function to the new gui
        user = self.gui.open_login_window()
        self.network.set_user(user)
        campus_names = self._get_campus_names()
        courses = self._get_courses_data()
        courses_choices = self.gui.open_academic_activities_window([])
        activities = self._get_academic_activities_data(campus_name, courses)
        AcademicActivity.union_courses([], [])
        activities += self.gui.open_custom_activities_window()
        formats = []
        schedules = csp.extract_schedules(activities)
        if not schedules:
            self.gui.open_notification_window("No schedules were found")
        else:
            self.convertor.convert_activities(schedules, "results", formats)

        self.gui.open_notification_window("The schedules were saved in the 'results' folder")

    def run_update_levnet_data_flow(self):
        self.network = NetworkHttp()

        self.logger.debug("Start updating the levnet data")
        user = self.database.load_hard_coded_user_data()
        assert user, "There is no user data, can't access the levnet website."
        self.logger.debug("User data was loaded successfully")

        self.network.set_user(user)
        assert self.network.check_connection(), "ERROR: Can't connect to the levnet website"
        self.logger.debug("The username and password are valid")

        self.database.clear_all_data()
        self.logger.debug("The database was cleared successfully")

        campus_names = self.network.extract_campus_names()
        self.logger.debug("The campus names were extracted successfully")
        self.logger.debug("The campus names are: %s", ", ".join(campus_names))

        self.database.save_campus_names(campus_names)

        courses = self.network.extract_all_courses(utils.get_campus_name_test())
        self.logger.debug("The courses were extracted successfully")
        self.logger.debug("The courses are: %s", ", ".join([course.name for course in courses]))

        self.database.save_courses_data(courses)

        common_campuses_names = self.database.get_common_campuses_names()

        for campus_name in common_campuses_names:
            self.logger.debug("Start extracting the academic activities data for the campus: %s", campus_name)
            activities, missings = self.network.extract_academic_activities_data(campus_name, courses)
            if activities and not missings:
                self.logger.debug("The academic activities data were extracted successfully")
            else:
                self.logger.debug("The academic activities data were extracted with errors")
                self.logger.debug("The missing courses are: %s", ', '.join(missings))

            self.database.save_academic_activities_data(campus_name, activities)
