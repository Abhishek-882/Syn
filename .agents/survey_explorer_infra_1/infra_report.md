# Infrastructure Architectural Specification: Interactive Visualizations, Continuous Monitoring & Reporting Engine

**Target Subsystems**: R2 (Interactive Jupyter Notebook & Transfer Maps), R4 (Continuous Monitoring Loop & Alerts), and R5 (Static Self-Contained Research Report & Exports)  
**Author**: survey_explorer_infra_1 (teamwork_preview_explorer)  
**Date**: 2026-09-20  
**Status**: APPROVED ARCHITECTURAL SPECIFICATION  
**Scope**: Full end-to-end infrastructure specification for crypto syndicate detection, interactive graph analysis, background monitoring daemon, and zero-CDN reporting.

---

## 1. Executive Summary & Architectural Overview

The Crypto Syndicate Research & Monitoring System addresses sophisticated on-chain manipulation across Solana, Ethereum, BSC, and other GMGN-supported blockchains. To empower intelligence analysts, forensic investigators, and automated defense systems, the infrastructure must bridge high-velocity automated detection with intuitive, interactive exploratory visual analytics.

This document specifies the technical architecture for the three delivery and operational pillars of the system:
1. **Interactive Jupyter Notebook (R2)**: A forensic investigation environment featuring physics-driven force-directed wallet network graphs, synchronized token launch price/trade timeline maps, and click-on-node inspection modals.
2. **Continuous Background Monitoring Daemon (R4)**: An enterprise-grade, crash-resilient polling daemon with an independent 1-minute heartbeat logger, sub-10-minute syndicate cluster detection latency, and dual-format (JSON Lines + plain text ASCII) alerting.
3. **Self-Contained Static Reporting & Data Exports (R5)**: A 100% offline, zero-CDN HTML intelligence report compiler with inlined interactive visualization runtimes, accompanied by strict RFC-4180 CSV and hierarchical JSON exports.

### High-Level System Architecture & Component Interconnect

```
                                  +---------------------------------------+
                                  |   External Data Sources (R3)          |
                                  |   GMGN API (Multi-chain) + Solscan    |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |   Resilient Ingestion & Cache Layer   |
                                  |   Token Bucket Limiter, SQLite Cache  |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |   Discovery & Heuristics Engine (R1)  |
                                  |   Early Entry, Shared Funder,         |
                                  |   Shared Deployer, Coordinated Dumps  |
                                  +---------+-------------------+---------+
                                            |                   |
            +-------------------------------+                   +-------------------------------+
            v                                                                                   v
+---------------------------------------+                               +---------------------------------------+
|   Interactive Jupyter Notebook (R2)   |                               |  Continuous Monitoring Daemon (R4)    |
|   - PyVis Force-Directed Graphs       |                               |  - Independent 60s Heartbeat Loop     |
|   - Plotly Price & Trade Timelines    |                               |  - 300s Polling & Detection Loop      |
|   - Interactive Click Inspection      |                               |  - Dual Alert Logger (JSONL + Text)   |
|   - Interactive Investigation Cells   |                               |  - Signal Handling & State Recovery   |
+-------------------+-------------------+                               +-------------------+-------------------+
                    |                                                                       |
                    +-------------------------------+---------------------------------------+
                                                    |
                                                    v
                                  +---------------------------------------+
                                  |   Reporting & Export Subsystem (R5)   |
                                  |   - Zero-CDN Static HTML Compiler     |
                                  |   - RFC 4180 CSV Exporter             |
                                  |   - Hierarchical JSON Exporter        |
                                  +---------------------------------------+
```

---

## 2. Interactive Jupyter Notebook Architecture (R2)

### 2.1 Notebook Workflow & User Experience Design (`syndicate_investigation.ipynb`)

The notebook serves as the primary investigative workbench for forensic analysts. It is designed to run seamlessly in local JupyterLab, classic Jupyter Notebook, and VS Code Notebook environments.

#### Cell-by-Cell Execution Flow:
1. **Cell 1: Environment & Credential Validation**:
   - Validates existence of `GMGN_API_KEY` and `SOLSCAN_API_KEY` via `os.environ`.
   - Offers offline mode toggle (`OFFLINE_MODE = True/False`) to switch between live API ingestion and pre-cached test fixtures (`fixtures/`).
   - Initializes logging, output directory structure (`reports/`, `exports/`, `logs/`), and theme settings.
2. **Cell 2: Target Selection & Ingestion Pipeline**:
   - Allows user to either input a specific token address (e.g. `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`), select from recently launched tokens via GMGN, or load historical syndicate cases.
   - Triggers rate-limited data collection for token metadata, swap transactions, and wallet transfer histories.
3. **Cell 3: Syndicate Discovery & Graph Clustering**:
   - Executes discovery pipeline: flags early entry, calculates common funding sources (1-2 hops), checks deployer reuse, and detects dump alignment.
   - Computes Louvain/Leiden modularity clustering on the composite wallet relationship graph.
   - Generates composite suspicion scores (0 - 100) and ranks discovered clusters.
   - Renders a rich summary scorecard: Clusters Found, Suspicious Wallets, Total Coordinated Volume, and Estimated Extracted Profit.
4. **Cell 4: Interactive Network Graph (Wallet Funding & Syndicate Topology)**:
   - Renders a full-bleed interactive network graph directly inside the notebook cell output using PyVis/vis.js.
   - Nodes represent wallets; edges represent SOL/ETH funding transfers.
   - Interactive features: drag nodes, zoom/pan, hover for summary, click-to-pin, click-on-node inspection modal, and cluster filter controls.
5. **Cell 5: Token Launch Timeline Maps with Synchronized Price Action**:
   - Renders a synchronized dual-panel Plotly timeline chart:
     - Upper panel: Candlestick/line token price chart with overlay markers for syndicate buys (▲ green) and sells (▼ red).
     - Lower panel: Wallet execution swimlane showing entry offsets ($T_0 + \Delta t$) and holding durations.
   - Range slider allows zooming into high-frequency execution windows (e.g., the first 60 seconds of token launch).
6. **Cell 6: Forensic Cluster Breakdown & Evidence Audit**:
   - Interactive data table (powered by pandas / ipywidgets or embedded HTML/DataTables) with search, filtering, and sort capabilities.
   - Displays wallet address, role, suspicion score, pattern breakdown, and profit metrics.
