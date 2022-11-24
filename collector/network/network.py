from typing import List, Optional, Tuple

from enum import Enum
import json
import requests

from bs4 import BeautifulSoup
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
from data.user import User
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


class Network:
    HTTP_OK = 200
    TIMEOUT = 10

    def __init__(self, user: Optional[User] = None, run_in_background: bool = False):
        self._user = user
        self.logger = utils.get_logging()
        self.run_in_background = run_in_background
        self._driver = None

    def __del__(self):
        if self._driver:
            self._driver.quit()
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

    def set_user(self, user: User):
        self.user = user

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

    def extract_academic_activities_data(self, campus_name: str, courses: List[int]) -> \
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
        pass

    def extract_campus_names(self) -> List[str]:

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
        return campuses

    def disconnect(self):
        """
        The function disconnects the user from the server.
        """
