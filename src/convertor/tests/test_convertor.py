import os
import shutil

import pytest
from src import utils
from src.convertor.convertor import Convertor
from src.data.academic_activity import AcademicActivity
from src.data.activity import Activity
from src.data.day import Day
from src.data.language import Language
from src.data.meeting import Meeting
from src.data.output_format import OutputFormat
from src.data.schedule import Schedule
from src.data.type import Type


class TestConvertor:

    @staticmethod
    def _create_schedule(file_name: str):
        activity = AcademicActivity("שם", Type.LECTURE, True, "שם המרצה", 1, 100, "מיקום")
        activity.add_slot(Meeting(Day.MONDAY, Meeting.str_to_time("10:00"), Meeting.str_to_time("12:00")))
        return Schedule("שם", file_name, "", [activity])

    @pytest.mark.parametrize("file_type, use_multiprocessing",
                             [(file_type, use_multiprocessing)
                              for file_type in OutputFormat for use_multiprocessing in [True, False]])
    def test_convert_type(self, file_type: OutputFormat, use_multiprocessing: bool):
        Language.set_current(Language.HEBREW)

        convertor = Convertor()
        path = utils.get_results_test_path()
        extension = file_type.value
        schedules = []
        shutil.rmtree(path, ignore_errors=True)

        for i in range(1, 5):
            schedules.append(TestConvertor._create_schedule(f"option_{i}"))

        activity = Activity("שם", Type.PERSONAL, True)
        activity.add_slot(Meeting(Day.FRIDAY, "10:00", "12:00"))
        schedules.append(Schedule("שם", f"option_{5}", "", [activity]))
        os.environ["multiprocessing"] = str(use_multiprocessing)
        # Just for coverage
        convertor.convert_activities([], path, [file_type])
        convertor.convert_activities(schedules, path, [file_type])
        for i in range(1, 5):
            file_name = f"option_{i}.{extension}"
            file_path = path / file_name
            assert file_path.is_file(), f"{file_name} is not exist"
            assert file_path.stat().st_size > 0, f"{file_name} is empty"

    def test_convert_all_types(self):
        convertor = Convertor()
        path = utils.get_results_test_path()
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
            folder_type_path = path / file_type.name.lower()
            for i in range(1, 11):
                file_name = f"option_{i}.{extension}"
                file_path = folder_type_path / file_name
                assert file_path.is_file(), f"{file_name} is not exist"
                assert file_path.stat().st_size > 0, f"{file_name} is empty"