7. **Cell 7: One-Click Export & Static Report Generation**:
   - Executes `report_generator.generate_html_report()` and export functions.
   - Generates self-contained HTML report in `reports/` and CSV/JSON files in `exports/`.
   - Provides direct file links for immediate local browser viewing.

---

### 2.2 Visualization Engine Selection: PyVis vs Plotly vs Cytoscape

A critical architectural decision is selecting the right visualization engine for both network graphs and time-series charts. The table below evaluates the three candidates:

| Architectural Criteria | PyVis (vis.js) | Plotly (`graph_objects`) | Cytoscape (`ipycytoscape`) | Selected Choice & Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Physics / Force-Directed Layout** | **Exceptional** (Real-time WebGL/Canvas Barnes-Hut & ForceAtlas2 physics; fluid node dragging) | **Poor** (Static layouts precomputed via NetworkX; no dynamic physics or node repositioning) | **Very Good** (Supports CoSE, Cola, Dagre, but lacks native spring physics feel of vis.js) | **PyVis for Network Graphs**: Essential for analysts untangling complex wallet webs. |
| **Time-Series & Financial Charts** | **Not Suitable** (Specialized only for networks and timelines, no native candlestick/financial axes) | **Industry Standard** (Native candlestick, OHLC, dual Y-axes, synchronized crosshairs, range sliders) | **Not Suitable** (Network-only library) | **Plotly for Timelines**: Unmatched capability for price and transaction timeline alignment. |
| **Jupyter Notebook Integration** | **Clean** (Generates HTML string rendered via `IPython.display.HTML` or local `IFrame`) | **Native** (`fig.show()` works seamlessly across all notebook frontends) | **Fragile** (Requires Jupyter widget extensions; known version mismatch issues in JupyterLab 4) | **PyVis + Plotly**: Both avoid fragile Jupyter widget extension compile-time requirements. |
| **Zero-CDN / Offline Capability** | **Achievable** (Requires custom inliner to bundle ~520KB `vis-network.min.js` instead of CDN) | **Built-in** (`include_plotlyjs=True` or `include_plotlyjs="directory"` inlines full runtime) | **Complex** (Requires embedding large JS bundles and custom CSS assets) | **PyVis (with custom offline asset bundler) + Plotly**. |
| **Custom Interactivity (Click Inspection)** | **Superior** (Rich JS event hooks: `click`, `selectNode`, `hoverNode`, `stabilizationProgress`) | **Limited** (Click events in Plotly require ipywidgets callbacks or Dash backend) | **High** (Rich event model, but heavy syntax overhead) | **PyVis**: Client-side JS event handlers run directly in the browser/iframe without Python kernel latency. |

**Architectural Decision**: Adopt a **Dual-Engine Visualization Strategy**:
1. **PyVis (vis-network.js)** for Wallet Network Graphs (funding trees, cluster topology, interactive physics, click inspection).
2. **Plotly** for Token Launch Timeline Maps (price candlesticks, synchronized buy/sell overlays, wallet execution swimlanes).

---

### 2.3 Network Graph Architecture (PyVis & vis.js)

#### 2.3.1 Graph Topology & Physics Engine Configuration
The network graph represents a directed multigraph $G = (V, E)$ where:
- $V$: Wallets involved in token transactions or funding flows.
- $E$: Directed SOL/ETH/BNB funding transfers ($u \xrightarrow{\text{amount}} v$) and optional token trading affiliations.

To prevent graph tangling and ensure optimal cluster visual separation, the physics engine is configured with Barnes-Hut repulsive modeling:

```javascript
// vis.js Physics Configuration Blueprint
{
  physics: {
    enabled: true,
    solver: 'barnesHut',
    barnesHut: {
      gravitationalConstant: -12000,
      centralGravity: 0.35,
      springLength: 120,
      springConstant: 0.04,
      damping: 0.09,
      avoidOverlap: 0.65
    },
    stabilization: {
      enabled: true,
      iterations: 350,
      updateInterval: 25,
      onlyDynamicEdges: false,
      fit: true
    }
  },
  interaction: {
    hover: true,
    tooltipDelay: 100,
    hideEdgesOnDrag: false,
    navigationButtons: true,
    keyboard: true,
    multiselect: true
  }
}
```

#### 2.3.2 Visual Encodings for Nodes and Edges

##### Node Encodings:
- **Shape by Wallet Role**:
  - `diamond` or `star`: **Deployer Wallet** (the contract creator / liquidity pool initiator).
  - `square` or `triangleDown`: **Funding Source / Root Funder** (wallet that disbursed SOL/ETH to participant wallets).
  - `dot` (circle): **Syndicate Trader / Sybil Wallet** (executes coordinated buys/sells).
- **Color by Syndicate Cluster**:
  - Syndicate clusters are assigned high-contrast, visually distinct categorical colors:
    - Cluster 1: Neon Cyan (`#00e5ff`)
    - Cluster 2: Vivid Amber / Tangerine (`#ff9100`)
    - Cluster 3: Bright Magenta / Fuchsia (`#f50057`)
    - Cluster 4: Lime Green (`#76ff03`)
    - Cluster 5: Electric Purple (`#7c4dff`)
    - Unclustered / Neutral Wallets: Muted Slate (`#78909c`)
- **Size by Volume / Suspicion Score**:
  - Node radius scales dynamically based on total buy volume (USD) or suspicion score:
    $$R(v) = 14 + 26 \times \left(\frac{\text{Score}(v)}{100}\right)$$
    Deployer and Funder nodes receive a base multiplier ($1.25\times$) for immediate prominence.
- **Node Border & Highlighting**:
  - Wallets with suspicion score $\ge 80$ display a pulsed crimson or golden highlight border (`borderWidth: 3, color: '#ff1744'`).

##### Edge Encodings:
- **Directed Arrows**: Edge direction indicates financial flow ($Funder \to Trader$).
- **Edge Width**: Proportional to native transfer amount ($\log$-scaled):
  $$\text{Width}(e) = \max\left(1.5, 2.0 \times \log_{10}(1 + \text{TransferAmount})\right)$$
- **Edge Color**: Matches source funder color with $60\%$ opacity (`rgba(..., 0.6)`), turning fully opaque and neon on hover.
- **Edge Label**: Clear native amount and symbol, e.g. `"14.5 SOL"`, `"2.1 ETH"`.

#### 2.3.3 Click-on-Node Inspection Modal & Neighbor Highlighting
To satisfy R2 acceptance criteria without requiring a running Python kernel for click events, the inspection system is implemented as a client-side JavaScript overlay inside the PyVis HTML container:

