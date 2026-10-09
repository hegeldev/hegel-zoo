# ipaddr

`Ipaddr`'s parsers, printers and prefix arithmetic against Python's `ipaddress` (3.13 or later,
run as a coprocess), and `Macaddr`'s parser against a model.

hegel itself links the installed `ipaddr`, which dune will not link beside the in-tree one, so
`hegel/` is a dune project of its own (`--root hegel`) that builds the checked-out
`lib/{ipaddr,macaddr}.ml{,i}`, symlinked, as the library `upstream`.

## What is tested

- `of_string`, `prefix_of_string`: the same text accepted, as the same address and length.
- `to_string`, `prefix_to_string`: the same canonical text.
- `prefix_bounds`: network, netmask, broadcast, first and last host.
- `mem`, `subset`: modelled with IPv4 mapped into `::ffff:0:0/96`, as ipaddr does on purpose.
- `succ`, `pred`, `subnets`, `is_multicast`, `v4_of_v6`: against the same operations in Python.
- `octets_roundtrip`, `macaddr_to_string_roundtrip`: round trips.
- `macaddr_of_string`: six hex pairs with one separator, `:` or `-`, throughout.

Python's zone IDs (`::1%eth0`), netmask suffixes and its reading of IPv4-mapped addresses as
IPv4 in `is_multicast` are Python's own and not drawn or modelled away.

## Not tested

`with_port_of_string`, `of_string_raw`, `scope`/`is_global`/`is_private` (Python's special-purpose
registry differs by design), `hosts`, domain names, the cstruct and sexp packages.

## History

- 2026-10-09: created at 8332fff3 (v5.6.2), hegel-ocaml 0.26.1; ipaddr/1-2.
