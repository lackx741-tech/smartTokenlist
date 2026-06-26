from __future__ import annotations

import argparse
from pathlib import Path

from classification import classify_project
from config import load_config
from discovery import CandidateDiscovery
from models import ProjectResult
from onchain import OnChainAnalyzer
from output_writer import write_csv, write_json
from scoring import score_project, summarize_project


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover and rank crypto presale/ICO projects")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to JSON config file (defaults to built-in sample behavior)",
    )
    parser.add_argument("--output-dir", default=None, help="Override output directory")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N projects")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root_dir = Path(__file__).resolve().parent

    config = load_config(args.config)
    if args.output_dir:
        config.output.output_dir = args.output_dir

    discoverer = CandidateDiscovery(config.discovery, root_dir=root_dir)
    candidates = discoverer.discover()
    if args.limit:
        candidates = candidates[: args.limit]

    analyzer = OnChainAnalyzer(config.onchain)
    results: list[ProjectResult] = []

    for candidate in candidates:
        project = ProjectResult(
            project_name=candidate.project_name,
            source_url=candidate.source_url,
            website=candidate.website,
            token_symbol=candidate.token_symbol,
            chain=candidate.chain,
            contracts=candidate.contracts,
            contract_address=(candidate.contracts[0] if candidate.contracts else ""),
            status=(candidate.metadata.get("status_hint") or "unknown"),
            sale_type=(candidate.metadata.get("sale_type") or "presale"),
            launchpad=(candidate.metadata.get("launchpad") or ""),
            start_date=candidate.metadata.get("start_date"),
            end_date=candidate.metadata.get("end_date"),
        )

        project.on_chain_metrics = analyzer.analyze(candidate)
        project.status = classify_project(project)
        project.score = score_project(project)
        project.summary = summarize_project(project)

        results.append(project)

    output_dir = root_dir / config.output.output_dir
    json_path = output_dir / "projects.json"
    csv_path = output_dir / "projects.csv"

    write_json(results, json_path)
    if config.output.include_csv:
        write_csv(results, csv_path)

    print(f"Discovered {len(results)} project(s)")
    print(f"JSON output: {json_path}")
    if config.output.include_csv:
        print(f"CSV output: {csv_path}")


if __name__ == "__main__":
    main()
