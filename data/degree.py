from enum import Enum
from dataclasses import dataclass


@dataclass
class DegreeData:
    name: str
    department: int
    years: int

    def __str__(self):
        # For example COMPUTER_SCIENCE -> Computer Science
        return self.name.replace("_", " ").title()


class Degree(Enum):
    COMPUTER_SCIENCE = DegreeData("COMPUTER_SCIENCE", 20, 3)
    SOFTWARE_ENGINEERING = DegreeData("SOFTWARE_ENGINEERING", 20, 3)
    BIOINFORMATICS = DegreeData("BIOINFORMATICS", 11, 3)

    def __str__(self):
        # For example COMPUTER_SCIENCE -> Computer Science
        return str(self.value)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.name)

    def __iter__(self):
        return iter((self.name, self.value.department))

    def __eq__(self, other):
        return self.name == other.name

    @staticmethod
    def get_defaults():
        return {Degree.COMPUTER_SCIENCE, Degree.SOFTWARE_ENGINEERING}
