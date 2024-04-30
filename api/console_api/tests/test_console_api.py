import json
import sys
from pathlib import Path
from typing import Dict
from unittest.mock import patch, Mock

import pytest

import utils
from api.console_api.console_api import GetCampuses, GetCourses, SelectChoices
from collector.db.db import Database
from collector.network.network import NetworkHttp
from data.academic_activity import AcademicActivity
from data.course import Course
from data.day import Day
from data.degree import Degree
from data.language import Language
from data.meeting import Meeting
from data.semester import Semester
from data.type import Type
from utils import ConsoleApi


@pytest.fixture(autouse=True)
def mock_network() -> NetworkHttp:
    with patch('api.console_api.console_api.NetworkHttp', new_callable=Mock) as network_http_obj_mock:
        network = network_http_obj_mock.return_value
        track_id = 1
        network.extract_all_activities_ids_can_enroll_in = Mock()
        network.extract_all_activities_ids_can_enroll_in.return_value = {
            "124.01": {track_id},
            "125.02": {track_id},
            "125.06": {track_id},
        }
        yield network


@pytest.fixture(autouse=True)
def mock_database() -> Database:
    class DatabaseMock(Database):

        def __init__(self):
            super().__init__("test_database")
            database_path = utils.get_database_path() / "test_database"
            self.shared_database_path = database_path / "database.db"
            self.user_name_file_path.unlink(missing_ok=True)

    database = DatabaseMock()
    database.init_database_tables()
    campuses = {
        1: ("A", "א"),
        2: ("B", "ב"),
        3: ("C", "ג"),
    }
    database.save_campuses(campuses)

    campus_name = campuses[1][0]
    langauge = Language.HEBREW
    activity1 = AcademicActivity("A", Type.LECTURE, True, "A", 124, 34, "", "124.01", "", 0, 100, 1213)
    activity2 = AcademicActivity("B", Type.LAB, True, "B", 125, 35, "", "125.02", "", 0, 100, 1213)
    activity3 = AcademicActivity("C", Type.LECTURE, True, "C", 126, 36, "", "126.03", "", 0, 100, 1213)
    activity4 = AcademicActivity("A", Type.LECTURE, True, "AA", 124, 34, "", "126.04", "", 0, 100, 1213)
    activity5 = AcademicActivity("B", Type.LAB, True, "BB", 125, 35, "", "125.06", "", 0, 100, 1213)
    activity1.add_slot(Meeting(Day.MONDAY, "10:00", "12:00"))
    activity2.add_slot(Meeting(Day.SUNDAY, "10:00", "12:00"))
    activity3.add_slot(Meeting(Day.WEDNESDAY, "10:00", "12:00"))
    activity4.add_slot(Meeting(Day.WEDNESDAY, "10:00", "12:00"))
    activity5.add_slot(Meeting(Day.THURSDAY, "10:00", "12:00"))

    activities = [
        activity1,
        activity2,
        activity3,
        activity4,
        activity5
    ]

    courses = [
        Course("A", 124, 34, set(Semester), set(Degree)),
        Course("B", 125, 35, set(Semester), set(Degree)),
        Course("C", 126, 36, set(Semester), set(Degree)),
    ]

    database.save_degrees(list(Degree))
    database.save_semesters(list(Semester))
    database.save_courses(courses, langauge)
    database.save_academic_activities(activities, campus_name, langauge)
    database.get_common_campuses_names = Mock()
    database.get_common_campuses_names.return_value = ["א"]
    with patch('api.console_api.console_api.Database', new_callable=Mock) as database_obj_mock:
        database_obj_mock.return_value = database
        yield database


