from abc import abstractmethod


class DnfCls:

    def __init__(self):
        self._weapon_cdr = 1
        self._talent_cdr = 1

    @abstractmethod
    def