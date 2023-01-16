from enum import Enum, auto
from typing import List, Optional, Dict, Set

from constraint import Problem
from constraint import AllEqualConstraint

from data.activity import Activity
from data.course_choice import CourseChoice
from data.day import Day
from data.degree import Degree
from data.schedule import Schedule
from data.settings import Settings
from data.translation import _


class Status(Enum):
    SUCCESS = auto()
    SUCCESS_WITH_ONE_FAVORITE_LECTURER = auto()
    SUCCESS_WITHOUT_FAVORITE_LECTURERS = auto()
    FAILED = auto()


class CSP:

    def __init__(self):
        self.courses_degrees = None
        self.activities_ids_groups = None
        self.courses_choices = None
        self.consist_one_favorite_teacher = False
        self.settings = None
        self.status = None
        self.last_courses_crashed = (None, None)

    def extract_schedules_minimal_consists(self, activities: List[Activity],
                                           activities_ids_groups: Dict[str, Set[int]] = None) -> List[Schedule]:
        """
        Extract only the schedules that consist the minimal conditions
        if the activities_ids is None, the function will return only schedules that consist by their meetings
        else will return only schedules that consist by their meetings and the activities_ids
        (help for classes can enroll consist).
        """
        all_activities_names, problem = self._prepare_activities(activities)
        self.activities_ids_groups = activities_ids_groups
        self.status = Status.SUCCESS
        for name in all_activities_names:
            for other_name in all_activities_names:
                if name == other_name:
                    continue
                problem.addConstraint(self._is_consist_activity, (name, other_name))
            if activities_ids_groups:
                problem.addConstraint(self._is_consist_activities_ids_can_enroll, (name,))
            problem.addConstraint(self._is_consist_itself, (name,))

        schedules = self._extract_solutions(problem)

        if not schedules:
            self.status = Status.FAILED

        return schedules

    def extract_schedules(self, activities: List[Activity],
                          courses_choices: Optional[Dict[str, CourseChoice]] = None,
                          settings: Settings = None,
                          activities_ids_groups: Dict[str, Set[int]] = None,
                          courses_degrees: Dict[int, Set[Degree]] = None) -> List[Schedule]:

        self.settings = settings or Settings()
        self.courses_choices = courses_choices or {}
        self.activities_ids_groups = activities_ids_groups
        self.courses_degrees = courses_degrees or {}
        all_activities_names, problem = self._prepare_activities(activities)

        for name in all_activities_names:
            for other_name in all_activities_names:
                if name == other_name:
                    continue
                problem.addConstraint(self._is_consist_activity, (name, other_name))
            problem.addConstraint(self._is_consist_favorite_teachers, (name,))
            problem.addConstraint(self._is_consist_itself, (name,))
            if set(self.settings.show_only_classes_in_days) != set(Day):
                problem.addConstraint(self._is_consist_classes_in_days, (name,))
            if self.settings.show_only_courses_with_free_places:
                problem.addConstraint(self._is_consist_capacity, (name,))
            if self.settings.show_only_courses_with_the_same_actual_number:
                problem.addConstraint(self._is_consist_actual_course, (name,))
            if not self.settings.show_hertzog_and_yeshiva:
                problem.addConstraint(self._is_consist_hertzog_and_yeshiva, (name,))
            if self.settings.show_only_classes_can_enroll and self.activities_ids_groups:
                problem.addConstraint(self._is_consist_activities_ids_can_enroll, (name,))

        schedule_result = self._extract_solutions(problem)

        if not schedule_result and courses_choices and not self.consist_one_favorite_teacher:
            # If there are no schedules, try to find schedules without favorite teachers
            self.status = Status.SUCCESS_WITH_ONE_FAVORITE_LECTURER
            self.consist_one_favorite_teacher = True
            return self.extract_schedules(activities, courses_choices, self.settings)

        if not schedule_result and courses_choices and self.consist_one_favorite_teacher:
            # If there are no schedules, try to find schedules without favorite teachers
            self.status = Status.SUCCESS_WITHOUT_FAVORITE_LECTURERS
            self.consist_one_favorite_teacher = False
            return self.extract_schedules(activities, None, self.settings)

        if not schedule_result:
            self.status = Status.FAILED
        elif self.status is None:
            self.status = Status.SUCCESS

        return schedule_result

    def get_status(self):
        return self.status

    def get_last_activities_crashed(self):
        return self.last_courses_crashed

    def _is_consist_activity(self, group_one: List[Activity], group_two: List[Activity]):
        result = all(not activity.is_crash_with_activities(group_one) for activity in group_two)
        if not result:
            self.last_courses_crashed = (group_one[0].name, group_two[0].name)
        return result

    def _is_consist_capacity(self, activities: List[Activity]):
        """
        Check if the activities consist the capacity
        :param activities: list of activities
        :param activities: List[Activity]
        :return: bool
        """
        return all(activity.type.is_personal() or activity.is_have_free_places() for activity in activities)

    def _is_consist_itself(self, activities: List[Activity]):
        for i, activity in enumerate(activities):
            for j in range(i + 1, len(activities)):
                if activity.is_crash_with_activity(activities[j]):
                    return False
        return True

    def _is_consist_favorite_teachers(self, activities: List[Activity]):
        """
        Check if the activities consist the favorite teachers
        :param activities: list of activities
        :param activities: List[Activity]
        :return: bool
        """
        # If there are no courses choices, return True or if it's a personal activity return True
        if not self.courses_choices or activities[0].name not in self.courses_choices.keys():
            return True
        names_list = []
        is_consist = True
        course_choice = self.courses_choices[activities[0].name]
        for activity in activities:
            if activity.type.is_lecture():
                names_list = course_choice.available_teachers_for_lecture
            elif activity.type.is_exercise():
                names_list = course_choice.available_teachers_for_practice
            if self.consist_one_favorite_teacher:
                is_consist = is_consist and activity.lecturer_name in names_list
            else:
                is_consist = is_consist and (not names_list or activity.lecturer_name in names_list)
            if self.consist_one_favorite_teacher and is_consist:
                break

        return is_consist

    def _is_consist_actual_course(self, activities: List[Activity]):
        """
        Check if the activities consist the actual course
        :param activities: list of activities
        :param activities: List[Activity]
        :return: bool
        """
        if activities[0].type.is_personal():
            return True
        # All academic activities must have the same actual course
        return len({activity.actual_course_number for activity in activities}) == 1

    def _is_consist_hertzog_and_yeshiva(self, activities: List[Activity]):
        if activities[0].type.is_personal():
            return True
        herzog = "הרצוג"
        yeshiva = """יש"ת"""
        descriptions = [activity.description for activity in activities if activity.description]
        return not any(description for description in descriptions if herzog in description or yeshiva in description)

    def _is_consist_classes_in_days(self, activities: List[Activity]):
        if activities[0].type.is_personal():
            return True
        return all(meeting.day in self.settings.show_only_classes_in_days
                   for activity in activities for meeting in activity.meetings)

    def _is_consist_activities_ids_can_enroll(self, activities: List[Activity]):
        # Ignore personal activities
        if activities[0].type.is_personal():
            return True

        # Ignore activities not related to your degree
        parent_course_number = activities[0].parent_course_number
        if parent_course_number in self.courses_degrees:
            course_degrees = self.courses_degrees[parent_course_number]
            if self.settings.degrees - course_degrees and not {self.settings.degree} & course_degrees:
                return True

        all_activities_ids_found = all(activity.activity_id in self.activities_ids_groups for activity in activities)
        if not all_activities_ids_found:
            return False

        problem = Problem()
        for activity in activities:
            problem.addVariable(activity.activity_id, list(self.activities_ids_groups[activity.activity_id]))
            problem.addConstraint(AllEqualConstraint())
        return problem.getSolution() is not None

    def _prepare_activities(self, activities: List[Activity]):
        problem = Problem()
        activities_by_name = Activity.get_activities_by_name(activities)

        for name, activities_values in activities_by_name.items():
            flat_activities_by_type = Activity.extract_flat_activities_by_type(activities_values)
            options_for_activity = Activity.extract_all_options_of_activity(flat_activities_by_type)
            problem.addVariable(name, options_for_activity)

        all_activities_names = list(activities_by_name.keys())

        return all_activities_names, problem

    def _extract_solutions(self, problem: Problem) -> List[Schedule]:
        activities_result = []
        schedule_result = []
        option_counter = 1

        for solution in problem.getSolutions():
            activities_result.clear()
            for activities_solution in solution.values():
                activities_result += activities_solution
            name = f"{_('Option')} {option_counter}"
            file_name = f"{_('option')}_{option_counter}"
            schedule = Schedule(name, file_name, "", activities_result.copy())
            schedule_result.append(schedule)
            option_counter += 1

        return schedule_result
