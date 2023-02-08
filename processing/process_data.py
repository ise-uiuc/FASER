import ast
import glob
import csv

from scipy import stats
import numpy as np


def flatten(list_of_lists):
    if len(list_of_lists) == 0:
        return list_of_lists
    if isinstance(list_of_lists[0], list):
        return flatten(list_of_lists[0]) + flatten(list_of_lists[1:])
    return list_of_lists[:1] + flatten(list_of_lists[1:])


def read_mutant_operation_and_line(file):
    mutation_type = ""
    mutated_line = ""
    new_line = ""
    mutation_line_file = ""
    with open(file, 'r', encoding="utf8") as f:
        lines = f.readlines()

    for index, line in enumerate(lines):

        if 'Reverse :' in line.strip():
            assert (lines[index + 5].strip() == '--- source')
            mutation_type = lines[index + 2].strip().split("=")[-1]
            mutation_line_file = lines[index + 4].strip().split("/")[-1] + "_" + lines[index + 3].strip().split("line_number")[-1]
        elif len(line) > 3 and line[0] == '-' and line[1] != '-':
            mutated_line = line[1:].strip()
            assert (mutation_type != "")
        elif len(line) > 3 and line[0] == '+' and line[1] != '+':
            new_line = line[1:].strip()
            assert (mutated_line != "")

            return mutation_line_file, mutation_type, mutated_line, new_line

    assert False


