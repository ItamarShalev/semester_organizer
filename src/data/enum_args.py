from enum import Enum
from typing import Union


class EnumArgs(Enum):

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

    @classmethod
    def from_str(cls, name: Union[int, str]):
        try:
            if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
                return cls(int(name))
            return cls[str(name).upper()]
        except KeyError:
            raise ValueError(f"Enum: {type(cls)} Invalid value: {name}") from None
