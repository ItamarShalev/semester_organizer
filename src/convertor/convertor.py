import csv
import functools
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, cast
import warnings
from multiprocessing import Pool
from dataclasses import dataclass

import pandas as pd
import dataframe_image as dfi

from src import utils
from src.data.academic_activity import AcademicActivity
from src.data.activity import Activity
from src.data.language import Language
from src.data.meeting import Meeting
from src.data.output_format import OutputFormat
from src.data.schedule import Schedule
from src.data.type import Type
from src.data.translation import _
from src.data.day import Day


@functools.total_ordering
class MeetingClass:
    def __init__(self, meeting: Meeting, activity: Activity):
        self.meeting = meeting
        self.activity = activity

    def __str__(self):
        activity = self.activity
        activity_name = activity.name
        activity_type = activity.type
        activity_time = str(self.meeting)
        if activity_type is not Type.PERSONAL:
            academic_activity = cast(AcademicActivity, activity)
            lecturer_name = academic_activity.lecturer_name
            course_location = academic_activity.location
            lecturer_type = [_(str(activity_type)), lecturer_name]
            activity_id = academic_activity.activity_id
            if Language.get_current() is Language.HEBREW:
                lecturer_type.reverse()
            result = f"{activity_name}\n"
            result += " - ".join(lecturer_type)
            result += f"\n{activity_time}\n{activity_id}\n{course_location}"
        else:
            result = f"{activity_name}\n{activity_time}"
        return result

    def __lt__(self, other):
        return self.meeting < other.meeting


@dataclass
class Color:
    strong: str
    weak: str


class Convertor:

    # https://www.w3schools.com/colors/colors_picker.asp will help to choose the right color
    # Every tuple contains the strong and weak variety of color

    # Gray
    PERSONAL_COLOR = "#bdc3c7"

    COLORS = [
        # Light blue
        Color("#4d94ff", "#80b3ff"),
        # Light green
        Color("#79d279", "#9fdf9f"),
        # Purple
        Color("#b366ff", "#cc99ff"),
        # Red
        Color("#ff8080", "#ffb3b3"),
        # Light yellow
        Color("#f9e79f", "#fcf3cf"),
        # Weak light blue
        Color("#99e6e6", "#d6f5f5"),
        # Shiny light green
        Color("#80ff80", "#b3ffb3"),
        # Blue
        Color("#005ce6", "#1a75ff"),
        # Green
        Color("#339933", "#40bf40"),
        # Yellow
        Color("#cc9900", "#ffbf00"),
    ]

    def __init__(self):
        warnings.simplefilter(action='ignore', category=FutureWarning)
        self._activities_colors = {}
        self._loger = utils.get_logging()

    def _init_activities_color_indexes(self, activities: List[Activity]):
        all_names = {activity.name for activity in activities if not activity.type.is_personal()}
        if all(name in self._activities_colors for name in all_names):
            return
        all_names = sorted(list(all_names))
        self._activities_colors = {}
        for index, name in enumerate(all_names):
            self._activities_colors[name] = Convertor.COLORS[index % len(Convertor.COLORS)]

    def _coloring(self, meeting_class):
        # White
        color = "#ffffff"
        if meeting_class:
            activity_type = meeting_class.activity.type
            activity_name = meeting_class.activity.name
            if activity_type.is_personal():
                color = Convertor.PERSONAL_COLOR
            elif activity_type.is_lecture():
                color = self._activities_colors[activity_name].strong
            elif activity_type.is_exercise():
                color = self._activities_colors[activity_name].weak
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
            "activity_id"
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
        df_styled.map(self._coloring)
        df_styled.set_properties(**{'border': '1px black solid',
                                    'text-align': 'center',
                                    'white-space': 'pre-wrap'})
        table_style = {"selector": 'th', "props": [('text-align', 'center')]}
        df_styled.set_table_styles([table_style])
        df_styled.hide(axis="index")

        return df_styled

    def convert_activities_to_excel(self, schedules: List[Schedule], folder_location: Path):
        shutil.rmtree(folder_location, ignore_errors=True)
        folder_location.mkdir(parents=True)
        self._init_activities_color_indexes(schedules[0].activities)
        for schedule in schedules:
            data_frame = self._create_schedule_table(schedule)
            file_location = folder_location / f"{schedule.file_name}.{OutputFormat.EXCEL.value}"
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

    def convert_activities_to_png(self, schedules: List[Schedule], folder_path: Path):
        shutil.rmtree(folder_path, ignore_errors=True)
        folder_path.mkdir(parents=True)
        self._init_activities_color_indexes(schedules[0].activities)
        use_multiprocessing = sys.version_info <= (3, 12) or os.environ.get("multiprocessing", "F").lower() == "true"
        self._loger.info(f"Use multiprocessing: {use_multiprocessing}")

        if use_multiprocessing:
            with Pool() as pool:
                pool.starmap(self.process_schedule, [(schedule, folder_path, self) for schedule in schedules])
        else:
            with ThreadPoolExecutor() as executor:
                path = folder_path
                futures = [executor.submit(self.process_schedule, schedule, path, self) for schedule in schedules]
                for future in futures:
                    # Wait for all tasks to complete
                    future.result()

    @staticmethod
    def process_schedule(schedule, folder_location, convertor):
        # pylint: disable=protected-access
        df = convertor._create_schedule_table(schedule)
        full_file_path = folder_location / f"{schedule.file_name}.{OutputFormat.IMAGE.value}"
        dfi.export(df, str(full_file_path), table_conversion="chrome")

    def convert_activities_to_csv(self, schedules: List[Schedule], folder_location: Path):
        shutil.rmtree(folder_location, ignore_errors=True)
        folder_location.mkdir(parents=True)
        self._init_activities_color_indexes(schedules[0].activities)
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
        for schedule in schedules:
            rows.clear()
            rows.append(headers.copy())
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

            if Language.get_current() is Language.HEBREW:
                for row in rows:
                    row.reverse()

            file_location = folder_location / f"{schedule.file_name}.{OutputFormat.CSV.value}"
            with open(file_location, 'w', encoding=utils.ENCODING, newline='') as file:
                writer = csv.writer(file, delimiter=',')
                writer.writerows(rows)

    def convert_activities(self, schedules: List[Schedule], folder_location: Path, formats: List[OutputFormat]):
        """
        The function will save each schedule in the folder location in the wanted formats.
        :param schedules: the schedules
        :param folder_location: the folder location
        :param formats: the formats
        :return:
        """
        if not schedules:
            return

        if OutputFormat.CSV in formats:
            if len(formats) == 1:
                csv_location = folder_location
            else:
                csv_location = folder_location / OutputFormat.CSV.name.lower()
            self.convert_activities_to_csv(schedules, csv_location)

        if OutputFormat.EXCEL in formats:
            if len(formats) == 1:
                excel_location = folder_location
            else:
                excel_location = folder_location / OutputFormat.EXCEL.name.lower()
            self.convert_activities_to_excel(schedules, excel_location)

        if OutputFormat.IMAGE in formats:
            if len(formats) == 1:
                png_location = folder_location
            else:
                png_location = folder_location / OutputFormat.IMAGE.name.lower()
            self.convert_activities_to_png(schedules, png_location)