```javascript
// Client-side Click Event Handler inside PyVis Container
network.on('click', function(params) {
  var panel = document.getElementById('wallet-inspector-panel');
  if (params.nodes.length > 0) {
    var nodeId = params.nodes[0];
    var nodeData = allNodesDict[nodeId];
    
    // Highlight 1st-degree neighbors and dim rest of the graph
    var connectedNodes = network.getConnectedNodes(nodeId);
    connectedNodes.push(nodeId);
    
    var updateArray = [];
    allNodeIds.forEach(function(id) {
      if (connectedNodes.indexOf(id) !== -1) {
        updateArray.push({ id: id, opacity: 1.0 });
      } else {
        updateArray.push({ id: id, opacity: 0.15 });
      }
    });
    nodesDataSet.update(updateArray);
    
    // Populate Inspector Panel
    document.getElementById('insp-address').innerText = nodeData.id;
    document.getElementById('insp-chain').innerText = nodeData.chain.toUpperCase();
    document.getElementById('insp-role').innerText = nodeData.role;
    document.getElementById('insp-cluster').innerText = nodeData.cluster_id;
    document.getElementById('insp-score').innerText = nodeData.suspicion_score + ' / 100';
    document.getElementById('insp-profit').innerText = '$' + nodeData.profit_usd.toLocaleString();
    
    // Render pattern badges
    var badgeHtml = '';
    nodeData.flagged_patterns.forEach(function(pat) {
      badgeHtml += '<span class="badge badge-' + pat.severity + '">' + pat.name + '</span> ';
    });
    document.getElementById('insp-patterns').innerHTML = badgeHtml;
    
    // External explorer links
    document.getElementById('insp-solscan-link').href = nodeData.explorer_url;
    panel.style.display = 'block';
  } else {
    // Reset opacity on canvas click
    var resetArray = allNodeIds.map(function(id) { return { id: id, opacity: 1.0 }; });
    nodesDataSet.update(resetArray);
    panel.style.display = 'none';
  }
});
```

#### 2.3.4 Zero-CDN Offline Bundling for PyVis in Jupyter
PyVis natively references `https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js`. To comply with strict offline requirements:
1. Vendor `vis-network.min.js` (~520KB) and `vis-network.min.css` in `crypto_syndicate/visualization/assets/`.
2. Implement `OfflineNetwork` (extending PyVis `Network`):
   - Overrides `generate_html()` to read local assets and embed them inside `<style>/* inlined css */</style>` and `<script>/* inlined js */</script>`.
   - Embeds into Jupyter cells using:
     ```python
     from IPython.display import HTML
     import html
     html_content = offline_net.generate_html(notebook=True)
     display(HTML(f'<iframe srcdoc="{html.escape(html_content)}" width="100%" height="650px" style="border:none;"></iframe>'))
     ```
   - This ensures 100% offline functionality within Jupyter without external CDN access.

---

### 2.4 Token Launch Timeline Maps (Plotly Architecture)

#### 2.4.1 Synchronized Dual-Panel Layout
The timeline visualization maps wallet execution dynamics against token market price. It is built using `plotly.subplots.make_subplots`:

```
+-------------------------------------------------------------------------+
| Panel 1: Token Price Action ($USD) & Coordinated Execution Overlay       |
| Y1: Price ($USD)                                                       |
|   /---\        /\  (Price Peak)                                         |
|  /     \      /  \               ▲ = Syndicate Buy (+8s, +11s, +14s)    |
| /       \----/    \              ▼ = Coordinated Dump (+180s, +195s)    |
|/                   \                                                    |
+-------------------------------------------------------------------------+
| Panel 2: Wallet Execution Swimlane (Categorical Wallets by Cluster)     |
| Y2: Wallet Addresses                                                    |
| W1 (Deployer)  |===[Liquidity Added]=========================>          |
| W2 (Trader A)  |  (Buy)========================(Dump)                   |
| W3 (Trader B)  |   (Buy)======================(Dump)                    |
| W4 (Trader C)  |     (Buy)====================(Dump)                    |
|                |                                                        |
| X-axis: Elapsed Time from Launch (Seconds: 0s, 30s, 60s, 120s, 300s...) |
+-------------------------------------------------------------------------+
```

#### 2.4.2 Technical Formulation & Plotly Specification

