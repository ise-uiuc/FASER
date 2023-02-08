import ast
from scipy.stats import norm
import numpy as np
import warnings

from src.lib.TailType import TailType

warnings.filterwarnings('ignore')

from src import Util
from src.lib.AssertSpec import AssertSpec
from src.lib.AssertType import AssertType
from statsmodels.distributions.empirical_distribution import ECDF
import scipy.stats.distributions as dist
import scipy.stats as st
import pandas as pd
import traceback as tb

from src.lib.DeltaDist import DeltaDist

default_threshold = {AssertType.ASSERT_APPROX_EQUAL: {'significant': 10 ** -7},
                     AssertType.ASSERT_ALMOST_EQUAL: {'decimal': 1.5 * 10 ** (-7)},
                     AssertType.ASSERT_ALLCLOSE: {'rtol': 10 ** (-7), 'atol': 0 },
                     AssertType.ASSERT_ARRAY_ALMOST_EQUAL: {'decimal': 1.5 * 10 ** (-6)},
                     AssertType.TF_ASSERT_ALL_CLOSE: {'rtol': 1e-6, 'atol': 1e-6},
                     AssertType.PYRO_ASSERT_EQUAL: {'prec': 1e-5},
                     AssertType.ASSERTALMOSTEQUAL : {'places': 10 ** (-7), 'delta': None}
                     }





