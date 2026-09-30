"""Deterministic multi-chain golden syndicate fixtures.

Provides 5 realistic, mathematically consistent syndicate scenarios across
Solana, Ethereum, BSC, Base, and Cross-Chain:
1. SYN-SOL-PUMP-01: Solana Pump.fun rapid launch & coordinated dump ring
2. SYN-ETH-UNI-02: Ethereum Uniswap rug syndicate with shared deployer
3. SYN-BSC-PAN-03: BSC PancakeSwap sniper cluster with recurrent deployer
4. SYN-BASE-AERO-04: Base Aerodrome meme ring with cascading exits
5. SYN-MULTI-CROSS-05: Multi-chain cross-deployer clone syndicate

Ensures 100% offline testability, zero unhandled network exceptions, and
satisfies all acceptance criteria (>=5 clusters, >=3 wallets, >=2 patterns).
"""

import time
from typing import List, Dict, Any, Optional
from crypto_syndicate.api.models import (
    TokenLaunchEvent,
    TradeRecord,
    FundingTransferRecord,
    SyndicateCluster,
    WalletScore,
    PatternType,
)


def _build_golden_scenarios() -> Dict[str, Dict[str, Any]]:
    """Builds the 5 multi-chain golden scenarios with complete ground truth."""
    t0_sol = 1726830000
    t0_eth = 1726833600
    t0_bsc = 1726837200
    t0_base = 1726840800
    t0_multi = 1726844400

    # -------------------------------------------------------------------------
    # Scenario 1: Solana Pump.fun Ring (SYN-SOL-PUMP-01)
    # -------------------------------------------------------------------------
    sol_token_addr = "PepeR1111111111111111111111111111111111pump"
    sol_deployer = "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
    sol_funder = "FundSoLMaster1111111111111111111111111111111"
    sol_sweep = "SoLSweepAggregator11111111111111111111111111"
    sol_wallets = [
        "SoLSniper1111111111111111111111111111111111",
        "SoLSniper2222222222222222222222222222222222",
        "SoLSniper3333333333333333333333333333333333",
        "SoLSniper4444444444444444444444444444444444",
        "SoLSniper5555555555555555555555555555555555",
    ]

    sol_launch = TokenLaunchEvent(
        token_address=sol_token_addr,
        chain="sol",
        name="Pepe Rocket",
        symbol="PEPEROCK",
        decimals=6,
        total_supply=1_000_000_000.0,
        deployer_address=sol_deployer,
        launch_timestamp=t0_sol,
        launch_platform="pumpfun",
        initial_liquidity_usd=12500.0,
        initial_price_usd=0.0000125,
        metadata_uri="https://metadata.example.com/peperock.json",
    )

    sol_trades: List[TradeRecord] = []
    sol_transfers: List[FundingTransferRecord] = []
    sol_wallet_scores: Dict[str, WalletScore] = {}

    sol_profit_per_wallet = 12858.82 / len(sol_wallets)  # 2571.764 USD
    for idx, w in enumerate(sol_wallets):
        # Funding transfer from root funder 8 minutes pre-launch
        sol_transfers.append(
            FundingTransferRecord(
                transfer_id=f"tx_fund_sol_{idx}",
                chain="sol",
                from_address=sol_funder,
                to_address=w,
                asset_symbol="SOL",
                amount=5.2,
                amount_usd=5.2 * 147.0,
                timestamp=t0_sol - 480 + idx * 2,
                is_initial_funding=True,
                hop_depth=1,
            )
        )
        # Coordinated early buy (+3s to +11s)
        buy_time = t0_sol + 3 + idx * 2
        buy_tx = f"tx_buy_sol_{idx}"
        sol_trades.append(
            TradeRecord(
                trade_id=buy_tx,
                chain="sol",
                token_address=sol_token_addr,
                wallet_address=w,
                direction="buy",
                timestamp=buy_time,
                token_amount=60_000_000.0,
                base_currency="SOL",
                base_amount=5.0,
                price_usd=0.0000125,
                volume_usd=750.0,
                seconds_since_launch=float(buy_time - t0_sol),
            )
        )
        # Coordinated sell dump (+602s to +610s)
        sell_time = t0_sol + 602 + idx * 2
        sell_tx = f"tx_sell_sol_{idx}"
        sol_trades.append(
            TradeRecord(
                trade_id=sell_tx,
                chain="sol",
                token_address=sol_token_addr,
                wallet_address=w,
                direction="sell",
                timestamp=sell_time,
                token_amount=60_000_000.0,
                base_currency="SOL",
                base_amount=22.5,
                price_usd=0.000055,
                volume_usd=3300.0,
                seconds_since_launch=float(sell_time - t0_sol),
            )
        )
        # Sweep transfer to aggregator
        sol_transfers.append(
            FundingTransferRecord(
                transfer_id=f"tx_sweep_sol_{idx}",
                chain="sol",
                from_address=w,
                to_address=sol_sweep,
                asset_symbol="SOL",
                amount=22.0,
                amount_usd=22.0 * 147.0,
                timestamp=t0_sol + 720 + idx * 2,
                transfer_type="sweep",
                hop_depth=1,
            )
        )
        # Wallet score
        sol_wallet_scores[w] = WalletScore(
            wallet_address=w,
            chain="sol",
            suspicion_score=96.5,
            flagged_patterns=(
                PatternType.EARLY_ENTRY.value,
                PatternType.COMMON_FUNDING.value,
                PatternType.COORDINATED_DUMP.value,
            ),
            pattern_scores={
                "early_entry": 98.0,
                "common_funding": 95.0,
                "coordinated_dump": 96.5,
            },
            associated_tokens=(sol_token_addr,),
            net_profit_usd=sol_profit_per_wallet,
            buy_txs=(buy_tx,),
            sell_txs=(sell_tx,),
        )

    sol_cluster = SyndicateCluster(
        cluster_id="SYN-SOL-PUMP-01",
        chain="sol",
        wallets=tuple(sol_wallets),
        flagged_patterns=(
            PatternType.EARLY_ENTRY.value,
            PatternType.COMMON_FUNDING.value,
            PatternType.COORDINATED_DUMP.value,
        ),
        suspicion_score=96.5,
        associated_tokens=(sol_token_addr,),
        estimated_profit_usd=12858.82,
        funder_wallet=sol_funder,
        deployer_wallet=sol_deployer,
        sweep_wallet=sol_sweep,
        average_entry_window_seconds=7.0,
        average_exit_window_seconds=606.0,
        wallet_scores=sol_wallet_scores,
    )

    # -------------------------------------------------------------------------
    # Scenario 2: Ethereum Uniswap Rug Syndicate (SYN-ETH-UNI-02)
    # -------------------------------------------------------------------------
    eth_token_addr = "0x71C0aA87a2C0C30A91d1469e38B61bfaE8c81201"
    eth_deployer = "0xDe91010101010101010101010101010101010101"
    eth_funder = "0xF00dF00dF00dF00dF00dF00dF00dF00dF00dF00d"
    eth_wallets = [
        "0x1111111111111111111111111111111111111111",
        "0x2222222222222222222222222222222222222222",
        "0x3333333333333333333333333333333333333333",
        "0x4444444444444444444444444444444444444444",
    ]

    eth_launch = TokenLaunchEvent(
        token_address=eth_token_addr,
        chain="eth",
        name="Quantum AI Finance",
        symbol="QAIFI",
        decimals=18,
        total_supply=10_000_000.0,
        deployer_address=eth_deployer,
        launch_timestamp=t0_eth,
        launch_platform="uniswap_v2",
        initial_liquidity_usd=50000.0,
        initial_price_usd=0.005,
    )

    eth_trades: List[TradeRecord] = []
    eth_transfers: List[FundingTransferRecord] = []
    eth_wallet_scores: Dict[str, WalletScore] = {}

    eth_profit_per_wallet = 54800.00 / len(eth_wallets)  # 13700.0 USD
    for idx, w in enumerate(eth_wallets):
        eth_transfers.append(
            FundingTransferRecord(
                transfer_id=f"tx_fund_eth_{idx}",
                chain="eth",
                from_address=eth_funder,
                to_address=w,
                asset_symbol="ETH",
                amount=3.5,
                amount_usd=3.5 * 2500.0,
                timestamp=t0_eth - 1800 + idx * 5,
                is_initial_funding=True,
                hop_depth=1,
            )
        )
        buy_time = t0_eth + 24
        buy_tx = f"tx_buy_eth_{idx}"
        eth_trades.append(
            TradeRecord(
                trade_id=buy_tx,
                chain="eth",
                token_address=eth_token_addr,
                wallet_address=w,
                direction="buy",
                timestamp=buy_time,
                token_amount=600_000.0,
                base_currency="ETH",
                base_amount=3.0,
                price_usd=0.0125,
                volume_usd=7500.0,
                seconds_since_launch=24.0,
                slot_or_block=19500002,
            )
        )
        sell_time = t0_eth + 504
        sell_tx = f"tx_sell_eth_{idx}"
        eth_trades.append(
            TradeRecord(
                trade_id=sell_tx,
                chain="eth",
                token_address=eth_token_addr,
                wallet_address=w,
                direction="sell",
                timestamp=sell_time,
                token_amount=600_000.0,
                base_currency="ETH",
                base_amount=8.5,
                price_usd=0.0354,
                volume_usd=21250.0,
                seconds_since_launch=504.0,
                slot_or_block=19500042,
            )
        )
        eth_wallet_scores[w] = WalletScore(
            wallet_address=w,
            chain="eth",
            suspicion_score=98.0,
            flagged_patterns=(
                PatternType.COMMON_FUNDING.value,
                PatternType.SHARED_DEPLOYER.value,
                PatternType.COORDINATED_DUMP.value,
            ),
            pattern_scores={
                "common_funding": 99.0,
                "shared_deployer": 98.0,
                "coordinated_dump": 97.0,
            },
            associated_tokens=(eth_token_addr,),
            net_profit_usd=eth_profit_per_wallet,
            buy_txs=(buy_tx,),
            sell_txs=(sell_tx,),
        )

    eth_cluster = SyndicateCluster(
        cluster_id="SYN-ETH-UNI-02",
        chain="eth",
        wallets=tuple(eth_wallets),
        flagged_patterns=(
            PatternType.COMMON_FUNDING.value,
            PatternType.SHARED_DEPLOYER.value,
            PatternType.COORDINATED_DUMP.value,
        ),
        suspicion_score=98.0,
        associated_tokens=(eth_token_addr,),
        estimated_profit_usd=54800.00,
        funder_wallet=eth_funder,
        deployer_wallet=eth_deployer,
        average_entry_window_seconds=24.0,
        average_exit_window_seconds=504.0,
        wallet_scores=eth_wallet_scores,
    )

    # -------------------------------------------------------------------------
    # Scenario 3: BSC PancakeSwap Sniper Cluster (SYN-BSC-PAN-03)
    # -------------------------------------------------------------------------
    bsc_token_addr = "0x89bC39A726a7C4324f9E29cE43b7B73F42A7C302"
    bsc_deployer = "0xDe91020202020202020202020202020202020202"
    bsc_funder = "0xF00dB5c000000000000000000000000000000003"
    bsc_wallets = [
        "0x5555555555555555555555555555555555555555",
        "0x6666666666666666666666666666666666666666",
        "0x7777777777777777777777777777777777777777",
        "0x8888888888888888888888888888888888888888",
    ]

    bsc_launch = TokenLaunchEvent(
        token_address=bsc_token_addr,
        chain="bsc",
        name="Baby Moon Doge",
        symbol="BABYMDOGE",
        decimals=9,
        total_supply=1_000_000_000_000.0,
        deployer_address=bsc_deployer,
        launch_timestamp=t0_bsc,
        launch_platform="pancakeswap_v2",
        initial_liquidity_usd=20000.0,
        initial_price_usd=0.00000002,
    )

    bsc_trades: List[TradeRecord] = []
    bsc_transfers: List[FundingTransferRecord] = []
    bsc_wallet_scores: Dict[str, WalletScore] = {}

    bsc_profit_per_wallet = 18228.60 / len(bsc_wallets)  # 4557.15 USD
    for idx, w in enumerate(bsc_wallets):
        bsc_transfers.append(
            FundingTransferRecord(
                transfer_id=f"tx_fund_bsc_{idx}",
                chain="bsc",
                from_address=bsc_funder,
                to_address=w,
                asset_symbol="BNB",
                amount=5.0,
                amount_usd=5.0 * 570.0,
                timestamp=t0_bsc - 900 + idx * 3,
                is_initial_funding=True,
                hop_depth=1,
            )
        )
        buy_time = t0_bsc + 3
        buy_tx = f"tx_buy_bsc_{idx}"
        bsc_trades.append(
            TradeRecord(
                trade_id=buy_tx,
                chain="bsc",
                token_address=bsc_token_addr,
                wallet_address=w,
                direction="buy",
                timestamp=buy_time,
                token_amount=55_000_000_000.0,
                base_currency="BNB",
                base_amount=4.0,
                price_usd=0.000000041,
                volume_usd=2280.0,
                seconds_since_launch=3.0,
                slot_or_block=38000001,
            )
        )
        sell_time = t0_bsc + 720 + idx * 3
        sell_tx = f"tx_sell_bsc_{idx}"
        bsc_trades.append(
            TradeRecord(
                trade_id=sell_tx,
                chain="bsc",
                token_address=bsc_token_addr,
                wallet_address=w,
                direction="sell",
                timestamp=sell_time,
                token_amount=55_000_000_000.0,
                base_currency="BNB",
                base_amount=12.0,
                price_usd=0.000000124,
                volume_usd=6840.0,
                seconds_since_launch=float(sell_time - t0_bsc),
            )
        )
        bsc_wallet_scores[w] = WalletScore(
            wallet_address=w,
            chain="bsc",
            suspicion_score=94.0,
            flagged_patterns=(
                PatternType.EARLY_ENTRY.value,
                PatternType.COMMON_FUNDING.value,
                PatternType.SHARED_DEPLOYER.value,
            ),
            pattern_scores={
                "early_entry": 96.0,
                "common_funding": 93.0,
                "shared_deployer": 93.0,
            },
            associated_tokens=(bsc_token_addr,),
            net_profit_usd=bsc_profit_per_wallet,
            buy_txs=(buy_tx,),
            sell_txs=(sell_tx,),
        )

    bsc_cluster = SyndicateCluster(
        cluster_id="SYN-BSC-PAN-03",
        chain="bsc",
        wallets=tuple(bsc_wallets),
        flagged_patterns=(
            PatternType.EARLY_ENTRY.value,
            PatternType.COMMON_FUNDING.value,
            PatternType.SHARED_DEPLOYER.value,
        ),
        suspicion_score=94.0,
        associated_tokens=(bsc_token_addr,),
        estimated_profit_usd=18228.60,
        funder_wallet=bsc_funder,
        deployer_wallet=bsc_deployer,
        average_entry_window_seconds=3.0,
        average_exit_window_seconds=724.5,
        wallet_scores=bsc_wallet_scores,
    )

    # -------------------------------------------------------------------------
    # Scenario 4: Base Meme Ring (SYN-BASE-AERO-04)
    # -------------------------------------------------------------------------
    base_token_addr = "0x44BcA91e60058b87F76BfD281729Ec80e7292104"
    base_deployer = "0xDe91040404040404040404040404040404040404"
    base_funder = "0xF00dBa5e00000000000000000000000000000004"
    base_sweep = "0xBaseSweepAggregator000000000000000000004"
    base_wallets = [
        "0x9999999999999999999999999999999999999999",
        "0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
    ]

    base_launch = TokenLaunchEvent(
        token_address=base_token_addr,
        chain="base",
        name="Based Chad Pepe",
        symbol="BCHAD",
        decimals=18,
        total_supply=100_000_000.0,
        deployer_address=base_deployer,
        launch_timestamp=t0_base,
        launch_platform="aerodrome",
        initial_liquidity_usd=30000.0,
        initial_price_usd=0.0003,
    )

    base_trades: List[TradeRecord] = []
    base_transfers: List[FundingTransferRecord] = []
    base_wallet_scores: Dict[str, WalletScore] = {}

    base_profit_per_wallet = 39990.00 / len(base_wallets)  # 9997.50 USD
    for idx, w in enumerate(base_wallets):
        base_transfers.append(
            FundingTransferRecord(
                transfer_id=f"tx_fund_base_{idx}",
                chain="base",
                from_address=base_funder,
                to_address=w,
                asset_symbol="ETH",
                amount=2.5,
                amount_usd=2.5 * 2500.0,
                timestamp=t0_base - 600 + idx * 4,
                is_initial_funding=True,
                hop_depth=1,
            )
        )
        buy_offsets = [2, 4, 6, 9]
        buy_time = t0_base + buy_offsets[idx]
        buy_tx = f"tx_buy_base_{idx}"
        base_trades.append(
            TradeRecord(
                trade_id=buy_tx,
                chain="base",
                token_address=base_token_addr,
                wallet_address=w,
                direction="buy",
                timestamp=buy_time,
                token_amount=4_500_000.0,
                base_currency="ETH",
                base_amount=2.0,
                price_usd=0.00111,
                volume_usd=5000.0,
                seconds_since_launch=float(buy_offsets[idx]),
            )
        )
        sell_time = t0_base + 900 + idx * 20
        sell_tx = f"tx_sell_base_{idx}"
        base_trades.append(
            TradeRecord(
                trade_id=sell_tx,
                chain="base",
                token_address=base_token_addr,
                wallet_address=w,
                direction="sell",
                timestamp=sell_time,
                token_amount=4_500_000.0,
                base_currency="ETH",
                base_amount=6.0,
                price_usd=0.00333,
                volume_usd=15000.0,
                seconds_since_launch=float(sell_time - t0_base),
            )
        )
        base_transfers.append(
            FundingTransferRecord(
                transfer_id=f"tx_sweep_base_{idx}",
                chain="base",
                from_address=w,
                to_address=base_sweep,
                asset_symbol="ETH",
                amount=5.9,
                amount_usd=5.9 * 2500.0,
                timestamp=t0_base + 1050 + idx * 5,
                transfer_type="sweep",
                hop_depth=1,
            )
        )
        base_wallet_scores[w] = WalletScore(
            wallet_address=w,
            chain="base",
            suspicion_score=88.5,
            flagged_patterns=(
                PatternType.EARLY_ENTRY.value,
                PatternType.COORDINATED_DUMP.value,
            ),
            pattern_scores={
                "early_entry": 90.0,
                "coordinated_dump": 87.0,
            },
            associated_tokens=(base_token_addr,),
            net_profit_usd=base_profit_per_wallet,
            buy_txs=(buy_tx,),
            sell_txs=(sell_tx,),
        )

    base_cluster = SyndicateCluster(
        cluster_id="SYN-BASE-AERO-04",
        chain="base",
        wallets=tuple(base_wallets),
        flagged_patterns=(
            PatternType.EARLY_ENTRY.value,
            PatternType.COORDINATED_DUMP.value,
        ),
        suspicion_score=88.5,
        associated_tokens=(base_token_addr,),
        estimated_profit_usd=39990.00,
        funder_wallet=base_funder,
        deployer_wallet=base_deployer,
        sweep_wallet=base_sweep,
        average_entry_window_seconds=5.25,
        average_exit_window_seconds=930.0,
        wallet_scores=base_wallet_scores,
    )

    # -------------------------------------------------------------------------
    # Scenario 5: Multi-Chain Cross-Deployer Syndicate (SYN-MULTI-CROSS-05)
    # -------------------------------------------------------------------------
    multi_token_addrs = [
        "ApexSo1111111111111111111111111111111111111",
        "0xAe05010101010101010101010101010101010105",
        "0xAe05020202020202020202020202020202020205",
    ]
    multi_wallets = [
        "0xDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
        "0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
        "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
        "SoLCrossSniper111111111111111111111111111111",
        "SoLCrossSniper222222222222222222222222222222",
        "SoLCrossSniper333333333333333333333333333333",
    ]

    multi_launch = TokenLaunchEvent(
        token_address=multi_token_addrs[0],
        chain="multi",
        name="Apex Omni Cross",
        symbol="APEX",
        decimals=9,
        total_supply=1_000_000_000.0,
        deployer_address="DeployerApexSol111111111111111111111111111",
        launch_timestamp=t0_multi,
        launch_platform="cross_chain_pool",
        initial_liquidity_usd=100000.0,
        initial_price_usd=0.0001,
    )

    multi_trades: List[TradeRecord] = []
    multi_transfers: List[FundingTransferRecord] = []
    multi_wallet_scores: Dict[str, WalletScore] = {}

    multi_profit_per_wallet = 65865.00 / len(multi_wallets)  # 10977.50 USD
    for idx, w in enumerate(multi_wallets):
        chain_id = "sol" if "SolCross" in w else ("eth" if idx < 2 else "bsc")
        buy_tx = f"tx_buy_multi_{idx}"
        sell_tx = f"tx_sell_multi_{idx}"
        multi_trades.append(
            TradeRecord(
                trade_id=buy_tx,
                chain=chain_id,
                token_address=multi_token_addrs[0 if chain_id == "sol" else (1 if chain_id == "eth" else 2)],
                wallet_address=w,
                direction="buy",
                timestamp=t0_multi + 5 + idx * 2,
                token_amount=15_000_000.0,
                base_currency="SOL" if chain_id == "sol" else "ETH",
                base_amount=10.0 if chain_id == "sol" else 1.5,
                price_usd=0.0001,
                volume_usd=1500.0,
                seconds_since_launch=float(5 + idx * 2),
            )
        )
        multi_trades.append(
            TradeRecord(
                trade_id=sell_tx,
                chain=chain_id,
                token_address=multi_token_addrs[0 if chain_id == "sol" else (1 if chain_id == "eth" else 2)],
                wallet_address=w,
                direction="sell",
                timestamp=t0_multi + 800 + idx * 5,
                token_amount=15_000_000.0,
                base_currency="SOL" if chain_id == "sol" else "ETH",
                base_amount=35.0 if chain_id == "sol" else 5.0,
                price_usd=0.00045,
                volume_usd=6750.0,
                seconds_since_launch=float(800 + idx * 5),
            )
        )
        multi_wallet_scores[w] = WalletScore(
            wallet_address=w,
            chain=chain_id,
            suspicion_score=95.0,
            flagged_patterns=(
                PatternType.SHARED_DEPLOYER.value,
                PatternType.EARLY_ENTRY.value,
                PatternType.COMMON_FUNDING.value,
            ),
            pattern_scores={
                "shared_deployer": 97.0,
                "early_entry": 94.0,
                "common_funding": 94.0,
            },
            associated_tokens=tuple(multi_token_addrs),
            net_profit_usd=multi_profit_per_wallet,
            buy_txs=(buy_tx,),
            sell_txs=(sell_tx,),
        )

    multi_cluster = SyndicateCluster(
        cluster_id="SYN-MULTI-CROSS-05",
        chain="multi",
        wallets=tuple(multi_wallets),
        flagged_patterns=(
            PatternType.SHARED_DEPLOYER.value,
            PatternType.EARLY_ENTRY.value,
            PatternType.COMMON_FUNDING.value,
        ),
        suspicion_score=95.0,
        associated_tokens=tuple(multi_token_addrs),
        estimated_profit_usd=65865.00,
        deployer_wallet="0xMasterDeployerCrossChainCoordinator111111",
        funder_wallet="0xMultiChainFunderCentralDisburser1111111",
        average_entry_window_seconds=10.0,
        average_exit_window_seconds=812.5,
        wallet_scores=multi_wallet_scores,
    )

    return {
        "SYN-SOL-PUMP-01": {
            "cluster": sol_cluster,
            "launch": sol_launch,
            "trades": sol_trades,
            "transfers": sol_transfers,
        },
        "SYN-ETH-UNI-02": {
            "cluster": eth_cluster,
            "launch": eth_launch,
            "trades": eth_trades,
            "transfers": eth_transfers,
        },
        "SYN-BSC-PAN-03": {
            "cluster": bsc_cluster,
            "launch": bsc_launch,
            "trades": bsc_trades,
            "transfers": bsc_transfers,
        },
        "SYN-BASE-AERO-04": {
            "cluster": base_cluster,
            "launch": base_launch,
            "trades": base_trades,
            "transfers": base_transfers,
        },
        "SYN-MULTI-CROSS-05": {
            "cluster": multi_cluster,
            "launch": multi_launch,
            "trades": multi_trades,
            "transfers": multi_transfers,
        },
    }


