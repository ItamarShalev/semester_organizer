from enum import auto
from data.enum_args import EnumArgs


class Flow(EnumArgs):
    GUI = auto()
    CONSOLE = auto()
    UPDATE_DATABASE = auto()
    UPDATE_SERVER_DATABASE = auto()
    UPDATE_GENERATED_JSON_DATA = auto()
    RELEASE = auto()
    LINTER = auto()
