from enum import Enum


class TailType(Enum):
    LIGHT = 1
    EXP = 2
    HEAVY = 3

    def __str__(self):
        return '%s' % self.name