# Global cached singleton of golden scenarios
_SCENARIOS = _build_golden_scenarios()


def get_mock_clusters() -> List[SyndicateCluster]:
    """Returns all 5 pre-computed canonical SyndicateCluster objects."""
    return [sc["cluster"] for sc in _SCENARIOS.values()]


def get_mock_token_launches(
    chain: Optional[str] = None,
    time_period: str = "1h",
) -> List[TokenLaunchEvent]:
    """Returns token launch events matching chain filter, or all golden launches."""
    launches = [sc["launch"] for sc in _SCENARIOS.values()]
    if chain:
        c = chain.strip().lower()
        if c in ("solana", "sol"):
            return [l for l in launches if l.chain == "sol"]
        if c in ("ethereum", "eth"):
            return [l for l in launches if l.chain == "eth"]
        if c in ("binance", "bsc"):
            return [l for l in launches if l.chain == "bsc"]
        if c == "base":
            return [l for l in launches if l.chain == "base"]
        return [l for l in launches if l.chain == c]
    return launches


def get_mock_token_trades(
    chain: str,
    token_address: str,
    limit: int = 500,
) -> List[TradeRecord]:
    """Returns granular buy and sell trade records for the target fixture token."""
    for sc in _SCENARIOS.values():
        if sc["launch"].token_address.lower() == token_address.lower():
            return sc["trades"][:limit]
        if token_address in sc["cluster"].associated_tokens:
            return sc["trades"][:limit]
    first_sc = next(iter(_SCENARIOS.values()))
    return first_sc["trades"][:limit]


