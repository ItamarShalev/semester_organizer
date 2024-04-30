import json
import re
import ssl
from collections import defaultdict
from contextlib import suppress
from typing import Optional, List, Set, Tuple, Dict, Union

from json import JSONDecodeError

from requests import Response, Session
from requests.exceptions import Timeout
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import urllib3

import utils
from data import translation
from data.academic_activity import AcademicActivity
from data.course import Course
from data.day import Day
from data.degree import Degree
from data.language import Language
from data.meeting import Meeting
from data.semester import Semester
from data.settings import Settings
from data.translation import _
from data.type import Type
from data.user import User


class WeakNetworkConnectionException(Exception):

    def __init__(self):
        super().__init__("ERROR: Weak network connection, please try to refresh or change your network and again later")


class InvalidServerRequestException(Exception):
    def __init__(self, url_request: str, data_request: Dict, response: Response, json_data: Dict = None):
        super().__init__("ERROR: Invalid server request, please try again later")
        self.url_request = url_request
        self.data_request = data_request or {}
        self.response = response
        self.json_data = json_data or {}

    def has_json(self):
        return bool(self.json_data)


class InvalidSemesterTimeRequestException(InvalidServerRequestException):
    pass


class TLSAdapter(HTTPAdapter):
    def __init__(self, ssl_version=None, **kwargs):
        self.ssl_version = ssl_version
        super().__init__(**kwargs)

    @staticmethod
    def session(ssl_version=ssl.PROTOCOL_TLSv1_2) -> Session:
        adapter = TLSAdapter(ssl_version)
        session = Session()
        session.mount(prefix='https://', adapter=adapter)
        return session

    def init_poolmanager(self, connections: int, maxsize: int, block: bool = False, **pool_kwargs):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=self.ssl_version,
            **pool_kwargs
        )


