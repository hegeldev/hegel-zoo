# calamine

[tafia/calamine](https://github.com/tafia/calamine).

## What is tested

**`src/xlsx/mod.rs`**
- `column_name_roundtrips`: PROPERTY: `column_number_to_name` produces a name that parses back to the same column index, for every valid column (0..MAX_COLUMNS). This is the cell-reference index<->name round-trip; it should hold for the entire valid column range including the XFD (MAX_COLUMNS-1) boundary.
- `reference_format_parse_roundtrip`: PROPERTY: a Reference (cell / column / row) formatted to text parses back to an equal Reference. Round-trip over the whole valid coordinate space, including absolute (`$`) markers and the MAX_ROWS / MAX_COLUMNS boundaries.
- `reference_parse_never_panics`: PROPERTY (parse robustness): `Reference::parse` must return Ok or Err on ANY byte string, never panic.
- `get_row_column_never_panics`: PROPERTY (parse robustness): `get_row` / `get_row_column` (used on the untrusted worksheet cell `r="A1"` attribute and on dimension strings) must never panic on arbitrary bytes. KNOWN FAILURE — real bug. `get_row_and_optional_column` accumulates the column with unchecked `col = col * 26 + ...` and the row with unchecked `row = row * 10 + ...`, so an over-long reference such as the 7-letter column "MWLQKWV" (or a long digit run) overflows u32 and panics in a debug/overflow-checked build instead of returning an Err. The sibling parser `Reference::parse` deliberately uses `wrapping_mul`/`wrapping_add` to avoid exactly this, so `get_row_column` is the inconsistent, panicking path. Oracle-independent panic. Pinned by drawing long letter-only refs.
- `column_number_to_name_bounds`: PROPERTY: `column_number_to_name` never panics on any u32 and enforces its documented bound (rejects col >= MAX_COLUMNS, succeeds below it).
- `get_dimension_never_panics`: PROPERTY (parse robustness): `get_dimension` (called on the untrusted `<dimension ref="...">` string) must never panic on arbitrary bytes. KNOWN FAILURE — real bug. `get_dimension` computes `end - start` with unchecked subtraction, so a reversed dimension such as `A2:A1` (a corrupt but syntactically valid worksheet dimension) underflows and panics ("attempt to subtract with overflow") in a debug/overflow-checked build instead of returning an Err. This is an oracle-independent robustness bug reachable from a crafted xlsx. Deterministically pinned by boosting toward reversed two-cell dimensions.
- `push_column_matches_column_number_to_name`: PROPERTY: `push_column` (used to render column references in XLS/XLSB formulas) must agree with the crate's own `column_number_to_name` (used for XLSX and validated by unit tests to match Excel's A/Z/AA/XFD scheme). KNOWN FAILURE — real bug. `push_column` drops the high-order digit for columns >= 26: it renders column 26 as "A" (not "AA") and column 27 as "B" (not "AB"). It is therefore also NOT injective — push_column(0) and push_column(26) both yield "A" — so distinct columns collide to the same formula reference. Oracle-independent (non-injective index->name mapping). Deterministically pinned: any column >= 26 fails, which is almost the entire drawn range.

**`tests/test.rs`**
- `readers_never_panic_on_arbitrary_bytes`: PROPERTY (arbitrary-bytes robustness): every statically-typed reader constructor must return Ok or Err on arbitrary bytes, never panic/hang.
- `auto_open_never_panics_on_arbitrary_bytes`: PROPERTY (arbitrary-bytes robustness): the format-sniffing entry point must not panic on arbitrary bytes; if it returns a workbook, iterating its sheets must also stay panic-free.
- `zip_magic_prefixed_bytes_never_panic`: PROPERTY (arbitrary-bytes robustness): bytes that begin with the ZIP local file header magic reach deeper into the zip/xlsx and ods decoders. They must still never panic. A crafted ZIP with a huge declared size must not OOM (the 4 KiB input cap keeps the test bounded either way).
- `corrupted_valid_xlsx_never_panics`: PROPERTY (valid-file-then-corrupt): start from a real, valid xlsx fixture, then flip bytes or truncate it. Opening the mutated file and reading every sheet must return Err gracefully, never panic.
- `expand_shared_formula_never_panics`: PROPERTY (parse robustness): `expand_shared_formula` is public and parses an untrusted formula template plus arbitrary source/target positions. It must return Ok or Err on any input, never panic.
- `data_accessors_are_consistent`: PROPERTY (Data conversions): the accessor/predicate methods on `Data` must be internally consistent and never panic. If `is_int` holds then `get_int` is Some; likewise for float/bool/string; and `as_string` never panics on any variant.
- `exceldatetime_to_ymd_never_panics`: PROPERTY (boundary values): `ExcelDateTime::to_ymd_hms_milli` is documented to "always return a date, even if the serial value is outside Excel's range". It must therefore never panic on any finite or non-finite f64. KNOWN FAILURE — real bug. For very large or infinite serials the internal `excel_datetime.floor() as u64` saturates to u64::MAX, and the subsequent `days += 109_572` overflows and panics ("attempt to add with overflow") in a debug/overflow-checked build instead of returning a (garbage-but-valid) date as documented. Oracle-independent panic. Pinned by boosting toward infinity / f64::MAX.

## Oracles

## Not tested

## History

- 2026-07-16: predecessor base commit `c53aff3d81a7` (support OOXML format (#681)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/calamine.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
