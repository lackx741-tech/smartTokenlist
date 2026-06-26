from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

from config import DiscoveryConfig
from models import CandidateRecord


class CandidateDiscovery:
    def __init__(self, config: DiscoveryConfig, root_dir: Path):
        self.config = config
        self.root_dir = root_dir

    def discover(self) -> List[CandidateRecord]:
        records: List[CandidateRecord] = []
        records.extend(self._load_manual_projects())
        records.extend(self._load_seed_urls())
        records.extend(self._search_query_candidates())
        return self._dedupe(records)

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.root_dir / p

    def _load_manual_projects(self) -> List[CandidateRecord]:
        path = self._resolve(self.config.manual_projects_file)
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        records = []
        for item in data:
            records.append(
                CandidateRecord(
                    project_name=item.get("project_name") or item.get("token_symbol") or "unknown-project",
                    source_url=item.get("source_url") or item.get("website") or "",
                    website=item.get("website", ""),
                    token_symbol=item.get("token_symbol", ""),
                    chain=(item.get("chain") or "unknown").lower(),
                    contracts=item.get("contracts", []),
                    description=item.get("description", ""),
                    metadata={
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                        "sale_type": item.get("sale_type", "presale"),
                        "launchpad": item.get("launchpad", ""),
                        "status_hint": item.get("status"),
                    },
                )
            )
        return records

    def _load_seed_urls(self) -> List[CandidateRecord]:
        path = self._resolve(self.config.seed_urls_file)
        if not path.exists():
            return []

        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            host = urlparse(url).netloc or "unknown-source"
            records.append(
                CandidateRecord(
                    project_name=host.split(":")[0],
                    source_url=url,
                    website=url,
                    metadata={"seed_source": True},
                )
            )
        return records

    def _search_query_candidates(self) -> List[CandidateRecord]:
        if not self.config.enable_serpapi:
            return []

        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return []

        records: List[CandidateRecord] = []
        for query in self.config.search_queries:
            url = (
                "https://serpapi.com/search.json?engine=google"
                f"&q={quote_plus(query)}&num={self.config.max_search_results}&api_key={quote_plus(api_key)}"
            )
            request = Request(url, headers={"User-Agent": "presale-discovery/1.0"})
            try:
                with urlopen(request, timeout=20) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except Exception:
                continue

            for result in payload.get("organic_results", []):
                link = result.get("link", "")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                if not link:
                    continue
                records.append(
                    CandidateRecord(
                        project_name=title or urlparse(link).netloc,
                        source_url=link,
                        website=link,
                        description=snippet,
                        metadata={"query": query},
                    )
                )
        return records

    def _dedupe(self, records: List[CandidateRecord]) -> List[CandidateRecord]:
        deduped: Dict[str, CandidateRecord] = {}
        for record in records:
            key = (record.source_url or "").strip().lower()
            if not key and record.contracts:
                key = record.contracts[0].lower()
            if not key:
                key = record.project_name.lower()
            if key not in deduped:
                deduped[key] = record
                continue
            existing = deduped[key]
            existing.contracts = sorted(set(existing.contracts + record.contracts))
            existing.description = existing.description or record.description
            existing.website = existing.website or record.website
            existing.token_symbol = existing.token_symbol or record.token_symbol
            existing.metadata.update(record.metadata)
        return list(deduped.values())
