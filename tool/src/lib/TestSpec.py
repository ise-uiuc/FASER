import hashlib

from src.lib.Param import Param


class Spec:
    def __init__(self, repo, filename, classname, testname, params, assertions, branchname=None,skip=False):
        self.repo = repo
        self.filename = filename
        self.classname = classname
        self.testname = testname
        self.params = params  # list of parameters
        self.assertions = assertions  # list of asserts
        self.skip = skip
        self.branchname = branchname

    def get_hash(self):
        s = '_'.join([self.filename, self.classname, self.testname, str(self.params[0].param_line), str(self.params[0].param_col),
                      str(self.assertions[0].line),
                      ]).encode("utf-8")
        return str(int(hashlib.sha1(s).hexdigest(), 16) % (10 ** 8))

    def _param_to_str(self, p:Param):
        return "{0},{1},{2},{3},{4}".format(p.name, p.param_line, p.param_col, p.param_type, p.param_default)

    def get_str(self):
        s="Repo: {0}\nFilename: {1}\nClassName: {2}\nTestname: {3}\nParams: {4}\nAssertion: {5}".format(self.repo,
                                                                                        self.filename,
                                                                                        self.classname,
                                                                                        self.testname,
                                                                                        '\n'.join([self._param_to_str(p) for p in self.params]),
                                                                                        self.assertions[0].assert_string)

        return s
