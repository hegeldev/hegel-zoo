# angstrom

Parsers built from a generated combinator tree (character, string, `take*`, `skip*`, `peek*`,
`advance`, `end_of_line`, `end_of_input`, `pos`, `commit`, `option`, `both`, `*>`, `<*`, `<|>`,
`count`, `many`, `many1`, `sep_by`, `consumed`, and `fix` for nested parentheses), run on inputs
built to match them.

## What is tested

- `parse_string_agrees_with_reference`: `parse_string` (`Prefix` and `All`) against a
  reference interpreter written from `angstrom.mli`.
- `buffered_agrees_with_reference`, `unbuffered_agrees_with_reference`: the input fed in chunks
  (sizes from 0) gives the same result and consumed length.
- `consumed_is_the_input_up_to_pos`, `bind_return_is_identity`, `fail_is_identity_of_alt`,
  `many_is_many1_or_nothing`, `consume_all_is_prefix_then_end_of_input`: laws.

`consumed` fails once its parser commits (the bytes may be gone); the reference models that.

## Not tested

`scan*`, the binary readers (`BE`/`LE`), bigstring variants, `Unsafe`, `available`, error
messages and marks, the Async/Lwt drivers.

## History

- 2026-10-09: created at 76c5ef5b (0.16.1+; upstream's last commit is 2024-09-11),
  hegel-ocaml 0.26.1; no bugs at 1000 test cases.
