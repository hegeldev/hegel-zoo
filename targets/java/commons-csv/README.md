# commons-csv

[Apache Commons CSV](https://github.com/apache/commons-csv) (`org.apache.commons:commons-csv`; the pom carries
1.15.0-SNAPSHOT, the last release being v1.14.1; pinned at the master commit of 2026-09-07) reads and writes the CSV
dialects described by a `CSVFormat`: single- or multi-character delimiters, a quote character with five quote modes,
an escape character, comment lines, a null string, record separators, trimming and surrounding-space handling, headers
with duplicate/missing-name policies, `maxRows`, and byte/character positions per record. About 6 600 lines of source,
most of it `CSVFormat`. Its 1.15.0 change list already carries some thirty fixes from a recent hardening wave (quoting of
values starting with the comment marker, straddling multi-character delimiters, chunked reads, byte positions, the
trailing delimiter with quoted empty fields ...), so the parser/printer pair is well defended along its main seams.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the library from the pinned tree into
the local Maven repository (Javadoc, sources, checkstyle, PMD, SpotBugs, RAT, japicmp, CycloneDX, the enforcer and
signing skipped). The ASF Generative Tooling Guidance applies to contributions (disclosure), nothing stricter.

## The oracles

- **The values themselves**: records printed with a `CSVFormat` are parsed with the same format and must give the
  values back, as the Javadoc of the null string, the quote modes (`ALL_NON_NULL`/`NON_NUMERIC` distinguish an
  unquoted empty field, which is null, from a quoted one), `trim` and `ignoreSurroundingSpaces` describes; the model
  in `CsvGen.expected` says what each printed value reads back as (nulls, the null-string collision, whitespace).
- **Python's `csv` module** (`hegel/oracle.py`, a child process over JSON lines) and **FastCSV 4.0.0** (in process)
  as independent readers and writers of the RFC 4180 dialects: well-formed text with known rows is read by all three
  the same way, Commons CSV's output is read back by both, and both writers' output (all quote strategies) is read by
  Commons CSV.
- **Text models** for the parser's bookkeeping: record start offsets in characters and UTF-8 bytes (with the
  builder's character and byte offsets), the current line number, comments attached to records and the trailer
  comment, the first end-of-line string, headers (auto-detected or explicit, skipped or not, with
  `DuplicateHeaderMode`, `allowMissingColumnNames`, `ignoreHeaderCase`), `maxRows` and record numbering, the
  documented refusals of the format builder, and the `CSVFormat` value semantics (equals/hashCode, builder copy,
  serialization, the deprecated `with*` methods, `format()`).
- A `Reader` that hands the text out in one- to three-character chunks, so that the lookahead for multi-character
  delimiters and CR LF sees short reads.

`CsvGen.format` draws delimiters (single characters including space and letters, multi-character strings), quote,
escape and comment characters, quote modes, null strings, record separators (LF, CR LF, CR), the boolean options, and
the predefined formats (`EXCEL`, `MYSQL`, `POSTGRESQL_CSV`, ...); values are strings over an alphabet holding every
special character of the format plus control characters, Unicode whitespace and surrogate pairs, `null`, JDK numbers,
`StringBuilder`s, `Reader`s and `InputStream`s (printed as Base64).

## Properties (`CommonsCsvTest`, 2; `CommonsCsvParserTest`, 3)

- `printerParserRoundTrip`: random format, records printed through `printRecord(Object...)`, `printRecord(Iterable)`,
  `printRecord(Stream)` and `print`/`println`, optional header comments; the parser gives the modelled values back,
  `getRecordCount` and `getRecordNumber` agree, comments arrive on the first record or as the trailer, and
  `CSVFormat.format(values)` is the printer's record without the separator.
- `rfcDialectsAgreeWithPythonAndFastCsv`: the three-way agreement on generated RFC text (empty lines, quoted fields
  with delimiters, quotes and line breaks, CR/LF/CR LF, unterminated last line), Commons CSV's printer output
  (`MINIMAL`, `ALL`, `NON_NUMERIC`) read by Python and FastCSV, Python's writer (`QUOTE_MINIMAL/ALL/NONNUMERIC`) and
  FastCSV's writer (`REQUIRED`, `ALWAYS`, `NON_EMPTY`, `EMPTY`) read by Commons CSV, the all-quoted writer read by
  `RFC4180`, `EXCEL` and `DEFAULT`.
