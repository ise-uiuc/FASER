import argparse
import numpy as np

import confidence

from process_data import DataFolder
from scipy.optimize import basinhopping


def _calculate_catch_pass_rate(assert_value, df):
    if df.lessthan:
        if df.pass_equal:
            pass_rate = sum(i <= assert_value for i in df.hist_diff_dict['original'][0]) / len(
                df.hist_diff_dict['original'][0])
            catch_rate = sum(i > assert_value for i in df.hist_diff_joint) / len(df.hist_diff_joint)
        else:
            pass_rate = sum(i < assert_value for i in df.hist_diff_dict['original'][0]) / len(
                df.hist_diff_dict['original'][0])
            catch_rate = sum(i >= assert_value for i in df.hist_diff_joint) / len(df.hist_diff_joint)
    else:
        if df.pass_equal:
            pass_rate = sum(i >= assert_value for i in df.hist_diff_dict['original'][0]) / len(
                df.hist_diff_dict['original'][0])
            catch_rate = sum(i < assert_value for i in df.hist_diff_joint) / len(df.hist_diff_joint)
        else:
            pass_rate = sum(i > assert_value for i in df.hist_diff_dict['original'][0]) / len(
                df.hist_diff_dict['original'][0])
            catch_rate = sum(i <= assert_value for i in df.hist_diff_joint) / len(df.hist_diff_joint)

    return pass_rate, catch_rate


def optimize(df, alpha):
    samples = df.hist_diff_dict['original'][0]
    original_bound = df.bound
    if not df.lessthan:
        samples = [-x for x in samples]  # reversing
        original_bound = -original_bound

    def f(b):  # define dual optimization problem
        b=b[0]
        emp_pass_rate, emp_catch_rate = _calculate_catch_pass_rate(b, df)
        stat_pass_rate = 1 - confidence.get_exceed_probability_with_subgaussian(samples, b)
        return -(alpha*stat_pass_rate + (1-alpha)*emp_catch_rate)

    sorted_samples = np.sort(samples)
    x0 = sorted_samples[-1]
    perc90 = np.percentile(sorted_samples, 90)
    print("Using x0: {}, alpha: {}, min x: {}".format(x0, alpha, perc90))
    minimizer_kwargs = {
        "method": "COBYLA",
        'constraints': ({'type': 'ineq', 'fun': lambda x: x - perc90},
                        {'type': 'ineq', 'fun': lambda x: original_bound - x},
                        )}
    opt = basinhopping(f, x0, niter=100, disp=False, minimizer_kwargs=minimizer_kwargs)
    print(opt)
    return opt


def main(args):
    df = DataFolder(args.data_folder, ks_pthreshold=0.01)
    df.process_folder() # process folder
    print("Begin Optimization...")
    opt_result = optimize(df, args.alpha)
    print("Finished Optimization")
    x = opt_result.get('x')
    if isinstance(x, np.ndarray):
        if len(x.shape) == 0:
            x = float(x)
        else:
            x = x[0]
    new_bound = x
    old_pass, old_catch = _calculate_catch_pass_rate(df.bound, df)
    new_pass, new_catch = _calculate_catch_pass_rate(new_bound, df)
    stat_pass_rate = 1 - confidence.get_exceed_probability_with_subgaussian(df.hist_diff_dict['original'][0], new_bound)

    print(">>> previous bound: {} mutation score: {} <<<".format(df.bound, old_catch))
    print(">>> new bound: {} | pass rate: {:.2f} | mutation score: {:.2f} | PP ms increase: +{:.2f}<<<".format(new_bound, stat_pass_rate,
                                                                                                 new_catch, new_catch-old_catch))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FASER bound computation arguments")
    parser.add_argument("--data_folder")
    parser.add_argument("--alpha", default=0.9, type=float)
    # np.random.seed(6)
    args = parser.parse_args()
    main(args)
