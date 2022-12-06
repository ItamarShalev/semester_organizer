from typing import List
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from data.output_format import OutputFormat
from data.semester import Semester
import utils


@dataclass_json
@dataclass
class Settings:
    attendance_required_all_courses: bool = True
    campus_name: str = utils.get_campus_name_test()
    year: int = utils.get_current_hebrew_year()
    semester: Semester = utils.get_current_semester()
    show_hertzog: bool = False
    show_only_courses_with_free_places: bool = True
    show_only_courses_active_classes: bool = True
    output_formats: List[OutputFormat] = field(default_factory=lambda: list(OutputFormat))
    force_update_data: bool = True