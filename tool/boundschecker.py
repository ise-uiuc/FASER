#!/usr/bin/env python3
import argparse
import glob
import json
import logging
import os
import shutil
import time
import subprocess as sp
from typing import List

import numpy as np

from Logger import Logger
from assertscraper import AssertScraper
from src.Config import Config
from src.TestDriver import TestDriver
from src.TestInstrumentor import TestInstrumentor
from src.Util import create_new_dir, filter_asserts, create_new_base_dir
from src.lib.AssertSpec import AssertSpec
from src.lib.AssertType import AssertType
from src.lib.TestRunResults import TestRunResults
from mutmut_wrapper import generate_mutations, get_unified_diff
from testspecs import testspecs

import csv


def _run_coverage(assert_spec, condaenvname, libdir):
    try:
        result = sp.run(['{4}/tool/src/runcoverage.sh {0} {1} {2} {3}'.format(
            assert_spec.test.filename,
            assert_spec.test.classname,
            assert_spec.test.testname,
            condaenvname,
            libdir,
        )],
            shell=True, stdout=sp.PIPE, stderr=sp.PIPE, timeout=500)
    except sp.TimeoutExpired as te:
        return te.output, te.stderr, -111
    return result.stdout, result.stderr, result.returncode


def _get_coverage_output(assert_spec, condaenvname, libdir):
    try:
        result = sp.run(['{2}/tool/src/getcoverage.sh {0} {1}'.format(
            assert_spec.test.filename,
            condaenvname,
            libdir,
        )],
            shell=True, stdout=sp.PIPE, stderr=sp.PIPE, timeout=500)
    except sp.TimeoutExpired as te:
        return te.output, te.stderr, -111
    return result.stdout, result.stderr, result.returncode


def _filter_file_path_for_coverage_for_mutation(file_path):
    file_name = file_path.split("/")[-1]

    if file_name == '__init__.py':
        return False

    if "test" in file_path.split("/") or "tests" in file_path.split("/"):
        return False

    if "test" in file_name.split(".")[0]:
        return False

    return True


def get_test_coverage(spec, condaenvname, libdir):
    # Run test and generate coverage information
    _, __, returncode = _run_coverage(spec, conda_env, libdir)
    assert (returncode == 0)  # check that at least it is successful
    out, error, returncode = _get_coverage_output(spec, conda_env, libdir)
    # print(out)
    # print(error)
    assert (returncode == 0)

    # Load coverage info
    with open("../projects/" + condaenvname + "/coverage.json") as f:
        r = json.load(f)

    coverage_for_mutation = {}
    # Filter coverage info
    for file_path, coverage_info in r['files'].items():
        if _filter_file_path_for_coverage_for_mutation(file_path) and len(coverage_info['executed_lines']) > 15:
            coverage_for_mutation["../projects/" + condaenvname + "/" + file_path] = coverage_info['executed_lines']

    return coverage_for_mutation


def run_tests(base_lib_log_dir, spec, args, run_mutation=False, mutation=None, source=None):
    assert_time_start = time.time()

    failed_asserts = 0
    restored = False

    global_start = time.time()

    if run_mutation:
        lib_log_dir = create_new_dir(base_lib_log_dir, "mutation", '_' + str(mutation[0]))
        with open(os.path.join(lib_log_dir, 'source.py'), 'w+') as s:
            s.write(mutation[1])
    else:
        lib_log_dir = create_new_dir(base_lib_log_dir, "original", "")

    lib_logger = Logger(lib_log_dir)
    lib_logger.logo("Testing library [%s]" % args.repo)
    lib_logger.logo("Rundir: %s" % lib_log_dir)
    lib_logger.logo(">>>Spec %d " % (i + 1))
    lib_logger.logo(spec.print_spec())

    if run_mutation:
        lib_logger.logo("mutation type={}".format(mutation[3]))  # mutation type
        lib_logger.logo("mutation line_number{}".format(mutation[2].line_number))
        lib_logger.logo("mutation file={}".format(mutation[2].filename))
        lib_logger.logo(get_unified_diff(source, mutation[1]))  # mutation diff

    try:
        instrumentor = TestInstrumentor(spec, logstring='log>>>', deps=args.dependencies.split(","))
        instrumentor.instrument()
        instrumentor.write_file()
        restored = False
        # samples values from test
        testdriver = TestDriver(spec,
                                parallel=True,
                                condaenvname=conda_env,
                                rundir=lib_log_dir,
                                libdir=PROJECT_DIR,
                                threads=threads,
                                config=config,
                                logger=lib_logger,
                                test_timeout=300)  # might need to adjust time out to be longer
        test_results: TestRunResults = testdriver.run_basic_test_loop()
        extracted_outputs = test_results.extracted_outputs
        parse_errors = test_results.parse_errors
        # save a copy of file and restore original file
        instrumentor.restore_file(testdriver.logdir)
        restored = True
        # actual value index
        avi = 1 if spec.reverse else 0
        # expected value index
        evi = 0 if spec.reverse else 1
        err = False
        assert_is_tight = False
        assert_time_stop = time.time()
    except Exception as e:
        import traceback
        traceback.print_exc()
        lib_logger.logo(e)
        if not restored:
            try:
                instrumentor.restore_file(testdriver.logdir)
            except:
                pass
    finally:
        assert_time_stop = time.time()
        lib_logger.logo("Assert-Time: {:.2f}s".format(assert_time_stop - assert_time_start))
        lib_logger.logo("========================================================")

    global_stop = time.time()
    lib_logger.logo("Failed asserts: {0}".format(failed_asserts))
    lib_logger.logo("Total Time: {0:.2f}s".format(global_stop - global_start))

    return test_results.codes


