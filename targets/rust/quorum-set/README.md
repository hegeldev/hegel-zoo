# quorum-set

[drmingdrmer/quorum-set](https://github.com/drmingdrmer/quorum-set): quorum sets (flat
majorities, joint configs, hierarchical `QuorumTree`s), the quorum-intersection relation used
for safe membership change, and `VecProgress`, the quorum-accepted progress tracker. The code was
extracted from openraft (0.10.0-alpha.34, September 2026), and so were the zoo's first six
properties for it: they came in with the openraft target and followed the code here.

## What is tested

**`src/progress/vec_progress/vec_progress_test.rs`**
- `hegel_vec_progress_matches_reference_model`: Model test over joint majority configs: a generated sequence of `update_progress`, `increase_to` and `upgrade_quorum_set` operations keeps `VecProgress` in agreement with the straightforward reference model (`model_quorum_accepted`) and preserves the internal voter ordering invariant.
- `hegel_vec_progress_matches_reference_model_with_trees`: The same model test with hierarchical `QuorumTree` quorum sets, including trees with `quorum_size` 0 (everything is a quorum) and deep nesting.
- `hegel_vec_progress_quorum_accepted_is_monotone_under_resets`: With `reset_entry_with` in the mix the documented contract is weaker: the quorum-accepted value never decreases (an accepted value is never withdrawn), it is never below what the current entries would justify, the ordering invariant still holds, and `upgrade_quorum_set` recomputes it exactly from the surviving entries.

**`src/quorum/quorum_intersection_test.rs`**
- `hegel_bridge_to_yields_pairwise_intersecting_quorums`: `bridge_to` must return an intermediate quorum set `X` with `self ~ X ~ other`: every quorum of `self` intersects every quorum of `X`, and every quorum of `X` intersects every quorum of `other`. This is the safety property that makes joint-consensus membership change correct; it is checked against an exhaustive enumeration of all quorums.
- `hegel_intersects_with_is_sound`: `intersects_with` may answer `None`, but a `Some` answer must be the exact relation: `Some(true)` only if every quorum pair intersects, `Some(false)` only if some pair is disjoint.
- `hegel_verify_intersection_is_exact_and_symmetric`: `verify_intersection` is documented as exact for any two `QuorumSet` implementations: it must agree with the pairwise enumeration for flat majorities, joints and trees, in every combination, and be symmetric.

**`src/quorum/quorum_set_test.rs`**
- `hegel_majority_quorum_matches_counting_oracle`: `BTreeSet::is_quorum` implements simple majority.
- `hegel_joint_quorum_is_majority_in_every_config`: A joint quorum set grants iff the granted set is a majority in every config.
- `hegel_quorum_is_upward_closed`: The `QuorumSet` trait requires implementations to be upward-closed: adding more ids to a quorum must still be a quorum.
- `hegel_tree_quorum_matches_counting_model`: `QuorumTree::is_quorum` agrees with the documented counting rule, and `ids()` yields exactly the leaf ids, each once.
- `hegel_tree_quorum_obeys_quorum_set_rules`: The three `QuorumSet` rules hold for trees: upward-closed, closed over `ids()` (foreign ids never change the answer), duplicate-safe.
- `hegel_tree_identity_is_independent_of_child_order`: A tree's identity does not depend on the order its children were given in: building from a permutation of the same children gives an equal tree with the same canonical id and the same quorum decisions.
- `hegel_tree_construction_errors_match_documentation`: Construction rejects exactly the documented inputs: a repeated child is a `DuplicateChild` error naming that child, and a quorum size above the number of distinct children is `UnsatisfiableQuorum` with the right counts.

## Oracles

- Majority: an independent count (`overlap * 2 > config.len()`), applied per config for joints.
- Trees: an independent recursive count over `children()` / `quorum_size()`, and a recursive leaf
  walk for `ids()`.
- Quorum intersection: exhaustive enumeration of every subset of a 7-id universe as a bitmask,
  then pairwise intersection of the two quorum lists — independent of upstream's
  `verify_intersection`, which enumerates splits instead and is itself checked against it.
- `VecProgress`: upstream's own reference model `model_quorum_accepted` (highest value such
  that the ids at or above it form a quorum) plus its voter-ordering invariant check and
  `validit::Validate`; the properties generate the quorum configurations and operation
  sequences that upstream's seeded LCG tests fix.

Generated trees have 1–4 distinct children, nesting depth ≤ 2 and leaf ids in `0..7` (or
`0..=9` for `VecProgress`), with `quorum_size` drawn in `0..=children` so construction must
succeed; `QuorumTree` gets a `PrettyPrintable` impl (its `Display`) in `quorum_set_test.rs`
because Hegel prints every drawn value.

## Not tested

- The empty joint config (`vec![]`) in the intersection properties: it accepts the empty set as a
  quorum, so by definition it has quorum intersection with nothing; upstream's example tests
  cover it.
- `Display`/`canonical_id` formats (hash fallback for long ids), `DisplayVecProgress`,
  `ProgressStats`, the `IdVal` entry type and application data (`update_data_with`).
- `update_progress` with a value below the current one (documented as a caller error, checked by
  a debug assertion).

## History

- 2026-09-03: base commit `ea702b485e90` (refactor: style: where clauses, ID naming, quorum_tree.rs; 0.2.0).
- 2026-09-13: created in the zoo. Six properties moved here from the openraft target (where
  upstream had just removed the code: openraft's `Coherent::find_coherent` / `is_coherent_with`
  are `QuorumBridge::bridge_to` / `QuorumIntersection::intersects_with` here, and
  `VecProgress::update` is `update_progress` returning `Option`), seven written for the tree type,
  `verify_intersection` and resets. First run at hegeltest 0.44.1: 125 tests pass, also at a
  3000-case budget; no bug found. Runs on stable (`RUSTUP_TOOLCHAIN`)
  because upstream's `rust-toolchain` names a nightly this machine lacks; MSRV is 1.88.
