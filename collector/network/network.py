from typing import List, Optional, Tuple

from enum import Enum
from contextlib import suppress
from abc import ABC, abstractmethod
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
import utils


class DriverType(Enum):
    EDGE = (webdriver.Edge, webdriver.EdgeOptions, EdgeService, EdgeDriverManager)
    CHROME = (webdriver.Chrome, webdriver.ChromeOptions, ChromeService, ChromeDriverManager)
    FIREFOX = (webdriver.Firefox, webdriver.FirefoxOptions, FirefoxService, FirefoxDriverManager)


class NoDriverFoundException(Exception):

    def __init__(self):
        super().__init__("ERROR: No driver found for this platform")


class WeakNetworkConnection(Exception):

    def __init__(self):
        super().__init__("ERROR: Weak network connection, please try to refresh or change your network and again later")


class Network(ABC):
    HTTP_OK = 200
    TIMEOUT = 10

    def __init__(self, user: Optional[User] = None):
        self._user = user
        self.logger = utils.get_logging()

    def __del__(self):
        self.disconnect()

    def set_user(self, user: User):
        self._user = user

    @abstractmethod
    def check_connection(self) -> bool:
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def extract_campus_names(self) -> List[str]:
        pass

    @abstractmethod
    def extract_all_courses(self, campus_name: str) -> List[Course]:
        pass

    @abstractmethod
    def extract_academic_activities_data(self, campus_name: str, courses: List[Course]) -> \
            Tuple[List[AcademicActivity], List[str]]:
        """
        The function fills the academic activities' data.
        The function will connect to the server and will extract the data from the server by the parent course number.
        :param user: the username and password
        :param campus_name: the campus name
        :param courses: all parent courses to extract
        :return: list of all academic activities by the courses, list of all the courses names that missing data
        """


class NetworkHttp(Network):

    def __init__(self, user: Optional[User] = None):
        super().__init__(user)
        self._session = None
        self._campuess = None

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

    def check_connection(self) -> bool:
        url = "https://levnet.jct.ac.il/api/home/login.ashx?action=TryLogin"
        data = {"username": self._user.username, "password": self._user.password}
        response = None
        try:
            response = self.session.post(url, data=json.dumps(data), timeout=Network.TIMEOUT)
        except Timeout as error:
            self.logger.error("Connection error: %s", str(error))
            return False

        self.logger.debug("Response: %s", response.text)
        self.logger.debug("Status code: %s", response.status_code)

        return response.status_code == Network.HTTP_OK and response.json()["success"]

    def connect(self):
        connected_successed = False
        try:
            connected_successed = self.check_connection()
        except Exception as error:
            self.logger.error("Connection error: %s", str(error))
            raise RuntimeError("Failed to connect") from error
        if not connected_successed:
            raise RuntimeError("Failed to connect")

    def disconnect(self):
        if not self._session:
            url = "https://levnet.jct.ac.il/api/common/account.ashx?action=Logout"
            with suppress(Exception):
                self.session.post(url, timeout=Network.TIMEOUT)
            self._session.close()
            self._session = None

    def extract_campus_names(self) -> List[str]:
        if not self.is_connected():
            self.connect()

        url = "https://levnet.jct.ac.il/api/common/parentCourses.ashx?action=LoadParentCourse&ParentCourseID=318"
        response = None
        try:
            response = self.session.post(url, timeout=Network.TIMEOUT)
        except Timeout as error:
            self.logger.error("Connection error: %s", str(error))
            raise WeakNetworkConnection() from error

        json_data = response.json()
        if not json_data["success"]:
            raise RuntimeError("Failed to extract campus names")
        self._campuess = {campus["name"]: campus["id"] for campus in json_data["extensions"]}
        return list(self._campuess.keys())

    def extract_academic_activities_data(self, campus_name: str, courses: List[Course]) -> \
            Tuple[List[AcademicActivity], List[str]]:
        """
        The function fills the academic activities' data.
        The function will connect to the server and will extract the data from the server by the parent course number.
        :param user: the username and password
        :param campus_name: the campus name
        :param courses: all parent courses to extract
        :return: list of all academic activities by the courses, list of all the courses names that missing data
        """
        not_found_courses = []
        academic_activities = []
        response = None
        type_converter = {
            "שעור": Type.LECTURE,
            "תרגיל": Type.PRACTICE,
            "מעבדה": Type.LAB
        }

        def convert_day(day):
            return Day(ord(day) - ord('א') + 1)

        for course in courses:
            url = f"https://levnet.jct.ac.il/api/common/parentCourses.ashx?" \
                  f"action=LoadActualCourses&ParentCourseID={course.parent_course_number}"
            data = {
                "selectedAcademicYear": utils.get_current_hebrew_year(),
                "selectedSemester": utils.get_current_semester().value,
                "selectedExtension": self.campuess[campus_name],
                "current": 1
            }
            try:
                response = self.session.post(url, data=json.dumps(data), timeout=Network.TIMEOUT)
            except Timeout as error:
                self.logger.error("Connection error: %s", str(error))
                raise WeakNetworkConnection() from error
            response_json = response.json()
            if not response_json["success"]:
                return [], [course.name for course in courses]
            if not response_json["totalItems"]:
                not_found_courses.append(course.name)
                continue
            actual_courses = [item["id"] for item in response_json["items"]]
            academic_activities_course = []
            for actual_course in actual_courses:
                url = f"https://levnet.jct.ac.il/api/common/actualCourses.ashx?" \
                      f"action=LoadActualCourse&ActualCourseID={actual_course}"
                try:
                    response = self.session.post(url, timeout=Network.TIMEOUT)
                except Timeout as error:
                    self.logger.error("Connection error: %s", str(error))
                    raise WeakNetworkConnection() from error
                response_json = response.json()
                if not response_json["success"]:
                    continue
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
                    activity.add_slots(meetings_list)
                    academic_activities_course.append(activity)
            if not academic_activities_course:
                not_found_courses.append(course.name)
                continue
            academic_activities.extend(academic_activities_course)
        return academic_activities, not_found_courses

    @property
    def campuess(self):
        if self._campuess is None:
            self.extract_campus_names()
        return self._campuess

    def extract_all_courses(self, campus_name: str) -> List[Course]:
        if not self.is_connected():
            self.connect()

        if campus_name not in self.campuess.keys():
            raise RuntimeError("Failed to extract courses")

        url = "https://levnet.jct.ac.il/api/common/plannedMultiYearPrograms.ashx?action=LoadPlannedMultiYearPrograms"

        payload = {"selectedAcademicYear": utils.get_current_hebrew_year(),
                   "selectedExtension": self.campuess[campus_name], "selectedDepartment": 20, "current": 1}
        response = self.session.post(url, data=json.dumps(payload), timeout=Network.TIMEOUT)
        if response.status_code != Network.HTTP_OK or not response.json()["success"]:
            raise RuntimeError("Failed to extract courses")
        classes_names = ["מדעי המחשב", "הנדסת תוכנה"]

        def is_relvant_program(item):
            is_relvant = item["credits"] and item["coursesCount"] > 0
            is_relvant = is_relvant and any((name in item["trackName"] for name in classes_names))
            return is_relvant

        relvants_programs = [item for item in response.json()["items"] if is_relvant_program(item)]
        courses = set()

        for program in relvants_programs:
            program_id = program["id"]
            url = f"https://levnet.jct.ac.il/api/common/plannedMultiYearPrograms.ashx?" \
                  f"action=GetMultiYearPlannedProgramMembersWithFilters&InitialProgramID={program_id}"
            response = self.session.post(url, data=payload)
            if not response.json()["success"]:
                raise RuntimeError("Failed to extract courses")
            semesters = [semster_program["members"] for semster_program in response.json()["allMembers"]]
            for semester in semesters:
                for course in semester:
                    name = course["parentCourseName"].strip()
                    parent_course_id = course["parentCourseID"]
                    course_number = course["parentCourseNumber"]
                    course_data = Course(name, course_number, parent_course_id)
                    courses.add(course_data)

        return list(courses)


