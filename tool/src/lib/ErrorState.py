from enum import Enum


class ErrorState(Enum):
    NOT_ENOUGH_TAIL_VALUES = 1
    NOT_EXP = 2
    NORMALITY_TEST_FAILED = 3

