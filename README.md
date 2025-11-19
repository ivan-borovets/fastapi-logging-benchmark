# Should we handle logs asynchronously?

# Problem statement

* In practice, logging to `stdout` is usually done via blocking I/O
* Blocking I/O can be offloaded to a separate thread at some cost
* **Does offloading logging to a separate thread pay off in terms of HTTP response time?**

# Goals

* Perform comparative analysis of common logging approaches by median response time from ASGI app endpoint
* Find out whether the most efficient logging setups actually process logs off the main thread

# Design

1. Set of independent ASGI app factories (`FastAPI`) is defined; each factory exposes single endpoint that differs
   only by logging strategy. Handler does nothing but call logger in a loop
2. Separate factory without logging serves as `baseline` for estimating overhead on response time
3. Benchmarker application receives list of cases (metadata + app factory) and processes them sequentially
4. For each case FastAPI app is started in separate process via `uvicorn` on free port. After a simple healthcheck
   (request to case endpoint with `n=1`), separate `subprocess` is started with `locust` in headless mode for same case
5. By default `locust` is configured to hit endpoint at roughly uniform rate of **~100 RPS**:
    * 50 "users" are created
    * each generates around 2 RPS
    * users are spawned at 10 users/sec
    * run time is `60s` by default
6. Each case uses same number of logs per HTTP request (`n_logs_req`), passed as parameter to app and controlling how
   many times logger is called inside handler
7. Log format is maximally standardized: all loggers are brought to common JSON format aligned with `aiologger`
   output (timestamp, level, file path, function, line number, message). `aiologger` format is chosen as reference
   because it is hardest to customize; other loggers can be matched to it via their formatters. This allows comparing
   primarily logging overhead, not differences in log format
8. `locust` results for each case are stored in CSV file. From it, aggregated row (`Name == "Aggregated"`) is read and
   the following values are extracted:
    * `Median Response Time`
    * `Average Response Time`
    * actual `Requests/s`
    * number of requests and failures
9. Based on these data, comparative analysis is built:
    * for `baseline`, its median response time is fixed
    * for all other cases, median and overhead relative to `baseline` are calculated (in milliseconds and percent)
10. Finally, summary table is printed for all cases, showing `baseline`, best variant, and full list of median response
    times

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
  Set of cases that in this methodology usually end up in top part of table by median response time for given load
  profile. Useful when you want to quickly inspect "fast" configurations without running full `all`
* **`stable_vs_unstable`**  
  Compact set with `baseline` and several contrasting logging approaches: some behave more stably (median and relative
  ordering of cases change little between runs), others are noticeably more sensitive to load changes and environment
  noise. This mode is useful if you want to play with `--n-logs-req` and `--time` and manually see how different logging
  strategies react to increased load and longer runs

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
  All cases write structured JSON logs to `stdout`. Variants with file output, network logging, external log systems or
  non-JSON/plain-text logging are not compared
* **Fixed load profile.**  
  Load is defined by single scenario: ~100 RPS for `60s` with simple `GET` requests doing no useful work in endpoint
  besides logging. Behaviour under other load profiles, run durations or request types is not examined
* **Limited set of metrics.**  
  Analysis relies on aggregated `locust` statistics (row `Name == "Aggregated"`): `Median Response Time`,
  `Average Response Time`, actual `Requests/s`, number of requests and failures. Tail latencies (p95/p99), full
  latency distributions, CPU/memory usage etc. are not considered
* **Sequential case runs.**  
  Cases are executed sequentially in single process. By default, order is fixed; `--shuffle` option randomly shuffles it
  and reduces systematic position bias. There is 5-second pause between cases (`COOLDOWN_BETWEEN_CASES_S`) to slightly
  smooth out CPU warm-up effects, but system drift (heating, background processes, etc.) is not fully eliminated
* **Limited set of logger configurations.**  
  Comparison covers specific `logging`, `aiologger` and `structlog` configurations used in this project. Results do
  not automatically generalize to other configurations, handlers or processor chains of same libraries
* **Stochastic results.**  
  Even with fixed settings, individual runs may differ significantly due to environment noise (background processes,
  scheduler, warm-up, etc.). For queue-based and background logging configurations (e.g. `stdlib_queue_*`,
  `aiologger_no_await_*`) spread can be especially noticeable. In practice, it makes sense to run benchmark multiple
  times and look at stability of relative ordering rather than relying on single run

# Test environment

`Intel Core i5-8250U` (4c/8t), `8 GB RAM`, `LMDE 6`, `Python 3.13.7`. Exact dependency versions are in `uv.lock`.

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
```

* `--mode {all,fastest,json,orjson,stable_vs_unstable}` — preset of cases (see "Cases and modes"). Default: `fastest`
* `--n-logs-req N_LOGS_REQ` — number of logs per HTTP request (default: `400`)
* `--time RUN_TIME` — `locust` run time, e.g. `30s`, `60s`, `2m` (default: `60s`)
* `--shuffle` — shuffle case order before running to reduce impact of fixed order on results (default: off)

You can also manually run app factory module and `locust` separately.
For example, for factory `yourfactory` on `http://127.0.0.1:8000`, `locust` run may look like:

```shell
locust -f src/benchmark/adapters/locustfile.py --headless -u 50 -r 10 -t 1m --tag yourfactory --n-logs-req 400 --host "http://127.0.0.1:8000"
```

# Adding your own case