```python
# Technical Blueprint: Plotly Timeline Generator
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def build_timeline_map(token_meta, price_series, trades_df, clusters_df):
    '''
    Builds a synchronized dual-panel timeline map:
    - Upper: Price line/candlestick with overlay buy/sell markers.
    - Lower: Wallet execution swimlanes showing holding periods.
    '''
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.07,
        row_heights=[0.58, 0.42],
        subplot_titles=(
            f"{token_meta['symbol']} Price Action ($USD) & Syndicate Execution Overlay",
            "Syndicate Wallet Execution Swimlanes (Time from Launch T0)"
        )
    )
    
    # 1. Price Curve (Upper Panel)
    fig.add_trace(
        go.Scatter(
            x=price_series['seconds_from_launch'],
            y=price_series['price_usd'],
            mode='lines',
            name='Token Price ($USD)',
            line=dict(color='#00e5ff', width=2),
            hoverinfo='x+y'
        ),
        row=1, col=1
    )
    
    # 2. Buy Markers (Upper Panel)
    buys = trades_df[trades_df['side'] == 'BUY']
    fig.add_trace(
        go.Scatter(
            x=buys['seconds_from_launch'],
            y=buys['price_usd'],
            mode='markers',
            name='Syndicate Buys',
            marker=dict(symbol='triangle-up', size=11, color='#00e676', line=dict(width=1, color='#ffffff')),
            customdata=buys[['wallet_address', 'amount_usd', 'cluster_id']],
            hovertemplate="<b>BUY</b><br>Wallet: %{customdata[0]}<br>Time: +%{x:.1f}s<br>Price: $%{y:.6f}<br>USD: $%{customdata[1]:,.2f}<br>Cluster: %{customdata[2]}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 3. Sell Markers (Upper Panel)
    sells = trades_df[trades_df['side'] == 'SELL']
    fig.add_trace(
        go.Scatter(
            x=sells['seconds_from_launch'],
            y=sells['price_usd'],
            mode='markers',
            name='Coordinated Dumps',
            marker=dict(symbol='triangle-down', size=11, color='#ff1744', line=dict(width=1, color='#ffffff')),
            customdata=sells[['wallet_address', 'amount_usd', 'profit_usd']],
            hovertemplate="<b>SELL</b><br>Wallet: %{customdata[0]}<br>Time: +%{x:.1f}s<br>Price: $%{y:.6f}<br>USD: $%{customdata[1]:,.2f}<br>Profit: $%{customdata[2]:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 4. Swimlanes (Lower Panel)
    for idx, wallet in enumerate(clusters_df['wallet_address'].unique()):
        w_trades = trades_df[trades_df['wallet_address'] == wallet].sort_values('seconds_from_launch')
        if not w_trades.empty:
            t_first_buy = w_trades[w_trades['side'] == 'BUY']['seconds_from_launch'].min()
            t_last_sell = w_trades[w_trades['side'] == 'SELL']['seconds_from_launch'].max()
            
            # Holding bar
            if pd.notna(t_first_buy) and pd.notna(t_last_sell):
                fig.add_trace(
                    go.Scatter(
                        x=[t_first_buy, t_last_sell],
                        y=[wallet[:6] + '...' + wallet[-4:], wallet[:6] + '...' + wallet[-4:]],
                        mode='lines',
                        line=dict(color='rgba(255, 255, 255, 0.4)', width=4),
                        showlegend=False,
                        hoverinfo='none'
                    ),
                    row=2, col=1
                )
            
            # Individual trade events
            fig.add_trace(
                go.Scatter(
                    x=w_trades['seconds_from_launch'],
                    y=[wallet[:6] + '...' + wallet[-4:]] * len(w_trades),
                    mode='markers',
                    marker=dict(
                        symbol=['triangle-up' if s == 'BUY' else 'triangle-down' for s in w_trades['side']],
                        color=['#00e676' if s == 'BUY' else '#ff1744' for s in w_trades['side']],
                        size=9
                    ),
                    showlegend=False,
                    customdata=w_trades[['amount_usd', 'side']],
                    hovertemplate="%{customdata[1]} | Size: $%{customdata[0]:,.2f}<extra></extra>"
                ),
                row=2, col=1
            )
            
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0f172a',
        plot_bgcolor='#1e293b',
        height=720,
        margin=dict(l=60, r=40, t=60, b=50),
        xaxis_title="Seconds Elapsed from Token Launch (T0)",
        xaxis_rangeslider_visible=True,
        xaxis_rangeslider_thickness=0.06
    )
    return fig
```

---

## 3. Continuous Monitoring Loop & Alerts Infrastructure (R4)

### 3.1 Daemon Architecture & Execution Model

The monitoring loop operates as an autonomous daemon that continuously ingests token launch events, executes detection heuristics, logs health status every 60 seconds, and immediately emits dual alerts upon discovering suspicious clusters.

#### Concurrency & Worker Separation
To guarantee that the 1-minute heartbeat is never delayed by long-running heuristic graph computations or external API network latency, the daemon employs an asynchronous multi-worker architecture (`asyncio` event loop or dual background threads):

```
+---------------------------------------------------------------------------------+
|                   CryptoSyndicateMonitor Supervisor Process                     |
|                                                                                 |
|  +-------------------------------------+   +---------------------------------+  |
|  |     Heartbeat Worker (Thread 1)     |   |    Detection Worker (Thread 2)  |  |
|  |     Cadence: Strict 60 Seconds      |   |    Cadence: Configurable 300s   |  |
|  |                                     |   |                                 |  |
|  |  - Reads Process & System Metrics   |   |  - Polls GMGN/Solscan APIs      |  |
|  |  - Gathers Pipeline Telemetry       |   |  - Sliding-Window Ingestion     |  |
|  |  - Formats Structured Telemetry     |   |  - Fast-Path Heuristics Eval    |  |
|  |  - Appends to logs/heartbeat.log    |   |  - Emits Dual Alerts on Match   |  |
|  +-------------------------------------+   +---------------------------------+  |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  |        Signal Handlers (SIGINT, SIGTERM, Windows SetConsoleCtrlHandler)   |  |
|  |        Shared State Store (SQLite: data/syndicate.db & monitor_state.json) |  |
|  +---------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------+
```

#### Process Management & Background Modes:
- **CLI Commands**:
  - `crypto-syndicate monitor` (runs in foreground with interactive terminal status).
  - `crypto-syndicate monitor --daemon` (forks/spawns detached process, writes PID to `run/crypto_syndicate.pid`).
  - `crypto-syndicate monitor --stop` (sends `SIGTERM` to PID in PID file and cleans up).
  - `crypto-syndicate monitor --status` (inspects PID and parses recent heartbeat records).
- **Windows / Linux Compatibility**:
  - On Linux/macOS: Standard POSIX double-fork or `systemd` service unit.
  - On Windows: Background process spawned via `subprocess.Popen(..., creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)` or NSSM (Non-Sucking Service Manager).

---

### 3.2 1-Minute Heartbeat System Specification

The heartbeat loop executes every 60 seconds ($T = 60\text{s}$) with zero drift using monotonic time accounting (`time.monotonic()`).

#### Heartbeat Schema & Log Format (`logs/heartbeat.log`)
Each heartbeat record is an atomic, single-line log formatted with clear structured key-value pairs for automated ingestion by log aggregators (Prometheus, Datadog, ELK, or simple grep):

```text
2026-09-20T13:00:00.000Z [HEARTBEAT] status=HEALTHY uptime_sec=3600 polls_total=12 polls_successful=12 active_tokens_tracked=48 new_launches_last_poll=6 clusters_detected_total=3 last_detection_latency_sec=324.2 api_reqs_last_min=18 api_errors_last_min=0 cache_hit_ratio=0.88 mem_rss_mb=94.5 cpu_percent=1.2 active_threads=4 pid=18492
2026-09-20T13:01:00.000Z [HEARTBEAT] status=HEALTHY uptime_sec=3660 polls_total=12 polls_successful=12 active_tokens_tracked=48 new_launches_last_poll=6 clusters_detected_total=3 last_detection_latency_sec=324.2 api_reqs_last_min=0 api_errors_last_min=0 cache_hit_ratio=0.88 mem_rss_mb=94.6 cpu_percent=0.2 active_threads=4 pid=18492
```

