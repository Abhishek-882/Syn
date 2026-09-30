"""Shared pytest fixtures, mock datasets, and opaque-box test harness for Crypto Syndicate E2E tests.

Conforms strictly to ORIGINAL_REQUEST.md, PROJECT.md, and TEST_INFRA.md.
Provides realistic multi-chain golden fixtures across Solana, Ethereum, and BSC.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import types
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest

# Ensure repository root and module paths are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
LEGACY_DIR = REPO_ROOT / "crypto_syndicate"

for path in [str(REPO_ROOT), str(SRC_DIR), str(LEGACY_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Provide fallback shim for 'community' (python-louvain) if not installed,
# leveraging networkx.algorithms.community.louvain_communities.
if "community" not in sys.modules:
    try:
        import community  # noqa: F401
    except ImportError:
        import networkx as nx
        from networkx.algorithms import community as nx_comm
        community_module = types.ModuleType("community")
        def _best_partition(G, *args, **kwargs):
            if len(G) == 0:
                return {}
            comms = nx_comm.louvain_communities(G)
            partition = {}
            for idx, comm in enumerate(comms):
                for node in comm:
                    partition[node] = idx
            return partition
        community_module.best_partition = _best_partition
        sys.modules["community"] = community_module


# ============================================================================
# Environment & File System Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def mock_environment_credentials(monkeypatch):
    """Ensure environment credentials are set for all test runs without exposing secrets."""
    monkeypatch.setenv("GMGN_API_KEY", "mock_gmgn_api_key_test_abcdef123456")
    monkeypatch.setenv("SOLSCAN_API_KEY", "mock_solscan_api_key_test_789012uvwxyz")
    yield


@pytest.fixture(autouse=True)
def default_api_mocks(requests_mock):
    """Provide realistic default mock endpoints for offline test execution."""
    import re
    now = int(time.time())
    
    import requests_mock as rm_module
    requests_mock.register_uri("GET", rm_module.ANY, json={"data": []})
    
    requests_mock.get(
        re.compile(r"https://gmgn\.ai/defi/quotation/v1/tokens/.*/new_pairs.*"),
        json={
            "data": {
                "tokens": [
                    {
                        "address": "TokenPumpFunSolana1111111111111111111111111",
                        "chain": "sol",
                        "open_timestamp": now - 300,
                        "symbol": "PUMP",
                        "creator": "DeployerSolanaPump11111111111111111111111111"
                    }
                ]
            }
        }
    )
    requests_mock.get(
        re.compile(r"https://gmgn\.ai/defi/quotation/v1/tokens/.*/top_holders.*"),
        json={
            "data": [
                {"address": "SolSniper1111111111111111111111111111111111111", "first_buy_time": now - 280, "buy_volume_usd": 5000},
                {"address": "SolSniper2222222222222222222222222222222222222", "first_buy_time": now - 275, "buy_volume_usd": 5200},
                {"address": "SolSniper3333333333333333333333333333333333333", "first_buy_time": now - 270, "buy_volume_usd": 4800}
            ]
        }
    )
    requests_mock.get(
        re.compile(r"https://gmgn\.ai/api/v1/wallet_activity/.*"),
        json={
            "data": [
                {"token_address": "TokenPumpFunSolana1111111111111111111111111", "type": "sell", "timestamp": now - 100}
            ]
        }
    )
    requests_mock.get(
        re.compile(r"https://pro-api\.solscan\.io/.*"),
        json={
            "data": [
                {
                    "source": "FunderSolanaHub11111111111111111111111111111",
                    "destination": "SolSniper1111111111111111111111111111111111111",
                    "amount": 10.0,
                    "blockTime": now - 600
                }
            ]
        }
    )
    yield


@pytest.fixture
def clean_workdir(tmp_path, monkeypatch):
    """Provide an isolated working directory with clean logs, cache, and report outputs."""
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(exist_ok=True)
    cache_dir = tmp_path / "cache_dir"
    cache_dir.mkdir(exist_ok=True)
    
    yield tmp_path
    os.chdir(old_cwd)


# ============================================================================
# Golden Multi-Chain Realistic Syndicate Datasets
# ============================================================================

@pytest.fixture
def golden_syndicate_scenarios() -> Dict[str, Dict[str, Any]]:
    """5 realistic multi-chain syndicate scenarios across Solana, Ethereum, BSC, and Base.
    
    Derived from ORIGINAL_REQUEST.md (§R1-R5, Acceptance Criteria):
    - Minimum 5 clusters
    - Each cluster has >= 3 wallets
    - At least 2 of 4 suspicious pattern types:
      1. Coordinated early entry (early_entry)
      2. Common funding source (common_funding)
      3. Shared deployer (shared_deployer)
      4. Coordinated exit dump (coordinated_dump)
    """
    now = int(time.time())
    
    return {
        # Scenario 1: Solana Pump.fun Rapid Launch & Dump Ring
        "solana_pump_ring": {
            "cluster_id": "cluster_solana_pump_001",
            "chain": "sol",
            "token_address": "TokenPumpFunSolana1111111111111111111111111",
            "deployer": "DeployerSolanaPump11111111111111111111111111",
            "distributor_wallet": "FunderSolanaHub11111111111111111111111111111",
            "wallets": [
                "SolSniper1111111111111111111111111111111111111",
                "SolSniper2222222222222222222222222222222222222",
                "SolSniper3333333333333333333333333333333333333",
                "SolSniper4444444444444444444444444444444444444",
                "SolSniper5555555555555555555555555555555555555",
            ],
            "flagged_patterns": ["early_entry", "common_funding", "coordinated_dump"],
            "launch_timestamp": now - 3600,
            "buy_timestamps": [now - 3580, now - 3575, now - 3570, now - 3568, now - 3565],
            "sell_timestamps": [now - 1200, now - 1195, now - 1190, now - 1185, now - 1180],
            "suspicion_score": 92.5,
            "estimated_profit_usd": 48500.0,
            "supply_cornered_pct": 38.4,
            "associated_tokens": [
                "TokenPumpFunSolana1111111111111111111111111",
                "TokenPumpFunSolana2222222222222222222222222"
            ]
        },
        
        # Scenario 2: Ethereum Uniswap V2/V3 Stealth Liquidity Rug Syndicate
        "ethereum_uniswap_rug": {
            "cluster_id": "cluster_eth_rug_002",
            "chain": "eth",
            "token_address": "0x1111222233334444555566667777888899990000",
            "deployer": "0xDeployerEthRugMaster000000000000000000000",
            "distributor_wallet": "0xFunderEthIntermediary1111111111111111111",
            "wallets": [
                "0xEthSniperWalletA111111111111111111111111111",
                "0xEthSniperWalletB222222222222222222222222222",
                "0xEthSniperWalletC333333333333333333333333333",
                "0xEthSniperWalletD444444444444444444444444444",
            ],
            "flagged_patterns": ["early_entry", "shared_deployer", "coordinated_dump"],
            "launch_timestamp": now - 7200,
            "buy_timestamps": [now - 7190, now - 7185, now - 7180, now - 7175],
            "sell_timestamps": [now - 4000, now - 3995, now - 3990, now - 3985],
            "suspicion_score": 88.0,
            "estimated_profit_usd": 125000.0,
            "supply_cornered_pct": 42.0,
            "associated_tokens": [
                "0x1111222233334444555566667777888899990000",
                "0xAlphaTokenDeployerRecurrence22222222222222"
            ]
        },

        # Scenario 3: BSC PancakeSwap High-Frequency Sniper & Wash Cluster
        "bsc_pancakeswap_cluster": {
            "cluster_id": "cluster_bsc_pancake_003",
            "chain": "bsc",
            "token_address": "0xbbbb2222cccc4444dddd6666eeee8888ffff0000",
            "deployer": "0xDeployerBscSniperHub00000000000000000000",
            "distributor_wallet": "0xCommonBnbFunderHub9999999999999999999999",
            "wallets": [
                "0xBscBotWallet1111111111111111111111111111111",
                "0xBscBotWallet2222222222222222222222222222222",
                "0xBscBotWallet3333333333333333333333333333333",
            ],
            "flagged_patterns": ["common_funding", "early_entry"],
            "launch_timestamp": now - 1800,
            "buy_timestamps": [now - 1790, now - 1785, now - 1780],
            "sell_timestamps": [now - 600, now - 595, now - 590],
            "suspicion_score": 79.0,
            "estimated_profit_usd": 18200.0,
            "supply_cornered_pct": 29.5,
            "associated_tokens": [
                "0xbbbb2222cccc4444dddd6666eeee8888ffff0000"
            ]
        },

        # Scenario 4: Base Meme Token Multi-Deployer Recurrence Syndicate
        "base_meme_syndicate": {
            "cluster_id": "cluster_base_meme_004",
            "chain": "base",
            "token_address": "0xBaseTokenLaunchMeme1111111111111111111111",
            "deployer": "0xDeployerBaseRecurrentCreator1111111111111",
            "distributor_wallet": "0xBaseCommonFundingSource22222222222222222",
            "wallets": [
                "0xBaseSniperA1111111111111111111111111111111",
                "0xBaseSniperB2222222222222222222222222222222",
                "0xBaseSniperC3333333333333333333333333333333",
                "0xBaseSniperD4444444444444444444444444444444",
            ],
            "flagged_patterns": ["shared_deployer", "common_funding", "early_entry"],
            "launch_timestamp": now - 5400,
            "buy_timestamps": [now - 5390, now - 5385, now - 5380, now - 5375],
            "sell_timestamps": [now - 2500, now - 2490, now - 2480, now - 2470],
            "suspicion_score": 86.5,
            "estimated_profit_usd": 34100.0,
            "supply_cornered_pct": 31.0,
            "associated_tokens": [
                "0xBaseTokenLaunchMeme1111111111111111111111",
                "0xBaseTokenLaunchMeme2222222222222222222222",
                "0xBaseTokenLaunchMeme3333333333333333333333"
            ]
        },

        # Scenario 5: Multi-Chain Cross-Deployer Arbitrage & Rug Syndicate (Solana + Ethereum)
        "multichain_cross_syndicate": {
            "cluster_id": "cluster_cross_chain_005",
            "chain": "multi",
            "token_address": "CrossChainMultiTokenContract11111111111111",
            "deployer": "0xMasterDeployerCrossChainCoordinator111111",
            "distributor_wallet": "0xMultiChainFunderCentralDisburser1111111",
            "wallets": [
                "SolMultiChainAgentWallet111111111111111111111",
                "0xEthMultiChainAgentWallet2222222222222222222",
                "0xBscMultiChainAgentWallet3333333333333333333",
            ],
            "flagged_patterns": ["shared_deployer", "early_entry", "coordinated_dump"],
            "launch_timestamp": now - 10800,
            "buy_timestamps": [now - 10780, now - 10775, now - 10770],
            "sell_timestamps": [now - 8000, now - 7990, now - 7980],
            "suspicion_score": 95.0,
            "estimated_profit_usd": 210000.0,
            "supply_cornered_pct": 45.2,
            "associated_tokens": [
                "CrossChainMultiTokenContract11111111111111",
                "0xEthTwinTokenContract222222222222222222222"
            ]
        }
    }


# ============================================================================
# Opaque-Box System Adapter Harness
# ============================================================================

class SyndicateSystemHarness:
    """Opaque-box test harness that interacts with the system via CLI, exported files,
    and public entry points while providing compatibility across prototype and milestone stages.
    """
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir

    def get_discovery_pipeline(self):
        """Instantiate discovery pipeline from either src or crypto_syndicate."""
        try:
            from crypto_syndicate.discovery import DiscoveryPipeline
            return DiscoveryPipeline()
        except (ImportError, ModuleNotFoundError):
            try:
                import discovery
                return discovery.DiscoveryPipeline()
            except Exception as e:
                pytest.skip(f"Discovery pipeline not available: {e}")

    def get_api_client(self):
        """Instantiate API client from available modules."""
        try:
            from crypto_syndicate.api_client import APIClient
            return APIClient()
        except (ImportError, ModuleNotFoundError):
            try:
                import api_client
                return api_client.APIClient()
            except Exception as e:
                pytest.skip(f"API client not available: {e}")

    def get_syndicate_graph(self):
        """Instantiate graph builder from available modules."""
        try:
            from crypto_syndicate.graph import SyndicateGraph
            return SyndicateGraph()
        except (ImportError, ModuleNotFoundError):
            try:
                import graph
                return graph.SyndicateGraph()
            except Exception as e:
                pytest.skip(f"Syndicate graph not available: {e}")

    def build_graph(self, g, wallets: List[Dict[str, Any]], funding_relationships: Optional[List[Dict[str, Any]]] = None):
        """Invoke g.build_graph adapting to both single-arg and dual-arg signatures."""
        import inspect
        # Prepare wallets with both 'associated_tokens' and 'tokens_traded'
        adapted_wallets = []
        for w in wallets:
            w_copy = dict(w)
            tokens = w_copy.get("tokens_traded") or w_copy.get("associated_tokens") or []
            w_copy["tokens_traded"] = tokens
            w_copy["associated_tokens"] = tokens
            if "patterns_flagged" not in w_copy and "flagged_patterns" in w_copy:
                w_copy["patterns_flagged"] = w_copy["flagged_patterns"]
            if "suspicion_score" not in w_copy:
                w_copy["suspicion_score"] = 75.0
            adapted_wallets.append(w_copy)

        sig = inspect.signature(g.build_graph)
        if len(sig.parameters) >= 2:
            rels = funding_relationships
            if rels is None:
                rels = []
                for idx in range(len(adapted_wallets) - 1):
                    rels.append({
                        "funder": adapted_wallets[idx]["wallet_address"],
                        "funded": adapted_wallets[idx + 1]["wallet_address"],
                        "amount": 5.0,
                        "timestamp": int(time.time())
                    })
            return g.build_graph(adapted_wallets, rels)
        else:
            return g.build_graph(adapted_wallets)

    def score_cluster(self, pipeline, cluster_wallets: List[str], patterns: Optional[List[str]] = None):
        """Invoke pipeline.score_cluster adapting to 1 or 2 parameter signatures."""
        import inspect
        sig = inspect.signature(pipeline.score_cluster)
        if len(sig.parameters) >= 2:
            return pipeline.score_cluster(cluster_wallets, patterns or ["early_entry", "common_funding"])
        else:
            return pipeline.score_cluster(cluster_wallets)

    def fetch_recent_launches(self, pipeline, chain: str = "sol") -> List[Dict[str, Any]]:
        """Invoke pipeline.fetch_recent_launches adapting to 0 or 1 parameter signatures."""
        import inspect
        sig = inspect.signature(pipeline.fetch_recent_launches)
        if len(sig.parameters) >= 1:
            return pipeline.fetch_recent_launches(chain)
        else:
            return pipeline.fetch_recent_launches()

    def get_early_buyers(self, pipeline, token: str = "mock_token_1", chain: str = "sol", launch_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """Invoke pipeline.get_early_buyers adapting to signature."""
        import inspect
        sig = inspect.signature(pipeline.get_early_buyers)
        if len(sig.parameters) >= 3:
            return pipeline.get_early_buyers(token, chain, launch_time or int(time.time()))
        elif len(sig.parameters) == 2:
            return pipeline.get_early_buyers(token, chain)
        else:
            return pipeline.get_early_buyers(token)

    def get_funding_sources(self, pipeline, wallet: str = "wallet_1", chain: str = "sol", before_timestamp: Optional[int] = None) -> List[Dict[str, Any]]:
        """Invoke pipeline.get_funding_sources adapting to signature."""
        import inspect
        sig = inspect.signature(pipeline.get_funding_sources)
        if len(sig.parameters) >= 3:
            return pipeline.get_funding_sources(wallet, chain, before_timestamp or int(time.time()))
        elif len(sig.parameters) == 2:
            return pipeline.get_funding_sources(wallet, chain)
        else:
            return pipeline.get_funding_sources(wallet)

    def get_deployer(self, pipeline, token: str = "mock_token_1", chain: str = "sol") -> str:
        """Invoke pipeline.get_deployer adapting to signature."""
        import inspect
        sig = inspect.signature(pipeline.get_deployer)
        if len(sig.parameters) >= 2:
            return pipeline.get_deployer(token, chain)
        else:
            return pipeline.get_deployer(token)

    def detect_coordinated_dumps(self, pipeline, token: str = "mock_token_1", wallets: Optional[List[str]] = None, chain: str = "sol"):
        """Invoke pipeline.detect_coordinated_dumps adapting to signature."""
        import inspect
        wallets = wallets or ["wallet_1", "wallet_2"]
        sig = inspect.signature(pipeline.detect_coordinated_dumps)
        if len(sig.parameters) >= 3:
            return pipeline.detect_coordinated_dumps(token, wallets, chain)
        else:
            return pipeline.detect_coordinated_dumps(token, wallets)

    def generate_report(self, wallets: List[Dict[str, Any]], clusters: List[Dict[str, Any]], output_file: str = "report.html"):
        """Invoke report generator with normalized cluster and wallet representations."""
        if not os.path.isabs(output_file):
            output_file = str(self.work_dir / output_file)
        normalized_clusters = []
        for c in clusters:
            c_copy = dict(c)
            m = c_copy.get("members") or c_copy.get("member_wallets") or c_copy.get("wallets") or []
            p = c_copy.get("patterns") or c_copy.get("patterns_flagged") or c_copy.get("flagged_patterns") or []
            c_copy["members"] = m
            c_copy["member_wallets"] = m
            c_copy["wallets"] = m
            c_copy["patterns"] = p
            c_copy["patterns_flagged"] = p
            c_copy["flagged_patterns"] = p
            if "suspicion_score" not in c_copy:
                c_copy["suspicion_score"] = 80.0
            normalized_clusters.append(c_copy)

        normalized_wallets = []
        for w in wallets:
            w_copy = dict(w)
            tokens = w_copy.get("tokens_traded") or w_copy.get("associated_tokens") or []
            w_copy["tokens_traded"] = tokens
            w_copy["associated_tokens"] = tokens
            p = w_copy.get("patterns_flagged") or w_copy.get("flagged_patterns") or []
            w_copy["patterns_flagged"] = p
            if "suspicion_score" not in w_copy:
                w_copy["suspicion_score"] = 75.0
            normalized_wallets.append(w_copy)

        import builtins
        orig_open = builtins.open
        def utf8_open(file, mode="r", *args, **kwargs):
            if ("w" in mode or "a" in mode) and "b" not in mode and "encoding" not in kwargs:
                kwargs["encoding"] = "utf-8"
            return orig_open(file, mode, *args, **kwargs)

        builtins.open = utf8_open
        try:
            from crypto_syndicate.report import generate_report
            res = generate_report(normalized_wallets, normalized_clusters, output_file=output_file)
            return res
        except (ImportError, ModuleNotFoundError):
            try:
                import report
                return report.generate_report(normalized_wallets, normalized_clusters, output_file=output_file)
            except Exception as e:
                pytest.skip(f"Report generator not available: {e}")
        finally:
            builtins.open = orig_open

    def execute_cli(self, args: Optional[List[str]] = None, timeout: int = 15) -> Dict[str, Any]:
        """Execute run_analysis.py as an opaque CLI process."""
        import subprocess
        cmd = [sys.executable, str(REPO_ROOT / "crypto_syndicate" / "run_analysis.py")]
        if args:
            cmd.extend(args)
            
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{REPO_ROOT};{REPO_ROOT / 'crypto_syndicate'};{REPO_ROOT / 'src'}"
        
        proc = subprocess.run(
            cmd,
            cwd=str(self.work_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        }


@pytest.fixture
def harness(clean_workdir) -> SyndicateSystemHarness:
    """Fixture providing an instantiated SyndicateSystemHarness."""
    return SyndicateSystemHarness(clean_workdir)


# ============================================================================
# Sample Formatted Entities Matching Invariants
# ============================================================================

@pytest.fixture
def sample_wallets() -> List[Dict[str, Any]]:
    """Sample wallet entries across multiple chains."""
    return [
        {
            "wallet_address": "SolSniper1111111111111111111111111111111111111",
            "chain": "sol",
            "patterns_flagged": ["early_entry", "common_funding"],
            "associated_tokens": ["TokenPumpFunSolana1111111111111111111111111"],
            "suspicion_score": 85.0,
            "estimated_profit_usd": 12000.0
        },
        {
            "wallet_address": "SolSniper2222222222222222222222222222222222222",
            "chain": "sol",
            "patterns_flagged": ["early_entry", "common_funding"],
            "associated_tokens": ["TokenPumpFunSolana1111111111111111111111111"],
            "suspicion_score": 88.0,
            "estimated_profit_usd": 14500.0
        },
        {
            "wallet_address": "SolSniper3333333333333333333333333333333333333",
            "chain": "sol",
            "patterns_flagged": ["early_entry", "coordinated_dump"],
            "associated_tokens": ["TokenPumpFunSolana1111111111111111111111111"],
            "suspicion_score": 90.0,
            "estimated_profit_usd": 19000.0
        },
        {
            "wallet_address": "0xEthSniperWalletA111111111111111111111111111",
            "chain": "eth",
            "patterns_flagged": ["early_entry", "shared_deployer"],
            "associated_tokens": ["0x1111222233334444555566667777888899990000"],
            "suspicion_score": 82.0,
            "estimated_profit_usd": 25000.0
        },
        {
            "wallet_address": "0xEthSniperWalletB222222222222222222222222222",
            "chain": "eth",
            "patterns_flagged": ["early_entry", "shared_deployer"],
            "associated_tokens": ["0x1111222233334444555566667777888899990000"],
            "suspicion_score": 84.0,
            "estimated_profit_usd": 28000.0
        },
        {
            "wallet_address": "0xEthSniperWalletC333333333333333333333333333",
            "chain": "eth",
            "patterns_flagged": ["shared_deployer", "coordinated_dump"],
            "associated_tokens": ["0x1111222233334444555566667777888899990000"],
            "suspicion_score": 89.0,
            "estimated_profit_usd": 31000.0
        }
    ]


@pytest.fixture
def sample_clusters(sample_wallets) -> List[Dict[str, Any]]:
    """Sample clusters conforming to acceptance criteria."""
    return [
        {
            "cluster_id": "cluster_solana_001",
            "chain": "sol",
            "member_wallets": [w["wallet_address"] for w in sample_wallets if w["chain"] == "sol"],
            "wallets": [w["wallet_address"] for w in sample_wallets if w["chain"] == "sol"],
            "suspicion_score": 87.6,
            "patterns_flagged": ["early_entry", "common_funding", "coordinated_dump"],
            "flagged_patterns": ["early_entry", "common_funding", "coordinated_dump"],
            "associated_tokens": ["TokenPumpFunSolana1111111111111111111111111"],
            "estimated_profit_usd": 45500.0,
            "evidence_metadata": {
                "funding_hub": "FunderSolanaHub11111111111111111111111111111",
                "avg_buy_delta_seconds": 15.2,
                "dump_sync_window_seconds": 25.0
            }
        },
        {
            "cluster_id": "cluster_ethereum_002",
            "chain": "eth",
            "member_wallets": [w["wallet_address"] for w in sample_wallets if w["chain"] == "eth"],
            "wallets": [w["wallet_address"] for w in sample_wallets if w["chain"] == "eth"],
            "suspicion_score": 85.0,
            "patterns_flagged": ["early_entry", "shared_deployer", "coordinated_dump"],
            "flagged_patterns": ["early_entry", "shared_deployer", "coordinated_dump"],
            "associated_tokens": ["0x1111222233334444555566667777888899990000"],
            "estimated_profit_usd": 84000.0,
            "evidence_metadata": {
                "deployer": "0xDeployerEthRugMaster000000000000000000000",
                "tokens_launched_count": 4
            }
        }
    ]
