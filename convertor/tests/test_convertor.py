import os
import shutil

import pytest

import utils
from convertor.convertor import Convertor
from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.day import Day
from data.meeting import Meeting
from data.output_format import OutputFormat
from data.schedule import Schedule
from data.type import Type


class TestConvertor:

    @staticmethod
    def _create_schedule(file_name: str):
        activity = AcademicActivity("שם", Type.LECTURE, True, "שם המרצה", 1, 100, "מיקום")
        activity.add_slot(Meeting(Day.MONDAY, Meeting.str_to_time("10:00"), Meeting.str_to_time("12:00")))
        return Schedule("שם", file_name, "", [activity])

    @pytest.mark.parametrize("file_type", [OutputFormat.CSV, OutputFormat.EXCEL])
    def test_convert_type(self, file_type: OutputFormat):

        convertor = Convertor()
        path = os.path.join(utils.get_results_path(), "test_results")
        extension = file_type.value
        schedules = []
        shutil.rmtree(path, ignore_errors=True)

        for i in range(1, 10):
            schedules.append(TestConvertor._create_schedule(f"option_{i}"))

        activity = Activity("שם", Type.PERSONAL, True)
        activity.add_slot(Meeting(Day.FRIDAY, "10:00", "12:00"))
        schedules.append(Schedule("שם", f"option_{10}", "", [activity]))

        convertor.convert_activities(schedules, path, [file_type])
        for i in range(1, 11):
            file_name = f"option_{i}.{extension}"
            file_path = os.path.join(path, file_name)
            assert os.path.isfile(f"{file_path}"), f"{file_name} is not exist"
            assert os.path.getsize(f"{file_path}") > 0, f"{file_name} is empty"

    @pytest.mark.skip(reason="Not implemented yet.")
    def test_convert_all_types(self):
        convertor = Convertor()
        path = os.path.join(utils.get_results_path(), "test_results")
        schedules = []
        shutil.rmtree(path, ignore_errors=True)

        for i in range(1, 10):
            schedules.append(TestConvertor._create_schedule(f"option_{i}"))
        activity = Activity("שם", Type.PERSONAL, True)
        activity.add_slot(Meeting(Day.FRIDAY, "10:00", "12:00"))
        schedules.append(Schedule("שם", f"option_{10}", "", [activity]))

        convertor.convert_activities(schedules, path, list(OutputFormat))

        for file_type in OutputFormat:
            extension = file_type.value
            folder_type_path = os.path.join(path, file_type.name.lower())
            for i in range(1, 11):
                file_name = f"option_{i}.{extension}"
                file_path = os.path.join(folder_type_path, file_name)
                assert os.path.isfile(f"{file_path}"), f"{file_name} is not exist"
                assert os.path.getsize(f"{file_path}") > 0, f"{file_name} is empty"
