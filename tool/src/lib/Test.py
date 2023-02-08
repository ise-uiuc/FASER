class Test:
    def __init__(self, filename, classname, testname):
        self.filename = filename
        self.classname = classname
        self.testname = testname

    def get_test_str(self) -> str:
        return "{0}::{1}::{2}".format(self.filename, self.classname, self.testname)