if __name__ == '__main__':
    filepath = os.path.abspath(os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../"))

    PROJECT_DIR = filepath

    parser = argparse.ArgumentParser(description='FASER arguments')
    parser.add_argument("-r", dest="repo")
    parser.add_argument('-cl', dest='classname', default=None)
    parser.add_argument('-test', dest='testname', default=None)
    parser.add_argument('-file', dest='filename', default=None)
    parser.add_argument('-line', dest='line', default=0, type=int)
    parser.add_argument('-conda', dest='conda_env', default=None)
    parser.add_argument('-deps', dest='dependencies', default="numpy")
    parser.add_argument('--resume', action='store_true', default=False)
    parser.add_argument('--no_mutants', action='store_true', default=False)

    args = parser.parse_args()
    print(args)

    config = Config()

    conda_env = args.conda_env
    threads = config.THREAD_COUNT

    project_log_dir = create_new_dir("{0}/tool/logs".format(PROJECT_DIR), args.repo)
    assertion_specs = []

    if args.testname is not None:
        for spec in testspecs:
            if spec.repo == args.repo and spec.testname == args.testname and spec.classname and args.filename in \
                    spec.assertions[0].test.filename:
                new_spec = spec.assertions[0]
                new_spec.test.testname = spec.testname
                new_spec.test.classname = spec.classname
                assertion_specs.append(new_spec)

        if len(assertion_specs) != 1:
            print("No assertions found")
            exit(1)
    else:
        for spec in testspecs:
            if spec.skip is not True and spec.repo == args.repo:
                new_spec = spec.assertions[0]
                new_spec.test.testname = spec.testname
                new_spec.test.classname = spec.classname
                assertion_specs.append(new_spec)

    for i, spec in enumerate(assertion_specs):
        # instrument the test
        if spec.assert_type == AssertType.ASSERTEQUAL or spec.assert_type == AssertType.ASSERT_EQUAL:
            print("...Skipping...")
            continue

        continue_from_previous = False
        last_mutation = 0
        last_mutation_remove = None
        if args.resume:
            for folder in glob.glob(project_log_dir + "/*"):
                if "_".join(folder.split("/")[-1].split("_")[:-1]) == args.repo + "_" + str(spec.test.classname) + "_" + str(
                        spec.test.testname):
                    continue_from_previous = True
                    base_lib_log_dir = folder
                    with open(os.path.join(base_lib_log_dir, "log.txt"), 'r') as f:
                        lines = f.readlines()
                        complete_mutation = False
                        for line in reversed(lines):  # read mutation in reverse
                            if '--- source' in line:
                                complete_mutation = True
                            elif "Mutation #" in line and not complete_mutation:
                                last_mutation_remove = int(line.split("Mutation #")[-1].strip())
                            elif "Mutation #" in line and complete_mutation:
                                last_mutation = int(line.split("Mutation #")[-1].strip())
                                break
                    break
        if not continue_from_previous:
            base_lib_log_dir = create_new_base_dir(project_log_dir,
                                                   args.repo + "_" + str(spec.test.classname) + "_" + str(
                                                       spec.test.testname))

            run_tests(base_lib_log_dir, spec, args, run_mutation=False)

        base_lib_logger = Logger(base_lib_log_dir)
        base_lib_logger.log(spec.print_spec())
        if not args.no_mutants:
            print("Generating Test Coverage")
            coverage_data = get_test_coverage(spec, conda_env, PROJECT_DIR)

            mutations = generate_mutations(
                coverage_data)  # only generate mutants from a list of files (part of coverage lines)
            base_lib_logger.logo("Number of generated mutants: {}".format(len(mutations)))

            crashed_assert = 0
            mutation_ran = 0

            for index, mutation in enumerate(mutations):
                if index <= last_mutation and continue_from_previous:
                    mutation_ran += 1
                    continue
                if continue_from_previous and last_mutation_remove is not None and index == last_mutation_remove:
                    sp.run("rm -rf " + base_lib_log_dir + "/mutation_" + str(mutation[0]), shell=True)

                base_lib_logger.logo("Mutation #{}".format(str(index)))

                with open(mutation[2].filename) as f:
                    source = f.read()

                # backup original file
                shutil.copy(mutation[2].filename,
                            mutation[2].filename + ".bak")
                # write new file
                with open(mutation[2].filename, 'w') as file:
                    file.write(mutation[1])

                codes = run_tests(base_lib_log_dir, spec, args, run_mutation=True, mutation=mutation, source=source)

                # Restore original file
                shutil.move(mutation[2].filename +
                            ".bak", mutation[2].filename)

                if 2 in codes:
                    crashed_assert += 1
                mutation_ran += 1

                base_lib_logger.logo(mutation[3])
                base_lib_logger.logo(get_unified_diff(source, mutation[1]))

            base_lib_logger.logo("Total Mutation Ran: {}, Crashed Mutants: {}".format(mutation_ran, crashed_assert))
