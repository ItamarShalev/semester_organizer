from enum import Enum


class OutputFormat(Enum):
    CSV = "csv"
    EXCEL = "xlsx"
    IMAGE = "png"

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)
