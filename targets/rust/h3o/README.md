# h3o

[HydroniumLabs/h3o](https://github.com/HydroniumLabs/h3o).

## What is tested

**`tests/api/cell_index.rs`**
- `pbt_u64_roundtrip`: (no doc comment)
- `pbt_try_from_rejects_corrupted_bits`: (no doc comment)
- `pbt_string_roundtrip`: (no doc comment)
- `pbt_hierarchy_at_own_resolution_is_identity`: (no doc comment)
- `pbt_parent_children_containment`: (no doc comment)
- `pbt_direct_children`: (no doc comment)
- `pbt_compact_uncompact_roundtrip`: (no doc comment)
- `pbt_compact_full_children_collapses_to_parent`: (no doc comment)
- `pbt_grid_disk_size_and_membership`: (no doc comment)
- `pbt_grid_disk_symmetry`: (no doc comment)
- `pbt_grid_disk_distances_consistency`: (no doc comment)
- `pbt_grid_distance_metric`: (no doc comment)
- `pbt_is_neighbor_iff_distance_one`: (no doc comment)
- `pbt_succ_pred_roundtrip`: (no doc comment)
- `pbt_area_decreases_with_resolution`: (no doc comment)
- `pbt_grid_path_cells_contract`: (no doc comment)

**`tests/api/directed_edge_index.rs`**
- `pbt_edges_origin_destination_reverse`: (no doc comment)
- `pbt_edge_roundtrips`: (no doc comment)

**`tests/api/latlng.rs`**
- `pbt_cell_center_roundtrip`: (no doc comment)
- `pbt_to_cell_containment`: (no doc comment)

**`tests/api/mod.rs`**
- `pbt_try_from_u64_never_panics_and_modes_are_exclusive`: (no doc comment)

**`tests/api/vertex_index.rs`**
- `pbt_vertexes_count_and_roundtrips`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-06-08: predecessor base commit `287e4b26b5b5` (little cleanup).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/h3o.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
