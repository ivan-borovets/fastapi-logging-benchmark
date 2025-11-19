import csv
from pathlib import Path
from benchmark.application.ports import ResultsParser
from benchmark.application.dtos import ParsedStats


class CsvResultsParser(ResultsParser):
    def parse(self, stats_file: Path) -> ParsedStats:
        with stats_file.open("r") as f:
            rows = list(csv.DictReader(f))

        agg = next((row for row in rows if row.get("Name") == "Aggregated"), None)
        if agg is None:
            raise ValueError(f"No aggregated row found in {stats_file}")

        return ParsedStats(
            requests=int(agg["Request Count"]),
            failures=int(agg["Failure Count"]),
            min_ms=float(agg["Min Response Time"]),
            median_ms=float(agg["Median Response Time"]),
            avg_ms=float(agg["Average Response Time"]),
            max_ms=float(agg["Max Response Time"]),
            actual_rps=float(agg["Requests/s"]),
        )
