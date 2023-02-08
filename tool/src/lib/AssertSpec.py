from src.lib.AssertType import AssertType
from src.lib.Test import Test
import hashlib
import astunparse

class AssertSpec:
    def __init__(self, test: Test, line: int, end_line: int=None, col_offset: int=-1, assert_type: AssertType=None, assert_string: str=None, args: list=[], base_assert=None, reverse=False):
        self.test = test
        self.line = line
        self.end_line = end_line if end_line is not None else self.line
        self.col_offset = col_offset
        self.assert_type = assert_type
        self.assert_string = assert_string
        self.args=args
        self.base_assert=base_assert  # only for instrumentation
        self.reverse = reverse

    def get_uniq_str(self):
        if self.test.classname == "none":
                    return "::".join([self.test.filename.split("/")[-1], self.test.testname, str(self.line), str(self.col_offset)])
        else:
                    return "::".join([self.test.filename.split("/")[-1], self.test.classname, self.test.testname, str(self.line), str(self.col_offset)])

    def print_spec(self) -> str:
        if self.base_assert is not None:
            return "Assert Spec>>\nFile: {0}\nClass: {1}\nTest: {2}\nLine: {3}\nEnd Line: {4}\nCol: {5}\nStr: {6}\nArgs: {7}\nBase: {8}\n".format(
                self.test.filename, self.test.classname, self.test.testname, self.line, self.end_line, self.col_offset,
                self.assert_string,
                [astunparse.unparse(t).strip() for t in self.args], self.base_assert.test.classname) + "Reverse : {0}\n".format(self.reverse)
        else:
            return "Assert Spec>>\nFile: {0}\nClass: {1}\nTest: {2}\nLine: {3}\nEnd Line: {4}\nCol: {5}\nStr: {6}\nArgs: {7}\n".format(
            self.test.filename, self.test.classname, self.test.testname, self.line, self.end_line, self.col_offset, self.assert_string,
            [astunparse.unparse(t).strip() for t in self.args]) + "Reverse : {0}\n".format(self.reverse)

    def get_hash(self):
        s='_'.join([self.test.filename, self.test.classname, self.test.testname, str(self.line), str(self.col_offset)]).encode("utf-8")
        return str(int(hashlib.sha1(s).hexdigest(), 16) % (10 ** 8))
