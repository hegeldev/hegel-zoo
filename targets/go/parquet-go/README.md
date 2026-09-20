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

Fourteen bugs, found 2026-09-20 at v0.32.0+. Writing: `Schema.Deconstruct` (and so the deprecated `Writer`)
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

Gates (`hegel/known.go` and the statistics check) cover the shapes of bugs 1, 4, 5, 6, 7, 8, 9,
11, 12, 13 and 14 (bug 10 does not arise in the properties, whose Go types match the files);
dictionary-encoded booleans, which the format allows for every physical type but parquet-cpp
refuses to read ("Dictionary encoding not implemented for boolean type"), are counted, not
compared. The generator keeps to the tag placements parquet-go accepts (logical types on LIST
elements go in `parquet-element`, bare slices take no logical type, pointers take no enum,
time, uuid, json or delta). The patch also un-ignores `hegel/oracle.py` (upstream's
`.gitignore` has `*.py`).