class TestConsoleApi:
    argv = None
    output_file = Path("result.json")
    input_file = Path("input.json")

    def setup_method(self, method: Type):
        self.argv = sys.argv
        self.output_file.unlink(missing_ok=True)
        self.input_file.unlink(missing_ok=True)

    def teardown_method(self, method: Type):
        sys.argv = self.argv
        self.output_file.unlink(missing_ok=True)
        self.input_file.unlink(missing_ok=True)

    def _get_json_data_result(self) -> Dict:
        assert self.output_file.is_file(), "ERROR: Output file does not exist"
        with open(self.output_file, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
        assert json_data["status"], "ERROR: Status is false."
        assert not json_data["message_error"], "ERROR: Message is not empty."
        assert len(json_data["result"]), "ERROR: There isn't any campus."
        return json_data


class TestGetCampuses(TestConsoleApi):

    @pytest.mark.parametrize("common", [False, True])
    def test_get_campuses(self, common: bool):
        command = GetCampuses
        sys.argv = [sys.argv[0]] + [command().snake_case_name(), "--output_file", self.output_file.name]
        sys.argv += ["--only_common"] if common else []
        ConsoleApi.run([command])
        json_data = self._get_json_data_result()
        assert set(json_data["result"][0].keys()) == {"id", "english_name", "hebrew_name"}, "ERROR: Missing keys."
        except_campuses = {1: ("A", "א"), }
        if not common:
            except_campuses[2] = ("B", "ב")
            except_campuses[3] = ("C", "ג")
        list_campuses = []
        for campus_id, (english_name, hebrew_name) in except_campuses.items():
            list_campuses.append({"id": campus_id, "english_name": english_name, "hebrew_name": hebrew_name})
        assert json_data["result"] == list_campuses, "ERROR: Missing excepted campuses."


class TestGetCourses(TestConsoleApi):

    @pytest.mark.parametrize("only_classes_can_enroll", [False, True])
    def test_get_courses(self, only_classes_can_enroll: bool):
        command = GetCourses
        sys.argv = [sys.argv[0]] + [command().snake_case_name(), "--output_file", self.output_file.name]
        sys.argv += ["--id", "test_id", "--campus_id", "1"]
        if only_classes_can_enroll:
            sys.argv += ["--only_classes_can_enroll", "--user_name", "user", "--password", "password"]
        ConsoleApi.run([command])
        json_data = self._get_json_data_result()
        a_course = json_data["result"][0]
        b_course = json_data["result"][1]
        if only_classes_can_enroll:
            assert len(json_data["result"]) == 2
            assert len(a_course["available_teachers_for_lecture"]) == 1
        assert a_course["name"] == "A"
        assert "A" in a_course["available_teachers_for_lecture"]
        assert b_course["name"] == "B"
        assert set(b_course["available_teachers_for_practice"]) == {"B", "BB"}


class TestSelectChoices(TestConsoleApi):

    def _prepare_choices_file(self) -> Path:
        input_dict = {
            "result": [
                {
                    "name": "A",
                    "parent_course_number": 34,
                    "available_teachers_for_lecture": [
                        "A"
                    ],
                    "available_teachers_for_practice": []
                },
                {
                    "name": "B",
                    "parent_course_number": 35,
                    "available_teachers_for_lecture": [],
                    "available_teachers_for_practice": [
                        "B",
                        "BB"
                    ]
                },
            ]
        }
        with open(self.input_file, "w", encoding='utf-8') as json_file:
            json.dump(input_dict, json_file)
        return self.input_file

    @pytest.mark.parametrize("max_output", [1, 2])
    def test_select_choices(self, max_output: int):
        choices_file = self._prepare_choices_file()
        command = SelectChoices
        sys.argv = [sys.argv[0]] + [command().snake_case_name(), "--output_file", self.output_file.name]
        sys.argv += ["--id", "test_id", "--max_output", str(max_output), "--choices_file", choices_file.name]
        ConsoleApi.run([command])
        json_data = self._get_json_data_result()
        result_path = Path(json_data["result"]["result_path"])
        all_results_files = set(path.name for path in result_path.rglob("**/*") if path.is_file())
        assert len(all_results_files) == max_output, "ERROR: There isn't one result file as excepted."
