from enum import Enum


class Degree(Enum):
    # name, department
    COMPUTER_SCIENCE = 20
    SOFTWARE_ENGINEERING = 20

    def __str__(self):
        # For example COMPUTER_SCIENCE -> Computer Science
        return self.name.replace("_", " ").title()

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))

    @staticmethod
    def get_defaults():
        return {Degree.COMPUTER_SCIENCE, Degree.SOFTWARE_ENGINEERING}
