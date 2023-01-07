import csv
import os
import shutil
from typing import List, cast

import utils
from data.academic_activity import AcademicActivity
from data.output_format import OutputFormat
from data.schedule import Schedule
from data.type import Type
from data.translation import _


class Convertor:

    def convert_activities_to_csv(self, schedules: List[Schedule], folder_location: str):
        headers = [
            _("activity type"),
            _("day"),
            _("start time"),
            _("end time"),
            _("course name"),
            _("course location"),
            _("activity id"),
            _("lecturer name"),
            _("course id")
        ]
        rows = []
        shutil.rmtree(folder_location, ignore_errors=True)
        os.makedirs(folder_location)
        for schedule in schedules:
            rows.clear()
            rows.append(headers)
            for activity in schedule.activities:
                for meeting in activity.meetings:
                    activity_type = _(str(activity.type))
                    activity_day = _(str(meeting.day))
                    start_time = meeting.get_string_start_time()
                    end_time = meeting.get_string_end_time()
                    if activity.type is not Type.PERSONAL:
                        academic_activity = cast(AcademicActivity, activity)
                        course_name = academic_activity.name
                        course_location = academic_activity.location
                        course_number = academic_activity.course_number
                        new_row = [
                            activity_type,
                            activity_day,
                            start_time,
                            end_time,
                            course_name,
                            course_location,
                            academic_activity.activity_id,
                            academic_activity.lecturer_name,
                            course_number
                        ]
                        rows.append(new_row)
                    else:
                        # Five empty cells since it's not relevant to personal activity
                        new_row = [
                            activity_type,
                            activity_day,
                            start_time,
                            end_time]
                        new_row += [None] * (len(headers) - len(new_row))
                        rows.append(new_row)

            file_location = os.path.join(folder_location, f"{schedule.file_name}.{OutputFormat.CSV.value}")
            with open(file_location, 'w', encoding=utils.ENCODING, newline='') as file:
                writer = csv.writer(file, delimiter=',')
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
