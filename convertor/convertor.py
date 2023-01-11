import csv
import functools
import os
import shutil
from typing import List, cast
import warnings
import pandas as pd
import utils
from data.academic_activity import AcademicActivity
from data.activity import Activity
from data.language import Language
from data.meeting import Meeting
from data.output_format import OutputFormat
from data.schedule import Schedule
from data.type import Type
from data.translation import _
from data.day import Day


@functools.total_ordering
class MeetingClass:
    def __init__(self, meeting: Meeting, activity: Activity):
        self.meeting = meeting
        self.activity = activity

    def __str__(self):
        if self.activity:
            activity = self.activity
            activity_name = activity.name
            activity_type = activity.type
            activity_time = str(self.meeting)
            if activity_type is not Type.PERSONAL:
                academic_activity = cast(AcademicActivity, activity)
                lecturer_name = academic_activity.lecturer_name
                course_location = academic_activity.location
                lecturer_type = [_(str(activity_type)), lecturer_name]
                if Language.get_current() is Language.HEBREW:
                    lecturer_type.reverse()
                result = f"{activity_name}\n"
                result += " - ".join(lecturer_type)
                result += f"\n{activity_time}\n{course_location}"
            else:
                result = f"{activity_name}\n{activity_time}"
            return result
        return str(self.meeting)

    def color(self):
        activity_type = self.activity.type
        color = "#000000"
        if activity_type.is_personal():
            color = '#3333ff'
        elif activity_type.is_lecture():
            color = '#00ffff'
        elif activity_type is Type.PRACTICE:
            color = '#00b3b3'
        elif activity_type is Type.LAB:
            color = '#4d94ff'
        return color

    def __lt__(self, other):
        return self.meeting < other.meeting

    def __eq__(self, other):
        return self.meeting == self.meeting


class Convertor:

    def __init__(self):
        warnings.simplefilter(action='ignore', category=FutureWarning)

    def _coloring(self, meeting_class):
        # White
        color = "#ffffff"
        color = meeting_class.color() if meeting_class else color
        return f'background-color: {color}'

    def _create_schedule_table(self, schedule):
        columns = [_(str(day)) for day in Day]
        all_days = list(Day)
        if Language.get_current() is Language.HEBREW:
            columns.reverse()
            all_days.reverse()
        week_table = {day.value: [] for day in all_days}

        _headers = [
            "activity_name",
            "activity_type",
            "lecturer_name",
            "course_location",
            "activity_id",
            "course_id"
        ]

        for activity in schedule.activities:
            for meeting in activity.meetings:
                day_index = meeting.day.value
                week_table[day_index].append(MeetingClass(meeting, activity))

        max_length = max(len(day_meetings) for day_meetings in week_table.values())
        for day_meetings in week_table.values():
            day_meetings.sort()
            day_meetings += [None] * (max_length - len(day_meetings))
        table_set = {_(str(day)): week_table[day.value] for day in all_days}

        df = pd.DataFrame(table_set, columns=columns)

        df.fillna('', inplace=True)

        df_styled = df.style
        df_styled.applymap(self._coloring)
        df_styled.set_properties(**{'border': '1px black solid',
                                    'text-align': 'center',
                                    'white-space': 'pre-wrap'})
        df_styled.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
        df_styled.hide(axis="index")

        return df_styled

    def convert_activities_to_excel(self, schedules: List[Schedule], folder_location: str):
        shutil.rmtree(folder_location, ignore_errors=True)
        os.makedirs(folder_location, exist_ok=True)
        for schedule in schedules:
            data_frame = self._create_schedule_table(schedule)
            file_location = os.path.join(folder_location, f"{schedule.file_name}.{OutputFormat.EXCEL.value}")
            # pylint: disable=abstract-class-instantiated
            writer = pd.ExcelWriter(file_location)
            data_frame.to_excel(writer, index=False, encoding=utils.ENCODING, sheet_name=schedule.name,
                                engine='xlsxwriter')
            for column in data_frame.columns:
                column_length = max(data_frame.data[column].astype(str).map(len).max(), len(column))
                column_length = min(column_length, 25)
                col_idx = data_frame.columns.get_loc(column)
                writer.sheets[schedule.name].set_column(col_idx, col_idx, column_length)

            writer.close()

    def convert_activities_to_csv(self, schedules: List[Schedule], folder_location: str):
        headers = [
            _("activity name"),
            _("activity type"),
            _("day"),
            _("start time"),
            _("end time"),
            _("lecturer name"),
            _("course location"),
            _("activity id"),
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
                            course_name,
                            activity_type,
                            activity_day,
                            start_time,
                            end_time,
                            academic_activity.lecturer_name,
                            course_location,
                            academic_activity.activity_id,
                            course_number
                        ]
                        rows.append(new_row)
                    else:
                        # Five empty cells since it's not relevant to personal activity
                        new_row = [
                            activity.name,
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

        if OutputFormat.EXCEL in formats:
            if len(formats) == 1:
                excel_location = folder_location
            else:
                excel_location = os.path.join(folder_location, OutputFormat.EXCEL.name.lower())
            self.convert_activities_to_excel(schedules, excel_location)
