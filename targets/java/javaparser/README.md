# javaparser

[JavaParser](https://github.com/javaparser/javaparser) (`com.github.javaparser:javaparser-core`,
3.29.0-SNAPSHOT at the pinned commit, 2026-09-15) parses Java source (Java 1.0 to 26) into an AST with
positions, comments and a metamodel, prints it back (a pretty printer, `ConcreteSyntaxModel`, and the
`LexicalPreservingPrinter` that keeps the original formatting), and offers fragment parsers for
expressions, statements, blocks and types. Its grammar is JavaCC (`javaparser-core/src/main/javacc/java.jj`).
The zoo pins `javaparser-core` alone; the symbol solver is out of scope.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs `javaparser-core` (and the
generator modules it depends on) from the pinned tree into the local Maven repository with `./mvnw`'s
settings (tests, javadoc, sources, the enforcer and signing skipped). The tests need a JDK 22+ (they use
javac's parse tree through `com.sun.source.tree` and two internal flag words; the surefire and compiler
configuration adds the `--add-exports` for those).

## The oracle

**javac's own parser**, at `--release 21`, stopped after parsing (`-XDshould-stop.at=PARSE`), is the
reference for acceptance and for the tree: a generated Java 21 program that javac's parser accepts must be
accepted by JavaParser, and both trees, rendered into one canonical S-expression (`Shape` for JavaParser's
AST, `JavacShape` for javac's `CompilationUnitTree`), must be equal. The rendering normalises the two
models' known differences: modifiers are sorted keyword sets, types are white-space-free text, javac's
folding of `-` into a decimal literal and of `"a" + "b"` into one literal is undone or mirrored (javac folds
adjacent string literals and text blocks of a `+` chain only when that chain is the top of its run of binary
operators — `"a" + "b" <= x` keeps both, `x + "a" + "b"` becomes `x + "ab"`; `Shape` follows
`JavacParser.foldStrings` exactly), javac's
`this(…)`/`super(…)` invocations become constructor calls, `new int[] {…}` ranks are reconciled,
enum constants and record components are recognised by javac's flags, and empty enum constant bodies are
ignored on javac's side (bug 18). Literal values are compared as values (`asInt`/`asDouble`/`asString`…
against javac's constants), which is how the escape and text-block bugs surfaced. Two javac leniencies are
excluded from the acceptance check: its parser accepts any expression as an assignment target (`a == b = c;`,
rejected only in attribution; JavaParser follows the JLS grammar), and it accepts `(int[]) -x`.

**The library against itself**: pretty print → parse (shape, `equals`, `hashCode`), the
`LexicalPreservingPrinter` (identity on the text), the fragment parsers against the compilation-unit parse,
`clone()` (equal, same hashCode, same shape, same nodes and ranges, detached), and the node ranges (nested
in the parent's, literals and names covering exactly their text).

## What is tested

`JavaParserTest`, each property on a fresh program from `JavaGen` — a random Java 21 compilation unit:
package, imports (static, on demand), classes/interfaces/enums/records/annotation types with type
parameters, `sealed`/`permits`, nested and local types, fields, methods (varargs, receiver parameters,
legacy `int m()[]`), constructors with `this(…)`/`super(…)`, compact constructors, initializers,
all statements (labels, switch statements and expressions with patterns, guards, `case null, default`,
`yield`, try-with-resources, multi-catch, `var`), all expression forms (lambdas, method references,
casts incl. intersection casts, `instanceof` with type and record patterns, switch expressions, array
creation, qualified `new`, anonymous classes, every literal form: hex/octal/binary/underscored numbers,
hex floats, octal and Unicode escapes, text blocks with escapes and `\<newline>`), Unicode identifiers,
contextual keywords as identifiers, optional trivia (comments everywhere, odd white space, CRLF):

- **`agreesWithJavac`** — javac accepts the program (else the generator is at fault: reported as
  "generator"), JavaParser accepts it, and the two shapes are equal.
- **`prettyPrintRoundTrip`** — `cu.toString()` is accepted by javac and by JavaParser with the same shape;
  where the program has no legacy array brackets and no text blocks (documented `ArrayType.origin` and raw
  text-block differences), the reparsed unit `equals` the original with the same `hashCode`.
- **`lexicalPreservationIsIdentity`** — `LexicalPreservingPrinter.setup(cu); print(cu)` is the original text.
- **`positionsAreConsistent`** — every node has a range that ends after it begins and lies within its
  parent's (except a `VariableDeclarator`'s type, which JavaParser places before the declarator by design);
  literals and simple names cover exactly their own text; text blocks start and end with `"""`.
- **`mutationsNeverCrash`** — the program with 1–3 random edits never makes JavaParser throw (a `Problem`
  is fine), `toString()`/`clone()` of the partial result never throw, and if javac's parser accepts the
  mutated text JavaParser does too with the same shape (only syntactic rejections count: JavaParser's
  validators check things javac checks after parsing).
- **`fragmentParsersAgree`** — printed expressions and statements of the unit re-parse with
  `parseExpression`/`parseStatement`/`parseBlock` to the same shape.
- **`cloneEqualsLaws`** — `clone()` is `equals` with the same `hashCode`, shape and printed form, has the
  same node classes and ranges (as a multiset), and shares no node or parent with the original.

`JavaParserPinsTest`: one pin per bug in bugs.toml, asserting the JLS behaviour; all 19 fail today
(`[expected_failures]`).

The generator avoids the shapes of the known bugs, which the pins carry: cast lambdas and method
references appear only as whole arguments, parenthesised or as an assignment's right side (bugs 1, 17);
`var` lambda parameters only outside variable initializers (2); no local enums (3); no `\` and no
`\s` escapes (4–6); text blocks without white space after the opening delimiter and without form feeds
(7, 8). The properties skip the rest: the round trips skip programs with `- -x`/`+ +x` (9) and the
lexical-preservation check skips `int m()[]` (10); the position check exempts the five range bugs (11–15)
and the clone check ignores pattern types (16).

## Not tested

The symbol solver, `ParserConfiguration` options other than the language level, comment attribution and
Javadoc parsing, language levels below 21 and preview features, `ConcreteSyntaxModel`/`PrettyPrinter`
beyond `toString()`, the `Node` observer/`LexicalPreservingPrinter` after edits, the metamodel and
visitors, module declarations, `Position`/`Range` arithmetic, `TokenRange`s. Programs outside the JLS
grammar that javac's parser nevertheless accepts are not generated: a cast to a primitive array type in
front of a unary `+`/`-` (`(int[]) -x`; JLS 15.16 allows only a UnaryExpressionNotPlusMinus after a
reference-type cast, and JavaParser rightly rejects it).

## Bugs found

21, in bugs.toml: JavaParser rejects valid programs (a cast lambda as an operand, `var` lambda parameters in
initializers, local enums, `'\''`, and — grammatical but never well-typed — a method reference as an
operand), gives wrong literal values (`\s`, Unicode-escaped backslashes, text blocks with white space after the
opening delimiter or containing a form feed), prints wrongly (`- -x` as `--x`, `int m()[]` as `int ()[]m`, the
form feed as a line break, `A { }` as `A`), has five range bugs (type parameters' annotations, patterns'
modifiers, `int x[]` names, catch parameters with qualified types, type annotations), does not make a
pattern's type its child in `instanceof`, accepts `import static x;` and `permits Foo<T>`, and keeps Unicode
escapes in identifiers (`\u0041b` is not `Ab`, bug 20), and crashes on a qualified type starting with `var` (bug 21).

Observed, not recorded: JavaParser accepts `import y;` (a single identifier), which the JLS grammar allows and
javac rejects; javac's parser refuses lambdas inside `case … when` guards and
`;` right after the imports, both of which JavaParser accepts and the JLS allows, so the generator does
not produce them.

## History

- 2026-09-16: created (turn 174); 19 bugs.
- 2026-09-18: base bumped a99f4dc25b72 → 554c6f70674f (2026-09-18, "fix: resolve qualified nested types against members only (fixes #5140)"; 3.29.0-SNAPSHOT); 19 bug(s) still reproduce. 7 tests pass.
- 2026-09-19: base bumped 554c6f70674f -> 98c8b8c43e7a (2026-09-18, "refactor: look up values among members, and drop the thread-local guard"); bug 20 (Unicode escapes in identifiers) found by `mutationsNeverCrash` during the bump, bug 21 (`var.X`) by `agreesWithJavac`, and the javac assignment-target leniency gated. 21 bugs.
- 2026-09-19: base bumped 554c6f70674f → 98c8b8c43e7a (2026-09-19, "refactor: look up values among members, and drop the thread-local guard"; 3.29.0-SNAPSHOT); 21 bug(s) still reproduce. 7 tests pass.
