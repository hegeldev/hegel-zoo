# prometheus-common

[prometheus/common](https://github.com/prometheus/common), package `expfmt`: the Prometheus
exposition formats. `TextParser`/`TextToMetricFamilies` reads the text format (including the
quoted UTF-8 names inside braces), `MetricFamilyToText` and `MetricFamilyToOpenMetrics` write
the text and the OpenMetrics 1.0 formats, `NewEncoder`/`NewDecoder`/`SampleDecoder`/
`ExtractSamples` wrap them, and `Format`, `NegotiateAccept` and `ResponseFormat` handle the
content types. The pin is `db5c9e8` (2026-09-18, after v0.71.0). The other packages of the
module (config, model, promslog, route, server, version) are not covered.

The repository is Apache-2.0; CONTRIBUTING.md says nothing about AI-written code and there are
no agent instructions. The zoo keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v ./expfmt` in the module root (Go 1.26+: `go mod tidy`
raised the directive from 1.25.0 for the hegel dependency). The patch adds, in the external
test package of `expfmt`, `hegel_test.go` (harness, the `Known` switch), `hegel_model_test.go`
(the canonical form, generators, the model writer), `hegel_props_test.go` (properties),
`hegel_ref_test.go` (the prometheus_client reference test) and `hegel_pins_test.go`, and
requires `hegel.dev/go/hegel v0.6.33` in go.mod. `TestHegelPrometheusClientAgrees` runs
`python3` with the `prometheus_client` module when it is on PATH (the CI's venv installs it)
and is skipped otherwise.

## Oracle

The text format specification (exposition_formats, "Text format details"), the OpenMetrics 1.0
specification and the package's own documentation:

- a model writer renders generated families to the text format with the freedom the
  specification allows: blanks and tabs between tokens, leading whitespace, blank lines and
  comments between lines, HELP and TYPE in either order (TYPE omitted for untyped families),
  type keywords in any case, quoted names (UTF-8 ones inside the braces, legacy ones quoted at
  will), the `quantile`/`le` label at any position, `_sum`/`_count` lines anywhere among a
  metric's lines, the sample lines of families interleaved, values in every spelling
  `strconv.ParseFloat` accepts (`1`, `1.0`, `1e+00`, `+1`, `NaN`/`nan`, `Inf`/`+inf`/`Infinity`),
  optional timestamps. The parser must produce the rendered families (empty ones dropped,
  UNTYPED where no TYPE line was written) under `UTF8Validation`, and reject the text under
  `LegacyValidation` iff a name is not legacy-valid; a reused parser and `NewDecoder` give the
  same result. A parsed histogram has all-integer or all-float counts, floats iff a count is
  fractional. A mutated text is rejected with a `ParseError` whose line is within the text, or
  what it parses to is written by `MetricFamilyToText` and read back unchanged.
- round trip: `MetricFamilyToText` output (and the text `Encoder`'s, byte for byte) parses
  back to the family with a `+Inf` bucket added where missing and gauge histograms as
  histograms; the written byte count is right; `ExtractSamples` gives the same samples before
  and after, one per sample line, and `SampleDecoder` the same.
- OpenMetrics: `MetricFamilyToOpenMetrics` output (and the OpenMetrics `Encoder`'s, `# EOF`
  from `Close`) has one sample line per sample with the suffixes the type demands (`_total`
  moved out of the HELP/TYPE/UNIT names for counters, `unknown` for untyped and for counters
  without `_total`), whole counts as integers, other numbers with a point or an exponent,
  timestamps in seconds, exemplars where present with labels, `_created` lines when asked;
  the package's own text parser reads a plain output back to the families.
- the prometheus_client Python parsers on a batch of 150 cases: its Prometheus text parser on
  the model writer's plain rendering and on `MetricFamilyToText` output must give the samples
  `ExtractSamples` gives (names, labels, values, timestamps within a millisecond); its strict
  OpenMetrics parser must accept `MetricFamilyToOpenMetrics` output of OpenMetrics-valid
  families (`_total` counters, monotone buckets ending in `+Inf`, quantiles in [0, 1],
  non-negative sums, units that suffix the name) and give the families, samples and exemplars
  written.
