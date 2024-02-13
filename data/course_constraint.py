import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from collections import OrderedDict
from copy import deepcopy


@dataclass(order=True)
class PrerequisiteCourse:
    id: int = field(compare=True)
    course_number: int
    name: str
    can_be_taken_in_parallel: bool = False

    def to_json(self, include_can_be_taken_in_parallel: bool) -> Dict:
        result = {
            "id": self.id,
            "course_number": self.course_number,
            "name": self.name,
        }
        if include_can_be_taken_in_parallel:
            result["can_be_taken_in_parallel"] = self.can_be_taken_in_parallel
        return result

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, PrerequisiteCourse) and self.id == other.id


@dataclass(order=True)
class ConstraintCourseData:
    id: int = field(hash=True, compare=True)
    course_number: int
    name: str
    aliases: List[str] = field(default_factory=list)
    blocked_by: List[PrerequisiteCourse] = field(default_factory=list)
    blocks: List[PrerequisiteCourse] = field(default_factory=list)

    def to_json(self, include_blocked_by: bool, include_blocks: bool, include_can_be_taken_in_parallel: bool) -> Dict:
        result = {
            "id": self.id,
            "name": self.name,
            "course_number": self.course_number,
            "aliases": self.aliases
        }
        if include_blocked_by:
            result["blocked_by"] = [course.to_json(include_can_be_taken_in_parallel) for course in self.blocked_by]
        if include_blocks:
            result["blocks"] = [course.to_json(include_can_be_taken_in_parallel) for course in self.blocks]
        return result

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, ConstraintCourseData) and self.id == other.id


class CourseConstraint:

    def __init__(self):
        self.name = None
        self.version = None
        self.comment = None

    def export(self, all_courses: List[ConstraintCourseData], include_blocked_by: bool, include_blocks: bool,
               file_path: Path, include_can_be_taken_in_parallel: bool = False):
        all_courses.sort(key=lambda course: course.id)
        assert self.version, "ERROR: Version json file unknown."
        assert self.comment is not None, "ERROR: Comment json file unknown"
        include_parallel = include_can_be_taken_in_parallel
        json_data = {
            "version": self.version,
            "_comment": self.comment,
            "courses": [course.to_json(include_blocked_by, include_blocks, include_parallel) for course in all_courses]
        }
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, sort_keys=False, indent=4)

    def extract_courses_data(self, file_path: Path) -> Dict[int, ConstraintCourseData]:
        assert file_path.exists(), "File does not exist"
        all_courses_ids = set()
        all_ids = set()
        courses = OrderedDict()

        def get_pre_request_courses_list(json_object: Dict, key: str) -> List[PrerequisiteCourse]:
            prerequisite_courses = []
            for prerequisite_json_object in json_object.get(key, []):
                pre_object_id = prerequisite_json_object["id"]
                if pre_object_id not in courses:
                    raise RuntimeError(f"ERROR: The object course id {pre_object_id} "
                                       f"should be above than course id: {json_object['id']}")
                pre_course_number = courses[pre_object_id].course_number
                name = courses[pre_object_id].name
                can_be_taken_in_parallel = prerequisite_json_object.get("can_be_taken_in_parallel", False)
                pre_object = PrerequisiteCourse(pre_object_id, pre_course_number, name, can_be_taken_in_parallel)
                prerequisite_courses.append(pre_object)
            return prerequisite_courses

        with open(file_path, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
        self.version = json_data["version"]
        self.comment = json_data["_comment"]
        for course_data in json_data["courses"]:
            if course_data.get("deprecated", False):
                continue
            object_id = course_data["id"]
            course_number = course_data["course_number"]
            assert object_id > 0, "ERROR: Object id must be positive non zero, edit the 'id' key in the file."
            assert course_number > 0, "ERROR: Course id must be positive, edit the 'course_number' key in the file."

            object_data = ConstraintCourseData(
                id=object_id,
                course_number=course_number,
                name=course_data["name"],
                aliases=course_data["aliases"] + [course_data["name"]],
                blocked_by=get_pre_request_courses_list(course_data, "blocked_by"),
                blocks=get_pre_request_courses_list(course_data, "blocks"),
            )
            assert object_id not in all_ids, f"ERROR: Found multiple id {object_id}, should remove it."
            assert course_number not in all_courses_ids, \
                f"ERROR: Found multiple course id {course_number}, should remove it."
            all_ids.add(object_id)
            all_courses_ids.add(course_number)
            courses[object_id] = object_data
        return courses

    def get_extended_blocked_by_courses(self, all_courses: Dict[int, ConstraintCourseData]) \
            -> Dict[int, ConstraintCourseData]:
        result_courses = deepcopy(all_courses)
        there_was_update = True
        while there_was_update:
            there_was_update = False
            for course in result_courses.values():
                old_pre_courses = course.blocked_by
                new_pre_courses = set(old_pre_courses)
                for pre_course_data in old_pre_courses:
                    pre_course_object = result_courses[pre_course_data.id]
                    new_pre_courses.update(pre_course_object.blocked_by)
                there_was_update = there_was_update or len(old_pre_courses) != len(new_pre_courses)
                course.blocked_by = list(sorted(new_pre_courses, key=lambda data: data.id))
        return result_courses

    def get_extended_blocks_courses(self, all_courses: Dict) -> Dict[int, ConstraintCourseData]:
        result_courses = deepcopy(all_courses)
        found_in_courses = set()
        for object_id, course in result_courses.items():
            found_in_courses.clear()
            for _object_id, other_course in result_courses.items():
                if object_id in {pre_course.id for pre_course in other_course.blocked_by}:
                    pre_course_obj = PrerequisiteCourse(other_course.id, other_course.course_number, other_course.name)
                    found_in_courses.add(pre_course_obj)
            course.blocks = list(sorted(found_in_courses, key=lambda data: data.id))
        return result_courses
