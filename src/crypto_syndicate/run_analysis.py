"""M6b - Main CLI entrypoint for Crypto Syndicate Research System."""

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure src/ is on the path when run directly
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

project_root = src_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from crypto_syndicate.discovery import DiscoveryPipeline
from crypto_syndicate.graph import SyndicateGraph
from crypto_syndicate.report import generate_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("crypto_syndicate.cli")


def main():
    parser = argparse.ArgumentParser(description="Crypto Syndicate Research System")
    parser.add_argument("--monitor", action="store_true", help="Start continuous monitoring loop")
    parser.add_argument("--chains", default="sol", help="Comma-separated chains: sol,eth,bsc (default: sol)")
    parser.add_argument("--output", default="./results", help="Output directory for reports (default: ./results)")
    parser.add_argument("--poll-interval", type=int, default=300, help="Monitor poll interval seconds (default: 300)")
    parser.add_argument("--mock", action="store_true", help="Use mock data (for testing without API keys)")
    parser.add_argument("--vector-store-url", default="http://localhost:6333", help="Qdrant vector store URL")
    parser.add_argument("--vector-store-path", default=None, help="Embedded local vector storage directory path")
    parser.add_argument("--find-similar", help="Query vector store for wallets behaviorally similar to target address")
    parser.add_argument("--top-k", type=int, default=5, help="Number of similar wallets to return (default: 5)")
    parser.add_argument("--tokens", help="Comma-separated tokens to analyze/scan concurrently")
    parser.add_argument("--correlate-campaigns", action="store_true", help="Run cross-token campaign correlation")
    parser.add_argument("--simulate", action="store_true", help="Run shadow counter-trade backtest simulation on detected syndicates")
    parser.add_argument("--capital", type=float, default=1000.0, help="Initial simulation capital in USD (default: 1000.0)")
    parser.add_argument("--latency", type=float, default=1.0, help="Simulated execution latency in seconds (default: 1.0)")
    parser.add_argument("--strategy", default="COUNTER_FRONT_RUN", choices=["COUNTER_FRONT_RUN", "COPY_EXIT", "TRAILING_STOP", "FIXED_TIME"], help="Simulation strategy (default: COUNTER_FRONT_RUN)")
    parser.add_argument("--terminal", action="store_true", help="Launch the clean 2D live terminal web server on port 8000")
    parser.add_argument("--port", type=int, default=8000, help="Port for web server (default: 8000)")
    args = parser.parse_args()

    chains = [c.strip() for c in args.chains.split(",") if c.strip()]
    os.makedirs(args.output, exist_ok=True)

    if args.terminal:
        from crypto_syndicate.server import start_terminal_server
        logger.info("Starting Syndicate 2D Terminal server on port %d...", args.port)
        server = start_terminal_server(port=args.port)
        url = f"http://localhost:{args.port}/web/syndicate_terminal.html"
        print(f"\n{'='*70}")
        print(f"SYNDICATE LIVE TERMINAL & SENTRY PLATFORM OPERATIONAL")
        print(f"{'='*70}")
        print(f"  URL : {url}")
        print(f"  SSE : http://localhost:{args.port}/events/stream")
        print(f"  API : http://localhost:{args.port}/api/syndicates")
        print(f"{'='*70}\n")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down terminal server.")
            server.server_close()
        return

    if args.simulate:
        from crypto_syndicate.scanner import LiveSyndicateScanner
        from crypto_syndicate.simulator import ShadowSimulatorEngine, SimulationConfig
        scanner = LiveSyndicateScanner(output_dir=args.output, mock_mode=args.mock)
        tokens = scanner.fetch_trending_tokens(limit=5)
        clusters = scanner.scan_tokens_concurrently(tokens)
        cfg = SimulationConfig(
            initial_capital_usd=args.capital,
            execution_latency_s=args.latency,
            strategy=args.strategy,
        )
        engine = ShadowSimulatorEngine(default_config=cfg)
        res = engine.run_backtest(clusters)
        opt = engine.optimize_exit_timing(clusters)
        print(f"\n{'='*75}")
        print(f"SHADOW COUNTER-TRADE BACKTEST REPORT ({args.strategy})")
        print(f"{'='*75}")
        print(f"  Total Trades Simulated : {res.total_trades}")
        print(f"  Winning Trades         : {res.winning_trades} ({res.win_rate_pct:.1f}% win rate)")
        print(f"  Total Net PnL          : ${res.total_net_pnl_usd:+,.2f}")
        print(f"  Average Return         : {res.avg_net_roi_pct:+.2f}%")
        print(f"  Max Drawdown           : {res.max_drawdown_pct:.2f}%")
        print(f"  Sharpe Ratio           : {res.sharpe_ratio:.2f}")
        print(f"  Optimal Exit Lead Time : T - {opt['optimal_lead_s']:.1f}s before dump (Peak PnL: ${opt['max_net_pnl_usd']:+,.2f})")
        print(f"{'-'*75}")
        for t in res.trades:
            print(f"  [{t.syndicate_id}] Entry T+{t.entry_time_s:.1f}s (${t.entry_price_usd:.4f}) -> Exit T+{t.exit_time_s:.1f}s (${t.exit_price_usd:.4f}) | ROI: {t.net_roi_pct:+.1f}% | Net: ${t.net_pnl_usd:+,.0f} ({t.exit_reason})")
        print(f"{'='*75}\n")
        return

    if args.correlate_campaigns:
        from crypto_syndicate.scanner import LiveSyndicateScanner
        scanner = LiveSyndicateScanner(output_dir=args.output, mock_mode=args.mock)
        tokens = scanner.fetch_trending_tokens(limit=5)
        clusters = scanner.scan_tokens_concurrently(tokens)
        camps = scanner.correlate_cross_token_campaigns(clusters)
        print(f"\n{'='*70}")
        print(f"CROSS-TOKEN CAMPAIGN CORRELATION: {len(camps)} CAMPAIGNS DETECTED")
        print(f"{'='*70}")
        for c in camps:
            toks = ", ".join(['$' + s for s in c['token_symbols']])
            print(f"  [{c['campaign_id']}] {c['name']} ({c['campaign_type']})")
            print(f"    Tokens: {toks} | Total Profit: ${c['total_profit_usd']:,.2f}")
            print(f"    Reused Wallets: {c['reused_wallets_count']} | Overlap: {c['jaccard_overlap']*100:.1f}%")
        print(f"{'='*70}\n")
        return

    if args.find_similar:
        from crypto_syndicate.vector_store import WalletVectorStore
        store_path = args.vector_store_path or os.path.join(args.output, "qdrant_storage")
        vstore = WalletVectorStore(url=args.vector_store_url, path=store_path)
        logger.info("Querying similar wallets for: %s (top_k=%d)", args.find_similar, args.top_k)
        results = vstore.find_similar_by_address(args.find_similar, top_k=args.top_k)
        print(f"\n{'='*70}")
        print(f"VECTOR SIMILARITY SEARCH: {args.find_similar}")
        print(f"{'='*70}")
        if not results:
            print("  No similar wallets found or target address not yet indexed in vector store.")
        else:
            for i, r in enumerate(results, 1):
                pats = ", ".join(r.get("patterns_flagged", []))
                print(f"  {i}. [{r['similarity_pct']}] {r['address']} | {r['syndicate_id']} | Chain: {r['chain']} | Patterns: {pats}")
        print(f"{'='*70}\n")
        return

    if args.monitor:
        from crypto_syndicate.monitor import MonitoringLoop
        logger.info("Starting monitoring loop | chains=%s | output=%s", chains, args.output)
        loop = MonitoringLoop(chains=chains, poll_interval=args.poll_interval, output_dir=args.output, mock_mode=args.mock)
        loop.run()
    else:
        logger.info("Running one-time analysis | chains=%s", chains)
        pipeline = DiscoveryPipeline(mock_mode=args.mock)
        wallets = pipeline.run_pipeline(chains=chains)
        logger.info("Discovery: %d wallet records found", len(wallets))

        sg = SyndicateGraph()
        sg.build_graph(wallets, pipeline.funding_relationships)
        clusters = sg.detect_clusters()
        logger.info("Clustering: %d syndicate clusters detected", len(clusters))

        paths = generate_report(wallets, clusters, output_dir=args.output)
        print(f"\n{'='*60}")
        print(f"Analysis Complete")
        print(f"{'='*60}")
        print(f"  Wallets analyzed : {len(wallets)}")
        print(f"  Syndicates found : {len(clusters)}")
        print(f"  CSV report       : {paths.get('csv', 'N/A')}")
        print(f"  JSON clusters    : {paths.get('json', 'N/A')}")
        print(f"  HTML report      : {paths.get('html', 'N/A')}")
        if clusters:
            top = clusters[0]
            cid = getattr(top, "cluster_id", None) or top.get("cluster_id", "unknown")
            score = float(getattr(top, "suspicion_score", 0.0) or top.get("suspicion_score", 0.0))
            wlist = getattr(top, "wallets", None) or top.get("wallets", [])
            pats = getattr(top, "flagged_patterns", None) or top.get("flagged_patterns", []) or top.get("patterns_flagged", [])
            print(f"\n  Top Syndicate    : {cid}")
            print(f"  Score            : {score:.1f}/100")
            print(f"  Wallets          : {len(wlist)}")
            print(f"  Patterns         : {', '.join(pats)}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
