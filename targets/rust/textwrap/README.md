# textwrap

[mgeisler/textwrap](https://github.com/mgeisler/textwrap).

## What is tested

**`src/core.rs`**
- `hegel_break_apart_partitions_word`: `Word::break_apart` must partition the word content, in order, into pieces of width at most `line_width` (a single `char` cannot be broken and can be up to 2 columns wide, hence the `max(2)`). Interior pieces carry no whitespace/penalty, the last piece inherits both, and every piece's cached width must agree with `display_width`.

**`src/fill.rs`**
- `hegel_fill_is_wrap_joined_with_line_ending`: `fill()` docs: "The result is a `String`, complete with newlines between each line. Use `wrap()` if you need access to the individual lines." — so `fill` must equal `wrap` joined with the configured line ending. The slow path is this join by construction; the property pits `fill`'s fast path against `wrap` (the public-API version of the `fill_fast_path` fuzz target, with generated `Options` instead of the defaults). KNOWN FAILURE (library bug): `fill()`'s fast path above ignores `Options::preserve_trailing_space` and unconditionally calls `text.trim_end_matches(' ')`, while `wrap_single_line()`'s fast path honours the option. Minimal counterexample: `fill(" ", Options::new(2).preserve_trailing_space(true))` returns `""`, but `wrap()` returns `[" "]` (and `fill_slow_path` returns `" "`). The option was added in commit 81e11fa, which updated wrap's fast path but not fill's. `test_cases` is raised because the failure needs the coincidence preserve_trailing_space && trailing ' ' && text.len() < width, which the default 100 cases often miss.
- `hegel_fill_inplace_matches_documented_fill_options`: `fill_inplace()` docs give an exact equivalence: it "behaves as if you had called `fill()`" with `break_words(false)`, LF line ending, `AsciiSpace` word separator, `FirstFit` wrap algorithm and `NoHyphenation` word splitter — except that `fill_inplace` "can leave trailing whitespace on lines". Compare the two line by line, modulo trailing spaces.

**`src/indentation.rs`**
- `hegel_dedent_undoes_indent`: `indent()` adds a fixed prefix to every non-blank line; `dedent()` "removes common leading whitespace from each line". When the common leading whitespace of the indented text is exactly the added prefix, dedent must undo indent. That holds when the prefix is pure whitespace, every non-blank input line starts at column zero (there is at least one), no line is whitespace-only (dedent drops the content of whitespace-only lines), and there are no '\r' characters (dedent uses `str::lines`, indent splits on '\n').

**`src/refill.rs`**
- `hegel_unfill_recovers_filled_paragraph`: `unfill()` docs: it "attempts to recover the original text from a single paragraph of wrapped text, such as what `fill()` would produce". For a paragraph of single-space-separated alphanumeric words (no characters unfill treats as prefixes, no hyphens) filled without word breaking, recovery must be exact and no indentation may be detected.
- `hegel_unfill_refill_never_panic`: Port of the `unfill` and `refill` fuzz targets: neither function may panic, no matter the input text or width.

**`src/word_separators.rs`**
- `hegel_find_words_reassemble_line`: `wrap_single_line_slow_path` relies on this: "We assume here that all words are contiguous in `line`. That is, the sum of their lengths should add up to the length of `line`." — every `WordSeparator` must produce words which, together with their trailing whitespace, reassemble the line exactly (and word separators never attach penalties).
- `hegel_found_word_widths_match_display_width`: `Word::width` is documented as "Cached width in columns" — it must agree with `core::display_width` for every word any separator finds.

**`src/wrap.rs`**
- `hegel_wrap_break_words_fits_width`: `Options::break_words` docs: "Allow long words to be broken if they cannot fit on a line. When set to `false`, some lines may be longer than `self.width`." — so with `break_words = true` (and no indentation, no preserved trailing whitespace), every output line must fit within the width. A single `char` cannot be broken any further and can be up to 2 columns wide, hence the `max(2)`. Restricted to `FirstFit`: the optimal-fit algorithm documents that it may deliberately overflow a line (see `Penalties::overflow_penalty`).
- `hegel_wrap_preserves_non_space_content`: Wrapping must never lose or invent content: per the "Leading and Trailing Whitespace" doc section, the output is the input words with only (trailing) `' '` whitespace dropped and line endings redistributed. So after deleting spaces and line-ending characters, input and output must be identical.
- `hegel_wrap_is_idempotent`: Wrapping already-wrapped text with the same options must be a no-op: every produced line already fits the options, so re-wrapping must not move content between lines. (Without indentation — indents are added on every pass and are trivially not idempotent.)

**`src/wrap_algorithms/optimal_fit.rs`**
- `hegel_wrap_optimal_fit_usize_widths_partition`: Port of the `wrap_optimal_fit_usize` fuzz target: fragments with integer widths ("of the same form as the ones generated by wrap" — the docs promise "when using fragment widths and line widths which fit inside an `u64`, overflows cannot happen") plus arbitrary penalties must never panic, must return `Ok`, and the result must partition the fragments in order.

**`src/wrap_algorithms.rs`**
- `hegel_wrap_first_fit_partitions_and_fits`: `wrap_first_fit` accumulates fragments "one by one and when a fragment no longer fits, start a new line". The output must partition the input fragments in order, and every line must fit its target width — except that a line's *first* fragment is allowed to overflow, since the function "will not (and cannot) attempt to split" fragments. Fragment and line widths are drawn as `u32` so that all sums are exactly representable in `f64` (the fit check below would otherwise be subject to rounding differences); this protects the test's oracle, not the library, which is documented to work with arbitrary `f64` widths.

## Oracles

## Not tested

## History

- 2026-06-28: predecessor base commit `e29daecac529` (Merge pull request #619 from mgeisler/rename-master-to-main).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/textwrap.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped e29daecac529 → 7d1435f71454 (2026-09-12, "Merge pull request #628 from xtqqczze/msrv-reduce"; 0.16.3); 1 bug(s) still reproduce. 234 tests pass.
- 2026-09-13: base bumped 7d1435f71454 → 7debe996ca88 (2026-09-13, "Merge pull request #629 from xtqqczze/authors"; 0.16.3); 1 bug(s) still reproduce. 234 tests pass.
- 2026-09-13: 10× budget run (`--test-cases 1000`) failed `hegel_wrap_is_idempotent`: new bug
  **textwrap/2** — with `UnicodeBreakProperties` and `break_words`, a space after opening
  punctuation stays inside the word (UAX #14 LB14), so `wrap("( ab", 2)` is `["( ", "ab"]`, a
  line with trailing whitespace the docs say is discarded, and re-wrapping differs. Pinned as an
  intermittent expected failure.
- 2026-09-13: base bumped 7debe996ca88 → 85da244320f3 (2026-09-13, "Merge pull request #632 from xtqqczze/lint-fuzz"; 0.16.3); 2 bug(s) still reproduce. 233 tests pass.
- 2026-09-13: base bumped 85da244320f3 → 932bd45e244d (2026-09-13, "Merge pull request #634 from mgeisler/update_dprint_plugins"; 0.16.3); 2 bug(s) still reproduce. 233 tests pass.
- 2026-09-13: base bumped 932bd45e244d → 5246c6367058 (2026-09-13, "Merge pull request #638 from mgeisler/release-0.16.4"; 0.16.4); 2 bug(s) still reproduce. 233 tests pass.
- 2026-09-13: base bumped 5246c6367058 → 6df2560c0d87 (2026-09-13, "Merge pull request #641 from mgeisler/update-agent-guidelines-tooling"; 0.16.4); 2 bug(s) still reproduce. 233 tests pass.
- 2026-09-14: base bumped 6df2560c0d87 → 655a60a8af0d (2026-09-14, "Merge pull request #642 from mgeisler/crates-io-trusted-publishing"; 0.16.4); 2 bug(s) still reproduce. 233 tests pass.
- 2026-09-14: base bumped 655a60a8af0d → c54a1f3e8f24 (2026-09-14, "Merge pull request #644 from mgeisler/document-pr-separation-of-concerns"; 0.16.4); 2 bug(s) still reproduce. 233 tests pass.
- 2026-09-15: base bumped c54a1f3e8f24 → 9b2e24ad12d3 (2026-09-15, "Merge pull request #645 from mgeisler/cleanup-wasm-demo-draw-text-arguments"; 0.16.4); 1 bug(s) still reproduce; intermittent, not seen this run: textwrap/2. 233 tests pass.
- 2026-09-15: base bumped 9b2e24ad12d3 → f26a8df61bff (2026-09-15, "Merge pull request #646 from mgeisler/deploy-pages-via-actions"; 0.16.4); 1 bug(s) still reproduce; intermittent, not seen this run: textwrap/2. 233 tests pass.
- 2026-09-17: base bumped f26a8df61bff → 07fdbbb92103 (2026-09-17, "Merge pull request #647 from youdie006/saturate-column-padding"; 0.16.4); 1 bug(s) still reproduce; intermittent, not seen this run: textwrap/2. 235 tests pass.
