
import os
import shutil
import pytest
import utils

from convertor.convertor import Convertor
from data.output_format import OutputFormat
from data.academic_activity import AcademicActivity
from data.meeting import Meeting
from data.type import Type
from data.day import Day
from data.schedule import Schedule


def _create_schedule(file_name: str):
    activity = AcademicActivity("a", Type.LECTURE, True, "a", 1, 100, "a")
    activity.add_slot(Meeting(Day.MONDAY, Meeting.str_to_time("10:00"), Meeting.str_to_time("12:00")))
    return Schedule("a", file_name, "", [activity])


@pytest.mark.skip(reason="Not implemented yet.")
@pytest.mark.parametrize("file_type", list(OutputFormat))
def test_convert_pdf(file_type: OutputFormat):
    convertor = Convertor()
    path = os.path.join(utils.get_results_path(), "test_results")
    extension = file_type.value
    schedules = []
    for i in range(1, 10):
        schedules.append(_create_schedule(f"option_{i}"))

    convertor.convert_activities(schedules, path, [file_type])
    for i in range(1, 10):
        file_name = f"option_{i}.{extension}"
        file_path = os.path.join(path, file_name)
        assert os.path.isfile(f"{file_path}"), f"{file_name} is not exist"
        assert os.path.getsize(f"{file_path}") > 0, f"{file_name} is empty"

    shutil.rmtree(path)


@pytest.mark.skip(reason="Not implemented yet.")
def test_convert_all_types():
    convertor = Convertor()
    path = os.path.join(utils.get_results_path(), "test_results")
    schedules = []
    for i in range(1, 10):
        schedules.append(_create_schedule(f"option_{i}"))

    convertor.convert_activities(schedules, path, list(OutputFormat))

    for file_type in OutputFormat:
        extension = file_type.value
        folder_type_path = os.path.join(path, file_type.name.lower())
        for i in range(1, 10):
            file_name = f"option_{i}.{extension}"
            file_path = os.path.join(folder_type_path, file_name)
            assert os.path.isfile(f"{file_path}"), f"{file_name} is not exist"
            assert os.path.getsize(f"{file_path}") > 0, f"{file_name} is empty"

    shutil.rmtree(path)
