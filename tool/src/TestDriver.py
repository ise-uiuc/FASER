import ast
import multiprocessing
import os
import re
import signal
import subprocess as sp
import traceback as tb

import numpy as np
import scipy
import scipy.stats as st

from CompareDistribution import CompareDistribution
from src import Util
from src.Util import sample_to_str, compute_max_diff
from src.lib.AssertSpec import AssertSpec
from src.lib.AssertType import AssertType
from src.lib.TestRunResults import TestRunResults


class TestDriver:
    def __init__(self, assert_spec: AssertSpec, rundir,
                 libdir,
                 parallel=False,
                 logstring="log>>>",
                 condaenvname=None,
                 threads=None,
                 config=None,
                 logger=None,
                 test_timeout=None,
                 suffix=""
                 ):
        self.assert_spec = assert_spec
        self.parallel = parallel
        self.config=config
        self.patch = None
        self.logdir=None
        self.logstring=logstring
        self.logger=logger
        self.condaenvname=condaenvname
        self.rundir=rundir
        self.libdir=libdir
        self.threads=threads
        self.test_timeout = test_timeout
        self.suffix = suffix

    def _parse_output(self, out, err):
        try:
            output_string = str(out).replace("-inf", str(np.finfo(np.float32).min)).replace("inf", str(np.finfo(np.float32).max))
            error_string = str(err).replace("-inf", str(np.finfo(np.float32).min)).replace("inf", str(np.finfo(np.float32).max))
            matched=re.findall("{0}([0-9.eE+,\[\]\(\) -]+)".format(self.logstring), output_string)
            if len(matched) == 0:
                matched=re.findall("{0}([0-9.eE+,\[\]\(\) -]+)".format(self.logstring), error_string)
        
            values=[np.array(ast.literal_eval(x)) if ('[' in x or '(' in x) else float(x) for x in matched]

            assert len(values) >= 2
            if len(values) >=2:
                actual=[values[i] for i in range(0, len(values), 2)]
                expected = [values[i] for i in range(1, len(values), 2)]
                values=[actual, expected]

            return values, 0
        except:
            #self.logger.logo('Not found ::: ')
            self.logger.logo("Error")
            self.logger.log("output string: {}".format(output_string))
            self.logger.log("error string: {}".format(error_string))
            return [np.finfo(np.float32).min, np.finfo(np.float32).min], 2

    def run_test(self, i):
        output, error, returncode = self.run_pytest(i)
        return output, error, returncode

    def run_pytest(self, i) -> (str,str):
        try:
            result=sp.run(['{4}/tool/src/runtest.sh {0} {1} {2} {3} {5}'.format(
                self.assert_spec.test.filename,
                self.assert_spec.test.classname,
                self.assert_spec.test.testname,
                self.condaenvname,
                self.libdir,
                i % multiprocessing.cpu_count()
            )],
                shell=True, stdout=sp.PIPE, stderr=sp.PIPE, timeout=self.test_timeout if self.test_timeout else None)
        except sp.TimeoutExpired as te:
            self.logger.logo("Timed out")
            result = sp.run(["ps -ef | grep 'python -m pytest -W' | grep -v grep | awk '{print $2}'"], shell=True)
            print(result.stdout)
            sp.run(["ps -ef | grep 'python -m pytest -W' | grep -v grep | awk '{print $2}' | xargs -r kill -9"], shell=True) # kill all tests thank you
            return te.output, te.stderr, -111
        return result.stdout, result.stderr, result.returncode

    def run_test_wrapper(self, i):
        print(".", end='')
        return self.run_test(i)

    def mp_handler(self, data):
        if self.threads is not None:
            self.logger.logo("Launching %d jobs, %d in parallel" % (len(data), self.threads))
            with multiprocessing.Pool(self.threads) as p:
                results = p.map(self.run_test_wrapper, data)
            print()
        else:
            # default thread behaviour
            self.logger.logo("Launching %d jobs, %d in parallel" % (len(data), self.config.THREAD_COUNT if self.parallel else 1))
            with multiprocessing.Pool(self.config.THREAD_COUNT if self.parallel else 1) as p:
                results = p.map(self.run_test_wrapper, data)
            print()



        return results

    @staticmethod
    def _append_samples(file, samples):
        with open(file, 'a') as samplefile:
            for sample in samples:
                # writing actual and expected
                for i in range(0, len(sample), 2):
                    samplefile.write("%s::%s\n" % (sample_to_str(sample[i]), sample_to_str(sample[i+1])))

    @staticmethod
    def _write_results(results, base_iters, resultdir):
        for i in range(base_iters, base_iters+len(results)):
            with open(os.path.join(resultdir, 'output_{0}'.format(i)), 'w+') as outfile:
                if results[i-base_iters][0] is not None and results[i-base_iters][1] is not None:
                    outfile.write(results[i-base_iters][0].decode("utf-8"))
                    outfile.write(results[i-base_iters][1].decode("utf-8"))

    def _write_report(self, outputs, extracted_outputs, errors, codes, convergence_scores):
        with open(os.path.join(self.logdir, 'report.txt'), 'w+') as report_file:
            report_file.write("Iterations: %d\n" % len(outputs))
            report_file.write("Passed : %d\n" % (sum([int(x)==0 for x in codes])))
            report_file.write("Failed : %d\n" % (sum([int(x) != 0 for x in codes])))

            report_file.write("Convergence scores: %s\n" % ' '.join([str(x) for x in convergence_scores]))
            report_file.write("")
            report_file.write(Util.samples_stat(extracted_outputs, self.assert_spec))

    def run_basic_test_loop(self):
        self.logdir = os.path.join(self.rundir, "assert_{0}{1}".format(self.assert_spec.get_hash(), self.suffix))
        self.logger.logo("Logdir: %s" % self.logdir)
        if os.path.exists(os.path.join(self.logdir, "report.txt")):
            self.logger.logo("Assertion exists.. exiting... ")
            self.logdir = None
            return TestRunResults()
        os.makedirs(self.logdir)

        samplefile_path = os.path.join(self.logdir, 'samples.txt')
        with open(samplefile_path, 'w+') as samplefile:
            samplefile.write(self.assert_spec.print_spec())
        outputs = []
        extracted_outputs = []
        parse_errors = []
        errors = []
        codes = []
        convergence_scores = []
        dist_names = []
        fit_errors = []
        distributions = []

        avg_ppfs = []
        sd_ppfs = []
        convergences = []
        estimated_ppfs = []

        sampling_iterations = 0
        next_batch_iterations = self.config.DEFAULT_ITERATIONS
        # actual value index
        avi = 1 if self.assert_spec.reverse else 0
        # expected value index
        evi = 0 if self.assert_spec.reverse else 1
        while sampling_iterations < self.config.MAX_ITERATIONS:
            # run the test N times
            results = self.mp_handler(list(range(next_batch_iterations)))
            self._write_results(results, sampling_iterations, self.logdir)
            # collect results
            newsamples = []
            for r in results:
                outputs.append(r[0])
                parsed_outputs, parse_error = self._parse_output(r[0], r[1])
                newsamples.append(parsed_outputs)
                parse_errors.append(parse_error)
                errors.append(r[1])
                if int(r[2]) != 0:
                    if len(re.findall("1 passed", str(r[0].decode("utf-8")))) == 0:
                        if parse_error != 2:
                            codes.append(r[2])
                        else:
                            codes.append(2) # A Crash in the test code most likely
                    else:
                        codes.append(0)
                else:
                    codes.append(r[2])

            self.logger.logo("Passed tests : %d" % (sum([int(x) == 0 for x in codes])))
            self.logger.logo("Failed tests : %d" % (sum([int(x) == 1 for x in codes])))
            self.logger.logo("Crashed tests: %d" % (sum([int(x) == 2 for x in codes])))

            self._append_samples(samplefile_path, newsamples)
            extracted_outputs = extracted_outputs + newsamples

            if sum([int(x) == 2 or int(x) == -111 for x in codes]) >= len(codes) / 2:
                self.logger.logo("Half of samples failed, exiting...")
                return TestRunResults(codes=codes)

            if AssertType.is_tolerance_assert(self.assert_spec):
                samples = [compute_max_diff(extracted_outputs[i][avi], extracted_outputs[i][evi])
                           for i in range(len(extracted_outputs)) if parse_errors[i] == 0]
            else:
                samples = [extracted_outputs[i][avi] for i in range(len(extracted_outputs)) if parse_errors[i] == 0]

            if Util.is_max_bound(self.assert_spec):
                samples = [np.max(k) for k in samples]
            elif Util.is_min_bound(self.assert_spec):
                samples = [-np.min(k) for k in samples]

            sampling_iterations += next_batch_iterations
            next_batch_iterations = self.config.SUBSEQUENT_ITERATIONS
            self.logger.logo("Continuing to next batch...")

        self._write_report(outputs, extracted_outputs, errors, codes, convergence_scores)

        return TestRunResults(extracted_outputs=extracted_outputs,
                              parse_errors=parse_errors, distributions=distributions,
                              fit_errors=fit_errors, dist_names=dist_names, avg_ppfs=avg_ppfs, sd_ppfs=sd_ppfs,
                              convergences=convergences, estimated_ppfs=estimated_ppfs, codes=codes)

    def run_test_loop(self):
        # create a directory for logs
        self.logdir = os.path.join(self.rundir, "assert_{0}{1}".format(self.assert_spec.get_hash(), self.suffix))
        self.logger.logo("Logdir: %s" % self.logdir)
        if os.path.exists(os.path.join(self.logdir, "report.txt")):
            self.logger.logo("Assertion exists.. exiting... ")
            self.logdir = None
            return TestRunResults()
        os.makedirs(self.logdir)

        samplefile_path=os.path.join(self.logdir, 'samples.txt')
        with open(samplefile_path, 'w+') as samplefile:
            samplefile.write(self.assert_spec.print_spec())
        outputs=[]
        extracted_outputs=[]
        parse_errors=[]
        errors=[]
        codes=[]
        convergence_scores=[]
        dist_names = []
        fit_errors = []
        distributions = []

        avg_ppfs = []
        sd_ppfs = []
        convergences = []
        estimated_ppfs = []

        sampling_iterations=0
        next_batch_iterations = self.config.DEFAULT_ITERATIONS
        # actual value index
        avi=1 if self.assert_spec.reverse else 0
        # expected value index
        evi=0 if self.assert_spec.reverse else 1
        while sampling_iterations < self.config.MAX_ITERATIONS:
            # run the test N times
            results=self.mp_handler(list(range(next_batch_iterations)))
            self._write_results(results, sampling_iterations, self.logdir)
            # collect results
            newsamples=[]
            for r in results:
                outputs.append(r[0])
                parsed_outputs, parse_error = self._parse_output(r[0], r[1])
                newsamples.append(parsed_outputs)
                parse_errors.append(parse_error)
                errors.append(r[1])
                if int(r[2]) != 0:
                    if len(re.findall("1 passed", str(r[0].decode("utf-8")))) == 0:
                        codes.append(r[2])
                    else:
                        codes.append(0)
                else:
                    codes.append(r[2])

            self.logger.logo("Passed tests : %d" % (sum([int(x)==0 for x in codes])))
            self.logger.logo("Failed tests : %d" % (sum([int(x) != 0 for x in codes])))

            self._append_samples(samplefile_path, newsamples)
            extracted_outputs = extracted_outputs + newsamples

            if sum([int(x) != 0 for x in codes]) >= len(codes) / 2:
                self.logger.logo("Half of samples failed, exiting...")
                return TestRunResults()

            if AssertType.is_tolerance_assert(self.assert_spec):
                samples = [compute_max_diff(extracted_outputs[i][avi], extracted_outputs[i][evi])
                           for i in range(len(extracted_outputs)) if parse_errors[i] == 0]
            else:
                samples = [extracted_outputs[i][avi] for i in range(len(extracted_outputs)) if parse_errors[i] == 0]

            if Util.is_max_bound(self.assert_spec):
                samples = [np.max(k) for k in samples]
            elif Util.is_min_bound(self.assert_spec):
                samples = [-np.min(k) for k in samples]
            compareDist = CompareDistribution(None,
                                              samples,
                                              [extracted_outputs[i][evi] for i in range(len(extracted_outputs)) if
                                               parse_errors[i] == 0],
                                              self.assert_spec,
                                              dist_type=None,
                                              logger=self.logger)
            var = np.var(np.hstack(samples))
            if var < 1e-20:
                self.logger.logo("Delta distribution.. breaking")
                dist_names.append("delta")
                break

            ppf = compareDist.run_mbpta_cv(samples, self.config.MIN_TAIL_VALUES,
                                     self.config.BOUNDS_MAX_PERCENTILE)

            # try box cox
            if np.isinf(ppf) and self.config.USE_BOXCOX:
                is_neg = False
                is_mixed = False
                # apply boxcox
                if np.max(samples) < 0:
                    s = -np.array(samples)
                    is_neg = True
                elif np.sign(np.min(samples)) != np.sign(np.max(samples)):
                    self.logger.logo("Error, mixed set")
                    is_mixed = True
                else:
                    s = np.array(samples)

                if not is_mixed:
                    try:
                        s, l = st.boxcox(s)
                        if is_neg:
                            s = -s
                        self.logger.logo(">>Box Cox, {0}".format(l))
                        ppf_bc = compareDist.run_mbpta_cv(s, self.config.MIN_TAIL_VALUES,
                                             self.config.BOUNDS_MAX_PERCENTILE)
                        if np.isfinite(ppf_bc):
                            if is_neg:

                                ppf = -scipy.special.inv_boxcox(-ppf_bc, l)
                            else:
                                ppf = scipy.special.inv_boxcox(ppf_bc, l)
                            self.logger.logo("Works, {0}".format(ppf))
                        else:
                            self.logger.logo("Does not work")
                    except:
                        tb.print_exc()
                        self.logger.logo("Error")

                try:
                    self.logger.logo(">>Estimating bootstrap extreme")
                    lower, upper, avg, error = Util.bootstrap_CI(samples, npstat=np.max)
                    self.logger.logo("Lower: {0}, Upper: {1}".format(lower, upper))
                    self.logger.logo("CI-Mean: {0} +- {1}".format(avg, error))
                except:
                    pass

                converged = np.isfinite(ppf)
                avg_ppfs.append(ppf)
                convergences.append(converged)
                self.logger.logo("Converged: {0}".format(converged))
                if converged:
                    break

            sampling_iterations += next_batch_iterations
            next_batch_iterations = self.config.SUBSEQUENT_ITERATIONS
            self.logger.logo("Continuing to next batch...")

        self._write_report(outputs, extracted_outputs, errors, codes, convergence_scores)

        return TestRunResults(extracted_outputs=extracted_outputs,
                              parse_errors=parse_errors, distributions=distributions,
                              fit_errors=fit_errors, dist_names=dist_names, avg_ppfs=avg_ppfs, sd_ppfs=sd_ppfs,
                              convergences=convergences, estimated_ppfs=estimated_ppfs, codes=codes)

