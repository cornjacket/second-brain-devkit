---
tags: [bench, distributed-systems]
---

# Two-Phase Commit

Two-phase commit coordinates an atomic transaction spanning multiple nodes so that either every participant commits or every participant aborts, never a mix. In the prepare phase a coordinator asks each participant to durably persist the transaction's effects and vote; a participant that votes yes enters an in-doubt state, having promised to commit and forfeited its ability to unilaterally abort. If all vote yes the coordinator logs a commit decision and broadcasts it in the second phase; any no vote or timeout forces a global abort. The protocol's fatal weakness is coordinator failure after some participants voted yes, leaving them blocked holding locks until the coordinator recovers its decision log, since they cannot safely resolve alone. Three-phase commit adds a pre-commit round to reduce blocking under a synchrony assumption, while consensus-based commit replaces the single coordinator with a replicated group so the decision survives its failure.
