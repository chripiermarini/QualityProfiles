# What is computed

This page describes the quantities computed by `quality-profiles` and how to read them.
The method is introduced in G. Fasano, C. Piermarini, M. Roma, *Benchmarking
Optimization Algorithms with Quality Profiles and Test Set Profiles*, Mathematical
Programming Computation (accepted), [arXiv:2607.16798](https://arxiv.org/abs/2607.16798).
Section and lemma numbers below refer to that paper.

For the functions and their parameters, see the [API reference](api.md).

## Inputs

For a set of test problems $P$ and a set of solvers $S$, the package needs, for every
problem $p \in P$:

* $f^{(p)}(x_0^{(p)})$, the objective value at the starting point $x_0^{(p)}$, which is
  common to all solvers (`f0[p]`);
* $f_s^{(p)}$, the best objective value found by each solver $s \in S$ (`f_solvers[p, s]`).

A solver's failure on a problem is marked with `NaN`, or with any non-finite value.

## Quality profiles

Let $f_L^{(p)}$ be a reference value for problem $p$. By default it is the best value
found by any solver, $f_L^{(p)} = \min_{s \in S} f_s^{(p)}$. The **(weak) quality
profile** of solver $s$ is (equation 2.1)

$$
Q_s(\tau) = \frac{1}{|P|}\,\mathrm{size}\Big\{p \in P :
f_s^{(p)} - f_L^{(p)} \le \tau\,\big(f^{(p)}(x_0^{(p)}) - f_L^{(p)}\big)\Big\},
\qquad \tau \in [0, 1].
$$

$Q_s(\tau)$ is the fraction of test problems on which solver $s$ reduced the gap between
the starting value and the reference value by at least a factor $\tau$. Values of $\tau$
larger than 1 add nothing, since every solver that does not end above the starting point
is counted at $\tau = 1$.

### Weak and strong profiles

* **Weak** profiles (the default) measure the progress from the starting point, i.e.
  against $f^{(p)}(x_0^{(p)}) - f_L^{(p)}$. They fit most applications.
* **Strong** profiles (`strong=True`) replace $f^{(p)}(x_0^{(p)})$ with the worst value
  found by any solver, $\max_{s \in S} f_s^{(p)}$ (Definition 2.1). They compare the
  solvers with each other, regardless of the starting point, and help when the solvers
  end up with close objective values. The worst solver on a problem is then credited
  only at $\tau = 1$.

### The reference value

The reference value can be chosen in several ways (Section 2):

1. the best value found by the solvers, $\min_s f_s^{(p)}$ (the default);
2. a value that does not depend on the compared solvers, for instance a known optimal
   value or the result of a separate reference solver (argument `f_ref`);
3. another combination of the solvers' values, such as their mean (also through `f_ref`).

With a reference value that does not depend on the solvers, each profile is independent
of the others: adding or removing a solver does not change the other curves
(Lemma 2.7). With the default choice, every profile depends on the whole set of
solvers.

## Scaling with r1 and r2

Solvers often have close profiles, especially near $\tau = 0$ or $\tau = 1$
(Observation 2.5). The package therefore computes the scaled profiles (equation 2.3)

$$
\big[Q_s(\tau^{r_1})\big]^{r_2}, \qquad \tau \in [0, 1],
$$

with positive exponents `r1` and `r2`:

* `r1 > 1` expands the region of high accuracy (precision levels close to 0), and
  `r1 < 1` expands the region close to 1;
* `r2 > 1` stretches the ordinate near 0, and `r2 < 1` stretches it near 1.

The defaults are `r1 = r2 = 1`. Change `r1` first, to zoom along the abscissa. Use `r2`
only to separate curves that are very close. The values on the ordinate are then raised
to the power `r2`, so they are no longer plain fractions of problems.

The relative ranking of the solvers does not depend on `r1` or `r2` (Lemma 2.6).

### Sampling

The profiles are sampled at the equally spaced points
$\tau_k = k / n$, $k = 0, \dots, n$, and evaluated at the precision levels
$\tau_k^{r_1}$, which are the abscissae of the plot. When $r_1 \neq 1$ these levels are no
longer equally spaced, so the default number of intervals grows with `r1`:

$$
n = \big\lfloor \max(1000,\ 1000\, r_1,\ 1000 / r_1) \big\rfloor .
$$

With `r1 = 1` the smallest positive precision level is $10^{-3}$. With `r1 = 5` it is
$(1/5000)^5 \approx 3 \cdot 10^{-19}$, and with `r1 = 10` it is $10^{-40}$. A larger
`r1` therefore lets the plot reach higher accuracy.

The sampling only decides where the curves are drawn: `QualityProfile.evaluate`
computes the profiles exactly at any precision level, without interpolation.

## How to read a profile

* $Q_s(0)$ is the fraction of problems on which solver $s$ found the best value among
  all solvers (with the default reference value).
* $Q_s(1)$ is the fraction of problems on which $s$ did not fail and did not end above
  the starting value. $Q_s(1) < 1$ means some failures.
* On a semilog plot, the value at precision $10^{-k}$ is the fraction of problems on
  which $s$ reduced $f(x_0) - f_L$ by at least $k$ orders of magnitude (Section 2.1).
  This is why a logarithmic abscissa is recommended.
* The higher the curve, the better the solver. If one curve is above another
  everywhere, that solver is uniformly preferable.

## Properties

The following properties are proved in the paper. The test suite checks each of them.

* **Range:** $0 \le Q_s(\tau) \le 1$.
* **Monotonicity:** $Q_s$ is nondecreasing in $\tau$ (Lemma 2.3).
* **Affine invariance:** applying the same transformation $a f + b$, with $a > 0$, to
  all objective values of a problem does not change the profiles (Lemma 2.2).
* **Invariance of the ranking** with respect to `r1` and `r2` (Lemma 2.6).
* **Independence** of the profiles when the reference value does not depend on the
  solvers (Lemma 2.7).

## A single number per solver

The area under a profile summarizes it with one number in $[0, 1]$ (Observation 2.9):
the larger the area, the better the solver. The package computes it with the trapezoidal
rule with respect to the uniform parameter $\tau$:

$$
A_s = \int_0^1 \big[Q_s(\tau^{r_1})\big]^{r_2}\, d\tau .
$$

Because the integral is taken in $\tau$, a larger `r1` gives more weight to high-accuracy
levels. The ranking by area can therefore change with `r1`; on the smooth CUTEst
experiment of the paper, CG+ ranks first with `r1 = 1` and TRON with `r1 = 5`. A single
number cannot show where two curves cross, so look at the profiles as well.

## Failures and invalid data

* A non-finite value of $f_s^{(p)}$ is a failure. The problem is never counted for that
  solver, but it stays in the denominator $|P|$, so failures keep the profile below 1.
* A solver that ends above the starting value is never credited on that problem.
* If $f^{(p)}(x_0^{(p)})$ is not finite, no solver is credited on problem $p$.
* If $f^{(p)}(x_0^{(p)}) = f_L^{(p)}$, only the solvers that reach $f_L^{(p)}$ are
  credited, at every precision level.
* If $f_L^{(p)} > f^{(p)}(x_0^{(p)})$ on some problem, for instance because every solver
  ended above the starting value, the profiles are not defined and `quality_profiles`
  raises a `ValueError` listing the offending rows.

## Relation to the reference MATLAB code

The package follows the reference MATLAB implementation
([fasano-g/Quality-Profiles](https://github.com/fasano-g/Quality-Profiles)): same grid,
same default reference value, same treatment of failures and same error condition. On
the same grid it gives exactly the same values. The test suite checks this against a
line-by-line port of the MATLAB loops.
