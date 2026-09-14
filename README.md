# Hegel zoo

A collection of (hopefully) high-quality property-based tests for open-source projects, in every language
[Hegel](https://github.com/hegeldev) supports.

These are fully LLM generated, and are primarily for our own evaluation of Hegel. Where possible,
we report bugs upstream, but in order to be respectful of maintainer time we don't do that without
a human review step to ensure the bug report is good and welcome, and the agent is working continuously
to write new tests and find new bugs. As a result, there are likely a number of bugs here that have
not yet been reported.

If you find your project in the zoo and would like help getting the hegel tests integrated into it,
or you would like our help triaging any bugs found in it, please get in touch and we'd be very happy
to help you with any of this.

## Layout

Each **target** — one upstream project in one language — lives at `targets/<lang>/<name>/`:

- `target.toml`: upstream URL, pinned base commit, Hegel version, how to run, and the tests
  that are expected to fail because of a known, still-open bug;
- `hegel.patch`: the tests, as a `git apply`-able diff against the base commit, plus the
  one-line dev-dependency on Hegel;
- `README.md`: what is tested, with which oracles, and what deliberately is not;
- `bugs.toml`: every bug the tests found, with its status and a per-version history. Note that these are not necessarily validated by a human yet, so we don't guarantee that any "bugs" listed there are genuinely bugs. However we've generally found the reliability of the agent reports pretty good so most of them probably are.

`zoo.toml` pins the Hegel library version per language. `TROPHIES.md` is generated from all
the `bugs.toml` files. `DESIGN.md` explains the choices.
`HACKING.md` says how to run the tests and how a target for each language is put together.
