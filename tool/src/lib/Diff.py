class Diff:
    def __init__(self, filename, line, end_line, new_assert):
        self.file = filename
        self.line = line
        self.end_line = end_line
        self.new_assert = new_assert

    @staticmethod
    def read_diff(file_loc):
        lines = open(file_loc, encoding='utf-8').readlines()
        diff = Diff(lines[0][2:], int(lines[1][2:].split(",")[0]), lines[3][1:])
        return diff

    @staticmethod
    def read_and_apply_text_diff(file_loc, repo_loc, repo_name):
        diff_lines = open(file_loc, encoding='utf-8').readlines()
        filepath = diff_lines[0][2:].strip()
        if "projects/optim" in filepath:
            base_filepath = filepath.split("projects/optim/{0}/".format(repo_name))[1]
        else:
            base_filepath = filepath.split("projects/{0}/".format(repo_name))[1]
        startline = int(diff_lines[1][2:].split(",")[0]) - 1
        numlines = int(diff_lines[1][2:].split(",")[1].split("::")[0])
        newfilelines = [k[1:] for k in diff_lines if k.startswith("+")]

        filelines = open(repo_loc+"/"+base_filepath, encoding='utf-8').readlines()
        for i in range(startline, startline + numlines):
            filelines[i] = newfilelines[i-startline]

        print("Writing file: %s, %d" % (repo_loc+"/"+base_filepath, startline))
        with open(repo_loc+"/"+base_filepath, "w", encoding='utf-8') as f:
            for l in filelines:
                f.write(l)

    def apply_diff(self, file=None):
        lines = open(self.file, encoding='utf-8').readlines()
        assert_line = lines[self.line-1]
        # assuming col offset is present in new assert
        lines[self.line - 1] = self.new_assert + "\n"
        for k in range(self.line, self.end_line):
            lines[k] = "\n"
        if file is None:
            file = self.file
        with open(file, "w", encoding='utf-8') as f:
            for l in lines:
                f.write(l)
                #f.write("\n")

    # save diff in string format
    def to_str(self, filename):
        with open(filename, "w") as f:
            f.write(">>{0}\n".format(self.file))
            # range: #start line, #lines to remove::#lines to add
            f.write(">>{0},{1}::{2}\n".format(self.line, self.end_line - self.line + 1, self.end_line - self.line + 1))
            # what lines to add, will remove all mentioned lines
            for l in range(self.line - 1, self.end_line):
                f.write("-{0}\n".format(open(self.file).readlines()[l].rstrip()))

            f.write("+{0}\n".format(self.new_assert.rstrip()))
            for _ in range(self.line, self.end_line):
                f.write("+\n")