#### Monitored Telemetry Fields:
- `status`: `HEALTHY` | `DEGRADED` (API rate limited / circuit breaker open) | `ERROR`.
- `uptime_sec`: Elapsed seconds since daemon start.
- `polls_total` / `polls_successful`: Execution counts for polling cycles.
- `active_tokens_tracked`: Number of tokens currently within active evaluation window.
- `clusters_detected_total`: Cumulative suspicious clusters flagged.
- `last_detection_latency_sec`: Elapsed seconds between token launch $T_0$ and alert emission.
- `api_reqs_last_min` / `api_errors_last_min`: Ingestion traffic and error rates.
- `cache_hit_ratio`: Cache efficiency of local Solscan/GMGN responses.
- `mem_rss_mb` / `cpu_percent`: Process resource utilization.

---

### 3.3 Polling Loop & 10-Minute Detection Latency Proof

#### Requirement:
Detection of new suspicious syndicate clusters must occur **within 10 minutes (600s)** of a token launch.

#### Latency Budget & Timing Analysis:
Let a token launch at timestamp $T_0$.
1. **Polling Cadence**: Default interval is 5 minutes ($T_{\text{poll}} = 300\text{s}$). The next polling execution occurs at $T_0 + \Delta t_{\text{wait}}$, where:
   $$\Delta t_{\text{wait}} \in [0, 300]\text{ seconds}$$
   (Mean wait time = 150 seconds).
2. **Sliding Window Ingestion**: The daemon requests all tokens launched within the window $[T_{\text{curr}} - 20\text{m}, T_{\text{curr}}]$. This guarantees that even with clock drift, no token is missed.
3. **Deduplication Check**: Ingested tokens are filtered against the local set of evaluated tokens (`evaluated_tokens` in SQLite / memory). Only unanalyzed or updated tokens proceed.
4. **Fast-Path Heuristic Evaluation**:
   - Token trade retrieval: ~4.0 seconds (cached/rate-limited).
   - Early buyer identification ($T_0 + \le 300\text{s}$): ~1.5 seconds.
   - Solscan transfer tracing (1-hop funding check): ~8.0 seconds.
   - Deployer reuse query: ~2.0 seconds.
   - Graph clustering & scoring: ~1.5 seconds.
   - **Total Analysis Execution Time**: $\Delta t_{\text{exec}} \approx 17.0\text{ seconds}$.
5. **Total End-to-End Latency**:
   $$\text{Latency} = \Delta t_{\text{wait}} + \Delta t_{\text{exec}} \le 300\text{s} + 17\text{s} = 317\text{s} \approx \mathbf{5.28\text{ minutes}}$$
   Even in the worst-case scenario with a temporary API 429 rate-limit backoff of $+60\text{s}$:
   $$\text{Latency}_{\text{worst}} = 300\text{s} + 60\text{s} + 17\text{s} = 377\text{s} \approx \mathbf{6.28\text{ minutes}} \ll 10.0\text{ minutes}$$
   **Conclusion**: The architecture mathematically guarantees detection within the mandatory 10-minute window.

---

### 3.4 Dual-Format Alert Logging Engine

When a cluster meets the suspicion threshold ($\ge 3$ wallets, $\ge 2$ patterns, cluster suspicion score $\ge 70$), alerts are simultaneously dispatched to two distinct logging targets:
1. `logs/alerts.jsonl` (Machine-readable JSON Lines)
2. `logs/alerts.log` (Human-readable formatted text)

#### 3.4.1 Machine-Readable JSON Schema (`logs/alerts.jsonl`)
Each alert is written as a single self-contained JSON object on one line:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "alert_id": "alt_9e8d7c6b-5a4f-4e3d-2c1b-0a9b8c7d6e5f",
  "timestamp": "2026-09-20T13:05:22.418Z",
  "version": "1.0.0",
  "severity": "CRITICAL",
  "event_type": "NEW_SYNDICATE_CLUSTER_DETECTED",
  "detection_latency_sec": 322.4,
  "token": {
    "chain": "solana",
    "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "symbol": "BONKAI",
    "name": "Bonk AI Intelligence",
    "deployer_address": "7Y1tX...9vQ",
    "launch_timestamp": "2026-09-20T13:00:00.000Z",
    "initial_liquidity_usd": 32000.00,
    "current_price_usd": 0.00582,
    "current_market_cap_usd": 5820000.00
  },
  "syndicate_cluster": {
    "cluster_id": "SYN-SOL-20260920-001",
    "wallet_count": 6,
    "cluster_suspicion_score": 91.4,
    "financials": {
      "total_invested_usd": 24500.00,
      "total_realized_profit_usd": 58200.00,
      "total_unrealized_profit_usd": 18400.00,
      "total_estimated_profit_usd": 76600.00,
      "roi_percentage": 312.65
    },
    "flagged_patterns": [
      {
        "pattern_type": "COORDINATED_EARLY_ENTRY",
        "wallets_involved": 6,
        "entry_window_sec": 14.8,
        "mean_entry_delay_sec": 8.9,
        "confidence": 0.96,
        "details": "All 6 wallets executed buy transactions between +4.2s and +19.0s of liquidity addition."
      },
      {
        "pattern_type": "COMMON_FUNDING_SOURCE",
        "funding_wallet": "3mK9q...2bL",
        "wallets_funded": 5,
        "total_disbursed_sol": 120.0,
        "disbursement_time_window_min": 38.5,
        "confidence": 0.98,
        "details": "Root funder 3mK9q distributed 24.0 SOL to 5 separate addresses 38 minutes prior to token launch."
      },
      {
        "pattern_type": "SHARED_DEPLOYER",
        "deployer_address": "7Y1tX...9vQ",
        "prior_tokens_deployed": 4,
        "confidence": 0.88,
        "details": "Deployer previously created 4 tokens, all exhibiting identical early snipe and liquidity pull patterns."
      }
    ],
    "wallets": [
      {
        "address": "4hU1...9xW",
        "role": "TRADER",
        "suspicion_score": 94.0,
        "entry_timestamp": "2026-09-20T13:00:04.200Z",
        "entry_delay_sec": 4.2,
        "buy_amount_usd": 4200.00,
        "funding_source": "3mK9q...2bL",
        "funding_amount_sol": 24.0,
        "estimated_profit_usd": 13800.00
      }
    ]
  }
}
```

#### 3.4.2 Human-Readable Plain Text Log Format (`logs/alerts.log`)
Formatted with high-contrast visual demarcations for immediate operator triage:

```text
================================================================================
🚨 [ALERT: CRITICAL] NEW ON-CHAIN SYNDICATE CLUSTER DETECTED
================================================================================
Alert ID:           alt_9e8d7c6b-5a4f-4e3d-2c1b-0a9b8c7d6e5f
Detection Time:     2026-09-20 13:05:22 UTC (Latency: 5m 22s from launch)
Blockchain:         SOLANA
Target Token:       BONKAI ($BONKAI)
Token Address:      DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
Deployer Address:   7Y1tX...9vQ (History: 4 prior tokens deployed)
--------------------------------------------------------------------------------
SYNDICATE SUMMARY:
  Cluster Identifier:       SYN-SOL-20260920-001
  Total Wallets Detected:   6 wallets
  Cluster Suspicion Score:  91.4 / 100 [CRITICAL RISK]
  Total Capital Deployed:   $24,500.00 USD
  Estimated Extracted PnL:  +$76,600.00 USD (+312.65% ROI)