class CompareDistribution:
    def __init__(self, samplesfile, actual, expected, assert_spec: AssertSpec, dist_type=norm, logger=None):
        self.sample_file = samplesfile
        self.spec = assert_spec        
        self.actual = actual
        self.expected = expected
        self.logger = logger
        self.enable_per_dim_comparison = True

        self.dist_type = dist_type
        self.minimum_variance_threshold = 1e-20
        if samplesfile is not None:
            self.parse()
        else:
            try:
                self.parse_arguments(
                    self.spec.assert_string[self.spec.assert_string.index("(") + 1:-1].strip().split(","))
            except:
                pass

    def parse_arguments(self, args):
        for arg in args:
            if 'decimal' in arg or 'significant' in arg:
                self.logger.logo("updating...")
                d = int(arg.split('=')[1].strip())
                if self.spec.assert_type == AssertType.ASSERT_APPROX_EQUAL:
                    default_threshold[self.spec.assert_type][arg.split(
                        "=")[0].strip()] = 10 ** -(d - 1)
                elif self.spec.assert_type == AssertType.ASSERT_ALMOST_EQUAL:
                    default_threshold[self.spec.assert_type][arg.split(
                        "=")[0].strip()] = 1.5 * 10 ** (-d)
                elif self.spec.assert_type == AssertType.ASSERT_ARRAY_ALMOST_EQUAL:
                    default_threshold[self.spec.assert_type][arg.split(
                        "=")[0].strip()] = 1.5 * 10 ** (-d)
                else:
                    self.logger.logo("unrecognized assert %s " %
                                     self.spec.assert_string)
                    raise RuntimeError
            elif 'rtol' in arg:
                self.logger.logo("updating...")
                rtol = float(arg.split('=')[1].strip())
                if self.spec.assert_type == AssertType.ASSERT_ALLCLOSE:
                    default_threshold[self.spec.assert_type]['rtol'] = rtol
                elif self.spec.assert_type == AssertType.TF_ASSERT_ALL_CLOSE:
                    default_threshold[self.spec.assert_type]['rtol'] = rtol
                else:
                    self.logger.logo("unrecognized assert %s " %
                                     self.spec.assert_string)
                    raise RuntimeError
            elif 'atol' in arg:
                self.logger.logo('updating...')
                atol = float(arg.split('=')[1].strip())
                if self.spec.assert_type == AssertType.ASSERT_ALLCLOSE:
                    default_threshold[self.spec.assert_type]['atol'] = atol
                elif self.spec.assert_type == AssertType.TF_ASSERT_ALL_CLOSE:
                    default_threshold[self.spec.assert_type]['atol'] = atol
                else:
                    self.logger.logo("unrecognized assert %s " %
                                     self.spec.assert_string)
                    raise RuntimeError
            elif 'prec' in arg:
                self.logger.logo("updating...")
                rtol = float(arg.split('=')[1].strip())
                if self.spec.assert_type == AssertType.PYRO_ASSERT_EQUAL:
                    default_threshold[self.spec.assert_type]['prec'] = rtol
                else:
                    self.logger.logo("unrecognized assert %s " %
                                     self.spec.assert_string)
                    raise RuntimeError
            elif 'atol' in arg:
                self.logger.logo("ignoring atol")
            elif 'places' in arg:
                places = int(arg.split("=")[1].strip())
                if self.spec.assert_type == AssertType.ASSERT_ALMOST_EQUAL:
                    default_threshold[self.spec.assert_type]['decimal'] = 1 * \
                        10 ** (-places)

    def compute_fit_score(self, samples, models=None):
        try:
            var = np.var(np.hstack(samples))
            if var < self.minimum_variance_threshold:
                self.logger.logo(
                    "Variance ({0}) too small, using delta distribution".format(var))
                return "delta", DeltaDist(samples)
        except:
            self.logger.logo(
                "Cannot compute variance, continuing with distribution computation...")
        if models is None:
            models = [dist.norm, dist.expon, dist.gamma, dist.pareto, dist.t, dist.lognorm, dist.cauchy, dist.dweibull,
                      dist.invweibull,
                      dist.logistic, dist.beta, dist.gumbel_l, dist.halfcauchy, dist.laplace]


        y, x = np.histogram(np.array(samples), bins='sturges')


        bin_width = x[1] - x[0]
        N = len(samples)
        x_mid = (x + np.roll(x, -1))[:-1] / 2.0
        DISTRIBUTIONS = models
        sses = []
        logpdfs = []
        for d in DISTRIBUTIONS:
            name = d.__class__.__name__[:-4]

            params = d.fit(np.array(samples))
            arg = params[:-2]
            loc = params[-2]
            scale = params[-1]

            pdf = d.pdf(x_mid, loc=loc, scale=scale, *arg)
            logpdf = d.logpdf(np.array(samples), loc=loc, scale=scale, *arg)
            pdf_scaled = pdf * bin_width * N

            sse = np.sum((y - pdf_scaled) ** 2)
            sses.append([sse, name, d(loc=loc, scale=scale, *arg)])
            logpdfs.append(
                [np.sum(logpdf), name, d(loc=loc, scale=scale, *arg)])

        results = pd.DataFrame(
            sses, columns=['SSE', 'distribution', 'dist']).sort_values(by='SSE')
        best_name = results[np.isfinite(
            results['SSE'])].iloc[0]['distribution']
        best_dist = results[np.isfinite(results['SSE'])].iloc[0]['dist']
        return best_name, best_dist

    def compute_best_extreme_dist(self, samples, max_bound=True, min_bound=False):
        try:
            var = np.var(np.hstack(samples))
            if var < self.minimum_variance_threshold:
                self.logger.logo(
                    "Variance ({0}) too small, using delta distribution".format(var))
                return "delta", DeltaDist(samples), 0
        except:
            self.logger.logo(
                "Cannot compute variance, continuing with distribution computation...")
        models = [dist.gumbel_r, dist.frechet_r, dist.weibull_max] + [dist.gumbel_l, dist.frechet_l, dist.weibull_min]
        y, x = np.histogram(np.array(samples), bins='sturges')

        bin_width = x[1] - x[0]
        N = len(samples)
        x_mid = (x + np.roll(x, -1))[:-1] / 2.0

        DISTRIBUTIONS = models

        sses = []
        logpdfs = []
        for d in DISTRIBUTIONS:
            name = d.__class__.__name__[:-4]

            params = d.fit(np.array(samples))
            arg = params[:-2]
            loc = params[-2]
            scale = params[-1]

            pdf = d.pdf(x_mid, loc=loc, scale=scale, *arg)
            logpdf = d.logpdf(np.array(samples), loc=loc, scale=scale, *arg)
            # to go from pdf back to counts need to un-normalise the pdf
            pdf_scaled = pdf * bin_width * N

            sse = np.sum((y - pdf_scaled) ** 2)
            sses.append([sse, name, d(loc=loc, scale=scale, *arg)])
            logpdfs.append(
                [np.sum(logpdf), name, d(loc=loc, scale=scale, *arg)])

        results = pd.DataFrame(
            sses, columns=['SSE', 'distribution', 'dist']).sort_values(by='SSE')
        best_name = results[np.isfinite(
            results['SSE'])].iloc[0]['distribution']
        best_dist = results[np.isfinite(results['SSE'])].iloc[0]['dist']
        error = results[np.isfinite(results['SSE'])].iloc[0]['SSE']

        return best_name, best_dist, np.sqrt(error)/len(samples)

    def parse(self):
        with open(self.sample_file, 'r') as f:
            lines = f.readlines()
            self.spec.assert_string = lines[7]
            self.logger.logo(self.spec.assert_string.strip())
            args = lines[8].split(':')[1].strip()[1:-2].split(',')
            self.parse_arguments(args)

    def evaluate(self):
        if self.sample_file is not None:
            with open(self.sample_file, 'r') as sf:
                lines = sf.readlines()[10:]
                actual = np.array([ast.literal_eval(
                    x.split("::")[0].strip()) for x in lines])
                expected = np.array([ast.literal_eval(
                    x.split("::")[1].strip()) for x in lines])
        else:
            actual = np.array(self.actual)
            expected = np.array(self.expected)

        if len(actual) == 0:
            self.logger.logo("No Samples!!")
            return 1.0

        if self.spec.assert_type in [AssertType.ASSERTLESS, AssertType.ASSERTLESSEQUAL]:
            p = self.check_assert_less(actual, expected)
        elif self.spec.assert_type in [AssertType.ASSERTGREATER, AssertType.ASSERTGREATEREQUAL]:
            p = self.check_assert_greater(actual, expected)
        elif self.spec.assert_type in [AssertType.ASSERT_ALLCLOSE, AssertType.TF_ASSERT_ALL_CLOSE]:
            p = self.check_assert_all_close_tolerance(
                actual, expected, default_threshold.get(self.spec.assert_type))
        elif self.spec.assert_type in [AssertType.PYRO_ASSERT_EQUAL, AssertType.ASSERT_ALMOST_EQUAL,
                                  AssertType.ASSERT_APPROX_EQUAL, AssertType.ASSERT_ARRAY_ALMOST_EQUAL]:
            p = self.check_assert_tolerance(
                actual, expected, default_threshold.get(self.spec.assert_type))
        elif self.spec.assert_type in [AssertType.ASSERT_ARRAY_LESS]:
            p = self.check_assert_less(actual, expected)
        elif self.spec.assert_type in [AssertType.ASSERTEQUAL, AssertType.ASSERT_EQUAL, AssertType.ASSERT_LIST_EQUAL, AssertType.ASSERTALLEQUAL]:
            p = self.check_assert_equal(actual, expected)
        elif self.spec.assert_type in [AssertType.ASSERTTRUE, AssertType.ASSERTFALSE, AssertType.ASSERT]:
            if '<' in self.spec.assert_string:
                p = self.check_assert_less(actual, expected)
            elif '>' in self.spec.assert_string:
                p = self.check_assert_greater(actual, expected)
            elif '==' in self.spec.assert_string:
                p = self.check_assert_equal(actual, expected)
            else:
                self.logger.logo("Unhandled assert %s " % self.spec.assert_string)
        else:
            self.logger.logo("Unhandled assert %s " % self.spec.assert_string)
            return 1.0

        if p > 0.0:
            self.logger.logo("Probability of fail (non-zero): %s" % str(p))
        else:
            self.logger.logo("Probability of fail : %s" % str(p))
        return p

    def check_assert_equal(self, actual: list, expected: list):
        num_fail = 0

        for i in range(len(actual)):
            if not np.equal(np.ndarray.flatten(np.array(actual[i])), np.ndarray.flatten(np.array(expected[i]))).all():
                num_fail += 1
        prob = num_fail / len(actual)
        return prob

    def check_assert_greater(self, actual: list, expected: list):
        if self.enable_per_dim_comparison and Util.getdims(actual) >= 2:
            probs = []
            for ind in range(len(actual[0])):
                actual_temp = [x[ind] for x in actual if len(x) > ind]
                expected_temp = expected if Util.getdims(expected) == 1 else [t[ind] for t in expected if len(t) > ind]
                if len(actual_temp) == 0 :
                    continue
                p = self.check_assert_greater(actual_temp, expected_temp)
                probs.append(p)
            return np.max(probs)  # max probability of failing
        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(actual)
                prob = dist.cdf(expected[0])
            except:
                self.logger.logo(tb.format_exc())
                return 1.0
        elif self.dist_type == norm:
            mean, var = norm.fit(actual)
            if var <= 0.0:
                var = 1e-20
            prob = norm.cdf(expected[0], loc=mean, scale=var)
        else:
            ecdf = ECDF(actual)
            prob = ecdf([expected[0]])[0]
        return np.max(prob)

    def check_assert_less(self, actual, expected):
        if self.enable_per_dim_comparison and (Util.getdims(actual) >= 2 or isinstance(actual[0], (list, np.ndarray))):
            probs = []
            for ind in range(len(actual[0])):
                actual_temp = np.array([arr.flatten()[ind] for arr in actual if ind < len(arr)])
                expected_temp = expected if Util.getdims(expected) == 1 else np.array([arr.flatten()[ind] for arr in expected if ind < len(arr)])
                if len(actual_temp) == 0:
                    continue
                p = self.check_assert_less(actual_temp, expected_temp)
                probs.append(p)
            return np.max(probs)  # max probability of failing
        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(actual)
                prob = dist.cdf(expected[0])
            except:
                import traceback as tb
                self.logger.logo(tb.format_exc())
                return 1.0
        elif self.dist_type == norm:
            mean, var = norm.fit(actual)
            if var <= 0.0:
                var = 1e-20
            prob = norm.cdf(expected[0], loc=mean, scale=var)
        else:
            ecdf = ECDF(actual)
            prob = ecdf([expected[0]])[0]
        return 1 - np.min(prob)  # ideally np.max(1-prob)

    def check_assert_all_close_tolerance(self, actual: list, expected: list, tol_thresh):
        if self.enable_per_dim_comparison and Util.getdims(actual) >= 2:
            probs = []
            for ind in range(len(actual[0])):
                actual_temp = [x[ind] for x in actual if ind < len(x)]
                expected_temp = expected if Util.getdims(expected) == 1 else [
                                                              t[ind] for t in expected if ind < len(t)]
                if len(actual_temp) == 0:
                    continue
                p = self.check_assert_all_close_tolerance(actual_temp, expected_temp,
                                                          tol_thresh)
                probs.append(p)
            return np.max(probs)  # max probability of failing

        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(np.subtract(np.abs(np.subtract(actual, expected)),
                                                                tol_thresh['atol']))
                prob = dist.cdf(tol_thresh['rtol'] * np.abs(expected))
            except:
                import traceback as tb
                self.logger.logo(tb.format_exc())
                return 1.0
        return 1 - np.min(prob)

    def check_assert_relative_tolerance(self, actual: list, expected: list, tol_thresh):
        if isinstance(tol_thresh, dict):
            if 'rtol' in tol_thresh:
                tol_thresh = tol_thresh['rtol']
            elif 'decimal' in tol_thresh:
                tol_thresh = tol_thresh['decimal']
            elif 'significant' in tol_thresh:
                tol_thresh = tol_thresh['significant']

        if self.enable_per_dim_comparison and Util.getdims(actual) >= 2:
            # for each index of actual, figure out the probability
            probs = []
            for ind in range(len(actual[0])):
                actual_temp = [x[ind] for x in actual if ind < len(x)]
                if len(actual_temp) == 0:
                    continue
                p = self.check_assert_relative_tolerance(actual_temp,
                                                         expected if Util.getdims(expected) == 1 else [
                                                             t[ind] for t in expected if ind < len(t)],
                                                         tol_thresh)
                probs.append(p)
            return np.max(probs)  # max probability of failing
        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(
                    np.abs(np.subtract(actual, expected)))
                prob = dist.cdf(tol_thresh)
            except:
                import traceback as tb
                self.logger.logo(tb.format_exc())
                return 1.0
        elif self.dist_type == norm:
            mean, var = norm.fit(np.abs(np.subtract(actual, expected)))
            if var <= 0.0:
                var = 1e-20
            prob = norm.cdf(tol_thresh, loc=mean, scale=var)
        else:
            ecdf = ECDF(np.abs(np.subtract(actual, expected)) /
                        np.abs(expected))
            prob = ecdf([tol_thresh])[0]
        return 1 - np.min(prob)

    # absolute tolerance
    def check_assert_tolerance(self, actual: list, expected: list, tol_thresh):
        if isinstance(tol_thresh, dict):
            if 'rtol' in tol_thresh:
                tol_thresh = tol_thresh['rtol']
            elif 'decimal' in tol_thresh:
                tol_thresh = tol_thresh['decimal']
            elif 'significant' in tol_thresh:
                tol_thresh = tol_thresh['significant']
            elif 'prec' in tol_thresh:
                tol_thresh = tol_thresh['prec']

        if self.enable_per_dim_comparison and Util.getdims(actual) >= 2:
            probs = []
            for ind in range(len(actual[0])):
                p = self.check_assert_tolerance([x[ind] for x in actual if ind < len(x)],
                                                expected if Util.getdims(expected) == 1 else [
                                                    t[ind] for t in expected if ind < len(t)],
                                                tol_thresh)
                probs.append(p)
            return np.max(probs)  # max probability of failing

        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(
                    np.abs(np.subtract(actual, expected)))
                prob = dist.cdf(tol_thresh)
            except:
                import traceback as tb
                self.logger.logo(tb.format_exc())
                return 1.0

        elif self.dist_type == norm:
            mean, var = norm.fit(np.abs(np.subtract(actual, expected)))
            if var <= 0.0:
                var = 1e-20
            prob = norm.cdf(tol_thresh, loc=mean, scale=var)
        else:
            ecdf = ECDF(np.abs(np.subtract(actual, expected)))
            prob = ecdf([tol_thresh])[0]
        return 1 - np.min(prob)

    def get_dist_limits(self, distrib, max_bound=True, min_bound=False, threshold=0.01):
        assert not max_bound or not min_bound

        if max_bound:
            if isinstance(distrib, DeltaDist):
              bound = distrib.b
            elif distrib.b == np.inf:
                self.logger.logo("Dist type: {0}, chosen bound: {1}".format(distrib.dist.name, distrib.ppf(0.95)))
                bound = distrib.ppf(0.95)
            else:
                bound = distrib.ppf(1.0)
            base_limit = bound
            bound = bound + threshold * np.abs(bound)
        else:
            if isinstance(distrib, DeltaDist):
                bound = distrib.b
            elif distrib.a == -np.inf:
                self.logger.logo("Dist type: {0}, chosen bound: {1}".format(distrib.dist.name, distrib.ppf(0.05)))
                bound = distrib.ppf(0.05)
            else:
                bound = distrib.ppf(0.0)
            base_limit = bound
            bound = bound - threshold * np.abs(bound)
        return bound, base_limit

    def get_new_bound_gev(self, dist, max_percentile):
        actual = np.array(self.actual)
        expected = np.array(self.expected)

        if len(actual) == 0:
            self.logger.logo("No Samples!!")
            return np.inf, np.inf

        if self.spec.assert_type in [AssertType.ASSERTLESS, AssertType.ASSERTLESSEQUAL]:
            if self.spec.reverse:
                b, e = dist.ppf(1-max_percentile), np.min(expected)
            else:
                b, e = dist.ppf(max_percentile), np.max(expected)
        elif self.spec.assert_type in [AssertType.ASSERTGREATER, AssertType.ASSERTGREATEREQUAL]:
            if self.spec.reverse:
                b, e = dist.ppf(max_percentile), np.max(expected)
            else:
                b, e = dist.ppf(1-max_percentile), np.min(expected)
        elif self.spec.assert_type in [AssertType.ASSERT_ALLCLOSE, AssertType.TF_ASSERT_ALL_CLOSE]:
            b, e = dist.ppf(max_percentile), np.max(expected)
        elif self.spec.assert_type in [AssertType.PYRO_ASSERT_EQUAL, AssertType.ASSERT_ALMOST_EQUAL,
                                  AssertType.ASSERT_APPROX_EQUAL, AssertType.ASSERT_ARRAY_ALMOST_EQUAL]:
            b, e = dist.ppf(max_percentile), np.max(expected)
        elif self.spec.assert_type in [AssertType.ASSERT_ARRAY_LESS]:
            if self.spec.reverse:
                b, e = dist.ppf(1-max_percentile), np.min(expected)
            else:
                b, e = dist.ppf(max_percentile), np.max(expected)
        elif self.spec.assert_type in [AssertType.ASSERTTRUE, AssertType.ASSERTFALSE, AssertType.ASSERT]:
            if '<' in self.spec.assert_string:
                if self.spec.reverse:
                    b, e = dist.ppf(1-max_percentile), np.min(expected)
                else:
                    b, e = dist.ppf(max_percentile), np.max(expected)
            elif '>' in self.spec.assert_string:
                if self.spec.reverse:
                    b, e = dist.ppf(max_percentile), np.max(expected)
                else:
                    b, e = dist.ppf(1-max_percentile), np.min(expected)
            else:
                self.logger.logo("Unhandled assert %s " % self.spec.assert_string)
        else:
            self.logger.logo("Unhandled assert %s " % self.spec.assert_string)
            return np.inf, np.inf, np.inf

        return b, e

    def get_new_threshold(self, threshold):
        if self.sample_file is not None:
            with open(self.sample_file, 'r') as sf:
                lines = sf.readlines()[10:]
                actual = np.array([ast.literal_eval(
                    x.split("::")[0].strip()) for x in lines])
                expected = np.array([ast.literal_eval(
                    x.split("::")[1].strip()) for x in lines])
        else:
            actual = np.array(self.actual)
            expected = np.array(self.expected)

        if len(actual) == 0:
            self.logger.logo("No Samples!!")
            return np.inf, np.inf, np.inf

        if self.spec.assert_type in [AssertType.ASSERTLESS, AssertType.ASSERTLESSEQUAL]:
            if self.spec.reverse:
                b, e, base = self.get_assert_greater_bound(actual, expected, threshold)
            else:
                b, e, base = self.get_assert_less_bound(actual, expected, threshold)
        elif self.spec.assert_type in [AssertType.ASSERTGREATER, AssertType.ASSERTGREATEREQUAL]:
            if self.spec.reverse:
                b, e, base = self.get_assert_less_bound(actual, expected, threshold)
            else:
                b, e, base = self.get_assert_greater_bound(actual, expected, threshold)
        elif self.spec.assert_type in [AssertType.ASSERT_ALLCLOSE, AssertType.TF_ASSERT_ALL_CLOSE]:
            b, e, base = self.get_assert_all_close_tolerance_bound(
                actual, expected, default_threshold.get(self.spec.assert_type), threshold)
        elif self.spec.assert_type in [AssertType.PYRO_ASSERT_EQUAL, AssertType.ASSERT_ALMOST_EQUAL,
                                  AssertType.ASSERT_APPROX_EQUAL, AssertType.ASSERT_ARRAY_ALMOST_EQUAL]:
            b, e, base = self.get_assert_tolerance_bound(
                actual, expected, default_threshold.get(self.spec.assert_type), threshold)
        elif self.spec.assert_type in [AssertType.ASSERT_ARRAY_LESS]:
            if self.spec.reverse:
                b, e, base = self.get_assert_greater_bound(actual, expected, threshold)
            else:
                b, e, base = self.get_assert_less_bound(actual, expected, threshold)
        elif self.spec.assert_type in [AssertType.ASSERTTRUE, AssertType.ASSERTFALSE, AssertType.ASSERT]:
            if '<' in self.spec.assert_string:
                if self.spec.reverse:
                    b, e, base = self.get_assert_greater_bound(actual, expected, threshold)
                else:
                    b, e, base = self.get_assert_less_bound(actual, expected, threshold)
            elif '>' in self.spec.assert_string:
                if self.spec.reverse:
                    b, e, base = self.get_assert_less_bound(actual, expected, threshold)
                else:
                    b, e, base = self.get_assert_greater_bound(actual, expected, threshold)
            else:
                self.logger.logo("Unhandled assert %s " % self.spec.assert_string)
        else:
            self.logger.logo("Unhandled assert %s " % self.spec.assert_string)
            return np.inf, np.inf, np.inf

        return b, e, base

    def get_assert_less_bound(self, actual, expected, threshold):
        if self.enable_per_dim_comparison and (Util.getdims(actual) >= 2 or isinstance(actual[0], (list, np.ndarray))):
            bounds = []
            base_bounds = []
            for ind in range(len(actual[0])):
                actual_temp = np.array([arr.flatten()[ind] for arr in actual if ind < len(arr)])
                expected_temp = expected if Util.getdims(expected) == 1 else np.array([arr.flatten()[ind] for arr in expected if ind < len(arr)])
                if len(actual_temp) == 0:
                    continue
                p, e, base = self.get_assert_less_bound(actual_temp, expected_temp, threshold)
                bounds.append(p)
                base_bounds.append(base)
            return np.max(bounds), np.max(expected), np.max(base_bounds)  # max probability of failing
        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(actual)
                bound, base_bound = self.get_dist_limits(dist, max_bound=True, min_bound=False, threshold=threshold)
            except:
                import traceback as tb
                self.logger.logo(tb.format_exc())
                return np.inf, np.inf, np.inf
        return np.max(bound), np.max(expected), base_bound  # ideally np.max(1-prob)

    def get_assert_greater_bound(self, actual, expected, threshold):
        if self.enable_per_dim_comparison and Util.getdims(actual) >= 2:
            # for each index of actual, figure out the probability
            bounds = []
            base_bounds = []
            for ind in range(len(actual[0])):
                actual_temp = [x[ind] for x in actual if len(x) > ind]
                expected_temp = expected if Util.getdims(expected) == 1 else [t[ind] for t in expected if len(t) > ind]
                if len(actual_temp) == 0:
                    continue
                p, _, base = self.get_assert_greater_bound(actual_temp, expected_temp, threshold)
                bounds.append(p)
                base_bounds.append(base)
            return np.min(bounds), np.min(expected), np.min(base_bounds)  # max probability of failing
        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(actual)
                bound, base_bound = self.get_dist_limits(dist, max_bound=False, min_bound=True, threshold=threshold)
            except:
                self.logger.logo(tb.format_exc())
                return -np.inf, np.min(expected), np.inf
        return np.min(bound), np.min(expected), base_bound

    def get_assert_all_close_tolerance_bound(self, actual: list, expected: list, tol_thresh, threshold):
        if self.enable_per_dim_comparison and Util.getdims(actual) >= 2:
            # for each index of actual, figure out the probability
            bounds = []
            base_bounds = []
            for ind in range(len(actual[0])):
                actual_temp = [x[ind] for x in actual if ind < len(x)]
                expected_temp = expected if Util.getdims(expected) == 1 else [
                    t[ind] for t in expected if ind < len(t)]
                if len(actual_temp) == 0:
                    continue
                p, e, base = self.get_assert_all_close_tolerance_bound(actual_temp, expected_temp,
                                                          tol_thresh, threshold)
                bounds.append(p)
                base_bounds.append(base)
            return np.max(bounds), tol_thresh['rtol'], np.max(base_bounds)

        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(np.subtract(np.abs(np.subtract(actual, expected)),
                                                                tol_thresh['atol']))
                bound, base_bound = self.get_dist_limits(dist, True, False, threshold)
                if expected != 0:
                    bound = bound / np.abs(expected)
                #prob = dist.cdf(tol_thresh['rtol'] * np.abs(expected))
            except:
                import traceback as tb
                self.logger.logo(tb.format_exc())
                return np.inf, np.inf, np.inf
        return np.max(np.abs(bound)), tol_thresh['rtol'], np.max(np.abs(base_bound))

    def get_assert_tolerance_bound(self, actual: list, expected: list, tol_thresh, threshold):
        if isinstance(tol_thresh, dict):
            if 'rtol' in tol_thresh:
                tol_thresh = tol_thresh['rtol']
            elif 'decimal' in tol_thresh:
                tol_thresh = tol_thresh['decimal']
            elif 'significant' in tol_thresh:
                tol_thresh = tol_thresh['significant']
            elif 'prec' in tol_thresh:
                tol_thresh = tol_thresh['prec']

        if self.enable_per_dim_comparison and Util.getdims(actual) >= 2:
            # for each index of actual, figure out the probability
            bounds = []
            base_bounds = []
            for ind in range(len(actual[0])):
                p, e, base = self.get_assert_tolerance_bound([x[ind] for x in actual if ind < len(x)],
                                                expected if Util.getdims(expected) == 1 else [
                                                    t[ind] for t in expected if ind < len(t)],
                                                tol_thresh, threshold)
                bounds.append(p)
                base_bounds.append(base)
            return np.max(bounds), tol_thresh, np.max(base_bounds)

        if self.dist_type is None:
            try:
                name, dist = self.compute_fit_score(
                    np.abs(np.subtract(actual, expected)))
                bound, base_bound = self.get_dist_limits(dist, True, False, threshold)
            except:
                import traceback as tb
                self.logger.logo(tb.format_exc())
                return np.inf, np.inf, np.inf
        return np.max(np.abs(bound)), tol_thresh, np.max(np.abs(base_bound))

    def check_sample_size(self, samples):
        N = len(samples)
        K = 2*int(np.sqrt(N))  # size of each subset of bootstrap subsamples
        M = K  # number of p values to be computed
        J = N  # chooses first J samples
        alpha = 0.1
        confidence_interval = 1 - alpha
        print("M: {0}, N: {1}, alpha: {2}, conf interval: {3}".format(M, N, alpha, confidence_interval))
        critical_value = dist.t.ppf(confidence_interval, M - 1)
        # print(samples)

        print("Sample size %d" % N)
        bootstrap_samples = [np.random.choice(samples, size=N, replace=True) for _ in range(M - 1)] + [samples]

        x_bootstrap_samples = [k[:J] for k in bootstrap_samples]

        k_bootstrap_samples = [[np.random.choice(t, size=len(t), replace=True) for _ in range(K - 1)] + [t] for t in
                               x_bootstrap_samples]
        print("Fitting...")
        gev_models = [[self.compute_fit_score(t, models=[dist.genextreme]) for t in x] for x in k_bootstrap_samples]
        return_levels = [[t[1].ppf(0.99) for t in k] for k in gev_models]
        sw_stats = [st.shapiro(t)[1] for t in return_levels]  # considering only p value
        print(sw_stats)
        avg_pvalue = np.mean(sw_stats)
        var_pvalue = np.sum([np.square(p - avg_pvalue) for p in sw_stats]) / (M - 1)
        sd_pvalue = np.sqrt(var_pvalue)
        print("Avg: {0}, Var: {1}, SD: {2}".format(avg_pvalue, var_pvalue, sd_pvalue))

        lower_bound = avg_pvalue - critical_value * sd_pvalue
        print("Lower bound: %f" % lower_bound)

        if lower_bound > alpha:
            print("Accept")
            return True
        else:
            print("Reject")
            return False

    def check_bootstrap_conf(self, samples, max_percentile, min_tail_values):
        alpha = 0.05
        N = len(samples)
        K = N
        M = K
        printf = lambda x: self.logger.logo(x)
        printf("Sample size %d" % N)
        printf("K: {0}, N: {1}".format(K, N))
        bootstrap_samples = [np.random.choice(samples, size=N, replace=True) for _ in range(M - 1)] + [samples]

        printf("Fitting...")
        gpd_return_levels = [self.run_mbpta_cv(t, min_tail_values, max_percentile, printf=None) for t in bootstrap_samples]
        if any(np.isinf(gpd_return_levels)):
            printf("Reject, infs")
            return False, -np.inf, -np.inf
        avg_return = np.mean(gpd_return_levels)
        sd_return = np.std(gpd_return_levels)
        w, p = st.shapiro(gpd_return_levels)
        printf("Shapiro stats: w: {0}, p: {1}".format(w, p))
        printf("Avg Return: {0}, Sd Return: {1}".format(avg_return, sd_return))
        if p > alpha:
            printf("Accept")
            return True, avg_return, sd_return
        else:
            printf("Reject")
            return False, -np.inf, -np.inf

    def gpd_test(self, samples):
        from rpy2.interactive.packages import importr
        from rpy2.robjects import FloatVector
        samples = np.array(samples)
        gpdtest = importr("gPdtest")
        res = gpdtest.gpd_test(FloatVector(samples))
        print("GPD: H+:{0}, H-:{1}".format(res[1][0], res[1][1]))
        if res[1][0] >= 0.05 or res[1][1] >= 0.05:
            return True
        else:
            return False

    def gpd_test2(self, samples):
        from rpy2.interactive.packages import importr
        from rpy2.robjects import FloatVector
        samples = np.array(samples)
        eva = importr("eva")
        try:
            res = eva.gpdAd(FloatVector(samples), bootstrap=True, bootnum=100,
                            allowParallel=True, numCores=5)
            pval = res[1][0]
            scale = res[2][0]
            shape = res[2][1]
        except:
            self.logger.logo("GPD exception")
            return 0, -np.inf, -np.inf

        return pval, scale, shape

    def llrtest(self, samples, alpha=0.05):
        d1_param = st.genpareto.fit(samples)

        # Good if already light or exp
        if d1_param[-3] < 0:
            return TailType.LIGHT, d1_param, 0, 1
        elif d1_param[-3] == 0:
            return TailType.EXP, d1_param, 0, 1

        d2_param = st.genpareto.fit(samples, fc=0)
        d1 = st.genpareto(d1_param[-3], loc=d1_param[-2], scale=d1_param[-1])
        d2 = st.genpareto(d2_param[-3], loc=d2_param[-2], scale=d2_param[-1])
        ll1 = np.sum([np.log(d1.pdf(x)) for x in samples])
        ll2 = np.sum([np.log(d2.pdf(x)) for x in samples])
        llr = -2 * (ll2 - ll1)
        chi = st.chi2(1).ppf(1 - alpha)
        pval = 1 - st.chi2(1).cdf(llr)
        if llr <= chi:
            return TailType.EXP, d2_param, llr, pval
        else:
            return TailType.HEAVY, d1_param, llr, pval

    def run_mbpta_cv(self, samples, min_tail_values, max_percentile, printf=None):
        if printf is None:
            printf = lambda x: self.logger.logo(x)
        samples = np.array(samples)
        N = len(samples)
        # select samples on the right of mode
        hist, edges = np.histogram(samples, bins='sturges')
        edges = np.sort(np.unique(samples))
        #i = np.argmax(hist)
        #samples = samples[samples > edges[i]]
        #printf("Selected samples: {0}, mode: {1}, total samples: {2}".format(len(samples), edges[i], N))
        if len(samples) < min_tail_values:
            printf("not enough tail values")
            return -np.inf

        best_th = -np.inf
        best_th_bc = -np.inf

        thresholds = list(np.sort([np.min(samples)-0.1] + list(edges)))
        thresholds = thresholds[-1::-1]  # reversed
        #thresholds = np.random.choice(thresholds, min(20, len(thresholds)))

        printf("Thresholds : {0}".format(thresholds))
        th_dict = dict()
        exp_param_dict = dict()
        for th in thresholds:
            s = samples[samples > th]
            if len(s) < min_tail_values:
                continue
            # test for exponentiality
            exc = [k - th for k in s]


            pval, scale, shape = self.gpd_test2(exc)
            printf("--Threshold: {0}, Size: {1}".format(th, len(s)))
            printf("GPD pval: {0}, shape: {1}, scale: {2}, Accepted: {3}".format(pval, shape, scale, pval > 0.05))

            if pval > 0.05:
                th_dict[th] = (pval, shape, scale)

                tail_type, exp_params, llrscore, pval = self.llrtest(exc)
                printf("LLR score: {0}, TailType: {1}, PVal: {2}, Exp_params: {3}".format(llrscore, tail_type, pval, exp_params))
                if tail_type == TailType.LIGHT or tail_type == TailType.EXP:
                    best_th = th
                    exp_param_dict[th] = exp_params
                    for p in [0.90, 0.95, 0.99, 0.999, 0.9999]:
                        estimate = best_th + st.genpareto(*exp_param_dict[best_th]).ppf(p)
                        printf(">>Estimates {0} :: {1}".format(p, estimate))


        printf("Best th: {0}".format(best_th))
        # choose the lowest threshold for computation
        if np.isfinite(best_th):
            printf("Computing exp dist")
            printf("Exp params: {0}".format(exp_param_dict[best_th]))
            for p in [0.90, 0.95, 0.99, 0.999, 0.9999]:
                estimate = best_th + st.genpareto(*exp_param_dict[best_th]).ppf(p)
                printf("Estimate {0} :: {1}".format(p, estimate))
            estimate = best_th + st.genpareto(*exp_param_dict[best_th]).ppf(max_percentile)
            printf("Estimate {0} : {1}".format(max_percentile, estimate))
            return estimate

        return -np.inf

    def get_best_fit_exp_tail_estimate(self, samples, min_tail_values, max_percentile, printf=None, adjust_ppf=False):
        if printf is None:
            printf = lambda x: self.logger.logo(x)
        samples = np.array(samples)
        hist, edges = np.histogram(samples, bins='sturges')
        i = np.argmax(hist)
        samples = samples[samples > edges[i]]
        if len(samples) < min_tail_values:
            printf("not enough tail values")
            return -np.inf

        best_th = -np.inf
        best_cv = np.inf
        thresholds = list(np.sort([np.min(samples) - 0.1] + list(np.unique(samples))))
        printf("Thresholds : {0}".format(thresholds))
        for th in thresholds:
            s = samples[samples > th]
            if len(s) < 50:
                continue
            exc = [k - th for k in s]

            cv_th = st.genpareto.fit(exc)[0]

            if np.abs(cv_th-1) < best_cv:
                best_th = th
                best_cv = np.abs(cv_th-1)

        printf("Best th: {0}, Best CV: {1}".format(best_th, best_cv))

        if np.isfinite(best_th):
            printf("Computing exp dist")
            estimate = self.fit_expon_to_tail(best_th, max_percentile, printf, samples)
            printf(estimate)
            return estimate
        return np.inf

    def fit_expon_to_tail(self, best_th, max_percentile, printf, samples):
        s = samples[samples > best_th]
        exceedences = [k - best_th for k in s]
        mean = np.mean(exceedences)
        exp_lambda = mean
        printf("lambda :{0}".format(exp_lambda))
        exp = st.expon(*st.expon.fit(exceedences))
        rtrn = exp.ppf(max_percentile)
        gp = st.genpareto(*st.genpareto.fit(exceedences))
        stat, pval = st.kstest(exp.rvs, gp.cdf)
        printf("GPD vs fitted exp: KS-stat {0}, pval {1}".format(stat, pval))
        printf(rtrn)
        estimate = best_th + rtrn
        return estimate

