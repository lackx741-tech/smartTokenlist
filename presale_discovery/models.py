from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CandidateRecord:
    project_name: str
    source_url: str
    website: str = ""
    token_symbol: str = ""
    chain: str = "unknown"
    contracts: List[str] = field(default_factory=list)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectResult:
    project_name: str
    source_url: str
    website: str
    token_symbol: str
    chain: str
    contracts: List[str]
    status: str = "unknown"
    sale_type: str = "presale"
    launchpad: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    on_chain_metrics: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
