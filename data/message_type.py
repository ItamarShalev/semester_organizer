from enum import Enum, auto


class MessageType(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return str(self)
