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
  both must reject the text. Lands on bug 1 most runs (2 and 3 in others), the shapes of bugs 4,
  5 and 9 drawn too.
- `TestHegelWriteReadByJava`: a generated map (keys and values with the special characters, control
  characters, Unicode whitespace, non-ASCII and supplementary characters) written with
  `Properties.Write` (UTF-8, or ISO-8859-1 in 30% of cases) is loaded by Java with the same encoding
  and must be the same map. Supplementary characters under ISO-8859-1 are written as `?`, which the
  package documents, so they are not drawn under ISO-8859-1. Lands on bug 6; the shapes of bugs 7
  and 8 are drawn too.
- `TestHegelReadJavaStore`: the same maps stored by `Properties.store(Writer)` are loaded by the
  package and must be the same map.

**`hegel/hegel_shapes_test.go`**: one narrow property per recorded bug, drawing the bug's region
with random contents inside otherwise shape-free text (a key continuation, a trailing backslash,
a separator-first line, a CR LF continuation, a surrogate-pair literal, a separator after a
continuation; a written key starting with `#` or `!`, Latin-1 under ISO-8859-1, a leading Unicode
space under ISO-8859-1): the deterministic expected failure for each bug.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug, with the map Java
gives for the text (the Write pins round-trip through the package's own `Load`, which fails too).

## Oracles

`java.util.Properties` (OpenJDK 25 here; the runner image's JDK), through `hegel/Oracle.java`.
Java is the definition of the format the package claims to read, so no differences are excluded
by design; the package's `${}` expansion is turned off, keys are compared as a map (Java keeps no
order), a UTF-8 BOM is not generated (the package strips one, Java does not), and lone surrogates
cannot be generated (Go has no spelling for them).

## Known bugs

Nine bugs (`bugs.toml`): five in the lexer (a continuation inside a key, before CR LF, or between
the key and the separator; a trailing backslash at end of input; the empty key), one in escape
decoding (surrogate pairs), three in `Write` (unescaped `#`/`!` at the start of a key;
ISO-8859-1 output that is really UTF-8 for U+0080-U+00FF, and raw for a leading Unicode space).
The generators draw all nine shapes at their natural rates; `hegel/known.go` names the shape of a
text (a scan in Java's terms: continuations by position, trailing backslash, empty key, surrogate
literal) or of a map, and a mismatch reports it. `HEGEL_NO_KNOWN=1` (read once) looks past the
recorded bugs: the grammar is built without the shapes (no surrogate-pair literals, no CR LF or
key continuations, no separator-first lines, no backslash tail, no `#`/`!`-leading keys, no
Latin-1 or leading Unicode space under ISO-8859-1), a residual filter catches what composition
still produces (about 2.6% of texts), the narrow properties draw the neighbouring clean shape,
and every property passes (the ninth bug was found that way, behind the first).

## Not tested

`${}` expansion, `Decode` into structs, the typed getters (`GetInt`, `GetDuration`, ...), `Filter*`,
comments carried through `WriteComment`, loading from files and URLs, `LoadMap`, `Merge`.

## History

- 2026-09-20: written against 7bc746f67ddc32a90a2154f393e4b27750e678c3 (2026-09-16, "test with
  go1.27") with hegel.dev/go/hegel v0.6.33; 9 bugs.
