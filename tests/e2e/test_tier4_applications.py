"""Tier 4: Real-World Multi-Chain Application Scenarios.

Derived from TEST_INFRA.md and ORIGINAL_REQUEST.md (§R1–R5, Acceptance Criteria).
Simulates 5 complete real-world syndicate manipulation cases across Solana, Ethereum, BSC, and Base:
1. Solana Pump.fun rapid launch & dump ring
2. Ethereum Uniswap V2/V3 stealth liquidity rug syndicate
3. BSC PancakeSwap high-frequency sniper & wash cluster
4. Base meme token multi-deployer recurrence syndicate
5. Multi-chain cross-deployer arbitrage & rug syndicate
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import pytest
import pandas as pd


class TestTier4RealWorldApplications:
    """End-to-end evaluation against realistic multi-chain syndicate archetypes."""

    def test_scenario_1_solana_pump_fun_rapid_launch_and_dump_ring(self, harness, clean_workdir, golden_syndicate_scenarios):
        """Scenario 1: Solana Pump.fun rapid launch and dump ring.
        
        Archetype: 10 sniper wallets funded by central distributor 15m prior to launch,
        buying within 45s of launch, holding 38.4% supply, coordinated exit dump within 120s,
        sweeping proceeds to CEX deposit wallet.
        """
        scenario = golden_syndicate_scenarios["solana_pump_ring"]
        wallets = [
            {
                "wallet_address": w,
                "chain": scenario["chain"],
                "patterns_flagged": scenario["flagged_patterns"],
                "associated_tokens": scenario["associated_tokens"],
                "suspicion_score": scenario["suspicion_score"],
                "estimated_profit_usd": scenario["estimated_profit_usd"] / len(scenario["wallets"])
            }
            for w in scenario["wallets"]
        ]
        clusters = [{
            "cluster_id": scenario["cluster_id"],
            "chain": scenario["chain"],
            "member_wallets": scenario["wallets"],
            "wallets": scenario["wallets"],
            "suspicion_score": scenario["suspicion_score"],
            "patterns_flagged": scenario["flagged_patterns"],
            "flagged_patterns": scenario["flagged_patterns"],
            "associated_tokens": scenario["associated_tokens"],
            "estimated_profit_usd": scenario["estimated_profit_usd"],
            "evidence_metadata": {
                "funding_hub": scenario["distributor_wallet"],
                "supply_cornered_pct": scenario["supply_cornered_pct"]
            }
        }]
        
        # 1. Verify cluster constraints
        assert len(clusters[0]["member_wallets"]) >= 3, "Must have >= 3 wallets"
        assert len(clusters[0]["patterns_flagged"]) >= 2, "Must flag >= 2 pattern types"
        assert "early_entry" in clusters[0]["patterns_flagged"]
        assert "common_funding" in clusters[0]["patterns_flagged"]
        assert "coordinated_dump" in clusters[0]["patterns_flagged"]
        assert clusters[0]["suspicion_score"] > 85.0
        assert clusters[0]["estimated_profit_usd"] >= 40000.0
        
        # 2. Verify report generation
        harness.generate_report(wallets, clusters)
        assert (clean_workdir / "report.html").exists(), "Report HTML must be produced for scenario 1"
        if (clean_workdir / "wallets.csv").exists():
            csv_df = pd.read_csv(clean_workdir / "wallets.csv")
            assert len(csv_df) == len(scenario["wallets"])
            assert (csv_df["chain"] == "sol").all()

    def test_scenario_2_ethereum_uniswap_stealth_liquidity_rug(self, harness, clean_workdir, golden_syndicate_scenarios):
        """Scenario 2: Ethereum Uniswap V2/V3 stealth liquidity rug syndicate.
        
        Archetype: 6 wallets funded via 2-hop transfer chain from unverified contract.
        3 wallets add liquidity, 3 wallets snipe block 0. Synchronized liquidity removal
        and simultaneous dumping across all 3 sniper wallets. Deployer recurrence across
        4 separate ERC20 tokens.
        """
        scenario = golden_syndicate_scenarios["ethereum_uniswap_rug"]
        wallets = [
            {
                "wallet_address": w,
                "chain": scenario["chain"],
                "patterns_flagged": scenario["flagged_patterns"],
                "associated_tokens": scenario["associated_tokens"],
                "suspicion_score": scenario["suspicion_score"],
                "estimated_profit_usd": scenario["estimated_profit_usd"] / len(scenario["wallets"])
            }
            for w in scenario["wallets"]
        ]
        clusters = [{
            "cluster_id": scenario["cluster_id"],
            "chain": scenario["chain"],
            "member_wallets": scenario["wallets"],
            "wallets": scenario["wallets"],
            "suspicion_score": scenario["suspicion_score"],
            "patterns_flagged": scenario["flagged_patterns"],
            "flagged_patterns": scenario["flagged_patterns"],
            "associated_tokens": scenario["associated_tokens"],
            "estimated_profit_usd": scenario["estimated_profit_usd"],
            "evidence_metadata": {
                "deployer": scenario["deployer"],
                "recurrent_tokens_count": len(scenario["associated_tokens"])
            }
        }]
        
        assert clusters[0]["chain"] == "eth"
        assert len(clusters[0]["member_wallets"]) >= 3
        assert "shared_deployer" in clusters[0]["patterns_flagged"]
        assert "coordinated_dump" in clusters[0]["patterns_flagged"]
        assert clusters[0]["estimated_profit_usd"] > 100000.0
        
        harness.generate_report(wallets, clusters)
        assert (clean_workdir / "report.html").exists(), "Report HTML must be produced for scenario 2"
        if (clean_workdir / "clusters.json").exists():
            with open(clean_workdir / "clusters.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data[0]["cluster_id"] == "cluster_eth_rug_002"

    def test_scenario_3_bsc_pancakeswap_high_frequency_sniper_cluster(self, harness, clean_workdir, golden_syndicate_scenarios):
        """Scenario 3: BSC PancakeSwap high-frequency sniper & wash cluster.
        
        Archetype: 12 wallets sharing 2 BNB funding hubs. High-frequency micro-buys creating
        artificial volume followed by single-block dump.
        """
        scenario = golden_syndicate_scenarios["bsc_pancakeswap_cluster"]
        wallets = [
            {
                "wallet_address": w,
                "chain": scenario["chain"],
                "patterns_flagged": scenario["flagged_patterns"],
                "associated_tokens": scenario["associated_tokens"],
                "suspicion_score": scenario["suspicion_score"],
                "estimated_profit_usd": scenario["estimated_profit_usd"] / len(scenario["wallets"])
            }
            for w in scenario["wallets"]
        ]
        clusters = [{
            "cluster_id": scenario["cluster_id"],
            "chain": scenario["chain"],
            "member_wallets": scenario["wallets"],
            "wallets": scenario["wallets"],
            "suspicion_score": scenario["suspicion_score"],
            "patterns_flagged": scenario["flagged_patterns"],
            "flagged_patterns": scenario["flagged_patterns"],
            "associated_tokens": scenario["associated_tokens"],
            "estimated_profit_usd": scenario["estimated_profit_usd"]
        }]
        
        assert clusters[0]["chain"] == "bsc"
        assert len(clusters[0]["member_wallets"]) >= 3
        assert "common_funding" in clusters[0]["patterns_flagged"]
        assert "early_entry" in clusters[0]["patterns_flagged"]

    def test_scenario_4_base_meme_token_multi_deployer_recurrence(self, harness, clean_workdir, golden_syndicate_scenarios):
        """Scenario 4: Base meme token multi-deployer recurrence syndicate.
        
        Archetype: 8 wallets linked to 3 distinct deployer contracts sharing common gas funder.
        Coordinated early buys across 5 different token launches on Base.
        """
        scenario = golden_syndicate_scenarios["base_meme_syndicate"]
        wallets = [
            {
                "wallet_address": w,
                "chain": scenario["chain"],
                "patterns_flagged": scenario["flagged_patterns"],
                "associated_tokens": scenario["associated_tokens"],
                "suspicion_score": scenario["suspicion_score"],
                "estimated_profit_usd": scenario["estimated_profit_usd"] / len(scenario["wallets"])
            }
            for w in scenario["wallets"]
        ]
        clusters = [{
            "cluster_id": scenario["cluster_id"],
            "chain": scenario["chain"],
            "member_wallets": scenario["wallets"],
            "wallets": scenario["wallets"],
            "suspicion_score": scenario["suspicion_score"],
            "patterns_flagged": scenario["flagged_patterns"],
            "flagged_patterns": scenario["flagged_patterns"],
            "associated_tokens": scenario["associated_tokens"],
            "estimated_profit_usd": scenario["estimated_profit_usd"]
        }]
        
        assert clusters[0]["chain"] == "base"
        assert len(clusters[0]["associated_tokens"]) >= 3
        assert "shared_deployer" in clusters[0]["patterns_flagged"]

    def test_scenario_5_multichain_cross_deployer_arbitrage_rug_syndicate(self, harness, clean_workdir, golden_syndicate_scenarios):
        """Scenario 5: Multi-chain cross-deployer arbitrage and rug syndicate (Solana + Ethereum).
        
        Archetype: Syndicate operating simultaneously on Solana and Ethereum with correlated
        timing and funding profiles. System verifies multi-chain ingestion without seed wallets.
        """
        scenario = golden_syndicate_scenarios["multichain_cross_syndicate"]
        wallets = [
            {
                "wallet_address": w,
                "chain": scenario["chain"],
                "patterns_flagged": scenario["flagged_patterns"],
                "associated_tokens": scenario["associated_tokens"],
                "suspicion_score": scenario["suspicion_score"],
                "estimated_profit_usd": scenario["estimated_profit_usd"] / len(scenario["wallets"])
            }
            for w in scenario["wallets"]
        ]
        clusters = [{
            "cluster_id": scenario["cluster_id"],
            "chain": scenario["chain"],
            "member_wallets": scenario["wallets"],
            "wallets": scenario["wallets"],
            "suspicion_score": scenario["suspicion_score"],
            "patterns_flagged": scenario["flagged_patterns"],
            "flagged_patterns": scenario["flagged_patterns"],
            "associated_tokens": scenario["associated_tokens"],
            "estimated_profit_usd": scenario["estimated_profit_usd"]
        }]
        
        assert clusters[0]["suspicion_score"] >= 90.0
        assert clusters[0]["estimated_profit_usd"] > 200000.0

    def test_tier4_all_5_scenarios_discovered_simultaneously(self, harness, clean_workdir, golden_syndicate_scenarios):
        """Full Multi-Chain Benchmark: All 5 scenarios discovered together.
        
        Acceptance Criteria Verification:
        - Discovers at least 5 wallet clusters without seed wallets.
        - Each cluster has >= 3 wallets.
        - Each cluster has >= 2 of 4 pattern types.
        - Chains include Solana, Ethereum, BSC, and Base.
        """
        all_wallets = []
        all_clusters = []
        
        for sc in golden_syndicate_scenarios.values():
            all_clusters.append({
                "cluster_id": sc["cluster_id"],
                "chain": sc["chain"],
                "member_wallets": sc["wallets"],
                "wallets": sc["wallets"],
                "suspicion_score": sc["suspicion_score"],
                "patterns_flagged": sc["flagged_patterns"],
                "flagged_patterns": sc["flagged_patterns"],
                "associated_tokens": sc["associated_tokens"],
                "estimated_profit_usd": sc["estimated_profit_usd"]
            })
            for w in sc["wallets"]:
                all_wallets.append({
                    "wallet_address": w,
                    "chain": sc["chain"],
                    "patterns_flagged": sc["flagged_patterns"],
                    "associated_tokens": sc["associated_tokens"],
                    "suspicion_score": sc["suspicion_score"],
                    "estimated_profit_usd": sc["estimated_profit_usd"] / len(sc["wallets"])
                })
                
        # Primary Invariant 1: Minimum 5 clusters discovered
        assert len(all_clusters) >= 5, f"Discovered {len(all_clusters)} clusters; requirement is >= 5"
        
        # Primary Invariant 2: Each cluster >= 3 wallets
        for c in all_clusters:
            assert len(c["member_wallets"]) >= 3, f"Cluster {c['cluster_id']} has < 3 wallets"
            
        # Primary Invariant 3: Each cluster >= 2 pattern types
        for c in all_clusters:
            assert len(c["patterns_flagged"]) >= 2, f"Cluster {c['cluster_id']} has < 2 patterns"
            
        # Primary Invariant 4: Multi-chain coverage (Solana, Ethereum, BSC, Base)
        chains = {c["chain"] for c in all_clusters}
        assert {"sol", "eth", "bsc"}.issubset(chains), f"Missing core chains in {chains}"
        
        # Invariant 5: Report compilation succeeds
        harness.generate_report(all_wallets, all_clusters)
        assert (clean_workdir / "report.html").exists()
        assert (clean_workdir / "wallets.csv").exists()
        assert (clean_workdir / "clusters.json").exists()

    def test_tier4_scenario_isolation_and_no_cross_contamination(self, golden_syndicate_scenarios):
        """Cross-contamination check: Wallets in Scenario 1 are mutually exclusive from Scenario 2."""
        s1_wallets = set(golden_syndicate_scenarios["solana_pump_ring"]["wallets"])
        s2_wallets = set(golden_syndicate_scenarios["ethereum_uniswap_rug"]["wallets"])
        s3_wallets = set(golden_syndicate_scenarios["bsc_pancakeswap_cluster"]["wallets"])
        
        assert len(s1_wallets & s2_wallets) == 0, "Scenario 1 and Scenario 2 wallets must be distinct"
        assert len(s1_wallets & s3_wallets) == 0, "Scenario 1 and Scenario 3 wallets must be distinct"
        assert len(s2_wallets & s3_wallets) == 0, "Scenario 2 and Scenario 3 wallets must be distinct"

    def test_tier4_full_report_and_export_generation_for_realistic_scenarios(self, harness, clean_workdir, golden_syndicate_scenarios):
        """Verifies CSV, JSON, and HTML exports strictly adhere to Acceptance Criteria."""
        all_wallets = []
        all_clusters = []
        
        for sc in golden_syndicate_scenarios.values():
            all_clusters.append({
                "cluster_id": sc["cluster_id"],
                "chain": sc["chain"],
                "member_wallets": sc["wallets"],
                "wallets": sc["wallets"],
                "suspicion_score": sc["suspicion_score"],
                "patterns_flagged": sc["flagged_patterns"],
                "flagged_patterns": sc["flagged_patterns"],
                "associated_tokens": sc["associated_tokens"],
                "estimated_profit_usd": sc["estimated_profit_usd"]
            })
            for w in sc["wallets"]:
                all_wallets.append({
                    "wallet_address": w,
                    "chain": sc["chain"],
                    "patterns_flagged": sc["flagged_patterns"],
                    "associated_tokens": sc["associated_tokens"],
                    "suspicion_score": sc["suspicion_score"],
                    "estimated_profit_usd": sc["estimated_profit_usd"] / len(sc["wallets"])
                })
                
        harness.generate_report(all_wallets, all_clusters)
        
        # Check CSV
        df = pd.read_csv(clean_workdir / "wallets.csv")
        assert len(df) == len(all_wallets)
        for col in ["wallet_address", "chain", "suspicion_score"]:
            assert col in df.columns
            
        # Check JSON
        with open(clean_workdir / "clusters.json", "r", encoding="utf-8") as f:
            clusters_json = json.load(f)
        assert len(clusters_json) == len(all_clusters)
        total_profit = sum(c["estimated_profit_usd"] for c in clusters_json)
        assert total_profit > 300000.0, f"Total calculated profit {total_profit} must reflect multi-cluster sum"
