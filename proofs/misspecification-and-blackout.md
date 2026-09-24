# Approximate dictionary coverage and audit-blackout necessity

This supplement isolates two reviewer-facing boundary questions: what changes when the true typed law is near, but not in, the finite dictionary; and why some dependence on audit arrival is unavoidable. It uses only the value-sensitivity/coupling property already proved in the main analysis.

## Setup

Let `p=(p_i)_i` be the true collection of typed mark laws. Let `P` be the finite planning dictionary and suppose it contains a cover point `p_bar` satisfying

`TV(p_i,p_bar_i) <= epsilon_i` for every type `i`.

For a policy `pi`, define a uniform typewise sensitivity coefficient

`B_i = sup |V_q(pi)-V_q'(pi)| / TV(q_i,q'_i)`,

where the supremum ranges over policies and model pairs that agree outside type `i`; the ratio is zero for equal coordinates. The bounded-loss and bounded-launch assumptions, together with the launch coupling, provide the explicit finite upper bound used in the paper.

## Proposition 1: cover-robust confidence

Inflate every type-`i` prefix-ball or completion-distance test by `epsilon_i`. On the original simultaneous concentration event, `p_bar` belongs to every inflated confidence set.

### Proof

For a prefix ball, the concentration event gives `TV(p_i,p_hat_i) <= r_it`. Therefore

`TV(p_bar_i,p_hat_i) <= TV(p_bar_i,p_i) + TV(p_i,p_hat_i) <= epsilon_i+r_it`.

For a completion set `E_it`, the concentration event gives `dist_TV(p_i,E_it) <= r_it`. The distance-to-set map is 1-Lipschitz, hence

`dist_TV(p_bar_i,E_it) <= TV(p_bar_i,p_i)+dist_TV(p_i,E_it) <= epsilon_i+r_it`.

The argument is simultaneous over types and times on the same event. No returned-only selection assumption is used.

## Proposition 2: regret under a known cover radius

Run the optimistic scheduler with the inflated confidence sets. Relative to the true-`p` oracle, the well-specified regret upper bound increases by at most

`2 T sum_i B_i epsilon_i`.

### Proof

Fix an episode and write `pi_t` for the selected policy and `pi_p` for a true-model optimal policy. On the good event, `p_bar` is feasible for the optimistic problem. Insert and subtract values under `p_bar`:

`V_p(pi_t)-V_p(pi_p)`

`= [V_p(pi_t)-V_p_bar(pi_t)]`

`+ [V_p_bar(pi_t)-V_p_bar(pi_p)]`

`+ [V_p_bar(pi_p)-V_p(pi_p)]`.

The first and third terms are each at most `sum_i B_i epsilon_i`. The middle term is controlled by the same optimism, planning-error, estimation-width, and delayed-exposure argument as in the well-specified proof because `p_bar` is feasible. Summing over `T` episodes yields the stated additive term. The failure event is handled exactly as in the main theorem.

This result requires declared radii that dominate the actual cover error. It does not estimate an unknown misspecification radius, and it does not convert a poor dictionary into a nonparametric learner.

## Proposition 3: audit-blackout lower bound

Suppose two admissible environments have identical laws for every observation available to the learner during the first `h` episodes, their unique optimal actions are opposite, and the loss gap of the wrong action is at least `Delta` in each environment. Then every randomized learner has expected regret at least `h Delta / 2` in one of the two environments over the blackout interval.

### Proof

Because the observable histories have the same law, the learner has the same action distribution in both environments at every blackout episode. Let `alpha_t` be the probability of choosing the action optimal only in environment 1. The average of the two one-step regrets is at least

`(Delta/2) [alpha_t + (1-alpha_t)] = Delta/2`.

After summing over `t=1,...,h`, the average cumulative regret is at least `h Delta/2`, so the larger of the two regrets is at least the same value.

This is deliberately a limited necessity statement. It rules out delay-free guarantees under unrestricted blackouts; it is not a matching lower bound for chronological prefix debt, unresolved-mass exposure, or their minimum.

## Machine checks

`python run.py check` verifies the distance-to-completion-set calculation on an exhaustive finite lattice and compares the production selector implementation with an independent brute-force computation. The off-grid campaign constructs truths outside the planning dictionary with recorded cover radii and checks nominal versus inflated set membership. Those finite checks support the implementation and examples; they do not replace the general arguments above.
