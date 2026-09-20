# properties

[magiconair/properties](https://github.com/magiconair/properties), a Go library for "Java
properties files", against `java.util.Properties` itself: generated `.properties` texts loaded by
both must give the same key/value map, what the package writes Java must read back unchanged, and
what Java stores the package must read back unchanged.

## What is tested

**`hegel/hegel_props_test.go`** (needs `java`, 11 or later: the oracle `hegel/Oracle.java` runs
under the source launcher as a child JVM, one request line in, one answer line out, strings as hex)
- `TestHegelLoadMatchesJava`: a generated text (comment lines with `#` and `!`, blank and
  whitespace lines, keys and values built from plain and non-ASCII pieces, the special characters
  `= : # ! \` and whitespace raw and escaped, `\uXXXX` literals including surrogate pairs, unknown
  escapes, continuations before LF, CR LF and CR with leading whitespace on the next line, every
  separator spelling, LF/CR LF/CR line ends, a backslash at the very end) is loaded by the package
  (`Loader{DisableExpansion: true}`, since Java has no `${}` expansion) and by `Properties.load`
  from a UTF-8 reader (one text in five as ISO-8859-1 on both sides). The maps must be equal, or
  both must reject the text.
- `TestHegelWriteReadByJava`: a generated map (keys and values with the special characters, control
  characters, Unicode whitespace, non-ASCII and supplementary characters) written with
  `Properties.Write` (UTF-8, or ISO-8859-1 in 30% of cases) is loaded by Java with the same encoding
  and must be the same map. Supplementary characters under ISO-8859-1 are written as `?`, which the
  package documents; those cases are counted, not judged.
- `TestHegelReadJavaStore`: the same maps stored by `Properties.store(Writer)` are loaded by the
  package and must be the same map.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug, with the map Java
gives for the text (the Write pins round-trip through the package's own `Load`, which fails too).

## Oracles

`java.util.Properties` (OpenJDK 25 here; the runner image's JDK), through `hegel/Oracle.java`.
Java is the definition of the format the package claims to read, so no differences are excluded
by design; the package's `${}` expansion is turned off, keys are compared as a map (Java keeps no
order), a UTF-8 BOM is not generated (the package strips one, Java does not), and lone surrogates
cannot be generated (Go has no spelling for them).

## Known bugs (gated)

Nine bugs (`bugs.toml`): five in the lexer (a continuation inside a key, before CR LF, or between
the key and the separator; a trailing backslash at end of input; the empty key), one in escape
decoding (surrogate pairs), three in `Write` (unescaped `#`/`!` at the start of a key;
ISO-8859-1 output that is really UTF-8 for U+0080-U+00FF, and raw for a leading Unicode space).
`hegel/known.go` gates the load bugs by the shape of the text (a scan in Java's terms:
continuations by position, trailing backslash, empty key, surrogate literal) and the Write bugs by
the map; `HEGEL_NO_KNOWN=1` makes the text generator avoid the gated shapes so that a round looks
past them (the ninth bug was found that way, behind the first).

## Not tested

`${}` expansion, `Decode` into structs, the typed getters (`GetInt`, `GetDuration`, ...), `Filter*`,
comments carried through `WriteComment`, loading from files and URLs, `LoadMap`, `Merge`.

## History

- 2026-09-20: written against 7bc746f67ddc32a90a2154f393e4b27750e678c3 (2026-09-16, "test with
  go1.27") with hegel.dev/go/hegel v0.6.33; 9 bugs.
