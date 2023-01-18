from datetime import datetime
from typing import List, Set
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from data.day import Day
from data.degree import Degree
from data.output_format import OutputFormat
from data.semester import Semester
from data.language import Language
import utils


@dataclass_json
@dataclass
class Settings:
    attendance_required_all_courses: bool = True
    campus_name: str = ""
    year: int = utils.get_current_hebrew_year()
    semester: Semester = utils.get_current_semester()
    _degree: str = "COMPUTER_SCIENCE"
    _degrees: List[str] = field(default_factory=lambda: [degree.name for degree in Degree.get_defaults()])
    show_hertzog_and_yeshiva: bool = False
    show_only_courses_with_free_places: bool = False
    show_only_courses_active_classes: bool = True
    show_only_courses_with_the_same_actual_number: bool = True
    dont_show_courses_already_done: bool = True
    show_only_classes_in_days: List[Day] = field(default_factory=lambda: list(Day))
    output_formats: List[OutputFormat] = field(default_factory=lambda: list(OutputFormat))
    show_only_classes_can_enroll: bool = True
    show_only_courses_with_prerequisite_done: bool = False
    language: Language = Language.HEBREW
    force_update_data: bool = True
    semester_start_date = datetime(2023, 2, 19)
    semester_end_date = datetime(2023, 7, 27)

    @property
    def degrees(self) -> Set[Degree]:
        return {Degree[degree] for degree in self._degrees}

    @degrees.setter
    def degrees(self, degrees: Set[Degree]):
        self._degrees = [degree.name for degree in degrees]

    @property
    def degree(self) -> Degree:
        return Degree[self._degree]

    @degree.setter
    def degree(self, degree: Degree):
        self._degree = degree.name
