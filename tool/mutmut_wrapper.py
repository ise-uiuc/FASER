from difflib import unified_diff

import mutmut
from mutmut import Config
from mutmut import Context


def make_config(paths_to_mutate=None):
    return Config(
        total=0,  # we'll fill this in later!
        swallow_output=True,
        test_command='python -m unittest',
        covered_lines_by_filename=None,
        coverage_data=None,
        baseline_time_elapsed=0.24,
        dict_synonyms=[''],
        using_testmon=False,
        tests_dirs=[],
        hash_of_tests='NO TESTS FOUND',
        test_time_multiplier=2.0,
        test_time_base=0.0,
        pre_mutation=None,
        post_mutation=None,
        paths_to_mutate=paths_to_mutate,
        mutation_types_to_apply={'or_test', 'annassign', 'operator', 'decorator', 'number', 'keyword', 'argument', 'lambdef',
                                'name', 'and_test', 'atom_expr'},
        no_progress=None
    )


def mutate_files(files):

    performed_mutation_ids = []
    performed_mutation_types = []

    for file in files:

        with open(file) as f:
            source = f.read()

        config = make_config()
        config.paths_to_mutate = [file]

        context = Context(
            source=source,
            filename=file,
            config=config,
            dict_synonyms=config.dict_synonyms,
        )

        mutmut.mutate(context)

        performed_mutation_ids.extend(context.performed_mutation_ids)
        performed_mutation_types.extend(context.performed_mutation_types)

    return performed_mutation_ids, performed_mutation_types


def get_unified_diff(source, mutant):
    output = ""
    for line in unified_diff(source.split('\n'), mutant.split('\n'), fromfile="source", tofile="mutant",
                             lineterm=''):
        output += line + "\n"
    return output


def print_mutations(performed_mutation_ids, performed_mutation_types, coverage_data):

    ret = []
    real_ret = []
    line_number_mutation_count = {}
    for index, id in enumerate(performed_mutation_ids):
        if id.line_number+1 in coverage_data[id.filename]: # only want mutants in coverage
            with open(id.filename) as f:
                source = f.read()

            context = Context(
                source=source,
                filename=id.filename,
                mutation_id=id,
                config=make_config([id.filename]),
                dict_synonyms=None
            )
            mutated_source = mutmut.mutate(context)[0]
            if len(id.line.strip()) > 3 and id.line.strip()[:3] == 'def': # ignore mutations done on function signature, often changes nothing
                continue
            if id.line.strip()[0] == '@':
                continue
            mutated_line = ""
            for line in unified_diff(source.split('\n'), mutated_source.split('\n'), fromfile="source", tofile="mutant",
                                     lineterm=''):
                if len(line) > 3 and line[0] == '-' and line[1] != '-':
                    mutated_line = line[1:].strip()
            assert (mutated_line != "")

            ret.append((index, mutated_source, id, performed_mutation_types[index], mutated_line))
            if performed_mutation_types[index] == 'number':
                if mutated_line not in line_number_mutation_count:
                    line_number_mutation_count[mutated_line] = 0
                line_number_mutation_count[mutated_line] += 1

    for item in ret:
        if item[3] == 'number' and line_number_mutation_count[item[4]] > 1:
            continue
        real_ret.append(item)
    return real_ret


# Return a list of possible mutations, with line number
def generate_mutations(coverage_data):
    performed_mutation_ids, performed_mutation_types = mutate_files(list(coverage_data.keys()))
    return print_mutations(performed_mutation_ids, performed_mutation_types, coverage_data)
