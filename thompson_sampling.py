from bandit import Bandit
from utils import thompson_arm_pull
import numpy as np
from math import sqrt


def thompson_sampling(bandit, num_rounds, type_of_pull='single'):
    """Function that reproduces the steps involved in Thompson sampling
    algorithm"""
    print("---------------Running Thompson Sampling ---------------")

    # we use 2 in order to calculate sample variance
    num_arms = bandit.num_arms
    alpha = -1
    num_initial_pulls = max([2, 3-(2*alpha)])
    for ite in range(num_initial_pulls):
        for arm in range(num_arms):
            if type_of_pull == 'monte_carlo':
                bandit.pull_arm(arm, prop_lis=[1 if i == arm else 0 for i in
                                               range(bandit.num_arms)])
            else:
                bandit.pull_arm(arm)

    # we use precision (tau) instead of sigma (precision = 1/sigma^2) for parameter updation
    # prior for tau ~ Ga(alpha, beta)
    # initialize this as Ga(alpha = 0, beta = 0) - This is basically reference prior
    # prior_params = (mu_param, sigma_param, alpha, beta)

    # prior_params are mu_0, n_0, alpha, beta
    prior_params = [(bandit.avg_reward_tracker[i], num_initial_pulls, 0.5, 0.5) for i in
                    range(num_arms)]

    for rnd in range(int(num_rounds - (num_initial_pulls * num_arms))):
        # based on the above prior params, we draw and calculate tau and mu before we can observe a sample(x) and update
        # we need tau prior and mu prior in order to choose which arm to pull in the case of thompson sampling and also
        # to calculate propensities of all arms
        # in normal posterior updation we do not have to draw tau and mu.
        tau_prior = [np.random.gamma(prior_params[i][2], prior_params[i][3]) for i in
                    range(num_arms)]
        mu_prior = [np.random.normal(prior_params[i][0], 1 / sqrt(prior_params[i][1] * tau_prior[i])) for i in
                    range(num_arms)]
        if type_of_pull == 'monte_carlo':
            chosen_arm, prop_lis = thompson_arm_pull(mean_lis=mu_prior, var_lis=1/np.array(tau_prior),
                                                     type_of_pull=type_of_pull)
            bandit.pull_arm(chosen_arm, prop_lis=prop_lis)
        else:
            chosen_arm = thompson_arm_pull(mean_lis=mu_prior, var_lis=1/np.array(tau_prior),
                                           type_of_pull=type_of_pull)
            bandit.pull_arm(chosen_arm)
        (mu_0_prior, n_0_prior, alpha_prior, beta_prior) = prior_params[chosen_arm]
        x = bandit.reward_tracker[-1]
        # We calculate the posterior parameters as per the normal inv gamma bayesian update rules
        n_0_post = n_0_prior + 1
        alpha_post = alpha_prior + 0.5
        beta_post = beta_prior + (0.5 * (n_0_prior / n_0_post) * ((x - mu_0_prior) ** 2))
        mu_0_post = (((n_0_prior) * (mu_0_prior)) + x) / (n_0_post)
        # we replace the prior with the posterior
        prior_params[chosen_arm] = (mu_0_post, n_0_post, alpha_post, beta_post)
    return bandit


if __name__ == '__main__':
    # Define bandit
    num_rounds = 100
    thompson_bandit = Bandit(name='thompson_sampling',
                             arm_means=[1,2,3],
                             arm_vars=[1,1,1]
                             )
    thompson_sampling(thompson_bandit, num_rounds=num_rounds)