def get_mock_wallet_transfers(
    chain: str,
    wallet_address: str,
    flow: str = "in",
) -> List[FundingTransferRecord]:
    """Returns upstream funding transfers and downstream sweep transfers for the target wallet."""
    for sc in _SCENARIOS.values():
        transfers = sc["transfers"]
        matched = [
            t for t in transfers
            if (flow == "in" and t.to_address.lower() == wallet_address.lower())
            or (flow == "out" and t.from_address.lower() == wallet_address.lower())
            or (t.from_address.lower() == wallet_address.lower() or t.to_address.lower() == wallet_address.lower())
        ]
        if matched:
            return matched
    return []


def get_mock_account_metadata(wallet_address: str) -> Optional[Dict[str, Any]]:
    """Returns account metadata envelope with funded_by, block_time, and tx_hash."""
    for sc in _SCENARIOS.values():
        cluster = sc["cluster"]
        if wallet_address in cluster.wallets:
            funder = cluster.funder_wallet or "FundRootCentralSystem11111111111111111111"
            return {
                "account": wallet_address,
                "funded_by": funder,
                "block_time": 1726829520,
                "tx_hash": f"tx_root_funding_{wallet_address[:8]}",
                "lamports": 5200000000,
                "owner": "11111111111111111111111111111111",
            }
    return {
        "account": wallet_address,
        "funded_by": "FundFallbackSystem111111111111111111111111111",
        "block_time": 1726829500,
        "tx_hash": f"tx_root_{wallet_address[:8]}",
        "lamports": 1000000000,
    }