class NetworkHttp:
    """
    :raises: InvalidServerRequestException if the server request is invalid.
             WeakNetworkConnection if the network is weak
    """

    HTTP_OK = 200
    TIMEOUT = 40

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
            self._session = TLSAdapter.session()
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
            raise InvalidServerRequestException(url, data, response) from error

        if not json_data["success"]:
            raise InvalidServerRequestException(url, data, response, json_data)
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
        data = {"username": user.username, "password": user.password, "defaultLanguage": None}
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

    def extract_all_activities_ids_can_enroll_in(self, settings: Settings,
                                                 parent_courses_already_did: List[int] = None) -> Dict[str, Set[int]]:
        self._config_for_build_schedule_start()
        try:
            self._config_year_and_semester(settings.year, settings.semester)
        except InvalidServerRequestException as error:
            if error.has_json():
                # Can't register yet.
                args = error.url_request, error.data_request, error.response, error.json_data
                raise InvalidSemesterTimeRequestException(*args) from None
        tracks = self._get_tracks(settings.year, settings.semester)
        activities_ids = defaultdict(set)
        parent_courses_already_did = parent_courses_already_did or []

        payload_track = {"selectedTrack": None}
        payload_member_id = {"programMemberId": None}

        url_for_track = "https://levnet.jct.ac.il/api/student/buildSchedule.ashx?action=LoadCoursesForTrack"
        url_for_member_id = "https://levnet.jct.ac.il/api/student/buildSchedule.ashx?action=LoadCoursesForProgram"
        for track in tracks:
            payload_track["selectedTrack"] = track
            json_data_track = self.request(url_for_track, payload_track)
            all_programs_member_id = [(item["programMemberId"], item["parentCourseId"])
                                      for item in json_data_track["coursesForTrack"]]
            for program_member_id, parent_course_id in all_programs_member_id:
                if parent_course_id in parent_courses_already_did:
                    continue
                payload_member_id["programMemberId"] = program_member_id
                json_data_member = self.request(url_for_member_id, payload_member_id)
                for course_program in json_data_member["coursesForProgram"]:
                    activity_id_without_group = course_program["courseFullNumber"]
                    for group in course_program["groups"]:
                        group_number = str(group["groupNumber"])
                        if group_number == "-1":
                            # Waiting list, don't add it.
                            continue
                        full_activity_id = activity_id_without_group + "." + group_number.zfill(2)
                        activities_ids[full_activity_id].add(track)
        return activities_ids

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

    def extract_campuses(self):
        if not self._campuses:
            self.extract_campus_names()
        return {campus_id: campus_name for campus_name, campus_id in self._campuses.items()}

    def extract_campus_names(self) -> List[str]:
        url = "https://levnet.jct.ac.il/api/common/parentCourses.ashx?action=LoadParentCourse&ParentCourseID=318"
        json_data = self.request(url)
        self._campuses = {campus["name"]: campus["id"] for campus in json_data["extensions"]}
        return list(self._campuses.keys())

    def extract_years(self) -> Dict[int, str]:
        url = "https://levnet.jct.ac.il/api/common/parentCourses.ashx?action=LoadParentCourse&ParentCourseID=318"
        json_data = self.request(url)
        all_years = json_data["academicYears"]
        min_index, max_index = 0, len(all_years)
        year_hebrew_number = utils.get_current_hebrew_year()
        for index, year_data in enumerate(all_years):
            if year_hebrew_number == year_data["id"]:
                min_index, max_index = max(0, index - 3), min(len(all_years), index + 3)
                break

        years = {campus["id"]: campus["name"] for campus in all_years[min_index: max_index]}
        return years

    @property
    def campuses(self):
        if self._campuses is None:
            self.extract_campus_names()
        return self._campuses

    def _extract_academic_activity_course(self, campus_name: str, course: Course) -> List[AcademicActivity]:
        """
        The function will extract all the academic activities from the given campus and parent course number
        :param campus_name: The name of the campus
        :param course: The course to extract the academic activities from
        :return: A list of AcademicActivity
        """

        url = f"https://levnet.jct.ac.il/api/common/parentCourses.ashx?" \
              f"action=LoadActualCourses&ParentCourseID={course.parent_course_number}"

        semester_value = Semester.ANNUAL.value if Semester.ANNUAL in course.semesters else self.settings.semester.value
        data = {
            "selectedAcademicYear": self.settings.year,
            "selectedSemester": semester_value,
            "selectedExtension": self.campuses[campus_name],
            "current": 1
        }

        type_converter = {
            _("Lesson"): Type.LECTURE,
            _("Exercise"): Type.PRACTICE,
            _("Project in Lab"): Type.LAB,
            _("Project"): Type.LAB,
            _("Lab"): Type.LAB,
            _("Seminar"): Type.SEMINAR,
        }
        activities = []

        def convert_day(day_letter):
            if Language.get_current() is Language.HEBREW:
                return Day(ord(day_letter) - ord('א') + 1)
            short_names_days_en = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            return Day(short_names_days_en.index(day_letter) + 1)

        response_json = self.request(url, data)
        if not response_json["totalItems"]:
            return []

        actual_courses = [item["id"] for item in response_json["items"]]
        for actual_course in actual_courses:
            url = f"https://levnet.jct.ac.il/api/common/actualCourses.ashx?" \
                  f"action=LoadActualCourse&ActualCourseID={actual_course}"
            response_json = self.request(url)
            details = response_json["details"]

            for course_group in response_json["groups"]:
                full_course_data = course_group["groupFullNumber"]
                try:
                    type_course = type_converter[course_group["groupTypeName"].strip()]
                except Exception as error:
                    self.logger.debug("Failed to convert type of course: %s", str(error))
                    type_course = Type.LAB
                lecturer = course_group["courseGroupLecturers"].strip()
                if lecturer == _("reshimat hamtana"):
                    continue
                group_meetings = course_group["courseGroupMeetings"].strip()
                group_comment = course_group["groupComment"]
                comment = group_comment.strip() if group_comment else ""
                if "בהמתנה" in comment:
                    continue
                meetings_list = []
                location = ""
                current_capacity, max_capacity = course_group["courseRelativeQuota"].split("/")
                current_capacity = int(current_capacity)
                max_capacity = int(max_capacity) if max_capacity != "--" else AcademicActivity.UNLIMITED_CAPACITY
                if not group_meetings:
                    continue
                for meeting in group_meetings.split("\r\n"):
                    meeting = meeting.strip()
                    day = re.search(_("day (.+?)[ :]"), meeting).group(1).strip()
                    start, end = re.search(r'(\d+:\d+)-(\d+:\d+)', meeting).group(1, 2)
                    location = re.search(",(.+?)$", meeting)
                    location = location.group(1).strip() if location else ""
                    meetings_list.append(Meeting(convert_day(day), Meeting.str_to_time(start),
                                                 Meeting.str_to_time(end)))
                activity = AcademicActivity(course.name, type_course, True, lecturer, course.course_number,
                                            course.parent_course_number, location, full_course_data, comment)
                activity.set_capacity(current_capacity, max_capacity)
                activity.actual_course_number = details["id"]
                activity.add_slots(meetings_list)
                activity.description = course_group["groupComment"]
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

    def extract_extra_course_info(self, course: Course) -> Tuple[bool, float]:
        base_api = "https://levnet.jct.ac.il/api/common/parentCourses.ashx"
        url = f"{base_api}?action=LoadParentCourse&ParentCourseID={course.parent_course_number}"

        response = self.request(url)
        details = response["details"]
        return details["active"], details["credits"]

    def extract_all_courses(self, campus_name: str, degrees: Union[Set[Degree], Degree, None] = None) -> List[Course]:
        assert campus_name in self.campuses.keys(), f"ERROR: {campus_name} is not a valid campus name"

        # Course number, Remove from degrees.
        skip_courses = {
            # Preliminary Course in Physics I.
            140002: {Degree.COMPUTER_SCIENCE, Degree.SOFTWARE_ENGINEERING}
        }

        if degrees is None:
            degrees = Degree.get_defaults()
        elif isinstance(degrees, Degree):
            degrees = {degrees}

        program_output_filter_data = {"filter": {"WithEnglish": True, "WithKodesh": False}}
        courses = {}
        for degree in degrees:
            for index_year in range(degree.value.years):
                url = "https://levnet.jct.ac.il/api/common/plannedMultiYearPrograms.ashx?action=" \
                      "LoadPlannedMultiYearPrograms"
                payload = {"selectedAcademicYear": self.settings.year - index_year,
                           "selectedExtension": self.campuses[campus_name],
                           "selectedDepartment": degree.value.department,
                           "current": 1}
                response_json = self.request(url, payload)

                def is_relevant_program(item, degree_data):
                    has_credits = bool(item["credits"] and item["coursesCount"] > 0)
                    class_name = _(degree_data.name)
                    server_track_name = item["trackName"].strip()
                    relevant_track_name = class_name.strip() == server_track_name
                    found_name = any(track_name.strip() == item["trackName"] for track_name in degree_data.track_names)
                    relevant_track_name = relevant_track_name or found_name
                    is_relevant = has_credits and relevant_track_name
                    return is_relevant

                relevance_programs = [item for item in response_json["items"] if
                                      is_relevant_program(item, degree.value)]

                for program in relevance_programs:
                    program_id = program["id"]
                    url = f"https://levnet.jct.ac.il/api/common/plannedMultiYearPrograms.ashx?" \
                          f"action=GetMultiYearPlannedProgramMembersWithFilters&InitialProgramID={program_id}"
                    response_json = self.request(url, program_output_filter_data)
                    semesters = [semester_program["members"] for semester_program in response_json["allMembers"]]
                    for semester in semesters:
                        for course in semester:
                            parent_course_name_key = "parentCourseName" if Language.get_current() is Language.HEBREW \
                                else "parentCourseEnglishName"
                            parent_name = course[parent_course_name_key]
                            # In case of new course without English name yet.
                            name = parent_name.strip() if parent_name else course["parentCourseName"].strip()
                            parent_course_id = course["parentCourseID"]
                            course_number = course["parentCourseNumber"]
                            is_current_year = index_year == 0
                            should_skip = course_number in skip_courses and degree in skip_courses[course_number]
                            if (not is_current_year and course_number in courses) or should_skip:
                                continue
                            semester = Semester(course["semesterID"])
                            course_data = Course(name, course_number, parent_course_id, semesters=semester)
                            course_data.add_degrees(degree)
                            is_mandatory = course["mandatory"]
                            if is_mandatory:
                                course_data.add_mandatory(degree)
                            if course_number in courses:
                                course_data = courses[course_number]
                                course_data.add_semesters(semester)
                                course_data.add_degrees(degree)
                                if is_mandatory:
                                    course_data.add_mandatory(degree)
                            else:
                                is_active, credits_count = self.extract_extra_course_info(course_data)
                                course_data.is_active = is_active
                                course_data.credits_count = credits_count
                                courses[course_number] = course_data

        return list(courses.values())

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

    def _config_year_and_semester(self, year: int, semester: Semester):
        payload = {"academicYear": year, "semester": semester.value}
        url = "https://levnet.jct.ac.il/api/student/buildSchedule.ashx?action=SelectSemesterForBuildSchedule"
        self.request(url, payload)

    def _get_tracks(self, year: int, semester: Semester):
        payload = {"academicYear": year, "semester": semester.value}
        url = "https://levnet.jct.ac.il/api/student/buildSchedule.ashx?action=LoadData"
        json_data = self.request(url, payload)
        tracks = [track["id"] for track in json_data["tracks"]]
        return tracks

    def _config_for_build_schedule_start(self):
        url = "https://levnet.jct.ac.il/api/student/RegistrationStatementsInLevnet.ashx?action=IsStudentMakeAStatement"
        self.request(url)
        url = "https://levnet.jct.ac.il/api/student/buildSchedule.ashx?action=LoadDataForBuildScheduleStart"
        self.request(url)
