> Should we handle logs asynchronously?

# Table of contents

1. [Problem statement](#problem-statement)
2. [Goals](#goals)
3. [Design](#design)
4. [Cases and run modes](#cases-and-run-modes)
5. [Limitations](#limitations)
6. [Test environment](#test-environment)
7. [How to run](#how-to-run)
8. [Adding your own case](#adding-your-own-case)
9. [Results](#results)
10. [Conclusions](#conclusions)
11. [Recommendations](#recommendations)
12. [TLDR](#tldr)

# Problem statement

* In practice, logging to `stdout` is usually done via blocking I/O
* Blocking I/O can be offloaded to a separate thread at some cost
* **Under load, does offloading logging to a separate thread pay off in terms of HTTP response time?**

# Goals

* Perform comparative analysis of common logging approaches under a fixed load profile by median and tail response time
  from ASGI app endpoint
* Compare them with log collector that reads `stdout` without pauses and with collector that stalls
* Check whether offloaded logging keeps up with load or defers work past measured window

# Design

1. Set of independent ASGI app factories (`FastAPI`) is defined; each factory exposes single endpoint that differs
   only by logging strategy. Handler does nothing but call logger in a loop
2. Separate factory without logging serves as `baseline` for estimating overhead on response time
3. Benchmarker application receives list of cases (metadata + app factory) and processes them sequentially
4. For each case FastAPI app is started in separate process via `uvicorn` on free port. After a simple healthcheck
   (request to case endpoint with `n=1`), separate `subprocess` is started with `locust` in headless mode for same case
5. App `stdout` and `stderr` go to single pipe, read by log collector thread of benchmarker, as container runtime does.
   Collector can stop reading for `--sink-pause-ms` after every `--sink-pause-every-ms` of reading: pipe buffer
   (64 KiB by default on Linux) fills up and writes to `stdout` block. Without pauses collector reads continuously
6. By default `locust` is configured to hit endpoint at roughly uniform rate of **~100 RPS**:
    * 400 "users" are created
    * each generates around 0.25 RPS
    * users are spawned at 100 users/sec
    * run time is `60s` by default

   `locust` users are closed-loop: each one waits for response before next request. Many slow users keep target rate
   until response time reaches 4s, so slow case doesn't lower its own load and hide its latency
7. Each case uses same number of logs per HTTP request (`n_logs_req`), passed as parameter to app and controlling how
   many times logger is called inside handler
8. Log format is maximally standardized: all loggers are brought to common JSON format aligned with `aiologger`
   output (timestamp, level, file path, function, line number, message). `aiologger` format is chosen as reference
   because it is hardest to customize; other loggers can be matched to it via their formatters. This allows comparing
   primarily logging overhead, not differences in log format
9. When run time is over, `locust` lets in-flight requests finish (`--stop-timeout`) and saves stats to JSON file.
   From it, the following values are extracted:
    * median, p95 and p99 response time
    * average response time
    * actual RPS
    * number of requests and failures
10. Collector counts log lines received while `locust` runs. Their share of `requests * n_logs_req` shows whether
    logger keeps up: below 100% means logs are queued and their cost is deferred past measured window
11. Based on these data, comparative analysis is built:
    * for `baseline`, its median response time is fixed
    * for all other cases, median and overhead relative to `baseline` are calculated (in milliseconds and percent)
12. Finally, summary table is printed for all cases, showing `baseline`, best variant, and full list of response
    times, actual RPS and share of delivered logs. Cases that didn't sustain 90% of target RPS or had failures are
    marked as not comparable

# Cases and run modes

Each case is separate ASGI app factory (`FastAPI`) with single endpoint that writes `n_logs_req` logs in a loop and
does nothing useful beyond that. Cases differ only by logging strategy, including choice of JSON serializer
(standard library `json` vs `orjson`):

* **No logging (`baseline`)**
    * `baseline` — endpoint without logging, used as reference to measure overhead on response time
* **Standard `logging` (stdlib)**
    * `stdlib_stream_json` / `stdlib_stream_orjson` — synchronous `logging` with stream handler, JSON via `json` or
      `orjson`
    * `stdlib_queue_json` / `stdlib_queue_orjson` — `logging` with queue-based handler/listener, JSON via
      `json` or `orjson`
* **`aiologger`**
    * `aiologger_no_await_json` / `aiologger_no_await_orjson` — `aiologger` without `await` in handler, JSON via `json`
      or `orjson`
    * `aiologger_with_await_json` / `aiologger_with_await_orjson` — `aiologger` with `await` in handler, JSON via
      `json` or `orjson`
* **`structlog`**
    * `structlog_sync_json` / `structlog_sync_orjson` — `structlog` with synchronous API (`log.info(...)`), JSON via
      `json` or `orjson`
    * `structlog_async_json` / `structlog_async_orjson` — `structlog` with async API (`await log.ainfo(...)`), JSON via
      `json` or `orjson`
    * `structlog_experimental_orjson` — `structlog` with synchronous API and `BytesLoggerFactory`, JSON directly via
      `orjson.dumps` to minimize overhead

For convenience, several predefined case sets ("modes") are provided:

* **`all`**  
  Full set: `baseline` and all `logging` / `aiologger` / `structlog` variants
* **`json`**  
  Only cases where JSON logging uses stdlib `json`: `baseline` and all `*_json` variants
  (`stdlib_*_json`, `aiologger_*_json`, `structlog_*_json`)
* **`orjson`**  
  Only cases where JSON is serialized via `orjson`: `baseline` and all `*_orjson` variants, including
  `structlog_experimental_orjson`
* **`fastest`**  
  `baseline`, synchronous `orjson` cases and `aiologger_no_await_orjson`. Useful when you want to quickly inspect
  fast configurations without running full `all`
* **`stable_vs_unstable`**  
  Compact set with `baseline`, synchronous `structlog_experimental_orjson` and offloaded `stdlib_queue_orjson` and
  `aiologger_no_await_orjson`. Useful to play with `--n-logs-req`, `--time` and collector stalls and see how
  synchronous and offloaded logging react

`baseline` is always present in all modes so that overhead can be compared against single reference point.

# Limitations

* **Single environment.**  
  Results are valid only for specific combination of hardware, OS, Python version and library versions
  (`uvicorn`, `fastapi`, `locust`, loggers). Absolute response times are not meant to be universal benchmarks; primary
  interest is relative differences between cases under these conditions
* **Single app process.**  
  For each case single-process `uvicorn` is started (one worker). Scenarios with multiple workers, separate logging
  processes or distributed systems are not considered
* **Only `stdout` and JSON logs.**  
  All cases write structured JSON logs to `stdout`/`stderr` pipe. Collector stalls are synthetic periodic pauses, not
  model of specific log driver. Variants with file output, network logging, external log systems or non-JSON/plain-text
  logging are not compared
* **Shared machine.**  
  App, log collector and `locust` run on same machine and compete for CPU
* **Fixed load profile.**  
  Load is defined by single scenario: ~100 RPS for `60s` with simple `GET` requests doing no useful work in endpoint
  besides logging. Behaviour under other load profiles, run durations or request types is not examined
* **Limited set of metrics.**  
  Analysis relies on `locust` statistics: median, p95/p99 and average response time, actual RPS, number of requests
  and failures, plus share of delivered logs. Full latency distributions, CPU/memory usage, delivery delay of each log
  etc. are not considered. Stats include 4-second ramp-up of `locust` users
* **Sequential case runs.**  
  Cases are executed sequentially in single process. By default, order is fixed; `--shuffle` option randomly shuffles it
  and reduces systematic position bias. There is 5-second pause between cases (`COOLDOWN_BETWEEN_CASES_S`) to slightly
  smooth out CPU warm-up effects, but system drift (heating, background processes, etc.) is not fully eliminated
* **Limited set of logger configurations.**  
  Comparison covers specific `logging`, `aiologger` and `structlog` configurations used in this project. Results do
  not automatically generalize to other configurations, handlers or processor chains of same libraries
* **Stochastic results.**  
  Even with fixed settings, individual runs may differ due to environment noise (background processes, scheduler,
  warm-up, etc.). In practice, it makes sense to run benchmark multiple times and look at stability of relative
  ordering rather than relying on single run

# Test environment

`Intel Core i7-1365U` (10c/12t), `32 GB RAM`, `Ubuntu 22.04`, `Python 3.13.9`. Exact dependency versions are in
`uv.lock`.

# How to run

* Dev prerequisites

```shell
uv sync --group dev
source .venv/bin/activate
pre-commit install
```

* Run and wait for results

```shell
benchmark
# for help, use `benchmark -h`
```

It is recommended to run `benchmark` in regular OS terminal, not in embedded IDE terminal

```text
usage: benchmark [-h] [--mode {all,fastest,json,orjson,stable_vs_unstable}] [--n-logs-req N_LOGS_REQ] [--time RUN_TIME] [--shuffle]
                 [--sink-pause-ms SINK_PAUSE_MS] [--sink-pause-every-ms SINK_PAUSE_EVERY_MS]
```

* `--mode {all,fastest,json,orjson,stable_vs_unstable}` — preset of cases (see "Cases and modes"). Default: `fastest`
* `--n-logs-req N_LOGS_REQ` — number of logs per HTTP request (default: `400`)
* `--time RUN_TIME` — `locust` run time, e.g. `30s`, `60s`, `2m` (default: `60s`)
* `--shuffle` — shuffle case order before running to reduce impact of fixed order on results (default: off)
* `--sink-pause-ms SINK_PAUSE_MS` — log collector stall duration; `0` drains pipe without pauses (default: `0`)
* `--sink-pause-every-ms SINK_PAUSE_EVERY_MS` — collector reading time between stalls (default: `1000`)

Hypothesis is checked by comparing same cases with fast and stalling collector:

```shell
benchmark --mode orjson --shuffle
benchmark --mode orjson --shuffle --sink-pause-ms 100 --sink-pause-every-ms 500
```

You can also manually run app factory module and `locust` separately.
For example, for factory `yourfactory` on `http://127.0.0.1:8000`, `locust` run may look like:

```shell
locust -f src/benchmark/adapters/locustfile.py --headless -u 400 -r 100 -t 1m --stop-timeout 10 --tag yourfactory --n-logs-req 400 --host "http://127.0.0.1:8000"
```

# Adding your own case

1. Add factory under `src/benchmark/adapters/app_factories`
2. Add task to `src/benchmark/adapters/locustfile.py`
3. Add case to `src/benchmark/cases.py`
4. If needed, register separate `mode` in:
    * `main.parse_args` (`choices`)
    * `main.main.factories`

# Results

Collector profiles: without pauses and stalling (`--sink-pause-ms 100 --sink-pause-every-ms 500`: stops for 100 ms after
every 500 ms of reading). Target load: 100 RPS. All cases except `structlog_async_*` sustained target load without
failures and delivered 100% of logs before load ended.

**400 logs/request**, 60 s per case, one run per profile (`--mode all` without pauses, `--mode orjson` stalling).
Response time in ms, median / p95 / p99:

| Case                            |     Without pauses |           Stalling | Median change |
|---------------------------------|-------------------:|-------------------:|--------------:|
| `baseline`                      |       35 / 53 / 59 |       31 / 52 / 73 |            -4 |
| `structlog_experimental_orjson` |    190 / 400 / 630 |    280 / 470 / 720 |           +90 |
| `structlog_sync_orjson`         |    210 / 460 / 580 |    320 / 650 / 860 |          +110 |
| `stdlib_stream_orjson`          |    230 / 520 / 840 |    330 / 550 / 830 |          +100 |
| `stdlib_queue_orjson`           |    230 / 500 / 660 |    220 / 430 / 530 |           -10 |
| `aiologger_no_await_orjson`     |   260 / 810 / 1100 |    210 / 460 / 620 |           -50 |
| `aiologger_with_await_orjson`   |   650 / 960 / 1300 |  620 / 1200 / 1400 |           -30 |
| `structlog_async_orjson`        |   ~20 s, 26 RPS \* |   ~22 s, 24 RPS \* |             — |
| `stdlib_queue_json`             |    210 / 420 / 540 |                  — |             — |
| `structlog_sync_json`           |    250 / 550 / 740 |                  — |             — |
| `stdlib_stream_json`            |   310 / 740 / 1000 |                  — |             — |
| `aiologger_no_await_json`       |  320 / 1100 / 1300 |                  — |             — |
| `aiologger_with_await_json`     | 1400 / 5100 / 5400 |                  — |             — |
| `structlog_async_json`          |   ~21 s, 25 RPS \* |                  — |             — |

\* target load not sustained, not comparable

**10 logs/request**, `--mode stable_vs_unstable`, 20 s per case without pauses and 60 s stalling:

| Case                            | Without pauses |        Stalling | Median change |
|---------------------------------|---------------:|----------------:|--------------:|
| `baseline`                      |   33 / 51 / 55 |    28 / 53 / 59 |            -5 |
| `structlog_experimental_orjson` |   31 / 65 / 73 | 120 / 140 / 170 |           +89 |
| `stdlib_queue_orjson`           |   39 / 90 / 94 |    36 / 59 / 66 |            -3 |
| `aiologger_no_await_orjson`     |   38 / 64 / 68 |    35 / 63 / 69 |            -3 |

Medians of one case differed by up to 30 ms between repeated short runs. Smaller differences between cases are noise

# Conclusions

* **Collector stalls add their duration to response time of synchronous logging.** With stalling collector median of
  synchronous cases grew by 90–110 ms at 400 logs/request and by 89 ms at 10 logs/request. Medians of offloaded cases
  didn't grow
* **Without stalls offloading is slower.** Median of `stdlib_queue_orjson` was higher than of synchronous
  `structlog_experimental_orjson` by 8 ms at 10 logs/request and by 40 ms at 400 logs/request
* **Offloading also removes JSON serialization from request handling.** Without stalls median of `stdlib_queue_json`
  was 100 ms lower than of `stdlib_stream_json`; with `orjson` both medians were 230 ms. At 400 logs/request `orjson`
  lowered median of synchronous cases by 40–80 ms compared to `json`
* **Offloaded loggers keep up with load.** Queue-based and fire-and-forget cases delivered 100% of logs before load
  ended with both collector profiles
* **`await` on logging calls is the slowest option.** Median of `aiologger_with_await_*` was 2.5–7 times higher than
  of offloaded cases. `structlog_async_*` runs each logging call in thread pool and sustained ~25 of 100 RPS
* **`aiologger` without `await` has wide tails.** Without stalls at 400 logs/request its p95 was 3.1–3.4 times its
  median, other cases without `await` had 2.0–2.4

Limitations of these conclusions: one run per configuration; 10 logs/request run without pauses lasted 20 s instead of
60 s; stall pattern is synthetic, so effect size in production depends on how often and how long log collector stalls.
Not investigated: why stalls delayed 77% of requests at 10 logs/request, while collector paused for one sixth of time,
and why ~30 KB written during a stall at 10 logs/request didn't fit into pipe buffer (pipe capacity wasn't measured)

# Recommendations

* **Don't use async logging APIs.** `await` on logging calls made median 2.5–7 times higher than offloading to
  a thread, and `aiologger` without `await` had the widest tails
* **By default, log synchronously with stdlib `logging` and `orjson` formatter.** At 400 logs/request `orjson` lowered
  median of synchronous handlers by 40–80 ms compared to `json`. `structlog` with `orjson` performed the same or
  slightly better
* **If `stdout` can stall, offload writes with stdlib `QueueHandler` + `QueueListener`.** Trade-offs:
    * gain: collector stall doesn't block event loop. Here a 100 ms stall added ~90 ms to median of synchronous logging
      at 10 and at 400 logs/request and didn't change median of queue-based logging
    * cost: without stalls queue-based median was up to 40 ms higher than of the fastest synchronous setup
    * records still in queue are lost if process crashes
    * unbounded queue grows in memory while `stdout` stalls; with bounded queue `QueueHandler` drops records when
      queue is full
    * listener thread has to be started on app startup and stopped on shutdown

`stdout` stalls when process that reads it falls behind:

* Docker in default `blocking` log delivery mode, especially with network log drivers (`fluentd`, `gelf`, `awslogs`,
  `splunk`)
* Kubernetes when node disk is slow or busy: container runtime writes logs to it
* systemd service when `journald` is overloaded
* pipe to slow process, slow SSH session, terminal paused with Ctrl+S

`stdout` rarely stalls when redirected to file on local disk or to `/dev/null`, and in Docker `non-blocking` mode, which
drops logs when its buffer is full. This list describes common setups and wasn't measured here

# TLDR

> — So, should we handle logs asynchronously?
>
> — Not with async logging APIs. Log synchronously with `orjson` formatter.
> If `stdout` can stall, offload writes to a thread with `QueueHandler` + `QueueListener`