class NetworkDriver(Network):

    def __init__(self, user: Optional[User] = None, run_in_background: bool = False):
        super().__init__(user)
        self.run_in_background = run_in_background
        self._driver = None

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
        :param url: the url to go to
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
        response = None

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

        return response.status_code == Network.HTTP_OK and response.json()["success"]

    def connect(self):
        """
        The function connects the user to the server.
        """
        # Catch the exception if the connection is weak
        try:
            self.logger.debug("Starting connection to the server...")
            self.driver.get('https://levnet.jct.ac.il/Login/Login.aspx')
            # Find the username bar
            username_bar = WebDriverWait(self.driver, Network.TIMEOUT).until(
                expected_conditions.element_to_be_clickable((By.ID, "username")))
            # Find the password bar
            password_bar = WebDriverWait(self.driver, Network.TIMEOUT).until(
                expected_conditions.element_to_be_clickable((By.ID, "password")))

            # Enter username and password
            username_bar.send_keys(self.user.username)
            password_bar.send_keys(self.user.password)

            # Wait for the login button
            login_button = WebDriverWait(self.driver, Network.TIMEOUT).until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH, '//*[@id="mainForm"]/section[2]/div/div[1]/div/div/div[5]/button')))

            # Enter the website by clicking the login button
            self.logger.debug("Login button found, clicking...")
            login_button.click()

            # Wait for the homepage to load
            WebDriverWait(self.driver, Network.TIMEOUT).until(
                expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="mainForm"]/aside/ul/li[35]/a')))
            self.logger.debug("Connection to the server succeeded.")
        except TimeoutException as error:
            raise WeakNetworkConnection() from error

    def extract_academic_activities_data(self, campus_name: str, courses: List[Course]) -> \
            Tuple[List[AcademicActivity], List[str]]:
        """
        The function fills the academic activities' data.
        The function will connect to the server and will extract the data from the server by the parent course number.
        :param user: the username and password
        :param campus_name: the campus name
        :param courses: all parent courses to extract
        :return: list of all academic activities by the courses, list of all the courses names that missing data
        """

    def extract_all_courses(self, campus_name: str) -> List[Course]:
        """
        For now, extract only courses related to the campus and computer department.
        :param campus_name: the campus name
        :return: list of courses
        """

    def extract_campus_names(self) -> List[str]:

        self.logger.debug("Extracting campus names...")
        self._get_url_after_connect('https://levnet.jct.ac.il/Course/ActualCourses.aspx')

        # Wait for the campus names to load
        try:
            WebDriverWait(self.driver, Network.TIMEOUT).until(
                expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="selectedExtension"]')))
        except TimeoutException as error:
            raise WeakNetworkConnection() from error

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
                    logout_button = WebDriverWait(self.driver, Network.TIMEOUT).until(
                        expected_conditions.element_to_be_clickable(
                            (By.XPATH, '//*[@id="mainForm"]/header/section[2]/ul[1]/li[4]/a')))
                    logout_button.click()
                except TimeoutException:
                    self.logger.debug("Logout button not found")
            self.logger.debug("Closing the driver...")
            self.driver.quit()
            self._driver = None