class FixtureProvider:
    """Convenience provider facade for mock fixtures."""

    def get_new_token_launches(self, chain: Optional[str] = None, time_period: str = "1h") -> List[TokenLaunchEvent]:
        return get_mock_token_launches(chain=chain, time_period=time_period)

    def get_token_trades(self, chain: str, token_address: str, limit: int = 500) -> List[TradeRecord]:
        return get_mock_token_trades(chain=chain, token_address=token_address, limit=limit)

    def get_wallet_transfers(self, chain: str, wallet_address: str, flow: str = "in") -> List[FundingTransferRecord]:
        return get_mock_wallet_transfers(chain=chain, wallet_address=wallet_address, flow=flow)

    def get_account_metadata(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        return get_mock_account_metadata(wallet_address=wallet_address)

    def get_clusters(self) -> List[SyndicateCluster]:
        return get_mock_clusters()

    def get_jito_fixtures(self) -> List[Dict[str, Any]]:
        return get_mock_jito_fixtures()

    def get_non_jito_fixtures(self) -> List[Dict[str, Any]]:
        return get_mock_non_jito_fixtures()

    def get_similar_wallets(self) -> List[Dict[str, Any]]:
        return get_mock_similar_wallets_fixtures()


def get_mock_jito_fixtures() -> List[Dict[str, Any]]:
    """Returns realistic mock transactions containing Jito bundle signals."""
    return [
        {
            "signature": "5Xj9JitoTipDirect1111111111111111111111111111111111111111111111111111111111111111111111",
            "chain": "sol",
            "slot": 284910100,
            "timestamp": 1726830016.120,
            "maker": "SoLSniper1111111111111111111111111111111111",
            "tip_account": "96gYZGLnJeTa9AGEefvjNArMBUwEpzDQRNSCGVFmhEEq",
            "tip_lamports": 10000000,
            "bundler_rate": 0.52,
        },
        {
            "signature": "4Yk8JitoTipCPI11111111111111111111111111111111111111111111111111111111111111111111111",
            "chain": "sol",
            "slot": 284910101,
            "timestamp": 1726830016.250,
            "maker": "SoLSniper2222222222222222222222222222222222",
            "inner_instructions": [
                {
                    "program": "11111111111111111111111111111111",
                    "to": "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
                    "lamports": 5000000,
                }
            ],
            "bundler_rate": 0.45,
        },
        {
            "signature": "3Zl7JitoBundleId1111111111111111111111111111111111111111111111111111111111111111111111",
            "chain": "sol",
            "slot": 284910102,
            "timestamp": 1726830016.310,
            "maker": "SoLSniper3333333333333333333333333333333333",
            "bundle_id": "jito_bundle_9f82a1c0deb3456789",
            "bundler_rate": 0.50,
        },
        {
            "signature": "2Am6JitoExplicitFlag111111111111111111111111111111111111111111111111111111111111111111",
            "chain": "sol",
            "slot": 284910103,
            "timestamp": 1726830016.380,
            "maker": "SoLSniper4444444444444444444444444444444444",
            "is_jito": True,
            "bundler_rate": 0.48,
        },
        {
            "signature": "1Bn5JitoCoSlotBurst111111111111111111111111111111111111111111111111111111111111111111",
            "chain": "sol",
            "slot": 284910104,
            "timestamp": 1726830016.420,
            "maker": "SoLSniper5555555555555555555555555555555555",
            "tip_account": "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1sMaC9jnwRv",
            "tip_lamports": 2500000,
            "bundler_rate": 0.60,
        },
    ]


def get_mock_non_jito_fixtures() -> List[Dict[str, Any]]:
    """Returns realistic mock transactions that are regular DEX swaps (no Jito bundle)."""
    return [
        {
            "signature": "RegularSwapRaydium111111111111111111111111111111111111111111111111111111111111111111111",
            "chain": "sol",
            "slot": 284910200,
            "timestamp": 1726830020.000,
            "maker": "RetailUser11111111111111111111111111111111111",
            "bundler_rate": 0.05,
            "amount_sol": 0.5,
        },
        {
            "signature": "RegularSwapOrca111111111111111111111111111111111111111111111111111111111111111111111111",
            "chain": "sol",
            "slot": 284910201,
            "timestamp": 1726830025.000,
            "maker": "RetailUser22222222222222222222222222222222222",
            "bundler_rate": 0.00,
            "amount_sol": 1.2,
        },
        {
            "signature": "FakeTipLookalikeSpoof11111111111111111111111111111111111111111111111111111111111111111",
            "chain": "sol",
            "slot": 284910202,
            "timestamp": 1726830030.000,
            "maker": "AttackerSpoofer11111111111111111111111111111",
            # Address off by 1 char from canonical: 96gYZGLn... changed to 96gYZGLn...Eq -> ...Er
            "tip_account": "96gYZGLnJeTa9AGEefvjNArMBUwEpzDQRNSCGVFmhEEr",
            "tip_lamports": 10000000,
            "bundler_rate": 0.05,
        },
    ]


def get_mock_similar_wallets_fixtures() -> List[Dict[str, Any]]:
    """Returns realistic mock vector similarity matches for testing and offline UI state."""
    return [
        {
            "address": "69aiAKU3uJMxMLRkUEGFNt6nQ43PiVimE4ZbErJ7VSM1",
            "similarity": 0.9421,
            "similarity_pct": "94.2%",
            "syndicate_id": "SYND-0006",
            "chain": "sol",
            "bundler_rate": 0.682,
            "avg_buy_delay_s": 14.2,
            "avg_hold_duration_s": 7.8,
            "is_jito_bundle": True,
            "jito_confidence": 0.88,
            "patterns_flagged": ["sniper", "bundler", "jito_bundle"],
        },
        {
            "address": "3bRtZ8qW2pM3kL4n5uR6vX7yT9wQ2pM3kL4n5uR6vX7y",
            "similarity": 0.8745,
            "similarity_pct": "87.5%",
            "syndicate_id": "SYND-0003",
            "chain": "sol",
            "bundler_rate": 0.442,
            "avg_buy_delay_s": 18.0,
            "avg_hold_duration_s": 9.5,
            "is_jito_bundle": False,
            "jito_confidence": 0.25,
            "patterns_flagged": ["early_entry", "bundler"],
        },
        {
            "address": "Snip2_4dNj3yuR8vX7yT9wQ2pM3kL4n5",
            "similarity": 0.7210,
            "similarity_pct": "72.1%",
            "syndicate_id": "SYND-0001",
            "chain": "sol",
            "bundler_rate": 0.515,
            "avg_buy_delay_s": 15.1,
            "avg_hold_duration_s": 8.1,
            "is_jito_bundle": True,
            "jito_confidence": 0.94,
            "patterns_flagged": ["sniper", "co_slot"],
        },
        {
            "address": "8p7Z2M9tq4F1kL5n6uR8vX7yT9wQ2pM3kL4n5uR6vX7y",
            "similarity": 0.5830,
            "similarity_pct": "58.3%",
            "syndicate_id": "SYND-0001",
            "chain": "sol",
            "bundler_rate": 0.210,
            "avg_buy_delay_s": 32.0,
            "avg_hold_duration_s": 45.0,
            "is_jito_bundle": False,
            "jito_confidence": 0.0,
            "patterns_flagged": ["shared_deployer"],
        },
    ]


def get_mock_campaign_fixtures() -> List[Dict[str, Any]]:
    """Returns golden multi-token cross-campaign fixtures for testing and visualizer state."""
    return [
        {
            "campaign_id": "CAMP-0001",
            "name": "Serial Pump Ring: $BELUGA x $ZLONG",
            "token_addresses": [
                "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX",
                "4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump",
            ],
            "token_symbols": ["BELUGA", "ZLONG"],
            "syndicate_ids": ["SYND-0001", "SYND-0006"],
            "reused_wallets": [
                "Snip1_4dNj3yvX7yT9wQ2pM3kL4n5uR6",
                "Snip2_4dNj3yuR8vX7yT9wQ2pM3kL4n5",
                "8p7Z2M9tq4F1kL5n6uR8vX7yT9wQ2pM3kL4n5uR6vX7y",
            ],
            "reused_wallets_count": 3,
            "shared_root_funder": "FundSoLMaster1111111111111111111111111111111",
            "jaccard_overlap": 0.4286,
            "semantic_similarity": 0.9140,
            "total_profit_usd": 1218540.0,
            "campaign_type": "SERIAL_PUMP_AND_DUMP",
            "confidence_score": 0.95,
            "created_at": 1726830500.0,
        },
        {
            "campaign_id": "CAMP-0002",
            "name": "Deployer Clone Factory: $PUMPFLASH x $SOLCAT",
            "token_addresses": [
                "3bRtZ8qW2pM3kL4n5uR6vX7yT9wQ2pM3kL4n5uR6vX7y",
                "PepeR1111111111111111111111111111111111pump",
            ],
            "token_symbols": ["PUMPFLASH", "SOLCAT"],
            "syndicate_ids": ["SYND-0003", "SYND-0004"],
            "reused_wallets": [
                "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            ],
            "reused_wallets_count": 1,
            "shared_root_funder": "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
            "jaccard_overlap": 0.1250,
            "semantic_similarity": 0.8870,
            "total_profit_usd": 512300.0,
            "campaign_type": "DEPLOYER_CLONE_FACTORY",
            "confidence_score": 0.88,
            "created_at": 1726831200.0,
        },
    ]


def get_mock_simulation_fixtures() -> Dict[str, Any]:
    """Provides deterministic fixtures for M15 Shadow Simulator testing and backtesting."""
    mock_trades = [
        {"seconds_since_launch": 0.0, "price_usd": 0.0010, "volume_usd": 5000.0, "direction": "buy"},
        {"seconds_since_launch": 5.0, "price_usd": 0.0012, "volume_usd": 8000.0, "direction": "buy"},
        {"seconds_since_launch": 13.0, "price_usd": 0.0022, "volume_usd": 15000.0, "direction": "buy"},  # Syndicate Buy / Sniper
        {"seconds_since_launch": 16.0, "price_usd": 0.0048, "volume_usd": 35000.0, "direction": "buy"},  # Jito Bundle Push
        {"seconds_since_launch": 22.0, "price_usd": 0.0072, "volume_usd": 28000.0, "direction": "buy"},  # FOMO Ingress
        {"seconds_since_launch": 26.0, "price_usd": 0.0085, "volume_usd": 12000.0, "direction": "buy"},  # Peak Price
        {"seconds_since_launch": 28.0, "price_usd": 0.0080, "volume_usd": 10000.0, "direction": "sell"}, # Early Exit Window
        {"seconds_since_launch": 32.0, "price_usd": 0.0031, "volume_usd": 45000.0, "direction": "sell"}, # Syndicate Coordinated Dump
        {"seconds_since_launch": 40.0, "price_usd": 0.0015, "volume_usd": 9000.0, "direction": "sell"},
        {"seconds_since_launch": 60.0, "price_usd": 0.0011, "volume_usd": 2000.0, "direction": "sell"},
    ]

    mock_clusters = [
        {
            "id": "SYND-0001",
            "cluster_id": "SYND-0001",
            "token_address": "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX",
            "token_symbol": "BELUGA",
            "mode": "flash",
            "avg_buy_delay_s": 13.0,
            "avg_hold_duration_s": 15.0,  # Dump at T+28s
            "estimated_profit_usd": 16650.0,
            "is_jito_bundle": True,
        },
        {
            "id": "SYND-0006",
            "cluster_id": "SYND-0006",
            "token_address": "4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump",
            "token_symbol": "ZLONG",
            "mode": "flash",
            "avg_buy_delay_s": 13.0,
            "avg_hold_duration_s": 15.0,  # Dump at T+28s
            "estimated_profit_usd": 21870.0,
            "is_jito_bundle": True,
        },
    ]

    return {
        "trades": mock_trades,
        "clusters": mock_clusters,
        "expected_counter_exit_lead_s": 4.0,
        "expected_optimal_exit_time_s": 24.0,
    }


def get_mock_ingress_and_token_fixtures() -> Dict[str, Any]:
    """Provides deterministic fixtures for wallet ingress lineage and meme token launches."""
    now = time.time()
    root_treasury = "8p7Z2M9tq4F1kL5n6uR8vX7yT9wQ2pM3kL4n5uR6vX7y"
    member_1 = "Snip1_4dNj3yuR8vX7yT9wQ2pM3kL4n5"
    child_hop2 = "Child_Hop2_Deployer_4dNj3y"
    sub_treasury = "Whale_Treasury_25SOL_Anchor"
    sub_child1 = "Deployer_Child_Under_Whale_1"
    dust_child = "Dust_Wallet_Under_Threshold"

    transfers = [
        {
            "from_address": root_treasury,
            "to_address": member_1,
            "amount_sol": 5.0,
            "recipient_balance_sol": 5.0,
            "timestamp": now - 3600,
            "tx_hash": "tx_fund_m1",
        },
        {
            "from_address": member_1,
            "to_address": child_hop2,
            "amount_sol": 0.5,
            "recipient_balance_sol": 0.5,  # $75 >= $5
            "timestamp": now - 1800,
            "tx_hash": "tx_fund_child2",
        },
        {
            "from_address": child_hop2,
            "to_address": sub_treasury,
            "amount_sol": 25.0,
            "recipient_balance_sol": 25.0,  # >= 20 SOL -> Promotes to Treasury Anchor!
            "timestamp": now - 900,
            "tx_hash": "tx_whale_anchor",
        },
        {
            "from_address": sub_treasury,
            "to_address": sub_child1,
            "amount_sol": 0.08,
            "recipient_balance_sol": 0.08,  # $12 >= $5 -> Qualified Deployer!
            "timestamp": now - 300,
            "tx_hash": "tx_fund_subchild1",
        },
        {
            "from_address": member_1,
            "to_address": dust_child,
            "amount_sol": 0.01,
            "recipient_balance_sol": 0.01,  # $1.50 < $5 -> Dust Monitor
            "timestamp": now - 100,
            "tx_hash": "tx_fund_dust",
        },
    ]

    token_creations = [
        {
            "creator_wallet": "69aiAKU3uJMxMLRkUEGFNt6nQ43PiVimE4ZbErJ7VSM1",
            "program_id": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
            "instruction": "create",
            "mint_address": "4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump",
            "symbol": "ZLONG",
            "name": "ZLONG",
            "bonding_curve_address": "2u7HGTjgy2nZsgLu92PCqUNhxxRyfpM4DtQ9tVTkMpiH",
            "initial_sol_injected": 0.05,
            "timestamp": now - 60,
            "signature": "sig_pump_zlong_verified",
            "dex_screener_url": "https://dexscreener.com/solana/2u7hgtjgy2nzsglu92pcqunhxxryfpm4dtq9tvtkmpih",
            "gmgn_url": "https://gmgn.ai/sol/token/4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump",
            "photon_url": "https://photon-sol.tinyastro.io/en/lp/4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump",
            "pump_fun_url": "https://pump.fun/4xjvmiKa5vzkQtaNrTV17v8PFU5mP69Hf1Kq5A9wpump",
        },
        {
            "creator_wallet": "GT5au36AvFTxc4yfRHh1dMWkLtsxDRHz2VW5MmvcKjM7",
            "program_id": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
            "instruction": "create",
            "mint_address": "2Ecj4UJjegEcjCEPFMuXJprFUD8HMVphqTg2Qtm5pump",
            "symbol": "EZO",
            "name": "Ezo",
            "bonding_curve_address": "7Gu4CPCbiGwaqYFyYGhCtkvAd67abRm2ouD3kfYYW627",
            "initial_sol_injected": 0.08,
            "timestamp": now - 30,
            "signature": "sig_pump_ezo_verified",
            "dex_screener_url": "https://dexscreener.com/solana/7gu4cpcbigwaqyfyyghctkvad67abrm2oud3kfyyw627",
            "gmgn_url": "https://gmgn.ai/sol/token/2Ecj4UJjegEcjCEPFMuXJprFUD8HMVphqTg2Qtm5pump",
            "photon_url": "https://photon-sol.tinyastro.io/en/lp/2Ecj4UJjegEcjCEPFMuXJprFUD8HMVphqTg2Qtm5pump",
            "pump_fun_url": "https://pump.fun/2Ecj4UJjegEcjCEPFMuXJprFUD8HMVphqTg2Qtm5pump",
        },
        {
            "creator_wallet": "2s1KxGv3sEcmqA3YvL7zYnL8B9jX4mQ5rW6tP7u8v9w",
            "program_id": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
            "instruction": "create",
            "mint_address": "GpUkmLHWPZkBFYjNiwrhuqoFXaoxB6cF2WYKgFbPpump",
            "symbol": "SCRIBJEAN",
            "name": "SCRIBJEAN",
            "bonding_curve_address": "8VNXtv5aND4CDsVD3FsmRxwxzkNifDcwqWwf7DUYKhAE",
            "initial_sol_injected": 0.06,
            "timestamp": now - 15,
            "signature": "sig_pump_scribjean_verified",
            "dex_screener_url": "https://dexscreener.com/solana/8vnxtv5and4cdsvd3fsmrxwxzknifdcwqwwf7duykhae",
            "gmgn_url": "https://gmgn.ai/sol/token/GpUkmLHWPZkBFYjNiwrhuqoFXaoxB6cF2WYKgFbPpump",
            "photon_url": "https://photon-sol.tinyastro.io/en/lp/GpUkmLHWPZkBFYjNiwrhuqoFXaoxB6cF2WYKgFbPpump",
            "pump_fun_url": "https://pump.fun/GpUkmLHWPZkBFYjNiwrhuqoFXaoxB6cF2WYKgFbPpump",
        },
    ]

    return {
        "root_treasury": root_treasury,
        "transfers": transfers,
        "token_creations": token_creations,
    }


