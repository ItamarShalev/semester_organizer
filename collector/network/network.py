from typing import List, Optional, Tuple, Dict

from enum import Enum
from contextlib import suppress
import json
import requests

from bs4 import BeautifulSoup

from requests.exceptions import Timeout

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from selenium.common.exceptions import SessionNotCreatedException
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService

from webdriver_manager.firefox import GeckoDriverManager as FirefoxDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager as EdgeDriverManager
from webdriver_manager.chrome import ChromeDriverManager

from data.academic_activity import AcademicActivity
from data.course import Course
from data.meeting import Meeting
from data.user import User
from data.type import Type
from data.day import Day
from data.settings import Settings
import utils


class DriverType(Enum):
    EDGE = (webdriver.Edge, webdriver.EdgeOptions, EdgeService, EdgeDriverManager)
    CHROME = (webdriver.Chrome, webdriver.ChromeOptions, ChromeService, ChromeDriverManager)
    FIREFOX = (webdriver.Firefox, webdriver.FirefoxOptions, FirefoxService, FirefoxDriverManager)


class NoDriverFoundException(Exception):

    def __init__(self):
        super().__init__("ERROR: No driver found for this platform")


class WeakNetworkConnectionException(Exception):

    def __init__(self):
        super().__init__("ERROR: Weak network connection, please try to refresh or change your network and again later")


class InvalidServerRequestException(Exception):
    def __init__(self):
        super().__init__("ERROR: Invalid server request, please try again later")