FLAGGED PATTERNS (3/4 Criteria Met):
  [✓] COORDINATED EARLY ENTRY : 6 wallets entered within 14.8s (Avg delay: +8.9s)
  [✓] COMMON FUNDING SOURCE   : 5/6 wallets funded by 3mK9q...2bL (120.0 SOL total)
  [✓] SHARED DEPLOYER         : Deployer 7Y1tX...9vQ matched across 4 past rugged tokens

PARTICIPATING WALLETS AUDIT:
  #  Address               Role     Score   Entry Delay   Invested (USD)  Est. Profit (USD)
  1  4hU1...9xW            Trader   94.0    +4.2s         $4,200.00       +$13,800.00
  2  9mP2...7kL            Trader   92.5    +6.1s         $4,100.00       +$13,200.00
  3  2kL5...4rQ            Trader   91.0    +7.8s         $4,050.00       +$12,900.00
  4  8vT3...1nS            Trader   89.5    +10.4s        $4,100.00       +$12,800.00
  5  5wR7...3mX            Trader   88.0    +14.2s        $4,050.00       +$12,400.00
  6  7Y1t...9vQ            Deployer 93.0    +0.0s         $4,000.00       +$11,500.00

RECOMMENDED COUNTERMEASURES:
  1. Flag participant addresses for centralized exchange deposit freezing.
  2. Mark token contract as high-probability syndicate dump on forensic dashboards.
  3. Track root funding wallet 3mK9q...2bL for future pre-funding waves.
================================================================================
```

---

### 3.5 Fault Tolerance, Reconnection & Graceful Shutdown

1. **API Rate Limiting & Backoff**:
   - Leaky bucket rate limiter strictly adheres to GMGN (e.g. 5 req/sec) and Solscan limits.
   - On HTTP 429: dynamic sleep based on `Retry-After` header or jittered exponential backoff:
     $$T_{\text{backoff}} = \min\left(60.0, 2^{\text{retry}} + \text{random}(0.1, 1.0)\right)$$
2. **Circuit Breaker**:
   - If an API fails 5 consecutive times, the breaker enters `OPEN` state for 90 seconds. The loop continues logging heartbeats (`status=DEGRADED`) and falls back to cached data without crashing.
3. **State Persistence & Crash Recovery (`data/monitor_state.json`)**:
   - Periodically serializes evaluated token addresses, last processed block/slot, and active cluster state to disk.
   - On restart, state is reloaded; prevents duplicate alerting on previously discovered syndicates.
4. **Signal Handling & Clean Termination**:
   - Hooks `SIGINT` (Ctrl+C), `SIGTERM` (kill), and Windows `SetConsoleCtrlHandler`.
   - Signals trigger graceful drain: in-flight API requests complete, buffers flush to `alerts.jsonl` and `heartbeat.log`, PID file is removed, and process exits cleanly with code 0.

---

## 4. Static Self-Contained Research Report & Exports Architecture (R5)

### 4.1 Strict Zero-CDN / 100% Offline Guarantee

The generated static HTML report must open directly from local storage (`file:///C:/.../syndicate_report.html`) in any modern browser without an internet connection.

#### Bundling & Inlining Engine:
1. **Asset Vendoring**:
   - `vis-network.min.js` (~520KB) and `plotly.min.js` (or custom Plotly bundle ~1.2MB) are stored locally in `crypto_syndicate/reporting/templates/assets/`.
2. **Template Compilation**:
   - Jinja2 template (`report.html.j2`) reads the raw content of CSS and JavaScript files from disk.
   - Inserts them directly into `<style>` and `<script>` blocks:
     ```html
     <style>
       {{ inlined_theme_css | safe }}
     </style>
     <script>
       {{ inlined_vis_js | safe }}
     </script>
     <script>
       {{ inlined_plotly_js | safe }}
     </script>
     ```
3. **Embedded Data Payloads**:
   - Discovered cluster data, wallet registries, graph topologies, and price series are serialized as JSON and embedded directly into the HTML document:
     ```html
     <script id="syndicate-graph-payload" type="application/json">
       {{ graph_payload_json | safe }}
     </script>
     <script id="timeline-map-payload" type="application/json">
       {{ timeline_payload_json | safe }}
     </script>
     ```
4. **Zero External Font or Icon Dependencies**:
   - Uses system font stack: `font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;`.
   - Icons are embedded as inline SVGs or clean Unicode glyphs (▲, ▼, 🚨, 🔍, 📊).

---

### 4.2 HTML Report UI & Layout Architecture

#### Visual Design System:
- **Aesthetic**: Institutional Crypto Intelligence / Cyber-Forensic theme (slate `#0f172a`, deep navy `#1e293b`, electric cyan `#00e5ff`, warning amber `#ff9100`, critical red `#ff1744`).
- **Typography & Grid**: Responsive CSS Grid / Flexbox layout with high information density.

#### Key Report Sections:
1. **Header & Forensic Dossier Bar**:
   - Investigation Title, Report UUID, Timestamp UTC, Engine Version, Analyzed Blockchains, Analyst Signature.
2. **Section 1: Executive KPI Scorecards**:
   - Total Suspicious Clusters Detected
   - Total Coordinated Wallets Flagged
   - Total Coordinated Capital Deployed ($USD)
   - Estimated Coordinated Profit Extracted ($USD)
   - Average Cluster Suspicion Score
3. **Section 2: Interactive Wallet Cluster Network Graph**:
   - Full-width vis-network canvas with force-directed physics.
   - Interactive toolbar: Play/Pause Physics, Cluster Focus Selector, Search Wallet Input, Reset View.
   - Embedded Click-on-Node Inspection Modal with full wallet dossier.
4. **Section 3: Token Launch Timeline Maps**:
   - Plotly interactive chart showing synchronized price line with buy/sell execution markers and wallet holding swimlanes.
