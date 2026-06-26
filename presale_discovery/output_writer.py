from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from models import ProjectResult


def write_json(results: Iterable[ProjectResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [item.to_dict() for item in results]
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_csv(results: Iterable[ProjectResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "project_name",
        "status",
        "score",
        "source_url",
        "website",
        "token_symbol",
        "chain",
        "contracts",
        "sale_type",
        "launchpad",
        "start_date",
        "end_date",
        "summary",
        "on_chain_metrics",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            row = item.to_dict()
            row["contracts"] = ";".join(item.contracts)
            row["on_chain_metrics"] = json.dumps(item.on_chain_metrics, ensure_ascii=False)
            writer.writerow({k: row.get(k, "") for k in fields})