class NetworkHttp:
    """
    :raises: InvalidServerRequestException if the server request is invalid.
             WeakNetworkConnection if the network is weak
    """
    HTTP_OK = 200
    TIMEOUT = 10

    def __init__(self, user: Optional[User] = None):
        self._user = user
        self._session = None
        self._campuses = None
        self.settings = Settings()
        self.logger = utils.get_logging()

    def __del__(self):
        self.disconnect()

    def set_settings(self, settings: Settings):
        self.settings = settings

    def set_user(self, user: User):
        self._user = user

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
            headers = {'sec-ch-ua': '"Microsoft Edge";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                       'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json;charset=UTF-8',
                       'DNT': '1', 'sec-ch-ua-mobile': '?0',
                       'User-Agent': 'Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42',
                       'sec-ch-ua-platform': '"Windows"', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors',
                       'Sec-Fetch-Dest': 'empty', 'host': 'levnet.jct.ac.il', }
            self._session.headers = headers
        return self._session

    def is_connected(self):
        return self._session and self._session.cookies

    def check_connection(self, user: Optional[User] = None) -> bool:
        """
        Check if the user is connected to the server, if no user given, check if the current user is connected
        :raises: InvalidServerRequestException if the server request is invalid.
        :param: user: the user to check the connection for
        :return: True if the user is connected, False otherwise
        """
        assert user or self._user, "No user was provided"
        if not user:
            user = self._user
        url = "https://levnet.jct.ac.il/api/home/login.ashx?action=TryLogin"
        data = {"username": user.username, "password": user.password}
        try:
            response = self.session.post(url, data=json.dumps(data), timeout=NetworkHttp.TIMEOUT)
        except Timeout as error:
            self.logger.error("Connection error: %s", str(error))
            return False

        connected_succeeded = response.status_code == NetworkHttp.HTTP_OK and response.json()["success"]
        self.logger.debug("Status code: %s, connected_succeeded = %s", response.status_code, str(connected_succeeded))

        return connected_succeeded

    def request(self, url: str, data: Optional[dict] = None) -> dict:
        try:
            if not self.is_connected():
                self.connect()
            if data:
                data = json.dumps(data)
            response = self.session.post(url, data=data, timeout=NetworkHttp.TIMEOUT)
        except Timeout as error:
            self.logger.error("Connection error: %s", str(error))
            raise WeakNetworkConnectionException() from error

        try:
            json_data = response.json()
        except json.JSONDecodeError as error:
            self.logger.error("Invalid server response")
            raise InvalidServerRequestException() from error

        if not json_data["success"]:
            raise InvalidServerRequestException()
        self.logger.debug("\n\n*************Status code: %s, json_data = %s", response.status_code,
                          str(json_data).encode(utils.ENCODING))
        return json_data

    def connect(self):
        try:
            connected_succeeded = self.check_connection()
        except Exception as error:
            self.logger.error("Connection error: %s", str(error))
            raise RuntimeError("Failed to connect") from error
        if not connected_succeeded:
            raise RuntimeError("Failed to connect")

    def disconnect(self):
        if self._session:
            url = "https://levnet.jct.ac.il/api/common/account.ashx?action=Logout"
            with suppress(Exception):
                self.request(url)
            self._session.close()
            self._session = None

    def extract_campus_names(self) -> List[str]:
        url = "https://levnet.jct.ac.il/api/common/parentCourses.ashx?action=LoadParentCourse&ParentCourseID=318"
        json_data = self.request(url)
        self._campuses = {campus["name"]: campus["id"] for campus in json_data["extensions"]}
        return list(self._campuses.keys())

    def extract_years(self) -> Dict[int, str]:
        url = "https://levnet.jct.ac.il/api/common/parentCourses.ashx?action=LoadParentCourse&ParentCourseID=318"
        json_data = self.request(url)
        years = {campus["id"]: campus["name"] for campus in json_data["academicYears"][1:8]}
        return years

    def _extract_academic_activity_course(self, campus_name: str, course: Course) -> List[AcademicActivity]:
        """
        The function will extract all the academic activities from the given campus and parent course number
        :param campus_name: The name of the campus
        :param course: The course to extract the academic activities from
        :return: A list of AcademicActivity
        """

        url = f"https://levnet.jct.ac.il/api/common/parentCourses.ashx?" \
              f"action=LoadActualCourses&ParentCourseID={course.parent_course_number}"
        data = {
            "selectedAcademicYear": self.settings.year,
            "selectedSemester": self.settings.semester.value,
            "selectedExtension": self.campuses[campus_name],
            "current": 1
        }

        type_converter = {
            "שעור": Type.LECTURE,
            "תרגיל": Type.PRACTICE,
            "מעבדה": Type.LAB,
            """פרוייקט-במ"מ""": Type.LAB,
            "פרויקט": Type.LAB,
            "סמינר": Type.SEMINAR
        }
        activities = []

        def convert_day(day_letter):
            return Day(ord(day_letter) - ord('א') + 1)

        response_json = self.request(url, data)
        if not response_json["totalItems"]:
            return []

        actual_courses = [item["id"] for item in response_json["items"]]
        for actual_course in actual_courses:
            url = f"https://levnet.jct.ac.il/api/common/actualCourses.ashx?" \
                  f"action=LoadActualCourse&ActualCourseID={actual_course}"
            response_json = self.request(url)

            for group in response_json["groups"]:
                full_course_data = group["groupFullNumber"]
                type_course = type_converter[group["groupTypeName"].strip()]
                lecturer = group["courseGroupLecturers"].strip()
                if lecturer == "רשימת המתנה אין לשבץ":
                    continue
                group_meetings = group["courseGroupMeetings"].strip()
                comment = group["groupComment"].strip()
                meetings_list = []
                location = ""
                current_capacity, max_capacity = group["courseRelativeQuota"].split("/")
                current_capacity = int(current_capacity)
                max_capacity = int(max_capacity) if max_capacity != "--" else AcademicActivity.UNLIMITED_CAPACITY
                if not group_meetings:
                    continue
                for meeting in group_meetings.split("\r\n"):
                    meeting = meeting.strip()
                    day = meeting[len("כל השבועות - יום ")]
                    length = len("כל השבועות - יום א: ")
                    start, end = meeting[length:length + len("00:00-00:00")].split("-")
                    location = meeting[len("כל השבועות - יום א: 18:10-19:40, "):].strip()
                    meetings_list.append(Meeting(convert_day(day), Meeting.str_to_time(start),
                                                 Meeting.str_to_time(end)))
                activity = AcademicActivity(course.name, type_course, True, lecturer, course.course_number,
                                            course.parent_course_number, location, full_course_data, comment)
                activity.set_capacity(current_capacity, max_capacity)

                activity.add_slots(meetings_list)
                activities.append(activity)
        return activities

    def extract_academic_activities_data(self, campus_name: str, courses: List[Course]) -> \
            Tuple[List[AcademicActivity], List[str]]:
        """
        The function fills the academic activities' data.
        The function will connect to the server and will extract the data from the server by the parent course number.
        :param: campus_name: the campus name
        :param: courses: all parent courses to extract
        :return: list of all academic activities by the courses, list of all the courses names that missing data
        """
        not_found_courses = []
        academic_activities = []

        for course in courses:
            activities = self._extract_academic_activity_course(campus_name, course)
            if not activities:
                not_found_courses.append(course.name)
            else:
                academic_activities.extend(activities)
        return academic_activities, not_found_courses

    @property
    def campuses(self):
        if self._campuses is None:
            self.extract_campus_names()
        return self._campuses

    def extract_all_courses(self, campus_name: str) -> List[Course]:

        if campus_name not in self.campuses.keys():
            raise RuntimeError(f"ERROR: {campus_name} is not a valid campus name")

        url = "https://levnet.jct.ac.il/api/common/plannedMultiYearPrograms.ashx?action=LoadPlannedMultiYearPrograms"

        payload = {"selectedAcademicYear": self.settings.year,
                   "selectedExtension": self.campuses[campus_name],
                   "selectedDepartment": 20, "current": 1}
        response_json = self.request(url, payload)

        classes_names = ["מדעי "
                         "המחשב", "הנדסת תוכנה"]

        def is_relevant_program(item):
            is_relevant = item["credits"] and item["coursesCount"] > 0
            is_relevant = is_relevant and any((class_name in item["trackName"] for class_name in classes_names))
            return is_relevant

        relevance_programs = [item for item in response_json["items"] if is_relevant_program(item)]
        courses = set()

        for program in relevance_programs:
            program_id = program["id"]
            url = f"https://levnet.jct.ac.il/api/common/plannedMultiYearPrograms.ashx?" \
                  f"action=GetMultiYearPlannedProgramMembersWithFilters&InitialProgramID={program_id}"
            response_json = self.request(url, payload)
            semesters = [semester_program["members"] for semester_program in response_json["allMembers"]]
            for semester in semesters:
                for course in semester:
                    name = course["parentCourseName"].strip()
                    parent_course_id = course["parentCourseID"]
                    course_number = course["parentCourseNumber"]
                    course_data = Course(name, course_number, parent_course_id)
                    courses.add(course_data)

        return list(courses)