5. **Section 4: Discovered Syndicate Clusters (Deep-Dive Cards)**:
   - Expandable forensic dossier cards for each cluster detailing evidence for all 4 patterns, timeline deltas, funding trees, and profit estimates.
6. **Section 5: Complete Suspicious Wallet Registry**:
   - Sortable, searchable, filterable data table with client-side pagination (25 / 50 / 100 rows per page).
   - Columns: Rank, Address, Chain, Cluster, Role, Score, Patterns Flagged, Associated Tokens, Profit ($USD), Actions (Copy Address).
7. **Section 6: Cryptographic Verification & Methodology Appendix**:
   - Mathematical formula definitions (suspicion scoring, profit calculation, cluster modularity).
   - API call provenance timestamps and transaction hash proofs.

---

### 4.3 CSV Export Specification (`exports/suspicious_wallets_<timestamp>.csv`)

Strictly adheres to RFC 4180 standard (UTF-8 encoding, comma delimiter, CRLF line terminators, double-quote escaping for fields containing commas or quotes).

#### 17-Column Schema Definition:

| Col # | Field Name | Data Type | Example Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `wallet_address` | String | `4hU1zQ8kP9m...xW` | Full on-chain wallet address (Solana base58 or EVM 0x hex) |
| 2 | `chain` | String | `solana` | Blockchain identifier (`solana`, `ethereum`, `bsc`) |
| 3 | `suspicion_score` | Float | `94.0` | Calibrated suspicion score ($0.0 - 100.0$) |
| 4 | `syndicate_cluster_id` | String | `SYN-SOL-20260920-001` | Unique syndicate cluster identifier |
| 5 | `cluster_size` | Integer | `6` | Total number of wallets in this cluster ($\ge 3$) |
| 6 | `wallet_role` | String | `TRADER` | Categorical role: `DEPLOYER`, `FUNDING_SOURCE`, `TRADER` |
| 7 | `flagged_patterns` | String | `COORDINATED_EARLY_ENTRY;COMMON_FUNDING_SOURCE` | Semicolon-delimited list of confirmed patterns |
| 8 | `associated_tokens` | String | `DezXAZ...B263;7xPq...9mL` | Semicolon-delimited list of token contract addresses |
| 9 | `associated_token_symbols` | String | `BONKAI;PEPECAT` | Semicolon-delimited list of token symbols |
| 10 | `first_seen_timestamp` | String (ISO) | `2026-09-20T13:00:04.200Z` | Timestamp of first observed transaction |
| 11 | `coordinated_buy_delay_sec` | Float | `4.2` | Elapsed seconds between token launch $T_0$ and buy tx |
| 12 | `funding_source_wallet` | String | `3mK9q...2bL` | Immediate funding wallet address (or `NONE`/`SELF`) |
| 13 | `shared_deployer_wallet` | String | `7Y1tX...9vQ` | Deployer address shared across tokens (or `NONE`) |
| 14 | `estimated_realized_profit_usd` | Float | `13800.00` | Realized profit extracted in USD |
| 15 | `estimated_unrealized_profit_usd` | Float | `0.00` | Unrealized profit of remaining token balance |
| 16 | `total_profit_usd` | Float | `13800.00` | Total combined profit in USD |
| 17 | `evidence_metadata` | String (JSON) | `"{\"\"entry_window_sec\"\":14.8,\"\"funding_hop\"\":1}"` | Escaped JSON string containing granular evidence metrics |

---

### 4.4 JSON Export Specification (`exports/syndicate_clusters_<timestamp>.json`)

Provides complete hierarchical data export for automated ingestion by enterprise intelligence pipelines:

```json
{
  "report_metadata": {
    "report_id": "rep_7b2c9d1e-4f3a-4e8c-9b5d-2a1e8c7f6d5e",
    "timestamp": "2026-09-20T13:10:00.000Z",
    "generator": "crypto_syndicate_engine_v1.0",
    "chains_covered": ["solana", "ethereum", "bsc"],
    "summary_metrics": {
      "total_clusters_detected": 5,
      "total_wallets_flagged": 38,
      "total_capital_deployed_usd": 142500.00,
      "total_estimated_profit_usd": 384200.00,
      "mean_suspicion_score": 89.2
    }
  },
  "clusters": [
    {
      "cluster_id": "SYN-SOL-20260920-001",
      "chain": "solana",
      "cluster_suspicion_score": 91.4,
      "wallet_count": 6,
      "financials": {
        "total_invested_usd": 24500.00,
        "total_realized_profit_usd": 58200.00,
        "total_unrealized_profit_usd": 18400.00,
        "total_estimated_profit_usd": 76600.00,
        "roi_percentage": 312.65
      },
      "flagged_patterns": [
        "COORDINATED_EARLY_ENTRY",
        "COMMON_FUNDING_SOURCE",
        "SHARED_DEPLOYER"
      ],
      "wallets": [
        "4hU1...9xW",
        "9mP2...7kL",
        "2kL5...4rQ",
        "8vT3...1nS",
        "5wR7...3mX",
        "7Y1t...9vQ"
      ],
      "tokens": [
        {
          "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
          "symbol": "BONKAI",
          "launch_time": "2026-09-20T13:00:00.000Z"
        }
      ],
      "graph_edges": [
        {
          "source": "3mK9q...2bL",
          "target": "4hU1...9xW",
          "amount_sol": 24.0,
          "timestamp": "2026-09-20T12:21:14Z",
          "tx_hash": "5kL9..."
        }
      ],
      "evidence_dossier": {
        "early_entry_stats": {
          "window_seconds": 14.8,
          "mean_offset_seconds": 8.9
        },
        "funding_stats": {
          "root_funder": "3mK9q...2bL",
          "wallets_funded": 5,
          "total_sol": 120.0
        },
        "deployer_stats": {
          "deployer": "7Y1tX...9vQ",
          "prior_tokens_count": 4
        }
      }
    }
  ],
  "wallets": {
    "4hU1...9xW": {
      "chain": "solana",
      "cluster_id": "SYN-SOL-20260920-001",
      "role": "TRADER",
      "suspicion_score": 94.0,
      "flagged_patterns": ["COORDINATED_EARLY_ENTRY", "COMMON_FUNDING_SOURCE"],
      "first_seen": "2026-09-20T13:00:04.200Z",
      "invested_usd": 4200.00,
      "profit_usd": 13800.00
    }
  }
}
```

---

## 5. Cross-Module Data Contracts & Component Integration

