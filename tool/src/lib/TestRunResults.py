class TestRunResults:
    def __init__(self, extracted_outputs=None, parse_errors=None, fit_errors=None,distributions=None,
                 dist_names=None, sd_ppfs=None, avg_ppfs=None, convergences=None, estimated_ppfs=None, codes=None):
        self.extracted_outputs = extracted_outputs
        self.parse_errors = parse_errors
        self.fit_errors = fit_errors
        self.distributions=distributions
        self.dist_names = dist_names
        self.avg_ppfs = avg_ppfs
        self.sd_ppfs = sd_ppfs
        self.convergences = convergences
        self.estimated_ppfs = estimated_ppfs
        self.codes = codes