- content negotiation: `NewFormat` inverts `FormatType`; `WithEscapingScheme` is read back by
  `ToEscapingScheme` and keeps the type (applied twice, one `escaping=` term); an Accept header
  naming an accepted format (with or without charset, with a q value, after another type) gets
  that format with the default escaping, an `escaping=` parameter is echoed, no match falls
  back to the text format if accepted else the first; `ResponseFormat` recognises the text and
  delimited-protobuf content types.

Generators draw 1-4 families of distinct, non-suffix-related names (legacy and UTF-8, with
quotes, backslashes, braces, newlines), every type, optional help (any characters), 1-3
metrics per family with distinct label sets of 0-3 labels (legacy and UTF-8 names, values with
quotes, backslashes, newlines, unicode, empty), values including the special floats, counts
below 2^53, fractional histogram counts, buckets with and without `+Inf`, quantiles, optional
timestamps; for OpenMetrics also exemplars (with and without labels or timestamps), created
timestamps and units.

## Method

| Property | Checks |
|---|---|
| ParseFollowsTheFormat | the model writer's text parsed under both schemes, fresh and reused parser, `NewDecoder`; histogram count consistency; mutations rejected with a `ParseError` in range or reproduced by the writer |
| TextRoundTrips | `MetricFamilyToText` and the text `Encoder`: byte count, parse back, `ExtractSamples` before/after, one sample per line, `SampleDecoder` |
| OpenMetricsIsWellFormed | `MetricFamilyToOpenMetrics` and the OpenMetrics `Encoder`: line structure, sample lines and suffixes, comment lines, exemplars, number spellings, the text parser on plain output |
| NegotiationReturnsWhatWasAsked | `NewFormat`/`FormatType`, `WithEscapingScheme`/`ToEscapingScheme`, `NegotiateAccept`, `ResponseFormat` |
| PrometheusClientAgrees | the prometheus_client Prometheus and OpenMetrics parsers on 150 cases each (plain test) |

`ZOO_COLLECT=1` records mismatches instead of failing and prints the agreement classes.

## Accepted differences

- Help texts are generated non-empty and without leading blanks: the parser drops an empty
  docstring and trims leading blanks (the format says all remaining tokens are the docstring).
- Summaries and histograms get legacy names in the parse and reference properties while bug 9
  stands (their sample lines are not written with the name inside the braces).
- `MetricFamilyToText` writes `float64(count)`, so counts are generated below 2^53; `-0` is
  not generated (written as `0`).
- prometheus_client's Prometheus parser names the samples of a counter family `<name>_total`
  when the family name lacks the suffix; `ExtractSamples` adds a `+Inf` bucket sample to a
  histogram without one; both are normalised before comparing. Its OpenMetrics parser does not
  read escapes in exemplar label values, so those are generated plain; its timestamps are
  not compared for OpenMetrics (it misreads the exponent form Go writes), the property checks
  the spelling instead.
- `ResponseFormat` does not know the OpenMetrics content type (FmtUnknown); only the text and
  delimited-protobuf types are checked.
- OpenMetrics 2.0 (`MetricFamilyToOpenMetrics20`, experimental) is not covered.

## Bugs found

Ten, in bugs.toml: a summary or histogram sample whose metric name is inside the braces is
booked with the previous line's family state, splitting metrics and panicking on a nil map
(high); a summary `_count` converted with `uint64(value)` unchecked (`-1` becomes 2^64-1);
the OpenMetrics `_created` line without the metric's timestamp (the reference parser rejects
the group); gauge histograms written with `_count`/`_sum` instead of `_gcount`/`_gsum`
(medium); a quote inside an unquoted name toggling quoting (`foo"bar"` is `foobar`);
`ExtractSamples(nil, ...)` panicking on a sample without a timestamp; trailing whitespace after
a value or timestamp rejected against the specification; a summary/histogram sample without a
quantile/le label accepted and its value dropped; an exemplar without labels dropped; an
exemplar written on a counter declared `unknown`, which OpenMetrics forbids (low).
The rest agreed at 2000 cases: every accepted spelling and layout, both validation schemes,
the text and OpenMetrics writers against the parser and against prometheus_client, and the
content negotiation.

## History

- 2026-09-21 (turn 347): target added at db5c9e8 with four properties, the prometheus_client
  reference test and 10 pins.
