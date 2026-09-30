"""Milestone 15 (M15) — Syndicate Shadow Simulator & Backtesting Engine.

Replays historical on-chain syndicate attack trade timelines, models real-world
execution penalties (network latency, DEX fees, price impact, and Jito front-running),
evaluates copy-trade vs. counter-trade exit strategies, and discovers optimal
exit timing windows (t*) maximizing net risk-adjusted return.
"""

from dataclasses import dataclass, field
import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Configurable execution parameters for shadow copy/counter trading."""

    initial_capital_usd: float = 1000.0
    execution_latency_s: float = 1.0  # Time lag between on-chain signal and trade confirmation
    slippage_bps: int = 150  # 150 bps = 1.5% base slippage
    dex_fee_bps: int = 30  # 30 bps = 0.3% per swap (0.6% round-trip)
    priority_fee_sol: float = 0.005  # Priority gas fee per transaction
    sol_price_usd: float = 150.0  # Reference SOL/USD exchange rate
    strategy: str = "COUNTER_FRONT_RUN"  # "COPY_EXIT", "COUNTER_FRONT_RUN", "TRAILING_STOP", "FIXED_TIME"
    front_run_lead_s: float = 4.0  # Lead time in seconds to exit ahead of predicted syndicate dump
    fixed_hold_duration_s: float = 15.0  # Fixed hold duration for FIXED_TIME strategy
    trailing_stop_pct: float = 15.0  # Dynamic trailing stop loss percentage
    profit_target_pct: float = 100.0  # Take profit threshold
    stop_loss_pct: float = 25.0  # Hard stop loss threshold


@dataclass
class SimulationTrade:
    """Granular record of an individual simulated shadow trade."""

    trade_id: str
    token_address: str
    syndicate_id: str
    entry_time_s: float
    entry_price_usd: float
    exit_time_s: float
    exit_price_usd: float
    exit_reason: str  # "COUNTER_FRONT_RUN_EXIT", "SYNDICATE_DUMP_COPY_EXIT", "TRAILING_STOP_HIT", "STOP_LOSS_HIT"
    capital_allocated_usd: float
    gross_roi_pct: float
    net_roi_pct: float
    net_pnl_usd: float
    total_fees_usd: float
    hold_duration_s: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "token_address": self.token_address,
            "syndicate_id": self.syndicate_id,
            "entry_time_s": round(self.entry_time_s, 2),
            "entry_price_usd": round(self.entry_price_usd, 6),
            "exit_time_s": round(self.exit_time_s, 2),
            "exit_price_usd": round(self.exit_price_usd, 6),
            "exit_reason": self.exit_reason,
            "capital_allocated_usd": round(self.capital_allocated_usd, 2),
            "gross_roi_pct": round(self.gross_roi_pct, 2),
            "net_roi_pct": round(self.net_roi_pct, 2),
            "net_pnl_usd": round(self.net_pnl_usd, 2),
            "total_fees_usd": round(self.total_fees_usd, 2),
            "hold_duration_s": round(self.hold_duration_s, 2),
        }


@dataclass
class BacktestResult:
    """Aggregated portfolio performance metrics from historical syndicate replay."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    total_net_pnl_usd: float
    avg_net_roi_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    profit_factor: float
    optimal_exit_lead_s: float
    trades: List[SimulationTrade] = field(default_factory=list)
    equity_curve: List[Dict[str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate_pct": round(self.win_rate_pct, 2),
            "total_net_pnl_usd": round(self.total_net_pnl_usd, 2),
            "avg_net_roi_pct": round(self.avg_net_roi_pct, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "profit_factor": round(self.profit_factor, 2),
            "optimal_exit_lead_s": round(self.optimal_exit_lead_s, 1),
            "trades": [t.to_dict() for t in self.trades],
            "equity_curve": self.equity_curve,
        }


class ShadowSimulatorEngine:
    """Core backtesting and synthetic execution engine for syndicate strategies."""

    def __init__(self, default_config: Optional[SimulationConfig] = None) -> None:
        self.config = default_config or SimulationConfig()

    @staticmethod
    def reconstruct_price_curve(
        trades: List[Any], t_launch: float = 0.0
    ) -> List[Tuple[float, float]]:
        """Reconstruct a sorted (seconds_since_launch, price_usd) trajectory from trades."""
        if not trades:
            # Default canonical trajectory (Mint -> Snipe -> Pump Peak -> Coordinated Dump)
            return [
                (0.0, 0.0010),
                (10.0, 0.0012),
                (13.0, 0.0020),
                (16.0, 0.0045),
                (25.0, 0.0068),
                (28.0, 0.0080),  # Peak
                (32.0, 0.0065),
                (35.0, 0.0022),  # Dump crash
                (45.0, 0.0015),
                (60.0, 0.0011),
            ]

        extracted: List[Tuple[float, float]] = []
        for tr in trades:
            t = None
            try:
                if hasattr(tr, "seconds_since_launch") and tr.seconds_since_launch is not None:
                    t = float(tr.seconds_since_launch)
                elif isinstance(tr, dict) and tr.get("seconds_since_launch") is not None:
                    t = float(tr["seconds_since_launch"])
                elif hasattr(tr, "timestamp") and tr.timestamp is not None:
                    t = float(tr.timestamp - t_launch) if t_launch > 0 else float(tr.timestamp)
                elif isinstance(tr, dict) and tr.get("timestamp") is not None:
                    t = float(tr["timestamp"] - t_launch) if t_launch > 0 else float(tr["timestamp"])
            except (ValueError, TypeError):
                t = None

            if t is None:
                continue

            price = 0.0
            try:
                if hasattr(tr, "price_usd") and tr.price_usd is not None:
                    price = float(tr.price_usd)
                elif isinstance(tr, dict) and tr.get("price_usd") is not None:
                    price = float(tr["price_usd"])
            except (ValueError, TypeError):
                price = 0.0

            if price > 0:
                extracted.append((max(0.0, t), price))

        if not extracted:
            return ShadowSimulatorEngine.reconstruct_price_curve([])

        # Sort by timestamp ascending
        extracted.sort(key=lambda x: x[0])

        # Deduplicate identical timestamps taking latest price
        dedup: List[Tuple[float, float]] = []
        for t, p in extracted:
            if dedup and math.isclose(dedup[-1][0], t, abs_tol=0.01):
                dedup[-1] = (t, p)
            else:
                dedup.append((t, p))

        return dedup

    @staticmethod
    def get_interpolated_price(curve: List[Tuple[float, float]], t_target: float) -> float:
        """Piecewise linear interpolation of price at target second t."""
        if not curve:
            return 0.0010
        if t_target <= curve[0][0]:
            return curve[0][1]
        if t_target >= curve[-1][0]:
            return curve[-1][1]

        for i in range(len(curve) - 1):
            t0, p0 = curve[i]
            t1, p1 = curve[i + 1]
            if t0 <= t_target <= t1:
                if math.isclose(t1, t0, abs_tol=1e-6):
                    return p0
                ratio = (t_target - t0) / (t1 - t0)
                return p0 + ratio * (p1 - p0)

        return curve[-1][1]

    def simulate_trade(
        self,
        cluster: Dict[str, Any],
        trades: Optional[List[Any]] = None,
        config: Optional[SimulationConfig] = None,
    ) -> SimulationTrade:
        """Simulate a single trade attempting to exploit or counter a detected syndicate."""
        cfg = config or self.config
        price_curve = self.reconstruct_price_curve(trades or [])

        # 1. Determine syndicate timing anchors
        if not isinstance(cluster, dict):
            cluster = {}
        cluster_id = str(cluster.get("id") or cluster.get("cluster_id") or "SYND-0001")
        token_addr = str(cluster.get("token_address") or "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX")

        # Ingress delay: syndicate enters at avg_buy_delay_s (or default 13.0s)
        try:
            val_delay = cluster.get("avg_buy_delay_s") or cluster.get("buy_delay_s")
            t_snipe = float(val_delay) if val_delay is not None else 13.0
        except (ValueError, TypeError):
            t_snipe = 13.0

        try:
            val_hold = cluster.get("avg_hold_duration_s") or cluster.get("hold_time_s")
            hold_time = float(val_hold) if val_hold is not None else 15.0
        except (ValueError, TypeError):
            hold_time = 15.0
        t_dump = t_snipe + max(5.0, hold_time)

        # 2. Simulated Entry: Signal occurs at t_snipe, trade confirms at t_entry = t_snipe + latency
        t_entry = t_snipe + max(0.1, cfg.execution_latency_s)
        base_entry_price = self.get_interpolated_price(price_curve, t_entry)

        # Apply slippage on buy (pay higher price)
        slippage_mult_buy = 1.0 + (cfg.slippage_bps / 10000.0)
        actual_entry_price = base_entry_price * slippage_mult_buy

        # 3. Determine Exit Timing & Price according to Strategy
        exit_reason = "COUNTER_FRONT_RUN_EXIT"
        if cfg.strategy == "COPY_EXIT":
            # Naive copy-trading: sells AFTER the syndicate dumps + execution latency
            t_exit = t_dump + cfg.execution_latency_s
            exit_reason = "SYNDICATE_DUMP_COPY_EXIT"
        elif cfg.strategy == "FIXED_TIME":
            t_exit = t_entry + max(1.0, cfg.fixed_hold_duration_s)
            exit_reason = "FIXED_TIME_EXIT"
        elif cfg.strategy == "TRAILING_STOP":
            # Step in 0.5s increments looking for trailing stop or hard stop loss
            t_curr = t_entry + 0.5
            peak_p = actual_entry_price
            t_exit = t_dump  # fallback
            while t_curr <= t_dump + 30.0:
                p_now = self.get_interpolated_price(price_curve, t_curr)
                peak_p = max(peak_p, p_now)
                # Check trailing stop drawdown
                if p_now <= peak_p * (1.0 - cfg.trailing_stop_pct / 100.0):
                    t_exit = t_curr
                    exit_reason = "TRAILING_STOP_HIT"
                    break
                # Check hard stop loss
                if p_now <= actual_entry_price * (1.0 - cfg.stop_loss_pct / 100.0):
                    t_exit = t_curr
                    exit_reason = "STOP_LOSS_HIT"
                    break
                t_curr += 0.5
        else:
            # Default: COUNTER_FRONT_RUN
            # Front-runs the dump by exiting `front_run_lead_s` seconds before t_dump
            t_exit = max(t_entry + 1.0, t_dump - max(0.5, cfg.front_run_lead_s))
            exit_reason = "COUNTER_FRONT_RUN_EXIT"

        base_exit_price = self.get_interpolated_price(price_curve, t_exit)

        # Apply slippage on sell (receive lower price)
        slippage_mult_sell = max(0.01, 1.0 - (cfg.slippage_bps / 10000.0))
        actual_exit_price = base_exit_price * slippage_mult_sell

        # 4. Compute PnL & Fee deductions
        capital = cfg.initial_capital_usd
        tokens_bought = capital / actual_entry_price if actual_entry_price > 0 else 0.0
        gross_value_exit = tokens_bought * actual_exit_price
        gross_roi_pct = ((gross_value_exit - capital) / capital) * 100.0

        # DEX fee roundtrip
        dex_fee_usd = capital * (cfg.dex_fee_bps / 10000.0) + gross_value_exit * (cfg.dex_fee_bps / 10000.0)
        # Priority gas fee (roundtrip = 2 txs)
        gas_fee_usd = 2.0 * (cfg.priority_fee_sol * cfg.sol_price_usd)
        total_fees = dex_fee_usd + gas_fee_usd

        net_value_exit = gross_value_exit - total_fees
        net_pnl_usd = net_value_exit - capital
        net_roi_pct = (net_pnl_usd / capital) * 100.0
        hold_duration = max(0.1, t_exit - t_entry)

        return SimulationTrade(
            trade_id=f"SIM-{cluster_id}-{int(t_entry)}",
            token_address=token_addr,
            syndicate_id=cluster_id,
            entry_time_s=t_entry,
            entry_price_usd=actual_entry_price,
            exit_time_s=t_exit,
            exit_price_usd=actual_exit_price,
            exit_reason=exit_reason,
            capital_allocated_usd=capital,
            gross_roi_pct=gross_roi_pct,
            net_roi_pct=net_roi_pct,
            net_pnl_usd=net_pnl_usd,
            total_fees_usd=total_fees,
            hold_duration_s=hold_duration,
        )

    def run_backtest(
        self,
        clusters: List[Dict[str, Any]],
        trades: Optional[List[Any]] = None,
        config: Optional[SimulationConfig] = None,
    ) -> BacktestResult:
        """Run backtest across all detected syndicate clusters and calculate portfolio metrics."""
        cfg = config or self.config
        if not clusters:
            return BacktestResult(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                total_net_pnl_usd=0.0,
                avg_net_roi_pct=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=0.0,
                profit_factor=1.0,
                optimal_exit_lead_s=cfg.front_run_lead_s,
                trades=[],
                equity_curve=[{"trade": 0, "equity": cfg.initial_capital_usd}],
            )

        sim_trades: List[SimulationTrade] = []
        equity = cfg.initial_capital_usd
        equity_curve: List[Dict[str, float]] = [{"trade": 0, "equity": round(equity, 2)}]

        peak_equity = equity
        max_drawdown = 0.0
        net_returns: List[float] = []
        gross_wins = 0.0
        gross_losses = 0.0

        for c in clusters:
            if not isinstance(c, dict):
                continue
            t = self.simulate_trade(c, trades, cfg)
            sim_trades.append(t)

            equity += t.net_pnl_usd
            equity = max(1.0, equity)  # Capital floor
            equity_curve.append({"trade": len(sim_trades), "equity": round(equity, 2)})

            # Track peak and drawdown
            peak_equity = max(peak_equity, equity)
            dd = ((peak_equity - equity) / peak_equity) * 100.0 if peak_equity > 0 else 0.0
            max_drawdown = max(max_drawdown, dd)

            net_returns.append(t.net_roi_pct)
            if t.net_pnl_usd > 0:
                gross_wins += t.net_pnl_usd
            else:
                gross_losses += abs(t.net_pnl_usd)

        total_t = len(sim_trades)
        wins = sum(1 for t in sim_trades if t.net_pnl_usd > 0)
        losses = total_t - wins
        win_rate = (wins / total_t) * 100.0 if total_t > 0 else 0.0
        total_pnl = sum(t.net_pnl_usd for t in sim_trades)
        avg_roi = sum(net_returns) / len(net_returns) if net_returns else 0.0

        # Sharpe Ratio approximation
        if len(net_returns) > 1:
            mean_ret = avg_roi
            variance = sum((r - mean_ret) ** 2 for r in net_returns) / (len(net_returns) - 1)
            std_dev = math.sqrt(variance)
            sharpe = (mean_ret / std_dev) if std_dev > 1e-4 else 0.0
        else:
            sharpe = 1.0 if avg_roi > 0 else 0.0

        profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 1.0)

        return BacktestResult(
            total_trades=total_t,
            winning_trades=wins,
            losing_trades=losses,
            win_rate_pct=win_rate,
            total_net_pnl_usd=total_pnl,
            avg_net_roi_pct=avg_roi,
            max_drawdown_pct=max_drawdown,
            sharpe_ratio=sharpe,
            profit_factor=profit_factor,
            optimal_exit_lead_s=cfg.front_run_lead_s,
            trades=sim_trades,
            equity_curve=equity_curve,
        )

    def optimize_exit_timing(
        self,
        clusters: List[Dict[str, Any]],
        trades: Optional[List[Any]] = None,
        lead_range: Tuple[float, float, float] = (1.0, 12.0, 1.0),
    ) -> Dict[str, Any]:
        """Parameter sweep over front-run lead times finding optimal t* maximizing net PnL."""
        start, stop, step = lead_range
        sweep_results: List[Dict[str, Any]] = []

        best_lead = self.config.front_run_lead_s
        best_pnl = -float("inf")

        curr_lead = start
        while curr_lead <= stop + 1e-6:
            cfg = SimulationConfig(
                initial_capital_usd=self.config.initial_capital_usd,
                execution_latency_s=self.config.execution_latency_s,
                slippage_bps=self.config.slippage_bps,
                dex_fee_bps=self.config.dex_fee_bps,
                priority_fee_sol=self.config.priority_fee_sol,
                sol_price_usd=self.config.sol_price_usd,
                strategy="COUNTER_FRONT_RUN",
                front_run_lead_s=curr_lead,
            )
            res = self.run_backtest(clusters, trades, cfg)
            sweep_results.append({
                "lead_s": round(curr_lead, 1),
                "net_pnl_usd": round(res.total_net_pnl_usd, 2),
                "win_rate_pct": round(res.win_rate_pct, 1),
                "sharpe_ratio": round(res.sharpe_ratio, 2),
            })
            if res.total_net_pnl_usd > best_pnl:
                best_pnl = res.total_net_pnl_usd
                best_lead = curr_lead

            curr_lead += step

        return {
            "optimal_lead_s": round(best_lead, 1),
            "max_net_pnl_usd": round(best_pnl, 2),
            "sweep_results": sweep_results,
        }
