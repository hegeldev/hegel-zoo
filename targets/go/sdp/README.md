# go/sdp

[pion/sdp](https://github.com/pion/sdp) v3 (v3.0.20): the Session Description Protocol
(RFC 4566) implementation of the Pion WebRTC stack, with a hand-written byte lexer and a
state machine over the line types (`base_lexer.go`, `unmarshal.go`), a marshaller with a size
precomputation (`marshal.go`), codec lookup helpers and JSEP builders. Tested here:
`SessionDescription.UnmarshalString` on generated text, `Marshal`/`MarshalSize`/`UnmarshalString`
round trips of generated descriptions.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of four
`hegel_zoo_*_test.go` files that drive the public API. `go test -count=1 -run TestHegel -v ./hegel`

## Oracles

- A model of RFC 4566 section 5 as the package documents it in the state table above
  `UnmarshalString` (`vosi?u?e?p?c?b*(tr*)+z?k?a*(mi?c?b*k?a*)*`, media-level lines in any
  order, the input allowed to end only after the first `t=`): line types and their order,
  `<type>=` at the start of each line, fields separated by runs of spaces or tabs, lines
  ended by CRLF or LF, the numeric fields decimal, `v=0` only, `IN` and `IP4`/`IP6`, the IANA
  media types, transport protocols and bandwidth types, `X-` experimental bandwidths, time
  units `d h m s` in `r=` and `z=`, ports 0-65535 with `/<count>`, the `<key>:<value>`
  attribute split at the first `:`, `u=` through `net/url`, and the package's documented
  leniency (a missing `o=` address type and address default to `IP4 0.0.0.0`). Errors are
  compared by the package's sentinel (`syntax error`, `EOF`, `invalid value`, `invalid
  numeric value`, `invalid port value`, `invalid syntax`, `url`), successes field by field.
- For round trips, the description itself: every field after `Marshal` and `UnmarshalString`,
  and `MarshalSize` against the length of `Marshal`'s output.

## Properties

- `TestHegelUnmarshal`: a description of the mandatory lines plus optional `i u e p c b`,
  1-2 `t=` with `r=`, `z=`, `k=`, attributes and 0-2 media sections with `i c b k a`, each
  line valid most of the time and otherwise with one malformed field (missing or extra
  fields, bad tokens, overflowing or signed numbers, stray CRs), then mutations (a dropped,
  repeated or swapped line, an unknown type, a blank line, a line without `=`, a leading
  space, a one-byte last line, no final line break); parsed by `UnmarshalString` and by the
  model. `Unmarshal([]byte)` must agree with `UnmarshalString`.
- `TestHegelRoundTrip`: a `SessionDescription` with every field the grammar carries (texts
  without line breaks, attribute keys without `:`, tokens without whitespace, 1-2 time
  descriptions, connection addresses with TTL and range, experimental bandwidths, media with
  0-3 formats) marshalled and parsed back unchanged; `MarshalSize == len(Marshal())`; CRLF
  line ends only.
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures).

## Bugs

Thirteen, recorded in `bugs.toml`: numeric fields beyond uint64 wrap (sdp/1); missing
numeric fields read as zero, so `t=` and `v=` pass (sdp/2); a final `0` without a line break
is an EOF error while `1` is accepted (sdp/3); a description cut off before its mandatory
lines, even the empty string, is accepted (sdp/4); a lone final byte is ignored (sdp/5); a CR
inside a text line cuts bytes from its end (sdp/6); extra fields on a field line are parsed
as the next line (sdp/7); an unpaired `z=` time is dropped (sdp/8); connection address TTL
and range are never parsed, breaking the round trip (sdp/9); `m=` port `9/2/3` drops `/3`
(sdp/10); an unknown protocol is reported as an invalid numeric value (sdp/11); `MarshalSize`
is one short for a media line without formats (sdp/12); `WithExtMap` sets the whole text as
the attribute key (sdp/13).

## Modelled as recorded

sdp/1-12 are in the model behind `HZKnown` switches (`uintWraps`, `missingNumericIsZero`,
`zeroAtEOFFails`, `truncatedDocumentAccepted`, `danglingByteIgnored`, `crCountTrimsLine`,
`extraFieldStartsLine`, `timeZoneOddDropped`, `connectionTTLNotParsed`, `portRangeTailIgnored`,
`protoErrorIsNumeric`, `emptyFormatsSizeOffByOne`); `ZOO_KNOWN_OFF=name` turns a switch off
and the property then fails. sdp/13 is a builder and is pinned only.

Design notes the model follows (undocumented, taken from the code):

- A missing `o=` address type or address defaults to `IP4` / `0.0.0.0` (`::` for IP6), as the
  code comments for camera compatibility; an `o=` with fewer fields still is an invalid value.
- Runs of spaces and tabs separate fields; a field line may end in whitespace; `\r\r\n` ends a
  line; a bare LF does too. Lines of a text type (`s i u e p b k a`) need a LF: at the end of
  the input they are an EOF error, and so is any field line whose last field is empty there
  (`c=IN IP4`, `m=... 0`, `z=1 2` at the very end).
- Media-level `i c b k` may repeat and appear after `a=` (the last one wins for `i c k`);
  session-level lines follow the table strictly (no `c=` after `b=`, no `k=` after `a=`, no
  second `z=`).
- `r=` and `z=` units are lowercase only and the numbers signed (`+3m`, `-1h`); `b=` values
  are unsigned without a sign; `a=` with a leading `:` is a key of its own; `a=k:` and `a=k`
  are the same attribute; a missing `c=` address is allowed at both levels.
- Session `b=` errors are invalid values, media `b=` errors invalid syntax.

## Not tested

`GetCodecMap`/`GetCodecForPayloadType`/`GetPayloadTypeForCodec` (rtpmap/fmtp/rtcp-fb merging,
where an explicit rtpmap for a static payload type is only half applied), `ExtMap` parsing
(`1-246` enforced, `1-256` claimed; attributes with spaces truncated), the other JSEP
builders, `NewJSEPSessionDescription`.

## History

- 2026-09-21: new target, two properties, 13 bugs.
