import csv
import os
import shutil
from typing import List, cast

from data.academic_activity import AcademicActivity
from data.output_format import OutputFormat
from data.schedule import Schedule
from data.type import Type


class Convertor:


    def convert_activities_to_csv(self, schedules: List[Schedule], folder_location: str):
        headers = ["activity type", "day", "start time", "end time", "course name", "course location"]
        rows = []
        shutil.rmtree(folder_location, ignore_errors=True)
        os.makedirs(folder_location)
        rows.append(headers)
        for schedule in schedules:
            for activity in schedule.activities:
                for meeting in activity.meetings:
                    activity_type = activity.type.name
                    activity_day = meeting.day.name
                    total_time = str(meeting)
                    if activity.type is not Type.PERSONAL:
                        academic_activity = cast(AcademicActivity, activity)
                        course_name = academic_activity.name
                        course_location = academic_activity.location
                        course_number = academic_activity.course_number
                        rows = [activity_type, activity_day, total_time, course_name, course_location, course_number]
                        rows.append(rows)
                    else:
                        # Three empty cells since it's not relevant to personal activity
                        rows = [activity_type, activity_day, total_time, None, None, None]
                        rows.append(rows)

            file_location = os.path.join(folder_location, f"{schedule.file_name}.{OutputFormat.CSV.value}")
            with open(file_location, 'w') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
    def convert_activities(self, schedules: List[Schedule], folder_location: str, formats: List[OutputFormat]):
        """
        The function will save each schedule in the folder location in the wanted formats.
        :param schedules: the schedules
        :param folder_location: the folder location
        :param formats: the formats
        :return:
        """

        if OutputFormat.CSV in formats:
            if len(formats) == 1:
                csv_location = folder_location
            else:
                csv_location = os.path.join(folder_location, OutputFormat.CSV.name.lower())
            self.convert_activities_to_csv(schedules, csv_location)
