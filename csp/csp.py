from typing import List, Dict

from constraint import Problem

from data.activity import Activity
from data.schedule import Schedule
from data.type import Type


def _get_flat_activities_by_type(activities: List[Activity]) -> List[List[Activity]]:
    result = {activity_type: [] for activity_type in Type}
    for activity in activities:
        result[activity.type].append(activity)
    return [item for item in result.values() if item]


def _get_activities_by_name(activities: List[Activity]) -> Dict[str, List[Activity]]:
    result = {}
    for activity in activities:
        if activity.name not in result:
            result[activity.name] = [activity]
        else:
            result[activity.name].append(activity)
    return result


def get_all_options_of_activity(activities_list: List[List[Activity]]) -> List[List[Activity]]:
    if not activities_list:
        return [[]]
    all_options = []
    options = get_all_options_of_activity(activities_list[1:])
    for activity in activities_list[0]:
        for option in options:
            all_options.append([activity] + option)
    return all_options


def is_consist(activity_one, activity_two):
    return all(not activity.is_crash_with_activities(activity_one) for activity in activity_two)


def extract_schedules(activities: List[Activity]) -> List[Schedule]:
    problem = Problem()
    activities_result = []
    schedule_result = []
    option_counter = 1
    activities_by_name = _get_activities_by_name(activities)

    for name, activities_values in activities_by_name.items():
        flat_activities_by_type = _get_flat_activities_by_type(activities_values)
        options_for_activity = get_all_options_of_activity(flat_activities_by_type)
        problem.addVariable(name, options_for_activity)

    all_names_activities = activities_by_name.keys()

    for name in all_names_activities:
        for other_name in all_names_activities:
            if name == other_name:
                continue
            problem.addConstraint(is_consist, (name, other_name))

    for solution in problem.getSolutions():
        activities_result.clear()
        for activities_solution in solution.values():
            activities_result += activities_solution
        schedule = Schedule(f"Option {option_counter}", f"option_{option_counter}", "", activities_result.copy())
        schedule_result.append(schedule)
        option_counter += 1

    return schedule_result
