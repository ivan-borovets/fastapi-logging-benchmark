"""
Introduced in separate module to avoid MonkeyPatchWarning
from locust while importing from locustfile
"""

from pathlib import Path
from typing import Final

BASE_DIR_PATH: Final[Path] = Path(__file__).resolve().parents[3]
LOCUSTFILE_PATH: Final[Path] = (
    BASE_DIR_PATH / "src" / "benchmark" / "adapters" / "locustfile.py"
)
OUTPUT_DIR_PATH: Final[Path] = BASE_DIR_PATH / "results"
TARGET_RPS_DEFAULT: Final[int] = 100

# User waits for response before next request.
# 400 users at 0.25 RPS keep 100 RPS until response time exceeds 4s
N_USERS_DEFAULT: Final[int] = 400
SPAWN_RATE_DEFAULT: Final[int] = 100
CONSTANT_THROUGHPUT_DEFAULT: Final[float] = TARGET_RPS_DEFAULT / N_USERS_DEFAULT

# On stop, wait for in-flight requests, otherwise they are missing from stats
STOP_TIMEOUT_S_DEFAULT: Final[int] = 10

NEW_FLAG_NAME: Final[str] = "--n-logs-req"
NEW_FLAG_HELP: Final[str] = "Logs per request (n)"

N_LOGS_REQ_DEFAULT: Final[int] = 400
RUN_TIME_DEFAULT: Final[str] = "60s"
