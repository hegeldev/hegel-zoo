# chalk

[rust-lang/chalk](https://github.com/rust-lang/chalk).

## What is tested

**`tests/hegel_properties.rs`**
- `identity_fold_is_identity`: Folding a term with a do-nothing folder is the identity. The default `try_super_fold_with` impls destructure and re-intern every `TyKind` variant, so any variant whose fields are dropped, reordered, or re-adjusted incorrectly would fail this.
- `shift_in_then_out_is_identity`: `shifted_in_from(n)` followed by `shifted_out_to(n)` is the identity on whole terms (documented inverse relationship in `fold/shift.rs`).
- `shift_out_then_in_is_identity`: If `shifted_out` succeeds, `shifted_in` restores the original term: success means no variable was bound by the eliminated level, so the downshift is invertible.
- `needs_shift_iff_shift_changes_term`: `needs_shift` (implemented via the *visitor* free-variable search) agrees exactly with whether shifting (implemented via the *folder*) actually changes the term. This cross-checks the visit and fold implementations of "free variable" against each other.
- `bound_var_shift_roundtrip`: `BoundVar::shifted_in_from(o)` then `shifted_out_to(o)` round-trips. Depths are capped at 2^16 here because the unchecked arithmetic in `DebruijnIndex::shifted_in_from` overflows near `u32::MAX`; that bug is pinned by the KNOWN FAILURE test `debruijn_shift_overflows_at_boundary`.
- `shifted_out_none_iff_within`: `shifted_out_to` returns `None` exactly when the index is bound within the outer binder (documented in `DebruijnIndex::shifted_out_to`).
- `debruijn_shift_overflows_at_boundary`: KNOWN FAILURE: `DebruijnIndex::shifted_in_from` computes `self.depth() + outer_binder.depth()` with unchecked arithmetic (chalk-ir/src/lib.rs). For depths whose sum exceeds `u32::MAX` this panics with "attempt to add with overflow" in debug builds and silently wraps (corrupting the index) in release builds. Neither `DebruijnIndex::new` nor `shifted_in_from` documents any bound on the depth. The generator draws both depths from [2^31, u32::MAX], so every case overflows and the failure is deterministic.
- `subst_and_substitution_apply_agree`: chalk-ir contains two independent substitution folders: `Subst` (chalk-ir/src/fold/subst.rs, used by `Binders::substitute`) and `SubstFolder` (chalk-ir/src/lib.rs, used by `Substitution::apply`). On terms in both domains -- all free variables refer to the innermost binder -- they must agree.
- `subst_after_shift_in_is_identity`: Substituting into a term that was just shifted *in* is a no-op: the shift guarantees no variable refers to the innermost binder, so the substitution merely undoes the shift (this is the binder-elimination semantics documented on `Subst`). The parameter list is irrelevant -- even an empty one works.
- `identity_substitution_is_recognized`: `Binders::identity_substitution` produces a substitution that `Substitution::is_identity_subst` recognizes as the identity.
- `substitute_identity_is_noop`: Substituting the identity substitution into a binder's value leaves the value unchanged.
- `subst_leaves_out_of_range_vars_untouched`: KNOWN FAILURE: the documentation on `Subst::parameters` (chalk-ir/src/fold/subst.rs) promises that a free variable with index `i >= parameters.len()` "will be left untouched", but `fold_free_var_ty` indexes `self.parameters[index]` unconditionally and panics with an index-out-of-bounds error instead. Every generated case uses an empty parameter list and a free variable, so the failure is deterministic.
- `could_match_is_reflexive`: `could_match` is documented as "a fast check to see whether two things could ever possibly match"; it over-approximates unifiability, so it must at minimum be reflexive. A missing or wrong arm in its big `TyKind` match would break this.
- `cast_ty_to_generic_arg_roundtrips`: Casting a `Ty` to a `GenericArg` and projecting it back yields the original type (and the kind accessors agree that it is a type).

## Oracles

## Not tested

## History

- 2026-02-08: predecessor base commit `627409a4735b` (Merge pull request #833 from Noratrieb/patch-1).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/chalk.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
