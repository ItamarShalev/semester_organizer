from typing import List, Optional, Tuple

from enum import Enum
import json
import requests

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

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
        super().__init__("No driver found for this platform")


class Network:
    HTTP_OK = 200
    TIMEOUT = 10

    def __init__(self, user: Optional[User] = None, run_in_background: bool = False):
        self.user = user
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
                self.logger.info("Driver found: %s", driver.name.capitalize())
                return result_driver
            except SessionNotCreatedException:
                self.logger.debug("Failed to create driver of type %s", driver.name.capitalize())
        raise NoDriverFoundException()

    @property
    def driver(self) -> webdriver:
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver

    def set_user(self, user: User):
        self.user = user

    def check_connection(self) -> bool:
        assert self.user, "ERROR: The user is not set."

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
        pass

    def disconnect(self):
        """
        The function disconnects the user from the server.
        """
