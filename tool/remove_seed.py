import sys
import glob
import copy
import pathlib
import os
import subprocess


def get_import_prefix(library_name):
    return "import " + library_name + " as "


def remove_seeds(file_path):
    numpy_alias = 'numpy'
    tensorflow_alias = 'tensorflow'
    pytorch_alias = 'torch'
    random_alias = 'random'
    file = open(file_path, 'r', encoding='utf-8', errors='ignore')
    file_contents = ""
    for line in file:
        stripped_line = line.strip()
        if stripped_line.startswith(get_import_prefix(numpy_alias)):
            numpy_alias = stripped_line[len(get_import_prefix(numpy_alias)):len(line) - 1]
        elif stripped_line.startswith(get_import_prefix(tensorflow_alias)):
            tensorflow_alias = stripped_line[len(get_import_prefix(tensorflow_alias)):len(line) - 1]
        elif stripped_line.startswith(get_import_prefix(pytorch_alias)):
            pytorch_alias = stripped_line[len(get_import_prefix(pytorch_alias)):len(line) - 1]
        elif stripped_line.startswith(get_import_prefix(random_alias)):
            random_alias = stripped_line[len(get_import_prefix(random_alias)):len(line) - 1]
        modified = False
        original_line = copy.copy(line)
        line = line.replace(numpy_alias + ".random.seed(", "pass # " + numpy_alias + " .random_seed(")
        line = line.replace(tensorflow_alias + ".random.set_seed(", "pass # " + tensorflow_alias + " .random.set_seed(")
        line = line.replace(tensorflow_alias + ".set_random_seed(", "pass # " + tensorflow_alias + " .set_random_seed(")
        line = line.replace(tensorflow_alias + ".random.set_random_seed(",
                            "pass # " + tensorflow_alias + " .random.set_random_seed(")
        line = line.replace(tensorflow_alias + ".compat.v1.random.set_random_seed(",
                            "pass # " + tensorflow_alias + " .compat.v1.random.set_random_seed(")
        line = line.replace(pytorch_alias + ".manual_seed(", "pass # " + pytorch_alias + " .manual_seed(")
        line = line.replace(pytorch_alias + ".cuda.manual_seed_all(",
                            "pass # " + pytorch_alias + " .cuda.manual_seed_all(")
        line = line.replace(pytorch_alias + ".seed(", "pass # " + pytorch_alias + " .seed(")
        if line.find("pass") == -1:
            line = line.replace(random_alias + ".seed(", "pass # " + random_alias + " .seed(")

        file_contents += line
    file.close()

    file = open(file_path, "w", encoding='utf-8')
    file.write(file_contents)
    file.close()


def remove_seeds_dir(directory):
    '''
    Searches for seed setting logic in all files in the given directory and comments
    it out, replacing it with a pass statement. This function recursively searches subdirectories.
    The comment adds an extra space to the original line of code,
    to prevent it from being repeatedly replaced if the script is run multiple times.
    @param directory: string        directory to remove seed-setting logic from
    '''
    for file_path in glob.glob(str(directory) + "/**/*.py", recursive=True):
        remove_seeds(file_path)


if __name__ == "__main__":
    '''USAGE: py remove_seeds_script.py [branch name] [directory to remove seeds from]'''
    original_dir = os.getcwd()
    git_item = pathlib.Path(sys.argv[2])

    git_dir = None
    if not git_item.is_file():
        git_dir = str(git_item)
    else:
        git_dir = str(git_item.parents[0])

    os.chdir(git_dir)
    subprocess.run(["pwd"])
    subprocess.run(["git", "branch", sys.argv[1]])
    subprocess.run(["git", "checkout", sys.argv[1]])

    os.chdir(original_dir)

    for item_num in range(2, len(sys.argv)):
        item_path = pathlib.Path(sys.argv[item_num])
        if not item_path.is_file():
            remove_seeds_dir(item_path)
        else:
            remove_seeds(item_path)

    os.chdir(git_dir)
    subprocess.run(["git", "config", "--global", "user.name", "test"])
    subprocess.run(["git", "commit", "-a", "-m", "automatically removed seed setting code"])
