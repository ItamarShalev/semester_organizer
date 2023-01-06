from typing import List, Optional, Dict

from constraint import Problem

from data.activity import Activity
from data.course_choice import CourseChoice
from data.schedule import Schedule
from data.settings import Settings
from data.type import Type


class CSP:

    def __init__(self):
        self.courses_choices = None
        self.consisnt_one_favorite_teacher = False
        self.settings = None

    def _get_flat_activities_by_type(self, activities: List[Activity]) -> List[List[Activity]]:
        result = {activity_type: [] for activity_type in Type}
        for activity in activities:
            result[activity.type].append(activity)
        return [item for item in result.values() if item]

    def _get_all_options_of_activity(self, activities_list: List[List[Activity]]) -> List[List[Activity]]:
        if not activities_list:
            return [[]]
        all_options = []
        options = self._get_all_options_of_activity(activities_list[1:])
        for activity in activities_list[0]:
            for option in options:
                all_options.append([activity] + option)
        return all_options

    def _is_consist_activity(self, activity_one, activity_two):
        return all(not activity.is_crash_with_activities(activity_one) for activity in activity_two)

    def _is_consist_capacity(self, activities: List[Activity]):
        """
        Check if the activities consist the capacity
        :param activities: list of activities
        :param activities: List[Activity]
        :return: bool
        """
        return all(activity.type.is_personal() or activity.is_have_free_places() for activity in activities)

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
        is_consinst = True
        course_choice = self.courses_choices[activities[0].name]
        for activity in activities:
            if activity.type.is_lecture():
                names_list = course_choice.available_teachers_for_lecture
            elif activity.type.is_exercise():
                names_list = course_choice.available_teachers_for_practice
            if self.consisnt_one_favorite_teacher:
                is_consinst = is_consinst and activity.lecturer_name in names_list
            else:
                is_consinst = is_consinst and (not names_list or activity.lecturer_name in names_list)
            if self.consisnt_one_favorite_teacher and is_consinst:
                break

        return is_consinst

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

    def extract_schedules(self, activities: List[Activity], courses_choices: Optional[Dict[str, CourseChoice]] = None,
                          settings: Settings = None) -> List[Schedule]:
        problem = Problem()
        self.settings = settings or Settings()
        activities_result = []
        schedule_result = []
        self.courses_choices = courses_choices or {}
        option_counter = 1
        activities_by_name = Activity.get_activities_by_name(activities)

        for name, activities_values in activities_by_name.items():
            flat_activities_by_type = self._get_flat_activities_by_type(activities_values)
            options_for_activity = self._get_all_options_of_activity(flat_activities_by_type)
            problem.addVariable(name, options_for_activity)

        all_names_activities = activities_by_name.keys()

        for name in all_names_activities:
            problem.addConstraint(self._is_consist_favorite_teachers, (name,))
            problem.addConstraint(self._is_consist_classes_in_days, (name,))
            if self.settings.show_only_courses_with_free_places:
                problem.addConstraint(self._is_consist_capacity, (name,))
            if self.settings.show_only_courses_with_the_same_actual_number:
                problem.addConstraint(self._is_consist_actual_course, (name,))
            if not self.settings.show_hertzog_and_yeshiva:
                problem.addConstraint(self._is_consist_hertzog_and_yeshiva, (name,))
            for other_name in all_names_activities:
                if name == other_name:
                    continue
                problem.addConstraint(self._is_consist_activity, (name, other_name))

        for solution in problem.getSolutions():
            activities_result.clear()
            for activities_solution in solution.values():
                activities_result += activities_solution
            schedule = Schedule(f"Option {option_counter}", f"option_{option_counter}", "", activities_result.copy())
            schedule_result.append(schedule)
            option_counter += 1

        if not schedule_result and courses_choices and not self.consisnt_one_favorite_teacher:
            # If there are no schedules, try to find schedules without favorite teachers
            self.consisnt_one_favorite_teacher = True
            return self.extract_schedules(activities, courses_choices, self.settings)

        if not schedule_result and courses_choices and self.consisnt_one_favorite_teacher:
            # If there are no schedules, try to find schedules without favorite teachers
            self.consisnt_one_favorite_teacher = False
            return self.extract_schedules(activities, None, self.settings)

        return schedule_result
