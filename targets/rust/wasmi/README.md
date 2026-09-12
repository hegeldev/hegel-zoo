# wasmi

[wasmi-labs/wasmi](https://github.com/wasmi-labs/wasmi).

## What is tested

**`tests/integration/exprs.rs`**
- `wasmi_execution_matches_reference_interpreter`: Property: Wasmi evaluates generated `i32` expression modules to exactly the result (or trap) computed by a Rust-side reference interpreter of the Wasm operator semantics.
- `execution_is_deterministic_across_engines_and_compilation_modes`: Property: executing the same module with the same inputs always produces the same outcome (value or trap), independently of the engine instance and of the chosen compilation mode (eager vs. lazy).
- `typed_and_untyped_calls_agree`: Property: calling an exported function via the untyped `Func::call` API and via the `TypedFunc` API produces the same outcome.

**`tests/integration/fuel_metering.rs`**
- `fuel_metering_does_not_change_outcome`: Property: enabling fuel metering (with ample fuel) never changes the execution outcome compared to unmetered execution — it only determines whether execution completes.
- `more_fuel_never_changes_outcome_or_consumption`: Property: giving more fuel than consumed never changes the outcome nor the amount of fuel consumed (fuel monotonicity).
- `insufficient_fuel_always_traps_out_of_fuel`: Property: giving less fuel than the run consumes always traps with `TrapCode::OutOfFuel` — never any other outcome.

**`tests/integration/func.rs`**
- `host_identity_func_roundtrips_arbitrary_values`: Property: a dynamically-typed identity host function ([`Func::new`]) with an arbitrary numeric signature returns all parameter values bitwise unchanged through [`Func::call`].
- `value_roundtrips_through_wasm_and_host`: Property: a numeric value passed from the host into a Wasm function, through an imported identity host function, and back out to the host arrives bitwise unchanged (Wasm -> host -> Wasm value roundtrip).

**`tests/integration/instantitation.rs`**
- `module_new_never_panics_on_arbitrary_bytes`: Property: `Module::new` never panics, whatever bytes it is fed — raw garbage (which also exercises the `wat` text frontend), bytes with a valid Wasm binary header, or mutations of a valid module.
- `module_validate_agrees_with_module_new`: (no doc comment)

**`tests/integration/multi_memory.rs`**
- `memory_behaves_like_byte_vec_model`: Property: the [`Memory`] API (read/write/grow/data) behaves exactly like a plain `Vec<u8>` reference model, including out-of-bounds error cases.

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `bd3732cea636` (Move `ArenaKey` and impls into its own submodule (#1989)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/wasmi.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
