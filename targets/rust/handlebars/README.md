# handlebars

[sunng87/handlebars-rust](https://github.com/sunng87/handlebars-rust).

## What is tested

**`tests/data_helper.rs`**
- `prop_if_matches_truthiness_model`: `{{#if}}` selects its main block iff the parameter is truthy, matching the documented truthiness model.
- `prop_unless_complements_if`: `{{#unless}}` is the exact complement of `{{#if}}` for the same value: swapping the two branches under `if` must reproduce `unless`. Sibling-API consistency check.
- `prop_each_index_matches_model`: `{{#each}}` over an array visits every element in order, exposing `@index` and `this`. Checked against a hand-built model.
- `prop_lookup_matches_model`: `{{lookup arr i}}` indexes an array by a numeric literal, yielding the element (rendered) or empty when out of bounds in non-strict mode. Oracle is Rust slice indexing.

**`tests/escape.rs`**
- `prop_autoescape_no_raw_specials`: Autoescape safety (XSS core contract): rendering an arbitrary string via a double-stache `{{ }}` expression must never emit a raw `< > " ' ` =` — the default HTML escape maps every one of them to an entity. Oracle-independent: the presence of any of those characters in the output is a self-evident violation.
- `prop_triple_stache_verbatim`: Triple-stache `{{{ }}}` is verbatim: rendering a string through it returns the string unchanged. Oracle-independent (we hold the input).

**`tests/root_var.rs`**
- `prop_relative_path_resolution`: Path resolution inside `{{#each}}`: `../b` climbs to the enclosing scope and `this` / the element render consistently. Checked against a hand model that resolves the paths the same way. `b` is drawn from `[A-Za-z0-9]*` so the model needn't reimplement HTML escaping (the point here is path resolution).
- `prop_missing_path_renders_empty`: Missing / deep paths render to empty string in the default (non-strict) mode rather than erroring or panicking.

**`tests/scoped_inline.rs`**
- `prop_partial_inline_equals_direct`: Including a registered partial with `{{> p}}` is transparent: rendering `{{> p}}` against some data equals rendering the partial's body directly against the same data. Oracle is the direct render of the same body.

**`tests/subexpression.rs`**
- `prop_compile_never_panics`: Template compilation / rendering must never panic on arbitrary Handlebars-shaped token soup: `render_template` returns `Ok` or `Err`, never aborts. Oracle-independent (a panic is self-evidently a bug).
- `prop_render_deterministic`: Rendering is deterministic: the same template + data + registry render to the same result (both the success value and the ok/err status), every time.

**`tests/hegel_shapes.rs`**
- `deeply_nested_templates_abort_the_process`: templates nested 400 to 2000 levels deep (`{{#if}}`
  blocks, `(not ...)` subexpressions; unclosed `{{#if}}` opens from 1300) with random names and
  filler, rendered in a child process: the process must not die of a signal - handlebars/1's
  region, where it overflows the stack; under `HEGEL_NO_KNOWN=1` depths below the measured
  thresholds (200; 1000 for the opens).

The generators are values built from hegeltest's combinators, one `tc.draw` per property: JSON
values as a `one_of!` with `null` first, HTML strings as vectors of drawn characters (the specials
first), token soup as a vector of fragments, and `prop_compile_never_panics` draws either soup
(rendered in process, a panic failing it) or a `Nesting` recipe (shape, depth 1-2000, name, filler)
rendered by a pure function and compiled and rendered in a child process (`tests/util/nesting.rs`:
the test binary re-executed with `--exact`, the case in an environment variable, `ulimit -v`, a
deadline, verdicts cached), so the recorded abort is drawn by default and the property is the
expected failure mapped to handlebars/1 (intermittent: the deep cases past the threshold are about
3% of cases). The three `#[ignore]`d reproducers stay as the pins.

## Oracles

## Not tested

## History

- 2026-07-16: predecessor base commit `2802ada08ad8` (chore(deps-dev): bump websocket-driver in /playground/www (#772)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/handlebars.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 2802ada08ad8 → 567b48015464 (2026-09-12, "Add the Auric SPA MVC framework to the related projects section (#787)"; 6.4.4); 0 bug(s) still reproduce; 1 ignored reproducer(s) not run. 241 tests pass.
- 2026-09-26: generators rewritten in combinator style; handlebars/1's shape is drawn by default
  and rendered in a child process, with a narrow property in `tests/hegel_shapes.rs`; the abort
  thresholds re-measured (~300 for blocks and subexpressions, ~1150 for unclosed opens).
