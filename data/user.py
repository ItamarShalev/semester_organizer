from dataclasses import dataclass


@dataclass
class User:
    username: str = None
    password: str = None

    def __bool__(self):
        return bool(self.username and self.password)