class NetworkDriver:
    HTTP_OK = 200
    TIMEOUT = 10

    def __init__(self, user: Optional[User] = None, run_in_background: bool = False):
        self._user = user
        self.run_in_background = run_in_background
        self._driver = None
        self.logger = utils.get_logging()

    def __del__(self):
        self.disconnect()

    def set_user(self, user: User):
        self._user = user

    def _create_driver(self):
        """
        The function creates the driver.
        :return: the driver
        """
        self.logger.info("Creating driver - waiting for the driver to be ready...")
        for driver in DriverType:
            try:
                driver_type, options_type, service, manager = driver.value
                options = options_type()
                if self.run_in_background:
                    options.add_argument('--headless')
                result_driver = driver_type(service=service(manager().install()), options=options)
                self.logger.info("%s Driver found.", driver.name.capitalize())
                return result_driver
            except SessionNotCreatedException:
                self.logger.debug("Failed to create driver of type %s", driver.name.capitalize())
        raise NoDriverFoundException()

    def _check_connection_to_server(self):
        """
        The function checks if the user is connected to the server.
        :return: True if the user is connected to the server, False otherwise
        """
        self.driver.get('https://levnet.jct.ac.il/Course/ActualCourses.aspx')
        try:
            WebDriverWait(self.driver, 4).until(
                expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="selectedExtension"]')))
        except TimeoutException:
            pass
        return "levnet.jct.ac.il/Login/Login.aspx" not in self.driver.current_url

    def _get_url_after_connect(self, url: str):
        """
        The function goes to the url after the user is connected to the server.
        :param: url: the url to go to
        """
        if not self._check_connection_to_server():
            self.connect()
        self.driver.get(url)

    @property
    def driver(self) -> webdriver:
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver

    @property
    def user(self) -> User:
        assert self._user, "User is not set"
        return self._user

    def check_connection(self) -> bool:

        self.logger.debug("Checking connection to the server...")

        url = "https://levnet.jct.ac.il/api/home/login.ashx?action=TryLogin"
        dictionary = {"username": self.user.username, "password": self.user.password, "defaultLanguage": 1}
        payload = str(json.dumps(dictionary, indent=4))

        headers = {'sec-ch-ua': '"Microsoft Edge";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                   'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json;charset=UTF-8',
                   'DNT': '1', 'sec-ch-ua-mobile': '?0',
                   'User-Agent': 'Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42', 'sec-ch-ua-platform': '"Windows"',
                   'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty',
                   'host': 'levnet.jct.ac.il', }

        try:
            self.logger.debug("Sending request to the server...")
            response = requests.request("POST", url, headers=headers, data=payload, timeout=self.TIMEOUT)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
            self.logger.error("Connection error: %s", str(error))
            return False

        self.logger.debug("Response: %s", response.text)
        self.logger.debug("Status code: %s", response.status_code)

        return response.status_code == NetworkDriver.HTTP_OK and response.json()["success"]

    def connect(self):
        """
        The function connects the user to the server.
        """
        # Catch the exception if the connection is weak
        try:
            self.logger.debug("Starting connection to the server...")
            self.driver.get('https://levnet.jct.ac.il/Login/Login.aspx')
            # Find the username bar
            username_bar = WebDriverWait(self.driver, NetworkDriver.TIMEOUT).until(
                expected_conditions.element_to_be_clickable((By.ID, "username")))
            # Find the password bar
            password_bar = WebDriverWait(self.driver, NetworkDriver.TIMEOUT).until(
                expected_conditions.element_to_be_clickable((By.ID, "password")))

            # Enter username and password
            username_bar.send_keys(self.user.username)
            password_bar.send_keys(self.user.password)

            # Wait for the login button
            login_button = WebDriverWait(self.driver, NetworkDriver.TIMEOUT).until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH, '//*[@id="mainForm"]/section[2]/div/div[1]/div/div/div[5]/button')))

            # Enter the website by clicking the login button
            self.logger.debug("Login button found, clicking...")
            login_button.click()

            # Wait for the homepage to load
            WebDriverWait(self.driver, NetworkDriver.TIMEOUT).until(
                expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="mainForm"]/aside/ul/li[35]/a')))
            self.logger.debug("Connection to the server succeeded.")
        except TimeoutException as error:
            raise WeakNetworkConnectionException() from error

    def extract_academic_activities_data(self, campus_name: str, courses: List[Course]) -> \
            Tuple[List[AcademicActivity], List[str]]:
        """
        The function fills the academic activities' data.
        The function will connect to the server and will extract the data from the server by the parent course number.
        :param: campus_name: the campus name
        :param: courses: all parent courses to extract
        :return: list of all academic activities by the courses, list of all the courses names that missing data
        """

    def extract_all_courses(self, campus_name: str) -> List[Course]:
        """
        For now, extract only courses related to the campus and computer department.
        :param: campus_name: the campus name
        :return: list of courses
        """

    def extract_campus_names(self) -> List[str]:

        self.logger.debug("Extracting campus names...")
        self._get_url_after_connect('https://levnet.jct.ac.il/Course/ActualCourses.aspx')

        # Wait for the campus names to load
        try:
            WebDriverWait(self.driver, NetworkDriver.TIMEOUT).until(
                expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="selectedExtension"]')))
        except TimeoutException as error:
            raise WeakNetworkConnectionException() from error

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        campuses_html = soup.find("select", {"ng-model": "query.selectedExtension"}).findAll("option")
        campuses = [campus.text.strip() for campus in campuses_html if campus.text.strip() != "הכל"]
        self.logger.debug("Campuses found: %s", campuses)
        return campuses

    def disconnect(self):
        """
        The function disconnects the user from the server.
        """
        self.logger.debug("Inside disconnect function")
        if self._driver is not None:
            if self._check_connection_to_server():
                self.logger.debug("Disconnecting from the server...")
                self.driver.get('https://levnet.jct.ac.il/Student/Default.aspx')
                # Wait for the logout button
                try:
                    logout_button = WebDriverWait(self.driver, NetworkDriver.TIMEOUT).until(
                        expected_conditions.element_to_be_clickable(
                            (By.XPATH, '//*[@id="mainForm"]/header/section[2]/ul[1]/li[4]/a')))
                    logout_button.click()
                except TimeoutException:
                    self.logger.debug("Logout button not found")
            self.logger.debug("Closing the driver...")
            self.driver.quit()
            self._driver = None
