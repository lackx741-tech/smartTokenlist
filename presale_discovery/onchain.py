from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

try:
    from web3 import Web3
except Exception:  # pragma: no cover - fallback for environments without web3
    Web3 = None

from config import OnChainConfig
from models import CandidateRecord

TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex() if Web3 else ""


class OnChainAnalyzer:
    def __init__(self, config: OnChainConfig):
        self.config = config
        self._web3_clients: Dict[str, Web3] = {}

    def analyze(self, candidate: CandidateRecord) -> Dict[str, object]:
        chain = (candidate.chain or "unknown").lower()
        contract_metrics: List[Dict[str, object]] = []

        for contract in candidate.contracts:
            contract_metrics.append(self._analyze_contract(chain, contract))

        aggregate = {
            "holder_count_estimate": sum(int(m.get("holder_count_estimate", 0)) for m in contract_metrics),
            "recent_tx_count": sum(int(m.get("recent_tx_count", 0)) for m in contract_metrics),
            "unique_wallet_interactions": sum(int(m.get("unique_wallet_interactions", 0)) for m in contract_metrics),
            "liquidity_presence_hint": any(bool(m.get("liquidity_presence_hint")) for m in contract_metrics),
            "contract_age_days": max([int(m.get("contract_age_days", 0)) for m in contract_metrics] + [0]),
        }

        return {
            "contracts": contract_metrics,
            "aggregate": aggregate,
        }

    def _analyze_contract(self, chain: str, contract_address: str) -> Dict[str, object]:
        if not Web3:
            return {
                "contract": contract_address,
                "status": "skipped",
                "reason": "web3 dependency is not installed",
            }

        web3 = self._get_web3(chain)
        if not web3:
            return {
                "contract": contract_address,
                "status": "skipped",
                "reason": f"No RPC endpoint configured for chain '{chain}'",
            }

        try:
            address = Web3.to_checksum_address(contract_address)
        except Exception:
            return {
                "contract": contract_address,
                "status": "error",
                "reason": "Invalid contract address",
            }

        try:
            latest = web3.eth.block_number
            lookback_from = max(0, latest - self.config.lookback_blocks)

            code = web3.eth.get_code(address)
            contract_exists = bool(code and code != b"\x00")

            deployment_block = self._estimate_deployment_block(web3, address, latest) if contract_exists else None
            contract_age_days = self._age_days_from_block(web3, deployment_block) if deployment_block is not None else None

            logs = web3.eth.get_logs(
                {
                    "fromBlock": lookback_from,
                    "toBlock": latest,
                    "address": address,
                    "topics": [TRANSFER_TOPIC],
                }
            )

            holder_count_estimate, unique_wallets, dex_interactions = self._transfer_stats(
                logs,
                set(self._checksum_known_dex(chain)),
            )

            return {
                "contract": contract_address,
                "status": "ok",
                "contract_exists": contract_exists,
                "deployment_block_estimate": deployment_block,
                "contract_age_days": contract_age_days,
                "holder_count_estimate": holder_count_estimate,
                "recent_tx_count": len(logs),
                "unique_wallet_interactions": unique_wallets,
                "dex_interactions": dex_interactions,
                "liquidity_presence_hint": dex_interactions > 0,
                "lookback_blocks": self.config.lookback_blocks,
            }
        except Exception as exc:
            return {
                "contract": contract_address,
                "status": "error",
                "reason": str(exc),
            }

    def _get_web3(self, chain: str) -> Web3 | None:
        if not Web3:
            return None
        if chain in self._web3_clients:
            return self._web3_clients[chain]

        endpoint = self.config.rpc_endpoints.get(chain)
        if not endpoint:
            return None

        client = Web3(Web3.HTTPProvider(endpoint, request_kwargs={"timeout": 20}))
        self._web3_clients[chain] = client
        return client

    def _estimate_deployment_block(self, web3: Web3, contract: str, latest: int) -> int | None:
        low, high = 0, latest
        first_seen = None

        while low <= high:
            mid = (low + high) // 2
            code = web3.eth.get_code(contract, block_identifier=mid)
            exists = bool(code and code != b"\x00")
            if exists:
                first_seen = mid
                high = mid - 1
            else:
                low = mid + 1
        return first_seen

    def _age_days_from_block(self, web3: Web3, block_number: int | None) -> int | None:
        if block_number is None:
            return None
        block = web3.eth.get_block(block_number)
        deployed_at = datetime.fromtimestamp(block.timestamp, tz=timezone.utc)
        delta = datetime.now(timezone.utc) - deployed_at
        return max(0, delta.days)

    def _transfer_stats(self, logs: List[object], known_dex: set[str]) -> tuple[int, int, int]:
        balances: Dict[str, int] = {}
        wallets: set[str] = set()
        dex_interactions = 0

        for log in logs:
            topics = log.get("topics", [])
            if len(topics) < 3:
                continue

            from_addr = self._topic_to_address(topics[1])
            to_addr = self._topic_to_address(topics[2])
            amount = int(log.get("data", "0x0"), 16)

            if from_addr:
                balances[from_addr] = balances.get(from_addr, 0) - amount
                wallets.add(from_addr)
            if to_addr:
                balances[to_addr] = balances.get(to_addr, 0) + amount
                wallets.add(to_addr)

            if from_addr in known_dex or to_addr in known_dex:
                dex_interactions += 1

        holder_count_estimate = sum(1 for _, balance in balances.items() if balance > 0)
        return holder_count_estimate, len(wallets), dex_interactions

    @staticmethod
    def _topic_to_address(topic: object) -> str:
        raw = topic.hex() if hasattr(topic, "hex") else str(topic)
        if raw.startswith("0x"):
            raw = raw[2:]
        if len(raw) < 40:
            return ""
        return f"0x{raw[-40:]}".lower()

    def _checksum_known_dex(self, chain: str) -> List[str]:
        if not Web3:
            return []
        out = []
        for address in self.config.known_dex_addresses.get(chain, []):
            try:
                out.append(Web3.to_checksum_address(address).lower())
            except Exception:
                continue
        return out
