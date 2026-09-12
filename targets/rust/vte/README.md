# vte

[alacritty/vte](https://github.com/alacritty/vte).

## What is tested

**`src/ansi.rs`**
- `processor_advance_never_panics`: Property: `Processor::advance` never panics and never fails to make progress, for arbitrary bytes (with synchronized-update escapes mixed in to exercise the sync buffering path) fed in arbitrary chunks.

**`src/lib.rs`**
- `advance_never_panics_on_arbitrary_chunked_input`: Property: `advance` never panics, for arbitrary bytes fed in arbitrary chunks through a single reused parser (parse robustness).
- `chunked_advance_equals_whole_input_advance`: Property: feeding input in arbitrary chunks produces exactly the same dispatch sequence as feeding it in one call. The `partial_utf8` buffer exists precisely to guarantee this (see the `partial_utf8*` unit tests).
- `print_never_receives_control_chars`: Property: `Perform::print` never receives C0/C1 control characters; those are documented to go through `Perform::execute` instead (see `ground_dispatch`).
- `execute_only_receives_control_bytes`: Property: `Perform::execute` only receives C0/C1 control function bytes, per its documentation.
- `csi_roundtrip`: Property: a well-formed CSI sequence built from arbitrary parameters, subparameters, an optional private marker, and intermediates round-trips through the parser into a single `csi_dispatch` with exactly that data.
- `osc_roundtrip`: Property: an OSC sequence built from arbitrary parameter byte strings round-trips through the parser into a single `osc_dispatch` with exactly those parameters and the right terminator flag.
- `csi_param_saturates_at_u16_max`: Property: numeric CSI parameters saturate at `u16::MAX` instead of overflowing (see `action_paramnext` and `parse_long_csi_param`). Leading zeros must not affect the value.
- `dcs_hook_put_unhook_protocol`: Property: the DCS callback protocol documented on `Perform` holds for arbitrary input: `put` and `unhook` only occur between a `hook` and its matching `unhook`, and hooks never nest.
- `dispatched_data_respects_size_limits`: Property: dispatched data always respects the documented size limits: at most `MAX_PARAMS` (sub)parameters, `MAX_INTERMEDIATES` intermediates, `MAX_OSC_PARAMS` OSC parameters, and CSI action chars in `0x40..=0x7E`.
- `advance_until_terminated_resumes_to_same_dispatches`: Property: `advance_until_terminated` is documented as equivalent to `advance`; terminating at arbitrary points and resuming with the remaining bytes must produce the same dispatch sequence overall.

**`src/params.rs`**
- `params_agree_with_model`: (no doc comment)
- `params_iter_size_hint_is_consistent`: Property: `ParamsIter::size_hint` must satisfy the `Iterator` contract: lower bound <= actual number of items <= upper bound.

## Oracles

## Not tested

## History

- 2026-02-28: predecessor base commit `abeae765dd54` (Add rustdoc attribute to ansi module).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/vte.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. Two upstream
  `assert_eq!(intermediates, &[])` sites in `src/lib.rs` rewritten as `assert!(intermediates.is_empty())`: with
  hegeltest's `serde_json` in scope the empty array's element type is ambiguous (E0282/E0283).
