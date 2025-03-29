from enum import IntEnum, auto


class Day(IntEnum):
    SUNDAY = auto()
    MONDAY = auto()
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return str(self)
