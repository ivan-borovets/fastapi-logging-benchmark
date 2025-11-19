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
N_USERS_DEFAULT: Final[int] = 50
SPAWN_RATE_DEFAULT: Final[int] = 10

# C = 100 rps / 50 users = 2 rps / user
# For (2 rps / user) set `-u 50` with cli
CONSTANT_THROUGHPUT_DEFAULT: Final[int] = 2

NEW_FLAG_NAME: Final[str] = "--n-logs-req"
NEW_FLAG_HELP: Final[str] = "Logs per request (n)"

N_LOGS_REQ_DEFAULT: Final[int] = 400
RUN_TIME_DEFAULT: Final[str] = "60s"
