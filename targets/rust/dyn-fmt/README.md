# dyn-fmt

[dyn-fmt](https://github.com/A1-Triard/dyn-fmt) is the smallest of the run-time formatters:
`"{}a{}b".format(&[1, 2])` replaces the `{}`s of a format string supplied at run time with the
arguments in order ("a runtime analog of `format!`"), `{{`/`}}` are literal braces, missing
arguments are written as nothing and extra ones ignored; `Arguments::new` is the analog of
`format_args!` and `dyn_write!` of `write!`; `no_std`; 938k downloads. Written in the zoo at
0.4.3 (upstream HEAD `c8599e0`, 2024-09-08, "passively maintained"); tests in `tests/hegel.rs`.

## The oracle

The rustdoc sentence itself: a format string is generated piece by piece — text (multi-byte,
control characters, every punctuation but braces), `{{`, `}}`, `{}` — alongside the text
`format!` would produce for it, with arguments of mixed `Display` types whose strings may
themselves contain braces.

- `format_replaces_holes_like_format`: `str::format` and `String::format`, too few and too many
  arguments, references and trait objects.
- `arguments_and_dyn_write_agree_with_format`: `Arguments` through `{}` (twice — the iterator is
  cloned), `dyn_write!` into a `String` and into a `Vec<u8>`.
- `text_and_arguments_pass_through_unchanged`: a brace-free format string is copied verbatim; an
  argument containing braces is copied verbatim.
- `unmatched_braces_never_panic`: brace soup never panics and loses no text character.
- `doc_examples`: the rustdoc, the README and the upstream unit tests' brace cases.

## Bugs (2)

- **dyn-fmt/1** (wrong-result, medium; `outer_format_spec_is_not_applied_piecewise`):
  `format!("{:>10}", Arguments::new("ab{}cd", &[1]))` pads each of `ab`, `1`, `cd` to 10;
  `{:.1}` truncates every text piece to one character. `format_args!` ignores the outer spec, a
  `String` is padded as a whole; every piece separately is neither.
- **dyn-fmt/2** (contract, low; `hole_after_unpaired_close_brace_is_replaced`):
  `"a}{}b".format(&[1])` is `a{b` — the character after an unpaired `}` is taken as text even
  when it opens a `{}`.

## Not bugs

- Unpaired braces are not an error: `{x}` is `x`, a trailing `{` or `}` vanishes, `{{{}` is
  `{1`. Undocumented, pinned by upstream's `complex_case_*` tests, and `format!` would refuse
  the string; only the swallowed hole above is recorded.
- The `unreachable_unchecked` in the parser is guarded by the `is_empty` check before it.
