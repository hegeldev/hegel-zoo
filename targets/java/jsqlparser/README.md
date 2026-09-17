# jsqlparser

[JSqlParser](https://github.com/JSQLParser/JSqlParser) (`com.github.jsqlparser:jsqlparser`, 5.5-SNAPSHOT at the
pinned commit, 2026-09-14) parses SQL statements of a dozen dialects (Oracle, SQL Server, MySQL/MariaDB,
PostgreSQL, H2, SQLite, …) into a Java class hierarchy, prints them back (`toString()`, `StatementDeParser`),
and offers `parseExpression`/`parseCondExpression`/`parseStatements`, `TablesNamesFinder` and
`Statement.getFeatures()`. Its grammar is JavaCC (`src/main/jjtree/net/sf/jsqlparser/parser/JSqlParserCC.jjt`);
`CCJSqlParserUtil.parse` tries a SIMPLE parse and retries in COMPLEX mode.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the jar from the pinned tree
into the local Maven repository (the root pom picks a JDK toolchain in `[17,24)` through the property
`toolchain.jdk.version`, which the setup widens to `[17,26)` for the zoo's JDK 25; tests, javadoc, sources,
enforcer, PMD, spotless, license and signing are skipped).

## The oracle

**SQLite**, in process through `org.xerial:sqlite-jdbc` 3.53.4.0 (SQLite 3.53.4, `jdbc:sqlite::memory:`), is the
reference for acceptance and meaning. `SqlGen` writes a random *SQLite program*: a small schema (one to three
tables `t0..t2` with an `id INTEGER PRIMARY KEY`, one to four data columns of mixed or no declared type, zero to
five rows) and one statement against it — a query (60 %: plain selects with joins/subqueries/CTEs/set
operations/VALUES, GROUP BY/HAVING, window functions, aggregates with DISTINCT/ORDER BY/FILTER, CASE, CAST,
COLLATE, LIKE/ESCAPE, BETWEEN, IN, EXISTS, IS [NOT] DISTINCT FROM, ORDER BY with ordinals/aliases/collations/NULLS
FIRST, LIMIT/OFFSET), a data change (25 %: INSERT with VALUES/DEFAULT VALUES/SELECT, upserts, REPLACE, UPDATE with
row values and FROM, DELETE, RETURNING) or a schema change (15 %: CREATE TABLE with constraints and foreign
keys, CREATE TABLE AS, CREATE INDEX, CREATE VIEW, DROP, ALTER TABLE). Thirty per cent of programs carry
*trivia*: random keyword case, tabs, CRLF, `/* c */` and `-- line comment` between tokens, quoted names in
`"…"` or `` `…` ``, a trailing `;`.

A program SQLite rejects is a generator fault (`generator:` in the failure text). For the rest, SQLite's
results give the meaning: a query's rows (sorted unless the query has a total order — the generator appends
every source's row key to ORDER BY when it wants one), a DML/DDL statement's update count, RETURNING rows and a
canonical snapshot of the whole database afterwards (`sqlite_master`, `pragma_table_xinfo`, index and foreign
key lists, every table's rows). `Db` is a fresh in-memory database per run.

## Properties (`JSqlParserTest`)

- **agreesWithSqlite** — a statement SQLite accepts, JSqlParser parses; its `toString()` runs in SQLite with the
  same result and the same database afterwards (column names normalised: comments, white space, keyword case
  and redundant parentheses are not meaning); the print is a fixpoint (`parse(toString()).toString()` equal —
  white-space-squashed when the text has a hex literal, bug 7), of the same statement class, and
  `StatementDeParser` prints the same text.
- **treeMatchesSqlite** — for queries, every expression in the tree (select items, WHERE, HAVING, ON, through
  WITH items, set operations and subqueries) is reprinted *fully parenthesised* from the AST (`Paren`) and
  spliced back into the statement (`Raw`, an `Expression` that prints as given text); SQLite must return the
  same rows for the parenthesised statement — i.e. JSqlParser's tree groups the operators as SQLite does. Every
  such expression without a subquery also reads back the same through `parseExpression`.
- **tablesAndFeatures** — `getFeatures().returnsResultSet()` agrees with SQLite's result-column count (DDL never
  returns rows; sqlite-jdbc reports a column for `ALTER TABLE … ADD … CHECK (…)`), `modifiesData`/`mayModifyData`/
  `modifiesSchema` agree with the statement kind, and `TablesNamesFinder.findTables` returns exactly the `t<n>`
  tables the text names (queries and DML).
- **statementsSplit** — one to four programs joined with `;` separators (with comments and blank lines around
  them) parse with `parseStatements` into the same `toString()`s as the single parses.
- **mutationsNeverCrash** — one to three random edits (token insertion/deletion/replacement from a pool)
  applied to a program: `parse` (with a 20 s timeout) either succeeds or fails with a `ParseException`,
  `TokenMgrException` or `JSQLParserException` (never a `RuntimeException`, never a timeout), and whatever is
  accepted prints, parses again and prints the same.

`HEGEL_TEST_CASES=800` × 5 properties runs in well under a minute.

## What the generator avoids

