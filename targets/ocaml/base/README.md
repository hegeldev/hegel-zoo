# base

Jane Street's `Base`: integer and float conversions and rounding, string and list functions,
`Map`, `Set` and `Hashtbl`, and the S-expression printers. Python 3 is the oracle for numbers,
encodings and S-expression reading; the rest is judged against list models. Built from the
`oxcaml` branch in an OxCaml switch, as upstream's master needs unreleased Jane Street libraries.

## What is tested

- `int_*`, `int32_*`, `int64_*`, `nativeint_*`, `int63_emul_*` (`Int63.Private.Emul`, `Int63`
  on 32-bit and JavaScript): `conversions` (`to_string`, `to_string_hum`, `Hex`, `Binary`, sexp
  and back), `arith` (`/`, `rem`, `%`, `/%`, `round_*`, log2 and pow2 functions, `popcount`,
  `clz`, `ctz`), `pow` (raises exactly on overflow).
- `float_to_string` (round trip, shortest digits), `float_round` (`round_*`, `iround_*`),
  `float_round_significant`, `float_round_decimal` (within the documented ulp),
  `float_to_string_hum`, `float_to_padded_compact_string` (`_custom` too).
- `string_search` (`Search_pattern`, `substr_*`, `Caseless`), `string_split`, `string_trim`,
  `string_tr_multi`, `string_escaping` (`String.Escaping`), `string_utf` (`Utf8`, `Utf16le/be`,
  `Utf32le/be`).
- `range` (`List.range`, `Sequence.range`), `list_slicing`, `list_sorting` (stability, which
  duplicate is kept), `array_sorting` (with the private sorts), `array_binary_search`.
- `sexp_printers_read_back`: `Sexp` and `Sexp.Utf8_as_string` printers.
- `map_machine`, `set_machine`, `hashtbl_machine`: against sorted association lists.

## Not tested

`Int63` itself (it is `Int` on 64-bit), the rest of `Float`, `Bytes`, `Char`, `Option`, `Result`,
`Or_error`, `Queue`, `Stack`, `Sequence` beyond `range`, the `_or_null` and local variants, and
`t_of_sexp` for containers.

## History

- 2026-10-09: created at 858a66ad (v0.18~preview.130.106+341), hegel-ocaml 0.26.1; five bugs.
