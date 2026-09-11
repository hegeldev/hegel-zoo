# Hegel zoo

A collection of high-quality property-based tests for open-source projects, in every language
[Hegel](https://github.com/hegeldev) supports.

The zoo grows out of [`DRMacIver/hegel-rust-oss-bug-finding`](https://github.com/DRMacIver/hegel-rust-oss-bug-finding),
which did this for Rust alone: a set of open-source crates at pinned base commits, a patch adding
Hegel tests to each, and a record of the bugs those tests found. The zoo extends that to all of
Hegel's languages and treats the tests themselves, rather than the bugs, as the thing being built.

It is worked on continuously by an agent, which adds tests for new repositories, records the bugs
they find (tracked across versions of each repository), updates to new versions of Hegel and
refactors, landing finished chunks on `main` as pull requests.

## Status

Bootstrap. This repository has just been created; its layout (how each language is organised,
whether tests are standalone packages against pinned upstream versions or patches, how bugs are
tracked per repository and version, how CI runs the tests, how the Hegel version is pinned) is
still to be proposed and settled. Nothing here is usable yet.
