# openraft

[databendlabs/openraft](https://github.com/databendlabs/openraft).

## What is tested

**`src/log_id/mod.rs`**
- `hegel_log_id_order_matches_tuple_oracle`: The module docs promise: log ids are ordered by leader id (term, then node id), then by index. Check both leader-id flavors against lexicographic tuple oracles.

**`src/membership/membership_test.rs`**
- `hegel_next_coherent_reaches_goal_within_two_steps`: Documented contract of `next_coherent`: repeatedly stepping toward a goal config reaches the uniform goal config within two steps, and each step is coherent with the previous one.
- `hegel_membership_change_yields_valid_coherent_membership`: A successful `Membership::change()` must yield a valid membership whose config is coherent with the previous config, and whose voters and learners partition the node set.
- `hegel_membership_serde_roundtrip`: (no doc comment)

**`src/progress/vec_progress.rs`**
- `hegel_vec_progress_matches_reference_model`: Model test: a generated sequence of `update`, `increase_to` and `upgrade_quorum_set` operations, over generated quorum configurations, keeps `VecProgress` in agreement with the straightforward reference model (`model_quorum_accepted`) and preserves the internal voter ordering invariant.

**`src/quorum/coherent_test.rs`**
- `hegel_find_coherent_yields_pairwise_intersecting_quorums`: `find_coherent` must return an intermediate quorum set `X` with `self ~ X ~ other`: every quorum of `self` intersects every quorum of `X`, and every quorum of `X` intersects every quorum of `other`. This is the safety property that makes joint-consensus membership change correct; it is checked against an exhaustive enumeration of all quorums.
- `hegel_is_coherent_with_implies_intersecting_quorums`: If `is_coherent_with` reports two joint configs as coherent, then every quorum of one must intersect every quorum of the other (the definition of coherence documented on the `Coherent` trait).

**`src/quorum/quorum_set_test.rs`**
- `hegel_majority_quorum_matches_counting_oracle`: `BTreeSet::is_quorum` implements simple majority, and the `&[ID]` implementation agrees with it.
- `hegel_joint_quorum_is_majority_in_every_config`: A joint quorum set grants iff the granted set is a majority in every config.
- `hegel_quorum_is_upward_closed`: The `QuorumSet` trait requires implementations to be upward-closed: adding more ids to a quorum must still be a quorum.

**`src/vote/vote.rs`**
- `hegel_adv_vote_order_matches_tuple_oracle`: `Vote<leader_id_adv>` is documented as totally ordered: term first, then node id, and a committed vote is greater than a non-committed one. Check against a lexicographic tuple oracle.
- `hegel_std_vote_partial_cmp_duality`: `partial_cmp` must be a dual: comparing `(b, a)` yields the reverse of comparing `(a, b)`, and `Some(Equal)` must coincide with `==`.
- `hegel_std_vote_partial_cmp_transitive`: `partial_cmp` must be transitive: `a <= b` and `b <= c` imply `a <= c`. This is required for `PartialOrd` and is what lets vote-granting decisions chain safely.
- `hegel_std_vote_partial_cmp_no_panic_on_full_domain`: Comparing any two publicly-constructible votes must not panic, even when `voted_for` is `None` (all `Vote` and `LeaderId` fields are `pub`, and serde accepts `"voted_for": null`).
- `hegel_std_vote_partial_cmp_none_voted_for_panics`: KNOWN FAILURE: comparing two `Vote<leader_id_std::LeaderId>` with equal terms panics when either side has `voted_for: None`, because `LeaderIdCompare::std` calls `RaftLeaderId::node_id()`, which is `self.voted_for.as_ref().unwrap()` (leader_id_std.rs). `voted_for` is a `pub` field of type `Option<NID>`, `Display` renders the `None` case, and the serde format accepts `"voted_for": null`, so such votes are publicly constructible; `PartialOrd` must not panic on them. Minimal counterexample: both sides `Vote { leader_id: LeaderId { term: 0, voted_for: None }, committed: false }`. This test fails deterministically (every generated case hits the bug) until the comparison handles `voted_for: None`.
- `hegel_vote_serde_roundtrip`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `0d15d99844e8` (feat: add heartbeat_min_interval to suppress redundant heartbeats).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/openraft.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
