# FASER: Balancing Effectiveness and Flakiness of Non-Deterministic Machine Learning Tests

## Installing 

### Conda setup
We recommend using a conda environment.

Run `conda install -c conda-forge r-base r-eva` to installed the required R packages

### Python Setup
Use Python (3.6-3.8) version due to issues in [astunparse library](https://github.com/simonpercivall/astunparse/issues/62)

To install the requirements, do `pip install -r requirements.txt`.

To install the custom `mutmut` library go to `tool/src/mutmut` and run `python setup.py install`

To set up experiment project: `repo_name` use `scripts/[repo_name]_setup.sh` script. See next section in more detail

To set up individual projects in general use the `scripts/general_setup.sh` script. See FLEX project for more detail

## Running 

Step 1: Create `projects` directory in root.

Step 2: Go to `tool/scripts` and run `bash [repo_name]_setup.sh ../../projects` to set up the project.

[Optional] Step 2.1: Remove any random seed setting by running `python remove_seed.py no_random ../projects/[repo_name]`

Step 3: Run `python boundschecker.py -r [repo_name] -conda [conda env name]` in the `tool/` directory to run all tests for that experiment project in `testspecs.py`.

E.g., for `Cleverhans`:
`python boundschecker.py -r cleverhans -conda cleverhans`

## Running One Single Test

Run `python boundschecker.py -r [repo_name] -test [test_name] -cl [class_name] -file [filename] -line [line number] -conda [conda env name]` in the `tool/` directory to run a single test.

E.g., for one test in `Cleverhans`
`python boundschecker.py -r cleverhans -test test_adv_example_success_rate_linf -cl TestSPSA -file cleverhans/torch/tests/test_attacks.py -line 75 -conda cleverhans`

## Computing a new bound

Go into the `processing` folder and use the `compute_bound.py` script with the directory of the collected data for and test and the chosen alpha value 

e.g., `python compute_bound.py --data_folder data/cleverhans_TestSPSA_test_adv_example_success_rate_linf_1637802988/ --alpha 0.9`

#### Sample output

```
>>>>> Beginning process Class: TestSPSA Test: test_adv_example_success_rate_linf
Found csv entry with bound: 0.5, lessthan: True, all_close: False, pass_equal: False
Num of crashed mutants: 29 same mutants: 20 diff mutants: 13
Begin Optimization...
Using x0: 0.24, alpha: 0.9, min x: 0.19
                        fun: -0.9783814527855432
 lowest_optimization_result:      fun: -0.9783814527855432
   maxcv: 0.0
 message: 'Optimization terminated successfully.'
    nfev: 20
  status: 1
 success: True
       x: array(0.2898199)
                    message: ['requested number of basinhopping iterations completed successfully']
      minimization_failures: 0
                       nfev: 2044
                        nit: 100
                          x: array(0.2898199)
Finished Optimization
>>> previous bound: 0.5 mutation score: 0.7623076923076924 <<<
>>> new bound: 0.2898199008350133 | pass rate: 0.99 | mutation score: 0.88 | PP ms increase: +0.12<<<
```

here the new bound suggested by faser is 0.29 and the increased mutation score with respect to the old developer bound is 12 PP 


## Explanation of flags

- Repo Name: -r
- Test Name: -test
- File name: -file
- Class name: -cl
- Line number of assertion: -line
- Conda env name: -conda
- Run without mutants: --no_mutants
- Resume old run: --resume (useful when there are large amounts of mutants or tests within a project)

## Directory Structure

The source code for the project is mainly contained in the `tool/` directory. The `tool/` directory is further split into sub-directories like `src` which contains implementation files, folders with setup scripts (`scripts`), logs folders and other implementation files. The root directory further contains some top level files like `requirements.txt`.

The processing code can be found under the `processing/` directory

## Configuration

The file `src/Config.py` contains all the configurations for the tool

- DEFAULT_ITERATIONS: Number of samples to collect in first round
- SUBSEQUENT_ITERATIONS: Number of samples to collect in subsequent rounds
- MAX_ITERATIONS: Max samples
- THREAD_COUNT: Number of threads

## Pull Requests

In total we have opened 19 Pull Requests with 14 Accepted.

See `pr_tracker.csv` for more detail. 

