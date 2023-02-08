class Config:
    def __init__(self):
        self.DEFAULT_ITERATIONS = 4
        self.SUBSEQUENT_ITERATIONS = 96
        self.MAX_ITERATIONS = 100
        self.THREAD_COUNT = 24

        self.PROBABILITY_OF_FAILURE = 0.01
        # enables probability update is the original test failure probability is above min threshold
        self.BOUNDS_DELTA = 1
        self.USE_BOXCOX = False

        self.BOUNDS_MAX_PERCENTILE = 0.9999
        self.MIN_TAIL_VALUES = 50

