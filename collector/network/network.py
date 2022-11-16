from typing import List, Optional, Tuple

import json
import requests

from data.academic_activity import AcademicActivity
from data.course import Course
from data.user import User
import utils


class Network:
    HTTP_OK = 200
    TIMEOUT = 10

    def __init__(self, user: Optional[User] = None):
        self.user = user
        self.cookies = None
        self.logger = utils.get_logging()
        self.headers = {'sec-ch-ua': '"Microsoft Edge";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                        'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json;charset=UTF-8',
                        'DNT': '1', 'sec-ch-ua-mobile': '?0',
                        'User-Agent': 'Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42',
                        'sec-ch-ua-platform': '"Windows"', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Dest': 'empty', 'host': 'levnet.jct.ac.il', }

    def connect(self) -> bool:
        if self.user is None:
            raise ValueError("The user is not set.")

        response = None

        url = "https://levnet.jct.ac.il/api/home/login.ashx?action=TryLogin"
        dictionary = {"username": self.user.username, "password": self.user.password, "defaultLanguage": 1}
        payload = str(json.dumps(dictionary, indent=4))

        try:
            response = requests.request("POST", url, headers=self.headers, data=payload, timeout=self.TIMEOUT)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
            self.logger.error("Connection error: %s", str(error))
            return False

        if response.status_code == Network.HTTP_OK:
            data = response.json()
            success = data["success"]
            if success:
                self.cookies = response.cookies
            return success

        return False

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

    def set_user(self, user: User):
        self.user = user