SQLite-only syntax JSqlParser does not claim: `==`, `GLOB`, `MATCH`, `x IS y` for non-NULL/boolean `y`, postfix
`NOT NULL`, `INSERT OR ABORT/FAIL/IGNORE/ROLLBACK` (only `OR REPLACE` parses), `UPDATE OR …`, `WITHOUT ROWID`,
`STRICT`, column-level `ON CONFLICT` clauses, `CAST(x AS ANY)`, `[bracket]` names (an option), chained
comparisons (`1 = 1 = 1`, `1 IS NULL = 0`). Operators of different families (`+ -`, `* / %`, `||`, `& | << >>`)
are never mixed without parentheses: JSqlParser puts `||` and the bitwise operators at the `+ -` level (the
majority dialect), SQLite binds `||` tightest and the bitwise operators below `+ -`. A `/` alone on a line is
JSqlParser's SQL*Plus-style statement terminator, so the generator keeps a divisor on its dividend's line.

SQLite quirks the generator respects: a constant integer in ORDER BY/GROUP BY is a column index even as `(15)`,
`-1` or `15 COLLATE NOCASE` (the generator writes `(e) + 0`); `INSERT … SELECT … ON CONFLICT` needs a WHERE on the
SELECT; RANGE frames with offsets need one ORDER BY expression; no subqueries in CHECK or index expressions, no
`.` in index expressions, a string literal there is read as a name; `ALTER TABLE … ADD` copies the column text
into the schema verbatim, so no comment between it and the `;`; `UPDATE … FROM` needs qualified columns and its
RETURNING sees the updated table only.

The known bugs' shapes are skipped (the pins carry them): stacked unary operators, a predicate followed by `IS
TRUE/FALSE`, bare `BINARY`/`RTRIM` collations, type names and `exclude` as bare column names, quoted names with
dots, `REPLACE … RETURNING`/`DEFAULT VALUES`, row-value SET starting with `(`, signed CASE operands,
conditions inside CAST, typeless columns in CREATE TABLE, `COLLATE` after `IS NULL`/`IS TRUE`.

## Not tested

Dialects other than SQLite's common subset (Oracle hints, T-SQL `TOP`, MySQL `LIMIT x, y`, PostgreSQL `::`
casts, MERGE, procedural blocks), `Feature`-driven parser configuration beyond the defaults (square-bracket
quoting, `allowComplexParsing` off), the visitor/deparser API beyond `StatementDeParser`, `getNestingDepth`/
`getUnbalancedPosition`, and performance (the 20 s timeout in `mutationsNeverCrash` never fired).

## Bugs found

See `bugs.toml` (16, all open at the pinned commit, all pinned in `JSqlParserPinsTest`): stacked unary
operators rejected (1); predicate `IS TRUE/FALSE` rejected (2); `COLLATE BINARY`/`RTRIM` rejected (3); type
names as bare columns rejected (4); `exclude` column rejected (5); quoted identifiers with dots split, `"."`
throws `RuntimeException` (6); `HexValue` keeps trailing white space, toString grows (7); `REPLACE INTO` takes
neither RETURNING nor DEFAULT VALUES (8); `parseStatements("SELECT 1;;")` rejected (9); row-value SET starting
with a subquery rejected (10); `CASE -1 WHEN …` rejected (11); `CAST(a = 1 AS …)` and other conditions in CAST
rejected (12); typeless columns with constraints or next to typed ones rejected (13); `3 ."id"` prints as
`3."id"`, which does not parse (14); `DELETE` without a table accepted, prints `DELETE null` (15); `a IS NULL
COLLATE NOCASE` and `a IS TRUE COLLATE NOCASE` rejected (16).

## Observed, not recorded

- `parse()` reads one statement and ignores everything after its `;` (`SELECT 1; SELECT 2` → `SELECT 1`, `SELECT
  1; garbage` too) — the grammar's `Statement() (';' | EOF)`, by design; `parseStatements` is the multi-statement
  entry point.
- `toString()` is near-verbatim but not identity: comments dropped, `TRUE` → `true`, `Trim( ' x ' )`,
  `VARCHAR (20)`, `REFERENCES t(id)`, `PARTITION BY a )`, `ANY(SELECT`; `CAST(a AS DECIMAL (5, 2))`.
- A chained `x COLLATE "BINARY" COLLATE NOCASE` (SQLite: the first wins) is a parse error; the generator never
  chains COLLATE.
- The empty identifier `""` is accepted by both SQLite and JSqlParser.
- `SELECT * FROM t JOIN u` without ON is a cross join in SQLite; JSqlParser parses it as a plain join (no
  semantics involved).
- sqlite-jdbc reports one result column for `ALTER TABLE t ADD c NUMERIC CHECK (…)` (the check over existing
  rows), so the `returnsResultSet` comparison is skipped for DDL.

## History

- 2026-09-16: created (turn 175) at 6312f9e5ea5d (5.5-SNAPSHOT); 16 bugs.
- 2026-09-17: base bumped 6312f9e5ea5d → dec8f5def498 (2026-09-17, "doc: Update changelog"; 5.5-SNAPSHOT); 16 bug(s) still reproduce. 5 tests pass.