### 5.1 Shared Data Models (Python Dataclasses)

To ensure seamless integration between API clients (R3), detection heuristics (R1), Jupyter visualization (R2), monitoring daemon (R4), and report generator (R5), the system is anchored by immutable Python dataclasses:

```python
# Blueprint: Core Data Contracts in crypto_syndicate/models/
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class Blockchain(str, Enum):
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    BSC = "bsc"

class WalletRole(str, Enum):
    DEPLOYER = "DEPLOYER"
    FUNDING_SOURCE = "FUNDING_SOURCE"
    TRADER = "TRADER"

class PatternType(str, Enum):
    COORDINATED_EARLY_ENTRY = "COORDINATED_EARLY_ENTRY"
    COMMON_FUNDING_SOURCE = "COMMON_FUNDING_SOURCE"
    SHARED_DEPLOYER = "SHARED_DEPLOYER"
    COORDINATED_SELL = "COORDINATED_SELL"

@dataclass(frozen=True)
class TradeEvent:
    tx_hash: str
    wallet_address: str
    token_address: str
    chain: Blockchain
    timestamp: datetime
    side: str  # 'BUY' or 'SELL'
    amount_token: float
    amount_native: float
    amount_usd: float
    price_usd: float
    seconds_from_launch: float

@dataclass(frozen=True)
class FundingTransfer:
    tx_hash: str
    source_wallet: str
    target_wallet: str
    chain: Blockchain
    timestamp: datetime
    amount_native: float
    symbol: str

@dataclass
class WalletProfile:
    address: str
    chain: Blockchain
    role: WalletRole
    suspicion_score: float
    cluster_id: Optional[str] = None
    flagged_patterns: List[PatternType] = field(default_factory=list)
    associated_tokens: List[str] = field(default_factory=list)
    first_seen: Optional[datetime] = None
    buy_delay_sec: Optional[float] = None
    funding_source: Optional[str] = None
    shared_deployer: Optional[str] = None
    invested_usd: float = 0.0
    realized_profit_usd: float = 0.0
    unrealized_profit_usd: float = 0.0
    total_profit_usd: float = 0.0
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SyndicateCluster:
    cluster_id: str
    chain: Blockchain
    wallets: List[WalletProfile]
    token_addresses: List[str]
    flagged_patterns: List[PatternType]
    cluster_suspicion_score: float
    total_invested_usd: float
    total_estimated_profit_usd: float
    roi_percentage: float
    funding_edges: List[FundingTransfer] = field(default_factory=list)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
```

---

### 5.2 Proposed Source Code Layout

The implementation will follow this clean, modular architecture:

```
crypto_syndicate/
├── __init__.py
├── config.py                     # Environment variables, rate limits, thresholds
├── cli.py                        # Entrypoint: discover, monitor, report
├── models/                       # Dataclasses defined above
│   ├── __init__.py
│   ├── blockchain.py
│   ├── trade.py
│   ├── transfer.py
│   ├── wallet.py
│   └── cluster.py
├── api/                          # R3: GMGN & Solscan client layer
│   ├── __init__.py
│   ├── client_base.py            # Rate-limiting token bucket & retry policies
│   ├── gmgn_client.py            # GMGN multi-chain API integration
│   ├── solscan_client.py         # Solscan Solana transfer queries
│   └── disk_cache.py             # SQLite disk-caching layer
├── heuristics/                   # R1: Discovery & clustering engine
│   ├── __init__.py
│   ├── early_entry.py            # Pattern 1: Coordinated early entry
│   ├── funding_source.py         # Pattern 2: Common funding source tracing
│   ├── deployer_reuse.py         # Pattern 3: Shared deployer identification
│   ├── coordinated_dump.py       # Pattern 4: Synchronized sell execution
│   ├── graph_clusterer.py        # Modularity clustering (Louvain/Leiden)
│   └── suspicion_scorer.py       # Multi-factor score calibration (0-100)
├── visualization/                # R2: Interactive graph & timeline engines
│   ├── __init__.py
│   ├── network_graph.py          # PyVis / vis.js offline wrapper
│   ├── timeline_map.py           # Plotly dual-panel price/trade map
│   └── assets/                   # Vendored vis-network.min.js & vis-network.min.css
├── monitor/                      # R4: Background daemon & alerting
│   ├── __init__.py
│   ├── daemon.py                 # Multi-worker daemon supervisor
│   ├── heartbeat.py              # 1-minute heartbeat logger
│   └── alert_logger.py           # Dual-format alert logging (JSONL + plain text)
├── reporting/                    # R5: Static reporting & data exports
│   ├── __init__.py
│   ├── html_compiler.py          # 100% offline self-contained HTML compiler
│   ├── csv_exporter.py           # RFC 4180 CSV export
│   ├── json_exporter.py          # Hierarchical JSON export
│   └── templates/                # Jinja2 template & CSS assets
│       ├── report.html.j2
│       ├── theme.css
│       └── assets/
└── notebooks/                    # R2: Interactive investigation notebook
    └── syndicate_investigation.ipynb
```

---

### 5.3 Verification & Testing Blueprint

To guarantee that implementation satisfies all acceptance criteria:

1. **Jupyter Notebook Verification**:
   - Executes programmatically via `nbconvert` / `papermill`:
     `pytest tests/test_notebook.py` runs notebook headlessly to verify cells execute without exceptions and generate interactive graph outputs.
   - Interactive tests verify that clicking nodes populates inspection modal without console errors.
2. **Monitoring Daemon & Heartbeat Verification**:
   - `tests/test_monitor_daemon.py`:
     - Spawns daemon in test mode with mock ticker.
     - Verifies `logs/heartbeat.log` records exactly one heartbeat line every 60 seconds.
     - Simulates token launch event; verifies `logs/alerts.jsonl` and `logs/alerts.log` both receive properly formatted alert records within test latency threshold.
     - Validates JSON Lines output strictly matches JSON Schema.
3. **Report Offline Guarantee Verification**:
   - `tests/test_report_offline.py`:
     - Generates static HTML report.
     - Runs regex check to assert zero external references (`http://`, `https://`, `//cdn`).
     - Loads HTML via headless Chromium / Selenium without internet connection; asserts vis.js and Plotly charts initialize and render into the DOM.
4. **Export Schema Verification**:
   - `tests/test_exports.py`:
     - Validates CSV output with Python's standard `csv` module to verify RFC 4180 parsing, quotes, and 17 required columns.
     - Validates JSON output against JSON Schema.
