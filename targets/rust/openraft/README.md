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
- 2026-09-13: base bumped 0d15d99844e8 → 3a3d15906f3a (2026-09-12, "test: turmoil: bump rand to 0.10 and move to upstream turmoil 0.7.2"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 606 tests pass. openraft/1 is fixed by an API change (`voted_for` is `NID`, not `Option<NID>`, since 0.10.0), so its pin was removed and the full-domain comparison property lost its exclusion. Upstream extracted `VecProgress`, `QuorumSet` and coherence into the separate `quorum-set` crate (drmingdrmer/quorum-set), so the six properties the patch carried in progress/vec_progress.rs, quorum/coherent_test.rs and quorum/quorum_set_test.rs no longer have a home here and were dropped (candidates for a `quorum-set` target); the membership coherence checks now use `QuorumIntersection::intersects_with(..) == Some(true)`, which has the old `Coherent::is_coherent_with` semantics.
- 2026-09-13: base bumped 3a3d15906f3a → bcf56b29eb32 (2026-09-13, "docs: serde: clarify compatibility guarantees"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 606 tests pass.
- 2026-09-13: base bumped bcf56b29eb32 → 899eed622bfe (2026-09-13, "fix: engine: apply smaller-log election backoff only while still behind"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 608 tests pass.
- 2026-09-13: base bumped 899eed622bfe → 13b84490ea05 (2026-09-13, "fix: replication: refresh clock on partial success"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 612 tests pass.
- 2026-09-13: base bumped 13b84490ea05 → 15699abf73ca (2026-09-13, "test: openraft: extend watch progress send interval"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 612 tests pass.
- 2026-09-14: base bumped 15699abf73ca → 260f170e6d59 (2026-09-14, "docs: errors: clarify ForwardToLeader retry semantics"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 612 tests pass.
- 2026-09-14: base bumped 260f170e6d59 → cad2925616f1 (2026-09-14, "chore: build: check isolated feature builds"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 612 tests pass.
- 2026-09-14: base bumped cad2925616f1 → 78153a39ab40 (2026-09-14, "test: rt: use runtime clock in Suite timing checks"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 612 tests pass.
- 2026-09-14: base bumped 78153a39ab40 → 65c3d167b50e (2026-09-14, "test: rt: poll sleep with the active waker"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 615 tests pass.
- 2026-09-15: base bumped 65c3d167b50e → 54094270ede0 (2026-09-15, "change: errors: report discarded client-write entries"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 615 tests pass.
- 2026-09-17: base bumped 54094270ede0 → ff31db46c5c3 (2026-09-17, "test: jepsen: use thread-safe libfaketime"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 615 tests pass.
- 2026-09-17: base bumped ff31db46c5c3 → c717fe98a286 (2026-09-17, "test: membership: wait for recovery term and membership"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 615 tests pass.
- 2026-09-18: base bumped c717fe98a286 → f1a2ec636416 (2026-09-18, "docs: openraft: document v0.10 feature flag migration"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 615 tests pass.
- 2026-09-18: base bumped f1a2ec636416 → 542b9046ee92 (2026-09-18, "change: openraft: gate heartbeats after quorum loss"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 618 tests pass.
- 2026-09-20: base bumped 542b9046ee92 → d356e98d3256 (2026-09-20, "test: jepsen: use alternate Maven Central endpoint"; 0.10.0-alpha.34); 0 bug(s) still reproduce. 625 tests pass.
