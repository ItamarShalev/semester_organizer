from enum import Enum, auto


class Semester(Enum):
    "Semester אלול"
    SUMMER = auto()
    "Semester א"
    FALL = auto()
    "Semester ב"
    SPRING = auto()
    "Semester שנתי"
    ANNUAL = auto()

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter((self.value, self.name.lower()))
