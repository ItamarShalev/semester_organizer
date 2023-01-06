from typing import List
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from data.day import Day
from data.output_format import OutputFormat
from data.semester import Semester
from data.language import Language
import utils


@dataclass_json
@dataclass
class Settings:
    attendance_required_all_courses: bool = True
    campus_name: str = utils.get_campus_name_test()
    year: int = utils.get_current_hebrew_year()
    semester: Semester = utils.get_current_semester()
    show_hertzog_and_yeshiva: bool = False
    show_only_courses_with_free_places: bool = False
    show_only_courses_active_classes: bool = True
    show_only_courses_with_the_same_actual_number: bool = True
    show_only_classes_in_days: List[Day] = field(default_factory=lambda: list(Day))
    show_only_classes_can_register: bool = False
    output_formats: List[OutputFormat] = field(default_factory=lambda: list(OutputFormat))
    language: Language = Language.HEBREW
    force_update_data: bool = True
