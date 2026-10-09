# containers

`containers` and `containers-data`: string and list functions, integer helpers, UTF-8 and
S-expressions against stdlib models, and six data structures as state machines against lists.

## What is tested

- `string_find`, `string_rfind`, `string_find_all`, `string_replace`, `string_split`,
  `string_pad`, `string_edit_distance`: against a naive scan, and a Levenshtein table.
- `list_sublists_of_len`, `list_range_by`, `list_group_by`, `list_uniq` (keeps the last
  occurrence): against list models.
- `list_sorted_diff_inverts_merge`, `list_sorted_remove_inverts_insert`: the documented inverses,
  and `List.merge`.
- `int_range_by`, `int_floor_div_rem`, `int_pow`, `int_popcount`, `int_to_string_binary`.
- `utf8_is_valid` (against `String.is_valid_utf_8`, with overlong, surrogate and truncated
  sequences), `utf8_to_list`, `sexp_roundtrip`.
- `vector_machine`, `deque_machine`, `bitvector_machine`, `heap_machine`, `fqueue_machine`,
  `ral_machine`: `CCVector`, `CCDeque`, `CCBV`, `CCHeap`, `CCFQueue` and `CCRAL` against lists.
- `deque_append_self`: a deque appended to itself.

`CCList.range_by` and deque self-appends run in a forked child with a deadline and a capped
heap: containers/1 and containers/3 can allocate without bound or never return.

## Not tested

The rest of both packages, including `CCParse`, `CCFormat`, the hash tables and maps, and the
`containers.*` sub-libraries.

## History

- 2026-10-09: created at 3a2bba39 (3.18), hegel-ocaml 0.26.1; four bugs.
