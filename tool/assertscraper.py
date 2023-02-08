import ast
import glob
import logging
import os

import astunparse

from src import Util
from src.lib.AssertSpec import AssertSpec
from src.lib.AssertType import AssertType
from src.lib.Test import Test

filepath = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../"))

PROJECT_DIR = filepath

class MyVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, classname: str, funcname: str, asserts: list, class_mapping: dict,
                 assert_strings: list, loglevel=logging.ERROR, allow_non_numeric_args=False):
        self.count = 0
        self.filename = filename
        self.classname = classname
        self.funcname = funcname
        self.asserts = asserts
        self.class_mapping = class_mapping
        self.assert_strings = assert_strings
        self.logger = logging.Logger("Assert Logger")
        self.logger.setLevel(loglevel)
        self.allow_non_numeric_args = allow_non_numeric_args

    def _log(self, *args):
        self.logger.log(logging.DEBUG, " ".join(args))

    def _add_assert(self, node, reverse=False):
        assert_name = None
        args=[]
        if isinstance(node, ast.Call):
            assert_name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            if len(node.args) > 2:
                args = node.args[2:]  # save the extra arguments\
            elif len(node.keywords) > 0:
                args = node.keywords
        elif isinstance(node, ast.Assert):
            assert_name = 'assert'
        else:
            print("Unknown assert : %s" % astunparse.unparse(node).strip())
            return
        end_line = self._get_end_line(node)
        end_line = node.lineno if end_line == -1 else end_line
        assert_spec = AssertSpec(Test(self.filename, self.classname, self.funcname),
                                 line=node.lineno,
                                 end_line=end_line,
                                 col_offset=node.col_offset,
                                 assert_type=AssertType.get_assert_type(assert_name),
                                 assert_string=astunparse.unparse(node).strip(),
                                 args=args,
                                 reverse=reverse)
        if self.filename not in  self.class_mapping:
            self.class_mapping[self.filename] = dict()
        if self.classname not in  self.class_mapping[self.filename]:
            self.class_mapping[self.filename][self.classname] = []

        assert_str = assert_spec.get_uniq_str()
        if assert_str in self.assert_strings:
            #print("Duplicate " + assert_str)
            return
        self.class_mapping[self.filename][self.classname].append(assert_spec)
        self.asserts.append(assert_spec)
        self.assert_strings.append(assert_spec.get_uniq_str())

    def _get_end_line(self, node):
        if hasattr(node, 'parent'):
            ind = -1
            parent = node.parent
            children = list(ast.iter_child_nodes(parent))
            #if hasattr(parent, 'body'):
            for i, n in enumerate(children):
                if n == node:
                    ind = i
                    break
            if ind == -1:
                print("Node not found")
            elif ind < len(children) - 1:
                if hasattr(children[ind+1], 'lineno'):
                    return children[ind+1].lineno - 1
                else:
                    return self._get_end_line(parent)
            else:
                return self._get_end_line(parent)

        return -1

    def visit_Assert(self, node):
        self._log(">>", astunparse.unparse(node).strip())
        self.get_threshold(node.test, node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ['assertTrue', 'assertFalse']:
                self._log(">>", astunparse.unparse(node).strip())
                if isinstance(node.args[0], ast.Compare):
                    self.get_threshold(node.args[0], node)
                else:
                    self._log("Not handled:", astunparse.unparse(node).strip())

            elif node.func.attr in ['assertGreater', 'assertGreaterEqual', 'assertLessEqual', 'assertLess', 'assertAlmostEqual', 'assertNotAlmostEqual']:
                self._log(">>", astunparse.unparse(node).strip())
                if self._is_fp_value(node.args[1]):
                    self._log(node.func.attr + ':' + astunparse.unparse(node.args[1]).strip())
                    self._add_assert(node)  # call node
                    self.count += 1
                elif self._is_fp_value(node.args[0]):
                    self._log(node.func.attr + ':' + astunparse.unparse(node.args[0]).strip())
                    self._add_assert(node, reverse=True)  # call node
                    self.count += 1
                else:
                    self._log("Not handled:", astunparse.unparse(node).strip())
            elif node.func.attr in ['assert_almost_equal', 'assert_approx_equal', 'assert_array_almost_equal',
                                    'assert_allclose', 'assert_array_almost_equal_nulp', 'assert_array_max_ulp',
                                   'assert_array_less', 'assert_equal']:
                # numpy asserts
                self._log(">>", astunparse.unparse(node).strip())
                # check if we want to consider comparison to a constant? capture atol, rtol or decimal arguments
                if Util.is_numerical_value(node.args[0]):
                    self._add_assert(node, reverse=True)
                else:
                    self._add_assert(node)
                self.count+=1
            elif node.func.attr in ['assertAllClose']:
                self._log(">>", astunparse.unparse(node).strip())
                if Util.is_numerical_value(node.args[0]):
                    self._add_assert(node, reverse=True)
                else:
                    self._add_assert(node)
                self.count += 1

        elif isinstance(node.func, ast.Name):
            if node.func.id in ['assertTrue', 'assertFalse']:
                self._log(">>", astunparse.unparse(node).strip())
                if isinstance(node.args[0], ast.Compare):
                    self.get_threshold(node.args[0], node)
                else:
                    self._log("Not handled:", astunparse.unparse(node).strip())
            elif node.func.id in ['assertGreater', 'assertGreaterEqual', 'assertLessEqual', 'assertLess', 'assertAlmostEqual', 'assertNotAlmostEqual']:
                self._log(">>", astunparse.unparse(node).strip())
                if self._is_fp_value(node.args[1]):
                    self._log(node.func.id + ':' + astunparse.unparse(node.args[1]).strip())
                    self._add_assert(node)  # call node
                    self.count += 1
                elif self._is_fp_value(node.args[0]):
                    self._log(node.func.attr + ':' + astunparse.unparse(node.args[0]).strip())
                    self._add_assert(node, reverse=True)  # call node
                    self.count += 1
                else:
                    self._log("Not handled:", astunparse.unparse(node).strip())
            elif node.func.id in ['assert_almost_equal', 'assert_approx_equal', 'assert_array_almost_equal',
                                    'assert_allclose', 'assert_array_almost_equal_nulp', 'assert_array_max_ulp',
                                    'assert_array_less', 'assert_equal']:
                # numpy asserts
                self._log(">>", astunparse.unparse(node).strip())
                # check if we want to consider comparison to a constant? capture atol, rtol or decimal arguments
                if Util.is_numerical_value(node.args[0]):
                    self._add_assert(node, reverse=True)
                else:
                    self._add_assert(node)
                self.count += 1
            elif node.func.id in ['assertAllClose']:
                self._log(">>", astunparse.unparse(node).strip())
                if Util.is_numerical_value(node.args[0]):
                    self._add_assert(node, reverse=True)
                else:
                    self._add_assert(node)
                self.count += 1

        self.generic_visit(node)

    def _is_fp_value(self, node):
        if self.allow_non_numeric_args:
            return True
        if isinstance(node, ast.Num):
            return True
        if isinstance(node, ast.UnaryOp) and isinstance(node.operand, ast.Num):
            return True

    def get_threshold(self, node, parent_node):
        if isinstance(node, ast.Compare) \
                and isinstance(node.ops[0], (ast.LtE, ast.Lt, ast.Gt, ast.GtE))\
                and len(node.comparators) == 1\
                and self._is_fp_value(node.comparators[0]):  # only handling the case with single comparator operator
            self._log(astunparse.unparse(node.comparators[0]).strip())
            self._add_assert(parent_node)
            self.count += 1
        elif isinstance(node, ast.Compare) \
                and isinstance(node.ops[0], (ast.LtE, ast.Lt, ast.Gt, ast.GtE)) \
                and len(node.comparators) == 1\
                and self._is_fp_value(node.left):  # only handling the case with single comparator operator
            self._log(astunparse.unparse(node.left).strip())
            self._add_assert(parent_node, reverse=True)
            self.count += 1
        else:
            self._log("Not handled : ", ast.dump(node))


class AssertScraper:
    def __init__(self, library_dir, libraryname, loglevel=logging.ERROR, allow_non_numeric_args=False):
        self.testfiles = glob.glob("{0}/**/*.py".format(library_dir) if not library_dir.endswith(".py") else library_dir, recursive=True)
        self.assertcount = 0
        self.markedflaky = 0
        self.testnames = []
        self.asserts = list()
        self.assert_strings = list()
        self.class_mapping = dict()
        self.loglevel=loglevel
        self.libraryname=libraryname
        self.allow_non_numeric_args=allow_non_numeric_args
        print(library_dir)

    @staticmethod
    def _has_flaky_annotation(decorator_list):
        for dec in decorator_list:
            if isinstance(dec, ast.Name):
                if 'flaky' in dec.id:
                    return True
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    if 'flaky' in dec.func.id:
                        return True
        return False

    @staticmethod
    def _is_skipped(decorator_list):
        for dec in decorator_list:
            s=astunparse.unparse(dec).strip()
            if 'skip' in s:
                return True

        return False

    @staticmethod
    def _is_parameterized(decorator_list):
        for dec in decorator_list:
            s=astunparse.unparse(dec).strip()            
            if 'parametrize' in s:
                return True

        return False

    @staticmethod
    def _valid_class(classDef):
        if classDef.name.startswith('_'):
            return False
        return True

    def _get_base_class_asserts(self, baseclassname):
        for tf in self.class_mapping:
            if baseclassname in self.class_mapping[tf]:
                return self.class_mapping[tf][baseclassname]
        return []

    def _create_sub_class_asserts(self, subclassname, filename, base_class_asserts):
        for a in base_class_asserts:
            assert_spec = AssertSpec(Test(filename, subclassname, a.test.testname),
                                     line=a.line,
                                     end_line=a.end_line,
                                     col_offset=a.col_offset,
                                     assert_type=a.assert_type,
                                     assert_string=a.assert_string,
                                     args=a.args,
                                     base_assert=a)
            self.assertcount+=1
            # print("Found assert in child ", assert_spec.print_spec())
            self.asserts.append(assert_spec)

    def filter_by_type(self, assert_types: list):
        res=[]
        for a in self.asserts:
            if 'numpy' in assert_types and AssertType.is_numpy_assert(a):
                res.append(a)
            elif 'python' in assert_types and AssertType.is_python_assert(a):
                res.append(a)
            elif 'unittest' in assert_types and AssertType.is_unittest_assert(a):
                res.append(a)
            elif 'tf' in assert_types and AssertType.is_tf_assert(a):
                res.append(a)
        self.asserts = res
        print("Filtered asserts: %s" % len(self.asserts))

    def parse_test_files(self):
        allclasses=[]
        for tf in self.testfiles:
            with open(tf, encoding='utf-8') as file:
                try:
                    a = ast.parse(file.read())
                except:
                    # ignoring files which cannot be parsed
                    #tb.print_exc()
                    #print(tf)
                    continue
                # annotate tree by linking the parents
                Util.annotate_tree(a)
                classes = [n for n in a.body if isinstance(n, ast.ClassDef)]
                # print("Filename: %s" % tf)
                for c in classes:
                    if not self._valid_class(c):
                        continue
                    class_decorators = c.decorator_list
                    if self._is_skipped(class_decorators):
                        continue
                    allclasses.append((tf, c))
                    functions = [n for n in c.body if isinstance(n, ast.FunctionDef)]
                    for f in functions:
                        if self._is_skipped(f.decorator_list):
                            continue
                        if self._is_parameterized(f.decorator_list):
                            continue
                        if f.name.lower().startswith("test"):
                            funcObj = dict()
                            funcObj['class'] = c.name
                            funcObj['name'] = f.name
                            funcObj['isflaky'] = self._has_flaky_annotation(c.decorator_list) or self._has_flaky_annotation(
                                f.decorator_list)
                            self.markedflaky += funcObj['isflaky']
                            funcObj['filename'] = tf
                            self.testnames.append(funcObj)
                            visitor = MyVisitor(tf, c.name, f.name, self.asserts, class_mapping=self.class_mapping,
                                                assert_strings=self.assert_strings, loglevel=self.loglevel,
                                                allow_non_numeric_args=self.allow_non_numeric_args)
                            visitor.visit(f)
                            self.assertcount += visitor.count

                filefunctions = [n for n in a.body if isinstance(n, ast.FunctionDef)]
                for f in filefunctions:
                    if self._is_skipped(f.decorator_list):
                        continue
                    if self._is_parameterized(f.decorator_list):
                        continue
                    if f.name.lower().startswith("test"):
                        funcObj = dict()
                        funcObj['class'] = "none"
                        funcObj['name'] = f.name
                        funcObj['isflaky'] = self._has_flaky_annotation(f.decorator_list)
                        self.markedflaky += funcObj['isflaky']
                        funcObj['filename'] = tf
                        self.testnames.append(funcObj)
                        visitor = MyVisitor(tf, "none", f.name, self.asserts, class_mapping=self.class_mapping,
                                            assert_strings=self.assert_strings,
                                            loglevel=self.loglevel,
                                            allow_non_numeric_args=self.allow_non_numeric_args)
                        visitor.visit(f)
                        self.assertcount += visitor.count

        #self.asserts=[]
        #self.assertcount=0
        # look for sub-classes of all classes
        for tf,c in allclasses:
            if len(c.bases) > 0:
                for base in c.bases:
                    cname = Util.get_name(base)
                    baseclassasserts = self._get_base_class_asserts(cname)
                    if len(baseclassasserts)>0:
                        self._create_sub_class_asserts(c.name, tf, baseclassasserts)

        print("Asserts found %d" % self.assertcount)

    def filter_asserts(self):
        with open("{0}/tool/test_logs/{1}.txt".format(PROJECT_DIR, self.libraryname), encoding='utf-8') as ff:
            tests=ff.read()
        #tests=list(filter(lambda t: "::" in t, tests))
        finalasserts=[]
        for a in self.asserts:
            if a.test.classname != "none":
                testname = a.test.filename.split("/")[-1]+"::" + a.test.classname + "::" + a.test.testname
            else:
                testname = a.test.filename.split("/")[-1]+"::" + a.test.testname
            if testname in tests:
                finalasserts.append(a)

        print("Filtered Asserts :%d" % len(finalasserts))
        self.asserts = finalasserts
        self.assertcount = len(finalasserts)
    
def fetchassert(function: ast.FunctionDef):
    function_body = function.body
    print("Function name: %s" % function.name)
    for stmt in function.body:
        if isinstance(stmt, ast.Assert):
            print(astunparse.unparse(stmt).strip())
            if isinstance(stmt.test, ast.Compare):
                print(stmt.test.ops)
                if isinstance(stmt.test.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                    print(stmt.test.left)
                    print(stmt.test.comparators)
                    # assuming only one comparison
                    if isinstance(stmt.test.comparators[0], ast.Num):
                        print("Compare with constant: ", stmt.test.comparators[0])
                elif isinstance(stmt.test.ops[0], ast.LtE):
                    print(stmt.test.left)
                    print(stmt.test.comparators)
                    if isinstance(stmt.test.comparators[0], ast.Num):
                        print("Compare with constant: ", stmt.test.comparators[0])
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            if isinstance(stmt.value.func, ast.Attribute):
                print(">>>", stmt.value.func.attr)
                # if stmt.value.func.attr == 'assertAllClose':

                for arg in stmt.value.args:
                    print("arg:", astunparse.unparse(arg).strip())
            else:
                # check if needed
                # print("<<<<",astunparse.unparse(stmt.value.func))
                pass


