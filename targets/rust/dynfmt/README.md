# dynfmt

[dynfmt](https://github.com/jan-auer/dynfmt) formats strings dynamically: a `Format` trait over
run-time format strings and `serde::Serialize` arguments, with `PythonFormat` ("the
`printf`-like format that python 2 used for formatting strings": `%(key)s`, flags, width,
precision, `[hlL]`, `d i o u x X e E f F g G c r s %`), `SimpleCurlyFormat` (`{}`, `{0}`,
`{name}`) and `NoopFormat`; 800k downloads, 0.2.0 released 2026-08. Written in the zoo at 0.2.0
(upstream HEAD `d970fe6`, 2026-08-12); tests in `tests/hegel.rs`, run with `--all-features`.

## The oracle

Python itself: the tests hold one `python3` child process open and ask it `fmt % args` for the
same format string and the same arguments (integers, strings, a list or a dict), so every
expected value in the pinned tests is Python's, not ours. Where the crate documents a Rust
choice — `%s` is `Display`, `%r` is JSON, arguments are Rust values (`true`, not `True`) — the
differential keeps to what both define.

- `specs_format_like_python`: one to five specs `%[#][-][h|l|L](d|i|u|o|x|X|s|c|%)`, positional
  or `%(key)`-named, integers (non-negative for the radix forms, `#` not with `X`) and strings
  (some containing `%`), text with multi-byte and control characters around them.
- `argument_errors_and_format_into`: `MissingArg(Index(n))` at the first missing index,
  `MapRequired`, `ListRequired`, `MissingArg(Key)`, `format_into` = `format`, a spec-free string
  is returned `Borrowed`.
- `curly_format_follows_its_contract`: `{}`, `{0}`, `{name}` against a model of the three
  documented rules, the auto counter continuing after an explicit index.
- `doc_examples`.
- The general generator avoids the pinned shapes: widths, precisions, `+`/` `/`0`, floats,
  negative radix forms, `%c` of an integer, non-integers under `%d`, unknown conversions, and
  text beginning with a digit or `*` right after a spec (dynfmt/4).
- The format strings are built as data and rendered by pure functions: a `Vec<Spec>`
  (conversion, value, flags, modifier, trailing text) rendered by `Spec::render`, with the
  `%(key)` names drawn as a set so they are distinct by construction; a `CurlyCall` of `Hole`s
  for the curly format. The shrinker can therefore drop a spec whole. Rewritten in combinator
  style 2026-09-23 (same properties and pins).

## Bugs (10)

- **dynfmt/1** (wrong-result, high; `width_and_flags_are_applied`): width and the `-` `0` `+`
  flags are parsed into `ArgumentSpec` and never applied — `%5d` of 3 is `3`.
- **dynfmt/2** (wrong-result, high; `precision_is_applied`): precision likewise — `%.3d` of 5 is
  `5`, `%.2s` of `hello` is `hello` — and floats have no default six digits: `%f` of 1.0 is `1`.
- **dynfmt/3** (wrong-result, high; `star_consumes_an_argument`): `%*d` of (5, 42) is `5`; the
  size argument is formatted as the value and every later argument shifts.
- **dynfmt/4** (wrong-result, medium; `precision_needs_a_dot`): the precision regex's dot is
  unescaped — `%d5d` is one spec, `%%0%%` prints `%%`, `%%5d` consumes an argument.
- **dynfmt/5** (wrong-result, medium; `space_flag_is_recognised`): `(?x)` drops the space from
  the flag class — `% d` is copied literally.
- **dynfmt/6** (wrong-result, medium; `negative_radix_forms_have_a_sign`): `%x` of -255 is
  `ffffffffffffff01` (and depends on the Rust integer type); Python `-ff`.
- **dynfmt/7** (contract, low; `char_conversion_of_an_integer`): `%c` of 65 is `65`.
- **dynfmt/8** (contract, medium; `integer_conversions_take_integers`): `%d` of 3.7 is `3.7`, of
  `"abc"` is `abc`.
- **dynfmt/9** (contract, low; `unknown_conversions_are_errors`): `%z` and a trailing `%` are
  copied as text; `Error::BadFormat` is unreachable.
- **dynfmt/10** (contract, low; `alternate_upper_hex_prefix_is_upper`): `%#X` is `0xFF`
  (upstream's test pins it).

## Not bugs

- Extra positional arguments are ignored where Python raises `TypeError`; `%r` is JSON, not
  `repr`; `%s` of a Rust `bool` is `true`; `%#o` is `0o52` (Python 3's form, Python 2 printed
  `052`); `%e` writes Rust's `4.2e0` exponent form (pinned upstream — the missing digits are
  dynfmt/2).
- `SimpleCurlyFormat` has no `{{` escape and no specs — documented as a subset.
- The `unsafe` in `FormatterTarget::convert` (a `ptr::swap` with an uninitialised placeholder)
  is sound as long as `into_inner` cannot panic; read, not tested.
