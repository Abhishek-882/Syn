"""Unit and adversarial test suite for M15 — Syndicate Shadow Simulator & Backtesting Engine."""

import unittest
from typing import Any, Dict, List

from crypto_syndicate.api.models import TradeRecord
from crypto_syndicate.api.fixtures import get_mock_simulation_fixtures
from crypto_syndicate.scanner import LiveSyndicateScanner
from crypto_syndicate.simulator import (
    BacktestResult,
    ShadowSimulatorEngine,
    SimulationConfig,
    SimulationTrade,
)


class TestShadowSimulatorEngine(unittest.TestCase):
    """Test suite verifying simulation execution, strategy logic, fee deductions, and backtesting."""

    def setUp(self):
        self.fixtures = get_mock_simulation_fixtures()
        self.trades = self.fixtures["trades"]
        self.clusters = self.fixtures["clusters"]
        self.engine = ShadowSimulatorEngine()

    def test_simulation_config_defaults(self):
        """Verify default configuration parameters."""
        cfg = SimulationConfig()
        self.assertEqual(cfg.initial_capital_usd, 1000.0)
        self.assertEqual(cfg.execution_latency_s, 1.0)
        self.assertEqual(cfg.slippage_bps, 150)
        self.assertEqual(cfg.dex_fee_bps, 30)
        self.assertEqual(cfg.strategy, "COUNTER_FRONT_RUN")
        self.assertEqual(cfg.front_run_lead_s, 4.0)

    def test_simulation_trade_dataclass(self):
        """Verify SimulationTrade dataclass serialization."""
        st = SimulationTrade(
            trade_id="SIM-TEST-1",
            token_address="Addr1",
            syndicate_id="SYND-0001",
            entry_time_s=14.0,
            entry_price_usd=0.0050,
            exit_time_s=24.0,
            exit_price_usd=0.0080,
            exit_reason="COUNTER_FRONT_RUN_EXIT",
            capital_allocated_usd=1000.0,
            gross_roi_pct=60.0,
            net_roi_pct=58.2,
            net_pnl_usd=582.0,
            total_fees_usd=18.0,
            hold_duration_s=10.0,
        )
        d = st.to_dict()
        self.assertEqual(d["trade_id"], "SIM-TEST-1")
        self.assertEqual(d["net_roi_pct"], 58.2)
        self.assertEqual(d["exit_reason"], "COUNTER_FRONT_RUN_EXIT")

    def test_reconstruct_price_curve_fallback(self):
        """Verify default canonical price curve is returned when trades list is empty."""
        curve = ShadowSimulatorEngine.reconstruct_price_curve([])
        self.assertGreater(len(curve), 5)
        # Should start low and have a peak
        t0, p0 = curve[0]
        self.assertEqual(t0, 0.0)
        self.assertGreater(p0, 0.0)

    def test_reconstruct_price_curve_from_trades(self):
        """Verify price curve reconstructed from trade dictionary list."""
        curve = ShadowSimulatorEngine.reconstruct_price_curve(self.trades)
        self.assertEqual(len(curve), len(self.trades))
        self.assertEqual(curve[0][0], 0.0)
        self.assertEqual(curve[0][1], 0.0010)
        self.assertEqual(curve[-1][0], 60.0)

    def test_get_interpolated_price_exact_and_between(self):
        """Verify piecewise linear price interpolation."""
        curve = [(0.0, 0.0010), (10.0, 0.0020), (20.0, 0.0040)]
        # Exact points
        self.assertAlmostEqual(ShadowSimulatorEngine.get_interpolated_price(curve, 0.0), 0.0010)
        self.assertAlmostEqual(ShadowSimulatorEngine.get_interpolated_price(curve, 10.0), 0.0020)
        # Between points (midpoint at t=5s should be 0.0015)
        self.assertAlmostEqual(ShadowSimulatorEngine.get_interpolated_price(curve, 5.0), 0.0015)
        # Clamped boundaries
        self.assertAlmostEqual(ShadowSimulatorEngine.get_interpolated_price(curve, -5.0), 0.0010)
        self.assertAlmostEqual(ShadowSimulatorEngine.get_interpolated_price(curve, 35.0), 0.0040)

    def test_simulate_trade_counter_front_run(self):
        """Verify COUNTER_FRONT_RUN strategy captures upside before dump."""
        cluster = self.clusters[0]  # Snipe at 13s, dump at 28s
        cfg = SimulationConfig(strategy="COUNTER_FRONT_RUN", front_run_lead_s=4.0, execution_latency_s=1.0)
        trade = self.engine.simulate_trade(cluster, self.trades, cfg)

        self.assertEqual(trade.entry_time_s, 14.0)  # 13 + 1
        self.assertEqual(trade.exit_time_s, 24.0)   # 28 - 4
        self.assertEqual(trade.exit_reason, "COUNTER_FRONT_RUN_EXIT")
        # Entry at T+14s ($0.0048 range), exit at T+24s ($0.0072+ range) -> positive net ROI
        self.assertGreater(trade.net_roi_pct, 0.0)
        self.assertGreater(trade.net_pnl_usd, 0.0)

    def test_simulate_trade_copy_exit_penalty(self):
        """Verify naive COPY_EXIT strategy suffers exit liquidity collapse."""
        cluster = self.clusters[0]
        cfg = SimulationConfig(strategy="COPY_EXIT", execution_latency_s=1.0)
        trade = self.engine.simulate_trade(cluster, self.trades, cfg)

        self.assertEqual(trade.exit_reason, "SYNDICATE_DUMP_COPY_EXIT")
        self.assertEqual(trade.exit_time_s, 29.0)  # 28s dump + 1s latency
        # Because it sells during/after dump crash, ROI should be significantly lower or negative
        counter_cfg = SimulationConfig(strategy="COUNTER_FRONT_RUN", front_run_lead_s=4.0)
        counter_trade = self.engine.simulate_trade(cluster, self.trades, counter_cfg)
        self.assertGreater(counter_trade.net_roi_pct, trade.net_roi_pct)

    def test_simulate_trade_fixed_time(self):
        """Verify FIXED_TIME strategy exits strictly at t_entry + hold_duration."""
        cluster = self.clusters[0]
        cfg = SimulationConfig(strategy="FIXED_TIME", fixed_hold_duration_s=8.0, execution_latency_s=1.0)
        trade = self.engine.simulate_trade(cluster, self.trades, cfg)

        self.assertEqual(trade.entry_time_s, 14.0)
        self.assertEqual(trade.exit_time_s, 22.0)
        self.assertEqual(trade.exit_reason, "FIXED_TIME_EXIT")

    def test_simulate_trade_trailing_stop(self):
        """Verify TRAILING_STOP strategy detects price decline from peak."""
        cluster = self.clusters[0]
        cfg = SimulationConfig(strategy="TRAILING_STOP", trailing_stop_pct=10.0, execution_latency_s=1.0)
        trade = self.engine.simulate_trade(cluster, self.trades, cfg)
        self.assertIn("TRAILING_STOP", trade.exit_reason)

    def test_fee_deductions_mathematical_precision(self):
        """Verify DEX swap fees and priority gas fees are accurately deducted."""
        cluster = self.clusters[0]
        cfg = SimulationConfig(
            initial_capital_usd=1000.0,
            dex_fee_bps=30,          # 0.3%
            priority_fee_sol=0.01,   # 0.01 SOL = $1.50 per tx
            sol_price_usd=150.0,
        )
        trade = self.engine.simulate_trade(cluster, self.trades, cfg)
        # Total fees should be greater than $3.00 (gas) + DEX fees
        self.assertGreater(trade.total_fees_usd, 6.0)
        # Net PnL must equal Gross PnL minus total fees
        gross_pnl = (trade.capital_allocated_usd * trade.gross_roi_pct) / 100.0
        self.assertAlmostEqual(trade.net_pnl_usd, gross_pnl - trade.total_fees_usd, places=2)

    def test_backtest_result_aggregation(self):
        """Verify portfolio level backtest aggregation and metrics."""
        cfg = SimulationConfig(strategy="COUNTER_FRONT_RUN", front_run_lead_s=4.0)
        result = self.engine.run_backtest(self.clusters, self.trades, cfg)

        self.assertEqual(result.total_trades, len(self.clusters))
        self.assertEqual(result.winning_trades, len(self.clusters))
        self.assertEqual(result.win_rate_pct, 100.0)
        self.assertGreater(result.total_net_pnl_usd, 0.0)
        self.assertEqual(len(result.equity_curve), len(self.clusters) + 1)
        self.assertEqual(result.equity_curve[0]["equity"], 1000.0)
        self.assertGreater(result.equity_curve[-1]["equity"], 1000.0)

    def test_backtest_empty_clusters(self):
        """Verify graceful return when clusters list is empty."""
        result = self.engine.run_backtest([])
        self.assertEqual(result.total_trades, 0)
        self.assertEqual(result.winning_trades, 0)
        self.assertEqual(result.win_rate_pct, 0.0)
        self.assertEqual(result.total_net_pnl_usd, 0.0)

    def test_optimize_exit_timing_sweep(self):
        """Verify parameter sweep returns best lead time maximizing net PnL."""
        opt = self.engine.optimize_exit_timing(self.clusters, self.trades, lead_range=(1.0, 10.0, 1.0))
        self.assertIn("optimal_lead_s", opt)
        self.assertIn("max_net_pnl_usd", opt)
        self.assertIn("sweep_results", opt)
        self.assertEqual(len(opt["sweep_results"]), 10)
        self.assertGreater(opt["max_net_pnl_usd"], 0.0)

    def test_adversarial_malformed_trades_and_clusters(self):
        """Verify engine does not crash on malformed, out-of-order, or non-numeric inputs."""
        malformed_trades = [
            {"seconds_since_launch": "invalid", "price_usd": None},
            {"timestamp": None},
            {"seconds_since_launch": 10.0, "price_usd": "0.005"},
            "non-dict",
            {},
        ]
        malformed_clusters = [
            {"id": None, "avg_buy_delay_s": None},
            {},
            "invalid_cluster",
        ]
        # Should safely compute without uncaught exceptions
        curve = self.engine.reconstruct_price_curve(malformed_trades)
        self.assertGreater(len(curve), 0)
        result = self.engine.run_backtest(malformed_clusters, malformed_trades)
        self.assertIsInstance(result, BacktestResult)

    def test_scanner_temporal_export_includes_simulation(self):
        """Verify scanner's generate_4d_temporal_state injects backtest and SIM timeline markers."""
        scanner = LiveSyndicateScanner(mock_mode=True)
        tokens = scanner.fetch_trending_tokens(limit=2)
        clusters = [
            {
                "id": "SYND-0001",
                "cluster_id": "SYND-0001",
                "identity_id": "SYND-0001",
                "alias": "Syndicate SYND-0001",
                "token_address": "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX",
                "token_symbol": "BELUGA",
                "chain": "sol",
                "creator": "8p7Z2M9tq4F1kL5n6uR8vX7yT9wQ2pM3kL4n5uR6vX7y",
                "wallets": ["Snip1", "Snip2"],
                "root_funder": "Root1",
                "confidence_score": 0.95,
                "suspicion_score": 88.5,
                "estimated_profit_usd": 16650.0,
                "behavior_mode": "flash",
                "buy_delay_s": 13.0,
                "hold_duration_s": 15.0,
                "bundler_rate": 0.515,
                "bot_rate": 0.667,
            }
        ]
        state = scanner.generate_4d_temporal_state(clusters)
        self.assertIn("backtest", state)
        self.assertIn("simulation_trades", state)
        self.assertIn("sim_alpha_pct", state["stats"])

        # Verify SIM_BUY and SIM_EXIT timeline events
        event_types = [e["type"] for e in state["timeline"]]
        self.assertIn("SIM_BUY", event_types)
        self.assertIn("SIM_EXIT", event_types)


if __name__ == "__main__":
    unittest.main()
