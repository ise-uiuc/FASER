import scipy.stats as st
import numpy as np

def check_normality(samples, threshold=0.05):
    #shapiro wilk test
    stat, pval = st.shapiro(samples)
    return pval >= threshold


def get_exceed_probability_with_subgaussian(samples, new_bound):
    # test for normality
    # using 1% significance
    if check_normality(samples, 0.01):  # 1% significance
        # is normal
        return dasgupta_inequality(samples, new_bound, one_sided=True)
    elif kurtosis(samples)[-1] > 0.05:
        # is subgaussian
        return dasgupta_inequality(samples, new_bound, one_sided=True)
    else:
        # not normal nor subgaussian
        return cantelli_estimated(samples, new_bound)


def cantelli_estimated(samples, new_bound):
    # one sided bound using estimated mean and variance
    # using tolhurst 2021

    N=len(samples)
    mean=np.mean(samples)
    std=np.std(samples)
    qn=np.sqrt(((N+1)/N)*std*std)
    g2=lambda k: (N*k*k)/(N-1+k*k)


    k=(new_bound-mean)/qn


    prob=1/(N+1)*np.floor((N+1)/(g2(k) + 1))
    return prob


def dasgupta_inequality(samples, new_bound, one_sided=False):
    mean=np.mean(samples)
    std=np.std(samples)
    ineq=lambda k: 1/(3*k*k)

    k=(new_bound-mean)/std
    return ineq(k)/2 if one_sided else ineq(k)


def kurtosis(samples, alternative='less'):
    # check if
    stat, pval = st.kurtosistest(samples, alternative=alternative)
    return stat, pval, pval >= 0.05