1. Add factory under `src/benchmark/adapters/app_factories`
2. Add task to `src/benchmark/adapters/locustfile.py`
3. Add case to `src/benchmark/cases.py`
4. If needed, register separate `mode` in:
    * `main.parse_args` (`choices`)
    * `main.main.factories`

# Results

* Under given settings (400 logs/endpoint, ~100 RPS, 60s, JSON to `stdout`) `baseline` consistently showed median
  response time around ~20 ms and served as reference point for estimating overhead
* For every pair "same logging approach + `json` vs `orjson`", `orjson` variant never had higher median than its
  counterpart on stdlib `json`
* `structlog_experimental_orjson`, `structlog_sync_orjson` and `stdlib_stream_orjson` consistently appeared in upper
  part of median ranking among logging cases
* Configurations using `await` in handler (`aiologger_with_await_*`, `structlog_async_*`) had median values orders of
  magnitude higher than `baseline` and their synchronous/no-await counterparts (hundreds–thousands of milliseconds
  versus tens)
* For `stdlib_queue_*` and `aiologger_no_await_orjson` median varied noticeably between runs: in some runs they were
  close to leaders, in others they lagged significantly behind stream/structlog-sync

As illustration, here is sample run for "stable" `orjson`-based cases:

| Case                            | Median (ms) | Overhead vs baseline |
|---------------------------------|------------:|---------------------:|
| `baseline`                      |          20 |           0% (+0 ms) |
| `structlog_experimental_orjson` |         110 |       +450% (+90 ms) |
| `structlog_sync_orjson`         |         120 |      +500% (+100 ms) |
| `stdlib_stream_orjson`          |         150 |      +650% (+130 ms) |
| `aiologger_with_await_orjson`   |         570 |     +2750% (+550 ms) |
| `structlog_async_orjson`        |        1700 |    +8400% (+1680 ms) |

Numbers are for single run on specific machine and are meant only as illustration of relative ordering

To illustrate behaviour under changing load, four cases from `stable_vs_unstable` mode were considered separately:

* `baseline` — no logging
* `structlog_experimental_orjson` — representative of fast and relatively stable configurations
* `stdlib_queue_orjson` and `aiologger_no_await_orjson` — representatives of potentially fast but more
  load-/noise-sensitive configurations (queue and fire-and-forget)

These cases were run under four combinations of `n_logs_req` and `run_time`:

* 400 logs, 1 minute (`400 / 1m`)
* 600 logs, 1 minute (`600 / 1m`)
* 400 logs, 2 minutes (`400 / 2m`)
* 600 logs, 2 minutes (`600 / 2m`)

Approximate median response times for one set of runs:

| Profile       | `baseline` | `structlog_experimental_orjson` | `stdlib_queue_orjson` | `aiologger_no_await_orjson` |
|---------------|-----------:|--------------------------------:|----------------------:|----------------------------:|
| 400 logs / 1m |      18 ms |                          110 ms |                 47 ms |                      160 ms |
| 600 logs / 1m |      19 ms |                          170 ms |                630 ms |                      720 ms |
| 400 logs / 2m |      24 ms |                          120 ms |                 30 ms |                       80 ms |
| 600 logs / 2m |      23 ms |                          160 ms |                630 ms |                      680 ms |

* `baseline` stayed around 20–25 ms across all profiles
* `structlog_experimental_orjson` grew with load more smoothly: median increased with more logs and longer runs but
  stayed in tens–hundreds of milliseconds range
* `stdlib_queue_orjson` and `aiologger_no_await_orjson` looked good under base load (`400 / 1m`) but as `n_logs_req`
  increased, their median moved into hundreds-of-milliseconds range and significantly exceeded
  `structlog_experimental_orjson` in overhead

Currently, repeated benchmark runs, collecting statistics across runs and tail analysis (p95/p99) are not automated:
this can be done manually by running `benchmark` multiple times with same parameters. When comparing results, it makes
sense to look not only at single metric value (median, p95), but also at spread between min and max across runs to see
how much numbers "wander".

# Conclusions

* Under given settings (400 logs/endpoint, ~100 RPS, 60s, JSON to `stdout`), logging significantly increases median
  response time compared to `baseline` without logs: there is no "almost free" logging at this load level
* JSON serializer choice matters: in all tested configurations `orjson` variant was never slower than its stdlib
  `json` counterpart and typically showed lower overhead
* Synchronous `structlog`+`orjson` and stream-based `logging`+`orjson` configurations look like most robust choice when
  you need predictable median latency under intensive logging
* Queue-based configurations (`stdlib_queue_*`) and fire-and-forget (`aiologger_no_await_orjson`) can provide low median
  latency under light load, but show significantly higher run-to-run variability and degradation when number of logs
  and run time increase. Under strict latency-stability requirements these variants are not recommended as primary
  solution in this methodology
* Using async logger APIs with `await` in handler (`aiologger_with_await_*`, `structlog_async_*`) consistently produced
  median latencies orders of magnitude higher than baseline and synchronous/no-await counterparts
  (hundreds–thousands of milliseconds vs tens). For tested profile, logging with `await` in HTTP critical path is the
  most expensive option and is not recommended when low latency is priority
* For tested configurations and load profile, offloading logging from main thread to separate thread or background
  worker **does not provide stable win** in HTTP response time. In terms of median response time, simple synchronous
  solutions with fast JSON serializer (e.g. `orjson`) look preferable
* All conclusions apply to specific configurations, load profile and environment of this setup and describe relative
  behaviour of tested cases, not universal ranking of logging solutions

# TLDR

> — So, should we handle logs asynchronously?
>
> — Only when low and stable latency isn’t a big deal
