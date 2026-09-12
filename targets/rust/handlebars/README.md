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

## Oracles

## Not tested

## History

- 2026-07-16: predecessor base commit `2802ada08ad8` (chore(deps-dev): bump websocket-driver in /playground/www (#772)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/handlebars.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
