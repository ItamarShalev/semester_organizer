import re


# pylint: disable=protected-access
class CaseInsensitiveDict(dict):
    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, str) else key

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super().__getitem__(self.__class__._k(key))

    def __setitem__(self, key, value):
        super().__setitem__(self.__class__._k(key), value)

    def __delitem__(self, key):
        return super().__delitem__(self.__class__._k(key))

    def __contains__(self, key):
        return super().__contains__(self.__class__._k(key))

    def pop(self, key, *args, **kwargs):
        return super().pop(self.__class__._k(key), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super().get(self.__class__._k(key), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super().setdefault(self.__class__._k(key), *args, **kwargs)

    def update(self, E=None, **F):
        E = E or {}
        super().update(self.__class__(E))
        super().update(self.__class__(**F))

    def _convert_keys(self):
        for key in list(self.keys()):
            value = super().pop(key)
            self[key] = value


class TextCaseInsensitiveDict(CaseInsensitiveDict):
    @classmethod
    def _k(cls, key):
        if isinstance(key, str):
            key = key.lower()
            # Remove all text sign from the start and the end of the text
            key = re.sub(r'[,.:;()!? \n\r\t=-]*$', '', key)
            key = re.sub(r'^[,.:;()!? \n\r\t=-]*', '', key)
            return key.lower().strip()
        return key
