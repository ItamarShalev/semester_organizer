from collector.db.db import Database
from collector.gui.gui import Gui
from collector.network.network import Network
from convertor.convertor import Convertor
from csp import csp


class Controller:

    def __init__(self):
        self.database = Database()
        self.network = Network()
        self.gui = Gui()
        self.convertor = Convertor()

    def _get_campus_names(self):
        campus_names = self.database.load_campus_names()
        if not campus_names:
            campus_names = self.network.extract_campus_names()
            self.database.save_campus_names(campus_names)
        return campus_names

    def _get_courses_data(self):
        courses = self.database.load_courses_data()
        if not courses:
            courses = self.network.extract_all_courses()
            self.database.save_courses_data(courses)
        return courses

    def _get_academic_activities_data(self, campus_name, courses, academic_activities, gui, network):
        database = Database()
        activities = []

        if database.check_if_courses_data_exists(courses):
            activities = database.load_academic_activities_data(courses)
        else:
            network.fill_academic_activities_data(campus_name, academic_activities)
            names_missing_activities = network.fill_academic_activities_data(campus_name, academic_activities)

            if names_missing_activities:
                message = "The following courses don't have activities: " + ", ".join(names_missing_activities)
                gui.open_notification_windows(message)
                activities = [activity for activity in activities if activity.name not in names_missing_activities]
            else:
                activities = academic_activities

            database.save_academic_activities_data(activities)
        return activities

    def main_gui_flow(self):
        user = self.gui.open_login_window()
        self.network.set_user(user)

        campus_names = self._get_campus_names()
        courses = self._get_courses_data()
        campus_name, activities = self.gui.open_academic_activities_window(campus_names, courses)
        courses = [activity.convert_to_course_object() for activity in activities]
        activities = self._get_academic_activities_data(campus_name, courses, activities, self.gui, self.network)
        activities += self.gui.open_custom_activities_windows()
        formats = self.gui.open_choose_format_window()
        schedules = csp.extract_schedules(activities)
        if not schedules:
            self.gui.open_notification_windows("No schedules were found")
        else:
            self.convertor.convert_activities(schedules, "results", formats)

        self.gui.open_notification_windows("The schedules were saved in the 'results' folder")
