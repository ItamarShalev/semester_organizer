from typing import List

from data.output_format import OutputFormat
from data.schedule import Schedule as schedule


class Convertor:

    def convert_activities(self, schedules: List[schedule], folder_location: str, formats: List[OutputFormat]):
        """
        The function will save each schedule in the folder location in the wanted formats.
        :param schedules: the schedules
        :param folder_location: the folder location
        :param formats: the formats
        :return:
        """
        raise NotImplementedError("Not implemented yet.")
