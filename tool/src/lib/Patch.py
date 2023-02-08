import ast
from typing import Any

import astunparse
import numpy as np
from diff_match_patch import diff_match_patch

from src import Util
from src.lib.AssertSpec import AssertSpec
from src.lib.Diff import Diff


class AssertReplacer(ast.NodeTransformer):
    def __init__(self, spec: AssertSpec, bound):
        self.spec = spec
        self.bound = bound
        self.modified = False
        self.modified_assert_string = ""

    def replace(self, file):
        fileast = ast.parse(open(file, encoding='utf-8').read())
        modified = self.visit(fileast)
        modified = ast.fix_missing_locations(modified)
        return astunparse.unparse(modified)

    def create_num_node(self, val):
        return ast.Num(n=val)

    def replace_threshold(self, node):
        if isinstance(node, ast.Compare) \
                and isinstance(node.ops[0], (ast.LtE, ast.Lt, ast.Gt, ast.GtE)) \
                and len(node.comparators) == 1 \
                and Util.is_numerical_value(node.comparators[0]):  # only handling the case with single comparator operator
            node.comparators[0] = self.create_num_node(self.bound)
            return node
        elif isinstance(node, ast.Compare) \
                and isinstance(node.ops[0], (ast.LtE, ast.Lt, ast.Gt, ast.GtE)) \
                and len(node.comparators) == 1 \
                and Util.is_numerical_value(node.left):  # only handling the case with single comparator operator
            node.left = self.create_num_node(self.bound)
            return node
        else:
            print("Not handled : ", ast.dump(node))
            return node

    def _get_replacement_node(self, node):
        return " "*node.col_offset + astunparse.unparse(node).strip()

    def visit_Assert(self, node: ast.Assert) -> Any:
        if node.lineno == self.spec.line:
            node.test = self.replace_threshold(node.test)
            self.modified_assert_string = self._get_replacement_node(node)
            return node
        self.generic_visit(node)
        return node

    def visit_Call(self, node: ast.Call) -> Any:
        if node.lineno == self.spec.line:
            func_name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            if func_name in ['assertTrue', 'assertFalse']:
                if isinstance(node.args[0], ast.Compare):
                    node.args[0] = self.replace_threshold(node.args[0])
                    self.modified_assert_string = self._get_replacement_node(node)
                    return node
                else:
                    print("Not handled: {0}".format(astunparse.unparse(node)))

            elif func_name in ['assertGreater', 'assertGreaterEqual', 'assertLessEqual', 'assertLess']:
                if Util.is_numerical_value(node.args[1]):
                    node.args[1] = self.create_num_node(self.bound)
                    self.modified = True
                    self.modified_assert_string = self._get_replacement_node(node)
                    return node
                elif Util.is_numerical_value(node.args[0]):
                    node.args[0] = self.create_num_node(self.bound)
                    self.modified = True
                    self.modified_assert_string = self._get_replacement_node(node)
                    return node
                else:
                    print("No location found")
            # decimal/significant
            elif func_name in ["assert_almost_equal", "assert_approx_equal", "assert_array_almost_equal"]:
                if np.abs(self.bound) > 0:
                    decimal = abs(int(np.log10(np.abs(self.bound/1.5))))
                else:
                    # this means the difference is almost 0
                    # keeping it default 7 for now
                    decimal = 7
                print("Decimal: {0}".format(decimal))
                args_new = list()
                args_new.append(node.args[0])
                args_new.append(node.args[1])
                args_new.append(ast.Num(n=decimal))
                node.args=args_new
                keyword_args = list()
                for k in node.keywords:
                    if k.arg == 'decimal' or k.arg == 'significant':
                        continue
                    keyword_args.append(k)
                node.keywords = keyword_args

                self.modified = True
                self.modified_assert_string = self._get_replacement_node(node)
                return node

            # rtol/atol
            elif func_name in ["assert_allclose", "assertAllClose"]:
                # assuming only rtol is present
                print("Rtol: {0}".format(self.bound))
                args_new = list()
                args_new.append(node.args[0])
                args_new.append(node.args[1])
                args_new.append(ast.Num(n=self.bound))
                keyword_args = list()
                for k in node.keywords:
                    if k.arg == 'rtol':
                        continue
                    keyword_args.append(k)

                node.args = args_new
                node.keywords=keyword_args
                self.modified = True
                self.modified_assert_string = self._get_replacement_node(node)
                pass
            elif func_name in ["assert_array_less"]:
                print("Array Less bound: {0}".format(self.bound))
                args_new = list()
                if Util.is_numerical_value(node.args[0]):
                    args_new.append(ast.Num(n=self.bound))
                    args_new.append(node.args[1])
                else:
                    args_new.append(node.args[0])
                    args_new.append(ast.Num(n=self.bound))
                node.args = args_new
                self.modified = True
                self.modified_assert_string = self._get_replacement_node(node)
        self.generic_visit(node)
        return node

class Patch:
    def __init__(self, bound, spec: AssertSpec, extracted_outputs):
        self.bound = bound
        self.spec = spec
        self.extracted_outputs = extracted_outputs

    def get_diff(self):
        assert_file = self.spec.test.filename if self.spec.base_assert is None else self.spec.base_assert.test.filename

        assert_replacer = AssertReplacer(self.spec, self.bound)
        modified_file = assert_replacer.replace(assert_file)
        original_assert = open(assert_file, encoding='utf-8').readline(self.spec.line-1).replace("\n", "")
        new_assert = assert_replacer.modified_assert_string
        diff = Diff(assert_file,
                    self.spec.line, self.spec.end_line, new_assert)
        #diff = self.get_patch(open(self.spec.test.filename).readline(self.spec.line-1), assert_replacer.modified_assert_string)
        #diff = self.get_patch(astunparse.unparse(ast.parse(open(self.spec.test.filename).read())), modified_file)
        return diff, modified_file

    def get_patch(self, t1, t2):
        dmp = diff_match_patch()
        patches = dmp.patch_make(t1, t2)
        diff = dmp.patch_toText(patches)
        return diff