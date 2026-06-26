from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class DiscoveryConfig:
    manual_projects_file: str = "sample_inputs/manual_projects.json"
    seed_urls_file: str = "sample_inputs/seed_urls.txt"
    search_queries: List[str] = field(
        default_factory=lambda: [
            "crypto presale live",
            "upcoming ICO launch",
            "ended token presale",
        ]
    )
    max_search_results: int = 10
    enable_serpapi: bool = False


@dataclass
class OnChainConfig:
    rpc_endpoints: Dict[str, str] = field(default_factory=dict)
    lookback_blocks: int = 1500
    known_dex_addresses: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "ethereum": [
                "0x7a250d5630b4cf539739df2c5dacab4c659f2488",  # Uniswap V2 Router
                "0xe592427a0aece92de3edee1f18e0157c05861564",  # Uniswap V3 Router
            ],
            "bsc": [
                "0x10ed43c718714eb63d5aa57b78b54704e256024e",  # PancakeSwap V2 Router
            ],
        }
    )


@dataclass
class OutputConfig:
    output_dir: str = "outputs"
    include_csv: bool = True


@dataclass
class AppConfig:
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)
    onchain: OnChainConfig = field(default_factory=OnChainConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


DEFAULT_CONFIG = AppConfig()


def _merge_dict(base: dict, overrides: dict) -> dict:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _expand_env_values(value):
    if isinstance(value, dict):
        return {k: _expand_env_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_values(v) for v in value]
    if isinstance(value, str):
        return os.path.expandvars(value)
    return value


def load_config(path: str | None) -> AppConfig:
    if not path:
        return DEFAULT_CONFIG

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as f:
        user_data = _expand_env_values(json.load(f))

    base_data = {
        "discovery": DEFAULT_CONFIG.discovery.__dict__,
        "onchain": DEFAULT_CONFIG.onchain.__dict__,
        "output": DEFAULT_CONFIG.output.__dict__,
    }
    merged = _merge_dict(base_data, user_data)

    return AppConfig(
        discovery=DiscoveryConfig(**merged.get("discovery", {})),
        onchain=OnChainConfig(**merged.get("onchain", {})),
        output=OutputConfig(**merged.get("output", {})),
    )
