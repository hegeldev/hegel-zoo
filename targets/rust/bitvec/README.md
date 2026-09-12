# bitvec

[ferrilab/bitvec](https://github.com/ferrilab/bitvec).

## What is tested

**`src/field/tests.rs`**
- `store_load_roundtrip`: `store_le`/`load_le` and `store_be`/`load_be` roundtrip any value through any legal field region, truncating to the field width and leaving all other bits alone, in both orderings.

**`src/slice/tests/api.rs`**
- `rotate_matches_bool_oracle`: `rotate_left`/`rotate_right` on an arbitrary subslice agree with the `Vec<bool>` oracle, under both orderings.
- `reverse_matches_bool_oracle`: `reverse` on an arbitrary subslice agrees with `<[bool]>::reverse` and leaves surrounding bits alone.

**`src/slice/tests/iter.rs`**
- `iteration_matches_bool_oracle`: Iteration (forward, reverse, and `len`) matches the `Vec<bool>` oracle.
- `chunks_match_bool_oracle`: `chunks`/`rchunks` match the `Vec<bool>` oracle.
- `chunks_exact_matches_bool_oracle`: `chunks_exact`/`rchunks_exact` (and remainders) match the `Vec<bool>` oracle.
- `windows_match_bool_oracle`: `windows` over an arbitrary subslice agrees window-for-window with `<[bool]>::windows`.

**`src/slice/tests/ops.rs`**
- `bitand_assign_matches_bool_oracle`: `&=` ANDs against the zero-extended right-hand side: excess bits of `self` are cleared. Checked on both the specialized same-type/same-ordering paths and the bit-by-bit mixed paths.
- `bitor_assign_matches_bool_oracle`: `|=` ORs against the zero-extended right-hand side: excess bits of `self` are untouched.
- `bitxor_assign_matches_bool_oracle`: `^=` XORs against the zero-extended right-hand side: excess bits of `self` are untouched.
- `not_on_subslice_inverts_only_that_range`: `!` on a subslice inverts exactly the bits inside the subslice and leaves the surrounding bits alone, even when the boundaries split a storage element.

**`src/slice/tests.rs`**
- `counting_and_searching_match_bool_oracle`: Every counting/searching query on an arbitrary subslice must agree with the `Vec<bool>` oracle, under both orderings and several storage widths.
- `shifts_match_bool_oracle`: `shift_start`/`shift_end` on an arbitrary subslice agree with the `Vec<bool>` oracle and do not disturb surrounding bits.

**`src/vec/tests.rs`**
- `model_u8_msb0`: (no doc comment)
- `model_u16_lsb0`: (no doc comment)
- `raw_slice_layout_matches_documented_encoding`: The buffer returned by `as_raw_slice` must match the documented in-memory encoding: under `Lsb0`, semantic bit `i` is bit `i % width` counting up from the least significant bit of element `i / width`; under `Msb0` it counts down from the most significant bit.
- `not_inverts_every_live_bit`: `!BitVec` must invert every live bit and preserve the length.

**`tests/equality.rs`**
- `?`: The same logical bit sequence is `==` no matter which storage type and bit-ordering hold it, and flipping any single bit breaks the equality.
- `?`: `to_bitvec` of an arbitrary subslice preserves the logical contents, regardless of the head offset of the source slice (Issue #10 class).
- `?`: Comparison of bit-slices is the lexicographic order of their `Vec<bool>` models, even across differing storage and ordering parameters.

## Oracles

## Not tested

## History

- 2023-04-12: predecessor base commit `5fb855073acc` (Merge pull request #201 from connorskees/feat/add-track-caller).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/bitvec.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
