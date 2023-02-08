import numpy as np


class DeltaDist:
    def __init__(self, vals):
        self.val = np.max(vals)
        self.b = self.val
        self.a = self.val

    def cdf(self, samples):
        if isinstance(samples, (list, np.ndarray)):
            return [1.0 if self.val <= k else 0.0 for k in samples]
        else:
            return 1.0 if self.val <= samples else 0.0

    def ppf(self, prob):
        return self.val