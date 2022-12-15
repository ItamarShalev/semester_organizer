from enum import IntEnum, auto


class Type(IntEnum):
    PERSONAL = auto()
    LECTURE = auto()
    LAB = auto()
    PRACTICE = auto()
    SEMINAR = auto()

    def is_lecture(self):
        return self in [Type.LECTURE, Type.SEMINAR]

    def is_exercise(self):
        return self in [Type.LAB, Type.PRACTICE]

    def is_personal(self):
        return self == Type.PERSONAL

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return str(self)
