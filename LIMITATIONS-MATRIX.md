# Assumption and limitation matrix

| Assumption | Where used | What fails without it | Covered extension / evidence | Not claimed |
|---|---|---|---|---|
| Typed potential-mark tapes are iid across launch index | simultaneous concentration and oracle comparison | arbitrary drift/correlation invalidates the confidence radii | finite off-grid TV-cover error | nonstationary or adversarial marks |
| Audits preserve identity and eventually reveal the complete categorical mark | completion set and chronological prefix | anonymous, corrupted, or permanently missing records need a different observation model | outcome-dependent and single-blocker latency | censoring/deletion robustness |
| True law is in a finite dictionary | exact optimism and finite planning | nominal confidence can become empty or exclude every dictionary point | known TV cover radius with additive approximation term | adaptation to unknown misspecification |
| Policy class and planning oracle are finite/available | optimistic policy selection | generic scheduling may be computationally intractable | explicit planning-error term; exact enumeration in the artifact | polynomial-time oracle for general systems |
| Per-episode loss and launches are bounded | coupling and failure-event conversion | sensitivity and regret can be unbounded | constants are explicit in the theorem | heavy-tailed unbounded service costs |
| Audit arrival is not subject to unrestricted blackout if sublinear delay cost is desired | delayed-exposure corollaries | indistinguishable environments force linear regret during a blackout | two-environment blackout lower bound | delay-free guarantee |
| Simulator benchmark is synthetic and finite | empirical mechanism checks | no direct evidence about real decoder/hardware throughput | exhaustive finite checks and frozen stress campaigns | deployed speedup, energy, or latency claims |
| Seeds are Monte Carlo replicates, not sampled deployments | uncertainty summaries | population inference would be unsupported | paired finite-cell summaries and seed-level MC uncertainty | real-world confidence intervals |

The paper's positive statements are conditional on the left-hand assumptions. The artifact checks implementation consistency under those assumptions; it does not convert them into empirical facts about an external system.
