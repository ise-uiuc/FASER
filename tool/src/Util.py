import ast
import os
import datetime
import shutil
from typing import List

import astunparse

from src.lib.AssertSpec import AssertSpec
from src.lib.AssertType import AssertType
import numpy as np


def create_new_dir(basedir: str, prefix='', suffix='') -> str:
    # dirname = str(int((datetime.datetime.now() - datetime.datetime.utcfromtimestamp(0)).total_seconds()))
    newdir = os.path.join(basedir, prefix + suffix)
    if not os.path.exists(newdir):
        os.makedirs(newdir)
    return newdir

def create_new_base_dir(basedir: str, name) -> str:
    newdir = os.path.join(basedir, name+"_"+str(int((datetime.datetime.now() - datetime.datetime.utcfromtimestamp(0)).total_seconds())))
    os.makedirs(newdir)
    return newdir

def getdims(array):
    dims = 0
    if isinstance(array, (np.ndarray, list)):
        dims += 1
        dims = dims + getdims(array[0])
    return dims


def compute_diff(x, y):
    if isinstance(x, (list, np.ndarray)) and len(x) == 0 and isinstance(y, (list, np.ndarray)) and len(y) == 0:
        return 0
    if isinstance(x, (list, np.ndarray)) and len(x) == 0:
        return np.abs(y)
    if isinstance(y, (list, np.ndarray)) and len(y) == 0:
        return np.abs(x)

    if isinstance(x, (list, np.ndarray)) and isinstance(y, (list, np.ndarray)):
        diffs = np.abs([compute_diff(xx, yy) for xx, yy in zip(x, y)])
    elif isinstance(x, (list, np.ndarray)):
        diffs = np.abs([compute_diff(xx, y) for xx in x])
    elif isinstance(y, (list, np.ndarray)):
        diffs = np.abs([compute_diff(x, yy) for yy in y])
    else:
        diffs = [abs(x - y)]

    return np.abs(diffs)


def relative_error(x, y, atol=0):
    error = abs(x - y)
    if y == 0:
        return np.inf
    rel_error = abs(error - atol) / abs(y)
    return rel_error


def compute_rel_diff(x, y):
    if isinstance(x, (list, np.ndarray)) and len(x) == 0 and isinstance(y, (list, np.ndarray)) and len(y) == 0:
        return 0
    if isinstance(x, (list, np.ndarray)) and len(x) == 0:
        return np.max(np.abs(y))
    if isinstance(y, (list, np.ndarray)) and len(y) == 0:
        return np.max(np.abs(x))

    if isinstance(x, (list, np.ndarray)) and isinstance(y, (list, np.ndarray)):
        diffs = np.max([compute_rel_diff(xx, yy) for xx, yy in zip(x, y)])
    elif isinstance(x, (list, np.ndarray)):
        diffs = np.max([compute_rel_diff(xx, y) for xx in x])
    elif isinstance(y, (list, np.ndarray)):
        diffs = np.max([compute_rel_diff(x, yy) for yy in y])
    else:
        diffs = np.max([relative_error(x, y)])

    return np.max(diffs)


def compute_max_diff(x, y):
    if isinstance(x, (list, np.ndarray)) and len(x) == 0 and isinstance(y, (list, np.ndarray)) and len(y) == 0:
        return 0
    if isinstance(x, (list, np.ndarray)) and len(x) == 0:
        return np.max(np.abs(y))
    if isinstance(y, (list, np.ndarray)) and len(y) == 0:
        return np.max(np.abs(x))

    if isinstance(x, (list, np.ndarray)) and isinstance(y, (list, np.ndarray)):

        diffs = np.max(np.abs([compute_max_diff(xx, yy) for xx, yy in zip(x, y)]))
    elif isinstance(x, (list, np.ndarray)):
        diffs = np.max(np.abs([compute_max_diff(xx, y) for xx in x]))
    elif isinstance(y, (list, np.ndarray)):
        diffs = np.max(np.abs([compute_max_diff(x, yy) for yy in y]))
    else:
        diffs = np.max([abs(x - y)])

    return np.max(np.abs(diffs))


# assuming samples are tuples
def samples_stat(samples, assertSpec: AssertSpec):
    actual = [s[0] for s in samples]
    expected = [s[1] for s in samples]
    try:
        output = "Assert: {4}\nStats::\nActual:: min: {0}, max: {1}\nExpected:: min: {2}, max: {3}\n".format(
            np.min(actual), np.max(actual), np.min(expected), np.max(expected), assertSpec.print_spec())
    except ValueError:
        return "Empty array"
    return output


def sample_to_str(s):
    if isinstance(s, list) or isinstance(s, np.ndarray):
        return "[{0}]".format(','.join([sample_to_str(i) for i in s]))
    elif isinstance(s, np.ndarray):
        return np.array2string(s, max_line_width=np.inf,
                               separator=',',
                               threshold=np.inf).replace('\n', '')
    else:
        return str(s)


def flatten(i):
    if isinstance(i, (list, np.ndarray)):
        return np.hstack([flatten(x) for x in i])
    if isinstance(i, (int, float)):
        return i
    print(i)
    assert False


