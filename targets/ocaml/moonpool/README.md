# moonpool

Moonpool's pools, futures, channels and queues, mostly as concurrent state machines run under
both `Concurrency.threads` and `Concurrency.domains`, with sequential models as a baseline.

## What is tested

- `chan_threads`/`_domains`, `blocking_queue_threads`/`_domains`: `Chan` and `Blocking_queue`
  under concurrent `try_push`/`try_pop`, blocking `push`/`pop`/`transfer` and `close`: nothing
  received twice or out of nowhere; once closed, every blocked call is woken, every value sent
  is received exactly once, and each consumer sees each producer's values in order.
- `ws_deque_threads`/`_domains`: the work-stealing deque with one owner (calls serialised by a
  mutex) and many stealers: no element taken twice, pops give the newest element or find every
  one stolen, steals take the oldest, `size` and the 255-element capacity.
- `lock_threads`/`_domains`: `Lock.update`, `update_map` and `with_` (raising) count exactly.
- `fut_threads`/`_domains`: promises fulfilled, cancelled and watched (`on_result`, `await` on
  `Ws_pool`/`Fifo_pool`/`Background_thread`, `map`, `bind`, `reify_error`, `join_list`,
  `wait_block`) from several workers, pools shut down between rounds: one resolution wins and
  every waiter sees it.
- `runner_threads`/`_domains`: tasks on the three runners (raising, awaiting children, yielding
  with task-local storage, `for_`/`for_list`/`for_iter`, fork-join, `run_wait_block`,
  `run_async` into `on_exn`), and `shutdown`: results, exceptions, and `Shutdown` after it.
- Sequential: `ws_deque_model`, `chan_model`, `blocking_queue_model` against `Queue`/lists;
  `fut_combinators` (`both`, `choose`, `join_*`, `wait_list`, `map_list`, `bind`, `join`,
  `let+`/`and+` over ready, later and never resolved futures); `fut_for_`;
  `fork_join_matches_list`; `main_runs_tasks`; `combinators_after_main`;
  `fulfill_wakes_every_waiter`; `shutdown_finishes_work`.

Every test runs in a forked child (the domain pool may start only after a fork) whose
watchdog ends it after 60s without progress; waits on futures have a 5s deadline.
`runner_*` lets work on `Fifo_pool` and `Background_thread` finish before shutting them down:
moonpool/2 is `shutdown_finishes_work`'s.

## Not tested

`Moonpool_dpool` directly, `moonpool-lwt`, `Exn_bt`, tracing, `Task_local_storage`'s Hmap
part, and the deque's concurrent owner (the owner's calls are serialised here).

## History

- 2026-10-12: created at 3aa6cfe8 (v0.12+), hegel-ocaml 0.26.1; five bugs.