- `headersMatchTheModel`: header modes against the model of the format's and the parser's validation, `getHeaderMap`,
  `getHeaderNames` (unmodifiable), `CSVRecord.get(int/name/null)`, `isSet`, `isMapped`, `isConsistent`, `toMap`,
  `putIn`, `values`, `stream`, record numbers from `setRecordNumber`, `maxRows` on the iterator, `getRecords`,
  `stream` and the printer's `printRecords`, `hasNext`/`next` at the end and after `close`, the header written by the
  printer unless skipped.
- `positionsAndCommentsMatchTheText`: texts of records, comment lines and empty lines with mixed line breaks, parsed
  from a `String` and from the chunked reader with `trackBytes`: values, `getCharacterPosition`, `getBytePosition`,
  `getComment`, `getCurrentLineNumber` after each record (read with `next()` alone, since `hasNext()` reads ahead),
  `getTrailerComment`, `getFirstEndOfLine`; then junk after a closing quote (`trailingData` or whitespace) and an
  unterminated quote (`lenientEof`).
- `formatsAreValues`: random builder settings: the documented `IllegalArgumentException`s (quote/escape/comment inside
  the delimiter, comment equal to quote or escape, `NONE` without an escape, duplicate header names per mode), every
  getter, `getHeader()` copies, `equals`/`hashCode`/`toString` of a builder copy, `maxRows`/`trailingData`/`lenientEof`
  in `equals`, Java serialization, the deprecated `with*` methods against the builder, the quoted null string in
  `QuoteMode.ALL` whatever the order of `setQuote`/`setNullString`, `format()` and `printRecord(Appendable)` against
  the printer, `Predefined`/`valueOf`, `newFormat`.

Known-bug shapes are skipped, never worked around: a null whose null string starts with the comment marker and a null
in a quote-less `QuoteMode.ALL` format are replaced by a plain value (1, 6); multi-character delimiters made of the
letters `r n t b f` are not generated (2); `isConsistent` is not checked when header names repeat (3);
`getFirstEndOfLine` is not checked when the text starts with a comment line (4); a format the parser refuses for a
case-insensitive duplicate header is accepted from the builder (5).

## Not tested

`printRecords(ResultSet)`/`printHeaders(ResultSet)`/`setHeader(ResultSet)` (JDBC), `setHeader(Class<Enum>)`,
`parse(File/Path/URL/InputStream)`, `CSVFormat.print(File/Path)`, `printer()`, byte-order marks, `autoFlush`,
record separators that are not line breaks (the Javadoc warns), concurrent printing.

## Bugs found

| id | severity | summary |
|---|---|---|
| commons-csv/1 | low | a null string starting with the comment marker is printed bare: the record reads back as a comment line |
| commons-csv/2 | low | escape mode: a value ending in a prefix of a multi-character delimiter containing `r n t b f` is not escaped and misread |
| commons-csv/3 | low | `CSVRecord.isConsistent` compares with the number of distinct header names |
| commons-csv/4 | low | `getFirstEndOfLine` ignores the line breaks ending comment lines |
| commons-csv/5 | low | a header differing only in case passes the format's duplicate check under `ignoreHeaderCase`, the parser then rejects it |
| commons-csv/6 | low | `QuoteMode.ALL` without a quote character prints the null string between double quotes |

Observed, not recorded: a record consisting of one null value in `QuoteMode.ALL` (no null string) prints as an empty
line and is dropped by `ignoreEmptyLines` — the fix for the same shape in the minimal mode (#629) excludes `ALL`
deliberately, as the source comment says; the header record read from the input does not advance record numbers (the
first data record is number 1, or the builder's `setRecordNumber`), as upstream's tests assert; `toMap()` iterates in
the header map's order, case-insensitively sorted under `ignoreHeaderCase`; an empty comment (`#` alone) on an
unterminated last line is not reported as the trailer comment while `#\n` is; `format()` keeps the trailing
delimiter; `getDelimiter()` (deprecated) returns the first character of a multi-character delimiter, as documented;
`print(InputStream)` writes plain Base64 with the pom's commons-codec 1.22.1 (1.19 would chunk it with CR LF).
FastCSV 4.0.0 loses quoted fields that contain a lone CR (its own defect; the FastCSV comparisons skip such rows).

## History

- 2026-09-16: created (turn 181) at bb0f0fbb0f84 (1.15.0-SNAPSHOT of 2026-09-07, after v1.14.1); 6 bugs.
- 2026-09-20: base bumped bb0f0fbb0f84 → 417d6a4502a2 (2026-09-19, "Bump github/codeql-action/* from 4.37.9 to 4.38.1"; 1.15.0-SNAPSHOT); 6 bug(s) still reproduce. 5 tests pass.
