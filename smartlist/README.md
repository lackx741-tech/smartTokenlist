# Smartlist Presale/ICO Discovery Tool

This folder contains a new, isolated implementation for discovering and researching crypto presale / ICO projects using configurable discovery sources plus on-chain interaction signals.

## What it supports

- Discovery candidates from:
  - manually curated project records (`sample_inputs/manual_projects.json`)
  - seed URL lists (`sample_inputs/seed_urls.txt`)
  - optional search queries through SerpAPI (`enable_serpapi`)
- Classification into: `past`, `live`, `upcoming`, `unknown`
- On-chain signal collection per contract (when RPC endpoints are configured):
  - holder count estimate from Transfer logs
  - transfer activity hints
  - wallet interaction counts
  - contract deployment age estimate
  - DEX interaction/liquidity presence hints
- Scoring and practical summary generation
- Structured outputs in JSON and CSV

## Files

- `main.py` – CLI entry point
- `config.py` – config schema and loader
- `models.py` – structured data models
- `discovery.py` – discovery sources ingestion
- `onchain.py` – on-chain metrics collector
- `classification.py` – status classifier
- `scoring.py` – ranking + summary
- `output_writer.py` – JSON/CSV export
- `sample_config.json` – example config
- `sample_inputs/` – sample manual records and seed URLs

## Setup

From repository root:

```bash
pip install -r requirements.txt
```

Set RPC endpoints for chains you want on-chain metrics from (or keep empty to run metadata-only):

```bash
export ETH_RPC_URL="https://..."
export BSC_RPC_URL="https://..."
```

## Usage

```bash
python /home/runner/work/smartTokenlist/smartTokenlist/smartlist/main.py \
  --config /home/runner/work/smartTokenlist/smartTokenlist/smartlist/sample_config.json
```

Outputs are written to:

- `/home/runner/work/smartTokenlist/smartTokenlist/smartlist/outputs/projects.json`
- `/home/runner/work/smartTokenlist/smartTokenlist/smartlist/outputs/projects.csv`

## Config notes

`sample_config.json` supports:

- discovery source file paths
- enabling/disabling query discovery
- lookback block depth for on-chain signal extraction
- chain RPC endpoints
- known DEX addresses for market/liquidity hints
- output format controls

You can extend discovery by adding new ingestion methods in `CandidateDiscovery` without changing the rest of the pipeline.
