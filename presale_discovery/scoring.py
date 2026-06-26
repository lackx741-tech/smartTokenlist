from __future__ import annotations

from models import ProjectResult


def score_project(project: ProjectResult) -> float:
    score = 0.0

    if project.website:
        score += 12
    if project.token_symbol:
        score += 8
    if project.contracts:
        score += 15

    if project.chain and project.chain != "unknown":
        score += 5

    aggregate = project.on_chain_metrics.get("aggregate", {})

    holders = int(aggregate.get("holder_count_estimate") or 0)
    tx_count = int(aggregate.get("recent_tx_count") or 0)
    wallets = int(aggregate.get("unique_wallet_interactions") or 0)
    has_liquidity_hint = bool(aggregate.get("liquidity_presence_hint"))
    age_days = int(aggregate.get("contract_age_days") or 0)

    if holders >= 500:
        score += 20
    elif holders >= 100:
        score += 14
    elif holders >= 20:
        score += 8

    if tx_count >= 1000:
        score += 15
    elif tx_count >= 100:
        score += 10
    elif tx_count >= 20:
        score += 6

    if wallets >= 200:
        score += 12
    elif wallets >= 50:
        score += 8
    elif wallets >= 10:
        score += 4

    if has_liquidity_hint:
        score += 10

    if 1 <= age_days <= 730:
        score += 5

    if project.status == "live":
        score += 10
    elif project.status == "upcoming":
        score += 7
    elif project.status == "past":
        score += 4

    return round(max(0.0, min(score, 100.0)), 2)


def summarize_project(project: ProjectResult) -> str:
    aggregate = project.on_chain_metrics.get("aggregate", {})
    holders = int(aggregate.get("holder_count_estimate") or 0)
    tx_count = int(aggregate.get("recent_tx_count") or 0)
    wallets = int(aggregate.get("unique_wallet_interactions") or 0)
    liquidity = "yes" if aggregate.get("liquidity_presence_hint") else "no"

    return (
        f"{project.project_name} is classified as {project.status}. "
        f"Chain: {project.chain}. Symbol: {project.token_symbol or 'N/A'}. "
        f"On-chain hints -> holders(est): {holders}, transfer activity: {tx_count}, "
        f"unique wallets: {wallets}, DEX/liquidity hint: {liquidity}."
    )