def get_name(node):
    if isinstance(node, ast.Attribute):
        return get_name(node.attr)
    if isinstance(node, ast.Subscript):
        return get_name(node.value)
    if isinstance(node, ast.Call):
        return ""
    if isinstance(node, ast.Name):
        return node.id
    assert isinstance(node, str), "type: %s" % type(node)
    return node  # should be str


def save_temp(source, target):
    shutil.copy(source, target)


def restore(source, target):
    shutil.move(source, target)


# check if a node is a constant value/array
def is_numerical_value(node):
    s = astunparse.unparse(node).strip()
    try:
        parsed_node = ast.literal_eval(s)
        np.array(parsed_node)
        return True
    except:
        return False


def is_max_bound(assert_spec_or_type, assert_str=None):
    if isinstance(assert_spec_or_type, AssertSpec):
        assert_type = assert_spec_or_type.assert_type
        assert_str = assert_spec_or_type.assert_string
        reverse = assert_spec_or_type.reverse
    else:
        assert_type = assert_spec_or_type
        reverse = False

    if assert_type in [AssertType.ASSERTLESS, AssertType.ASSERTLESSEQUAL, AssertType.ASSERT_ARRAY_LESS] and not reverse:
        return True
    elif assert_type in [AssertType.ASSERT_ALLCLOSE, AssertType.PYRO_ASSERT_EQUAL, AssertType.TF_ASSERT_ALL_CLOSE
                         ]:
        return True
    elif assert_type in [AssertType.ASSERTTRUE, AssertType.ASSERTFALSE, AssertType.ASSERT] \
            and '<' in assert_str \
            and not reverse:
        return True
    elif assert_type in [AssertType.ASSERTTRUE, AssertType.ASSERTFALSE, AssertType.ASSERT] \
            and '>' in assert_str \
            and reverse:
        return True
    elif assert_type in [AssertType.ASSERTGREATER, AssertType.ASSERTGREATEREQUAL] and reverse:
        return True
        # significant/decimal/places
    elif assert_type in [AssertType.ASSERT_ARRAY_ALMOST_EQUAL, AssertType.ASSERT_APPROX_EQUAL,
                         AssertType.ASSERT_ALMOST_EQUAL, AssertType.ASSERTALMOSTEQUAL]:
        return True
    else:
        return False


def is_min_bound(assert_spec):
    assert_type = assert_spec.assert_type
    assert_str = assert_spec.assert_string
    if assert_type in [AssertType.ASSERTLESS, AssertType.ASSERTLESSEQUAL,
                       AssertType.ASSERT_ARRAY_LESS] and assert_spec.reverse:
        return True
    elif assert_type in [AssertType.ASSERTTRUE, AssertType.ASSERTFALSE, AssertType.ASSERT] \
            and '<' in assert_str and assert_spec.reverse:
        return True
    elif assert_type in [AssertType.ASSERTGREATER, AssertType.ASSERTGREATEREQUAL] and not assert_spec.reverse:
        return True
    elif assert_type in [AssertType.ASSERTTRUE, AssertType.ASSERTFALSE,
                         AssertType.ASSERT] and '>' in assert_str and not assert_spec.reverse:
        return True

    else:
        return False


def is_places_or_decimal(assert_spec_or_type):
    if isinstance(assert_spec_or_type, AssertSpec):
        assert_type = assert_spec_or_type.assert_type
    else:
        assert_type = assert_spec_or_type
    return assert_type in [AssertType.ASSERT_ALMOST_EQUAL, AssertType.ASSERTALMOSTEQUAL,
                           AssertType.ASSERT_APPROX_EQUAL,
                           AssertType.ASSERT_ARRAY_ALMOST_EQUAL]


def get_ppf(assert_spec, percentile, dist):
    return dist


def annotate_tree(node):
    if node is None:
        return
    for n in ast.iter_child_nodes(node):
        n.parent = node
        annotate_tree(n)


def check_fit_window(fit_error_changes, threshold, window_size):
    if len(fit_error_changes) < window_size:
        return False
    for i in range(window_size):
        if fit_error_changes[-i] > threshold:
            return False
    return True


def filter_asserts(asserts: List[AssertSpec], classname=None, testname=None, filename=None, lineno=None):
    filtered = []
    for a in asserts:
        if classname is not None and classname.lower() != 'none':
            if a.test.classname != classname:
                continue
        if testname is not None:
            if a.test.testname != testname:
                continue
        if filename is not None:
            if filename not in a.test.filename:
                continue
        if lineno > 0:
            if lineno != a.line:
                continue
        filtered.append(a)
    return filtered


def bootstrap_CI(samples, npstat=np.min, alpha=0.95, resamples=1000, resample_ratio=0.5):
    stats = []
    for i in range(resamples):
        size = int(len(samples) * resample_ratio)
        bt_samples = np.random.choice(samples, size=size, replace=True)
        stats.append(npstat(bt_samples))
    ordered = np.sort(stats)
    lower = np.percentile(ordered, 100 * ((1 - alpha) / 2))
    upper = np.percentile(ordered, 100 * (alpha + ((1 - alpha) / 2)))
    return lower, upper, np.mean(ordered), (upper - lower) / 2