class DataFolder(object):
    def __init__(self, folder, ks_pthreshold=0.01):
        # copy
        self.folder = folder
        self.ks_pthreshold = ks_pthreshold
        self.log_crash_length = 14
        self.log_success_length = 110
        self.log_data_start_line = 10

        # calculation
        self.lessthan = True
        self.assert_abs_difference = False
        self.assert_all_close = False
        self.pass_equal = False

        with open(self.folder+"original/log.txt", 'r') as f:
            t_line = f.readlines()
        self.filename = t_line[4].split("File: ")[-1].strip()
        self.classname = t_line[5].split("Class:")[-1].strip()
        self.testname = t_line[6].split("Test: ")[-1].strip()
        print("\n>>>>> Beginning process Class: {} Test: {}".format(self.classname, self.testname))
        with open('test_info.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['filename'] in self.filename and row['classname'] == self.classname and row['testname'] == self.testname:
                    self.bound = float(row['bound'])
                    if row['all_close'] == 'yes':
                        self.assert_all_close = True
                        self.assert_abs_difference = True
                        self.rtol_bound = float(row['rtol_bound'])
                    if row['lessthan'] == 'no':
                        self.lessthan = False
                    if row['pass_equal'] == 'yes':
                        self.pass_equal = True
                    print("Found csv entry with bound: {}, lessthan: {}, all_close: {}, pass_equal: {}".format(self.bound, self.lessthan, self.assert_all_close, self.pass_equal))

        file = glob.glob(self.folder+"original/**/samples.txt")[0]
        if self.assert_all_close:
            ret = self._read_samples_text_file_all_close(file)
        else:
            ret = self._read_samples_text_file(file)

        self._read_original_pass_fail()
        # ret data
        self.hist_dict = {}
        self.hist_diff_dict = {}
        self.hist_diff_joint = []
        self.hist_diff_joint_ind = []
        self.hist_same_joint = []
        self.mutation_line = {}
        self.max_value = -1
        self.min_value = 100
        self.n_crashed_mutants = 0
        self.n_same_mutants = 0
        self.n_diff_mutants = 0
        self.all_log_same_value = True
        self.atom_diff_mutants = 0
        self.atom_same_mutants = 0

    def _read_original_pass_fail(self):
        num_passed_tests = -1
        file = glob.glob(self.folder + "original/log.txt")[0]
        with open(file, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if "Passed tests : " in line and int(line.split('Passed tests : ')[-1]) > 4:
                num_passed_tests = int(line.split('Passed tests : ')[-1])
        assert(num_passed_tests != -1)

    def _calculate_ks_pvalue(self, values, original_distribution):  # return True for SAME distribution
        ks_result = stats.ks_2samp(np.array(values), np.array(original_distribution))
        if ks_result.pvalue >= self.ks_pthreshold:  # cannot reject null hypothesis, two distribution are the same
            return True
        else:  # can reject null hypothesis, two distribution are different
            return False

    def _check_crashed_log(self, lines):
        assert (len(lines) >= self.log_crash_length)
        if len(lines) == self.log_crash_length:  # Crashed Mutant
            return True
        # assert (len(lines) == self.log_success_length)
        return False

    def _read_samples_text_file_all_close(self, file):
        ret = []
        with open(file, 'r') as f:
            lines = f.readlines()

        if self._check_crashed_log(lines):
            return ret

        for assert_value in lines[self.log_data_start_line:]:
            if '[' not in assert_value:  # crashed_mutant in the middle
                continue
            try:
                prod_value = flatten(ast.literal_eval(assert_value.split("::")[0]))
            except:
                print(assert_value)
                continue
            prod_value = np.array(prod_value)
            compar_value = flatten(ast.literal_eval(assert_value.split("::")[1]))
            compar_value = np.array(compar_value)
            compar_value = np.resize(compar_value, prod_value.shape[0])

            if self.assert_abs_difference:
                if compar_value.shape != prod_value.shape:
                    continue
                ret.extend(np.subtract(np.abs(np.subtract(prod_value, compar_value)), self.rtol_bound * np.abs(compar_value)))
            else:
                ret.extend(prod_value)

        return ret

    def _read_samples_text_file(self, file):
        ret = []
        with open(file, 'r') as f:
            lines = f.readlines()

        if self._check_crashed_log(lines):
            return ret

        for assert_value in lines[self.log_data_start_line:]:
            if '[' not in assert_value:  # crashed_mutant in the middle
                continue
            prod_value = assert_value.split("::")[0].split("[")[1].split("]")[0]
            compar_value = assert_value.split("::")[1].split("[")[1].split("]")[0]
            try:
                if ',' in prod_value: # retry
                    retry_value = prod_value.split(",")[0]
                    if self.assert_abs_difference:
                        ret.append(abs(float(retry_value) - float(compar_value.split(",")[0])))
                    else:
                        ret.append(float(retry_value))
                else:
                    if self.assert_abs_difference:
                        ret.append(abs(float(prod_value) - float(compar_value)))
                    else:
                        ret.append(float(prod_value))
            except:
                # print(file)
                pass

        return ret

    def process_folder(self):

        for m_folder in glob.glob(self.folder + "/*"):
            mutation_type = "original"
            mutated_line = "original"
            mutation_line_file = "original"
            new_line = "original"
            if "log.txt" in m_folder: # ignore base log file
                continue
            files = glob.glob(m_folder + "/**/samples.txt")
            assert (len(files) == 1)
            file = files[0]

            if self.assert_all_close:
                ret = self._read_samples_text_file_all_close(file)
            else:
                ret = self._read_samples_text_file(file)

            if 'original' not in m_folder:
                mutation_line_file, mutation_type, mutated_line, new_line = read_mutant_operation_and_line(m_folder + "/log.txt")

            if len(ret) > 0:
                self.hist_dict[file.split("/")[-3]] = (ret, mutation_line_file, mutation_type, mutated_line, new_line)
                if ret.count(ret[0]) != len(ret):
                    self.all_log_same_value = False
            else:
                if mutation_line_file not in self.mutation_line:
                    self.mutation_line[mutation_line_file] = []
                self.mutation_line[mutation_line_file].append((mutation_type, 'crash', mutated_line, new_line))
                self.n_crashed_mutants += 1
        for index, item in enumerate(self.hist_dict.items()):
            if not self._calculate_ks_pvalue(item[1][0], self.hist_dict['original'][0]):
                self.hist_diff_dict[item[0]] = item[1]
                self.hist_diff_joint.extend(item[1][0])
                self.hist_diff_joint_ind.append(item[1][0])
                self.n_diff_mutants += 1
                if item[1][1] not in self.mutation_line:
                    self.mutation_line[item[1][1]] = []
                self.mutation_line[item[1][1]].append((item[1][2], 'different', item[1][3], item[1][4]))
                if item[1][2] == 'atom_expr':
                    self.atom_diff_mutants += 1
                # print(item[0])
            elif item[0] != 'original':
                self.hist_same_joint.extend(item[1][0])
                self.n_same_mutants += 1
                if item[1][1] not in self.mutation_line:
                    self.mutation_line[item[1][1]] = []
                self.mutation_line[item[1][1]].append((item[1][2], 'same', item[1][3], item[1][4]))
                if item[1][2] == 'atom_expr':
                    self.atom_same_mutants += 1

            if max(item[1][0]) > self.max_value:
                self.max_value = max(item[1][0])
            if min(item[1][0]) < self.min_value:
                self.min_value = min(item[1][0])
        self.hist_diff_dict['original'] = self.hist_dict['original']
        # self.hist_diff_joint.extend(self.hist_dict['original'][0])
        print("Num of crashed mutants: {} same mutants: {} diff mutants: {}".format(self.n_crashed_mutants, self.n_same_mutants, self.n_diff_mutants))