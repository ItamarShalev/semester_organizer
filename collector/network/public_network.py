import json
from contextlib import suppress
from typing import Optional, List, Set, Tuple

from json import JSONDecodeError
from requests.exceptions import Timeout
import requests
import urllib3

import utils
from data import translation
from data.language import Language
from data.settings import Settings
from data.user import User


class WeakNetworkConnectionException(Exception):

    def __init__(self):
        super().__init__("ERROR: Weak network connection, please try to refresh or change your network and again later")


class InvalidServerRequestException(Exception):
    def __init__(self):
        super().__init__("ERROR: Invalid server request, please try again later")


class PublicNetworkHttp:
    """
    :raises: InvalidServerRequestException if the server request is invalid.
             WeakNetworkConnection if the network is weak
    """

    HTTP_OK = 200
    TIMEOUT = 25

    def __init__(self, user: Optional[User] = None):
        self._user = user
        self._session = None
        self._campuses = None
        self.settings = Settings()
        self.logger = utils.get_logging()
        urllib3.disable_warnings()

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
            headers = {
                'sec-ch-ua': '"Microsoft Edge";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json;charset=UTF-8',
                'DNT': '1',
                'sec-ch-ua-mobile': '?0',
                'User-Agent': 'Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'host': 'levnet.jct.ac.il'
            }
            self._session.headers = headers
        return self._session

    def is_connected(self):
        return self._session and self._session.cookies

    def request(self, url: str, data: Optional[dict] = None) -> dict:
        try:
            if not self.is_connected():
                self.connect()
            if data:
                data = json.dumps(data)
            response = self.session.post(url, data=data, timeout=self.TIMEOUT, verify=False)
        except Timeout as error:
            self.logger.debug("\n\nFAIL: request url = %s", url)
            self.logger.error("Connection error: %s", str(error))
            raise WeakNetworkConnectionException() from error

        try:
            json_data = response.json()
        except JSONDecodeError as error:
            self.logger.debug("\n\nFAIL: request url = %s", url)
            self.logger.error("Invalid server response")
            raise InvalidServerRequestException() from error

        if not json_data["success"]:
            raise InvalidServerRequestException()
        self.logger.debug("\n\nSUCCESS: request url = %s", url)
        return json_data

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
            response = self.session.post(url, data=json.dumps(data), timeout=self.TIMEOUT, verify=False)
        except Timeout as error:
            self.logger.debug("FAIL: request url = %s", url)
            self.logger.error("Connection error: %s", str(error))
            return False

        connected_succeeded = response.status_code == self.HTTP_OK and response.json()["success"]
        success_or_fail = "SUCCESS" if connected_succeeded else "FAIL"
        self.logger.debug("%s: request url = %s,\nStatus code: %s", success_or_fail, url, response.status_code)

        return connected_succeeded

    def connect(self):
        try:
            connected_succeeded = self.check_connection()
        except Exception as error:
            self.logger.error("Connection error: %s", str(error))
            raise RuntimeError("Failed to connect") from error
        if not connected_succeeded:
            raise RuntimeError("Failed to connect")
        self.change_language(Language.get_current())

    def extract_all_activities_ids_can_enroll_in(self) -> List[str]:
        return []

    def extract_courses_already_did(self) -> Set[Tuple[str, int]]:
        """
        Extract the courses that the user already did
        :return: a set of tuples of the course name and the course number (not parent course number)
        """
        courses = set()
        current_page = 1
        payload = {"selectedAcademicYear": None, "selectedSemester": None, "current": current_page}
        url = "https://levnet.jct.ac.il/api/student/grades.ashx?action=LoadGrades"
        while True:
            json_data = self.request(url, payload)
            current_page += 1
            payload["current"] = current_page
            items = json_data["items"]
            if not items:
                break
            for item in items:
                if not item["finalGradeName"].isdigit() or int(item["finalGradeName"]) < int(item["effectiveMinGrade"]):
                    continue
                if item["isDroppedOut"]:
                    continue
                course_number = item["actualCourseFullNumber"].split(".")[0]
                courses.add((item["courseName"], int(course_number)))
        return courses

    def change_language(self, language: Language):
        if not self._user:
            return
        url = "https://levnet.jct.ac.il/api/home/local.ashx?action=ChangeLanguage"
        data = {"language": language.name.capitalize()}
        self.request(url, data)
        self._campuses = None
        translation.config_language_text(language)

    def disconnect(self):
        if self._session:
            url = "https://levnet.jct.ac.il/api/common/account.ashx?action=Logout"
            with suppress(Exception):
                self.request(url)
            self._session.close()
            self._session = None
