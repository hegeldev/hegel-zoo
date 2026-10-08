# go/parquet-go: files written by parquet-go read by pyarrow, and files written by pyarrow read by parquet-go

[parquet-go](https://github.com/parquet-go/parquet-go) reads and writes Apache Parquet files from
Go values: struct tags declare the schema (logical types, encodings, compression, lists, maps,
optional fields) and the library writes pages, dictionaries, statistics and indexes. This target
generates schemas and rows, writes them with parquet-go and has pyarrow (parquet-cpp) read the
files back, so that what parquet-go writes is what the reference implementation reads; and in
the other direction has pyarrow write the files, for its own writer options, and parquet-go read
them.

The tests live in `hegel/`, a package added by the patch; the oracle is `hegel/oracle.py`, a
child process speaking one JSON line each way (it needs python3 with pyarrow). Schemas are built
with `reflect.StructOf` and parquet struct tags from a generated spec: booleans, signed and
unsigned integers of every width, floats, strings, byte arrays, fixed-length arrays, UUID, JSON,
ENUM, decimals over INT32, INT64 and FIXED_LEN_BYTE_ARRAY, DATE, TIME and TIMESTAMP at every
unit, nested groups, optional fields (pointers), bare repeated fields, LISTs with optional or
required elements and MAPs, with plain, dictionary, delta and byte-stream-split encodings and
every compression codec per column; writer options cover data page versions, page and write
buffer sizes, page statistics, row-group size limits, key/value metadata, bloom filters and the
dictionary size limit. Rows are compared in a canonical form both sides produce (bits for
floats, unscaled integers for decimals, hex for binary).

Properties (`HEGEL_COLLECT=1` counts mismatches instead of failing, `HEGEL_TEST_CASES=n` sets
the case count):

- `TestHegelPyarrowReadsWhatParquetGoWrites`: pyarrow reads the file to the value, and its
  metadata says what the rows and options say: row counts per row group, the compression of
  every column, the encodings asked for, and for the flat columns the null count and the minimum
  and maximum of each row group (with the format's ordering per type, NaN excluded).
- `TestHegelReadsBackWhatItWrites`: parquet-go reads its own file back to the value through the
  reflection reader, and the row API yields as many rows.
- `TestHegelWriterPathsAgree`: the deprecated `Writer` (documented as behaving like
  `GenericWriter[any]`) writes the same rows to a file pyarrow reads to the same values.
- `TestHegelDamagedFilesNeverPanic`: a file with flipped, deleted, inserted or truncated bytes
  never makes `OpenFile` or reading its rows panic (`HEGEL_DUMP=dir` keeps the files that do).
- `TestHegelReadsWhatPyarrowWrites`: pyarrow writes the rows (the oracle's `write` op builds
  Arrow arrays from the canonical values) with generated `write_table` options - codec per file
  and per column, dictionary encoding, `column_encoding` (PLAIN, RLE, DELTA_BINARY_PACKED,
  DELTA_LENGTH_BYTE_ARRAY, DELTA_BYTE_ARRAY, BYTE_STREAM_SPLIT), data page version, statistics,
  row group size, page size, batch size, page index, `store_decimal_as_integer`, key/value
  metadata, and the LIST element name (`element`, or `item`/`array`/... with
  `use_compliant_nested_type=False`) - and parquet-go reads the file back to the value through
  the reflection reader; the row API yields the rows of every row group; the row groups, the
  key/value metadata, the column chunks' value and null counts, the statistics' bounds
  (`FileColumnChunk.Bounds`) and the page index's null counts and bounds say what the rows say.
  The generator gives the Go type the physical type pyarrow picks (decimals as
  FIXED_LEN_BYTE_ARRAY of parquet-cpp's length for the precision, or INT32/INT64 with
  `store_decimal_as_integer`), turns ENUM into a string and bare repeated fields into LISTs.

- Eighteen narrow properties, one per recorded bug, in `hegel/hegel_shapes_test.go` (thirteen
  added 2026-10-08) and `hegel_props_test.go`/`hegel_reverse_test.go` (the five of 2026-09-28):
  each draws the bug's shape region with random contents, is judged as the wide properties
  judge and fails every run naming the bug; under `HEGEL_NO_KNOWN=1` each draws the
  neighbouring region instead (required list elements, zeros of one sign, columns the file
  has, level lengths as written, dictionary floats without NaN, non-negative index lengths,
  `element`, matching physical types, files with rows, v1 pages, pages with values, codecs
  other than LZ4_RAW, page counts as written) and passes.

Twenty bugs, fourteen found 2026-09-20 at v0.32.0+ and six by the weekly 1000-case run of 2026-09-28. Writing: `Schema.Deconstruct` (and so the deprecated `Writer`)
panics on `[]*T` list elements and writes `[]string` elements tagged optional as nulls (1,
medium); a `[N]byte` decimal whose precision needs more than N bytes passes `SchemaOf` and
panics on write (2, low); a decimal tag on `[]int32` yields a bogus fixed-length column whose
file cannot be read back (3, low); float statistics keep the first zero seen instead of -0.0 for
the min and +0.0 for the max, and write NaN bounds for all-NaN columns, against parquet.thrift
(4, low); reading into a struct with a `[N]byte` column the file lacks panics where other
missing columns read as zero (5, medium); a damaged v2 data page makes `ReadRows` panic in
`decodeLevelsV2` (6, medium); the statistics of a dictionary-encoded float column holding a NaN
skip values and write NaN bounds ({-1, NaN, 1}: min 1) (7, medium); negative column or offset
index lengths in the footer make `OpenFile` panic in `ReadPageIndex` (8, medium). Everything else
pyarrow read to the bit: values of every type and nesting, null counts, minima and maxima,
compression and encodings. Reading pyarrow's files: the reflection reader reads LIST elements
not named `element` as zero values or drops them (9, high); DECIMAL conversion between
INT32/INT64 and FIXED_LEN_BYTE_ARRAY copies little-endian bytes, so pyarrow's default decimals
read into int fields byte-reversed (10, high); an empty file with a dictionary page and no data
page fails with `Seek: invalid offset` (11, medium); RLE-encoded booleans (parquet-cpp's
encoding in data pages v2) misdecode runs, ten trues reading as one (12, high); a v2 data page
of zero values dereferences nil (13, medium); LZ4_RAW pages that compress by less than 3x are
decoded from a stale pooled buffer, giving zeros, garbage or decoding errors, with parquet-go's
own files too (14, high). Everything else parquet-go read right: every type and nesting, every
other codec and encoding, statistics and page index bounds, row groups and metadata.
The weekly run added: when the first column chunk has no column index (parquet-cpp writes none
for a float chunk with an all-NaN page) `ReadPageIndex` stores an empty index for every other
chunk (15, medium); and four ways a damaged file takes the process down instead of returning an
error — a damaged byte-array page makes the reflection readers panic in `unsafe.Slice` (16,
medium), `OpenFile` allocates the footer length the trailer claims, up to 4 GB, before checking
it (17, medium), the LZ4 codec doubles its buffer on every decode error until the runtime aborts
(18, medium), a leaf annotated MAP or LIST makes `OpenFile` panic in `Kind` (19, medium), and a
v2 page header counting more nulls than values panics in `makeNumValues` (20, medium).

## Known shapes drawn by default

The generators draw the shapes of every recorded bug the wide properties can reach, at their
natural rates: optional LIST elements, `[N]byte` columns, v2 data pages, float columns with
signed zeros or NaN, dictionary encoding, LZ4_RAW with pages that compress by less than 3x
(strings of thousands of characters in three cases in a hundred), pyarrow's element names,
page versions, encodings and empty tables, and byte damage of every kind. A disagreement with
pyarrow, with the rows written, or a death of the child process is classified by
`known(caseInfo)` in `hegel/known.go` (and by the statistics check for bugs 4 and 7), and the
property fails naming the bug ("the shape of parquet-go/N"). The wide properties are mapped
in `target.toml` to the bug their shrunk failure lands on: `TestHegelWriterPathsAgree` to /1
and `TestHegelReadsWhatPyarrowWrites` to /11 plain (forty of forty rounds at a hundred cases,
thirty of thirty at twenty); `TestHegelPyarrowReadsWhatParquetGoWrites` to /4 (29 of 30 runs,
one also /7), `TestHegelDamagedFilesNeverPanic` to /17 (28 of 30, with /5, /6, /8, /16, /18,
/19 and /20 as its other basins) and `TestHegelReadsBackWhatItWrites` to /14 (19 of 30)
intermittent, since a hundred-case run misses them now and then. Bug 10 (decimal byte order)
is reached only by its pin and narrow property, since the wide properties' Go types match
the files; bug 15 by its narrow property. `HEGEL_NO_KNOWN=1` (read once) ends a case whose
shape the classifier names, and every property passes at a thousand cases (the twenty pins
fail). parquet-cpp's missing column index under an all-NaN page is tolerated, not a bug;
dictionary-encoded booleans, which the format allows for every physical type but parquet-cpp
refuses to read ("Dictionary encoding not implemented for boolean type"), are counted, not
compared (under two per cent of cases). A candidate, counted and skipped
(`candidate/go/parquet-go-21`, `HEGEL_DUMP=dir` keeps the file): reading a damaged page of a
codec other than LZ4 sometimes exhausts the child's 2.5 GB address space - the RLE level
decoder allocating the run length the damaged bytes claim - not yet reproduced standalone.
The generator keeps to the tag placements parquet-go accepts (logical types on LIST
elements go in `parquet-element`, bare slices take no logical type, pointers take no enum,
time, uuid, json or delta). The patch also un-ignores `hegel/oracle.py` (upstream's
`.gitignore` has `*.py`). Reads are bounded (the reflection reader stops a row past the
count, the row API past each row group's `NumRows`), so a damaged file cannot read forever.

## History

- 2026-09-20: new target, five properties, 14 bugs; 2026-09-28: six bugs from the weekly run,
  five narrow properties.
- 2026-10-08: generators rewritten in combinator style (the schema as a depth-indexed tower
  of field records, rows as a generator derived from the schema, writer and pyarrow options
  as records, damage as a list of edits applied modulo the length); the classifier's rules for
  bugs 1, 4-9 and 11-14 made unconditional so the shapes fail by default; thirteen narrow
  properties; the wide mappings re-measured.
