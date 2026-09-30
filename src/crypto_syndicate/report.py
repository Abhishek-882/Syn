"""M5 - Report Generation: CSV, JSON, and self-contained HTML with inline D3.js."""

import csv
import json
import logging
import os
import datetime
from typing import Any, Dict, List, Optional, Set

from crypto_syndicate.api.models import SyndicateCluster
from crypto_syndicate.d3_fallback import get_d3_source

logger = logging.getLogger("crypto_syndicate.report")


def _fetch_d3() -> str:
    """Fetch sanitized offline D3 v7 source without external CDN dependencies."""
    try:
        return get_d3_source()
    except Exception as exc:
        logger.warning("Could not load bundled D3.js (%s). Using fallback.", exc)
        return '/* offline-d3-v7 fallback */\nconsole.warn("D3 minimal fallback");'


def _cluster_to_dict(c: Any) -> Dict[str, Any]:
    if hasattr(c, "to_dict"):
        return c.to_dict()
    if isinstance(c, dict):
        return dict(c)
    return {}


def generate_report(wallets: List[Dict[str, Any]], clusters: List[Any], output_dir: str = ".", output_file: Optional[str] = None) -> Dict[str, str]:
    if output_file:
        if output_file.endswith(".html"):
            derived = os.path.dirname(output_file)
            if derived:
                output_dir = derived
        html_path = output_file
    else:
        html_path = os.path.join(output_dir, "report.html")

    os.makedirs(output_dir, exist_ok=True)
    html_dir = os.path.dirname(html_path)
    if html_dir:
        os.makedirs(html_dir, exist_ok=True)

    paths = {}
    paths["csv"] = _write_csv(wallets, output_dir)
    paths["json"] = _write_json(clusters, output_dir)
    paths["html"] = _write_html(wallets, clusters, html_path)
    logger.info("Report written: csv=%s, json=%s, html=%s", paths["csv"], paths["json"], paths["html"])
    return paths


def _write_csv(wallets: List[Dict[str, Any]], output_dir: str) -> str:
    path = os.path.join(output_dir, "wallets.csv")
    fieldnames = [
        "wallet_address",
        "chain",
        "suspicion_score",
        "patterns_flagged",
        "associated_tokens",
        "estimated_profit_usd",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        sorted_wallets = sorted(wallets or [], key=lambda x: x.get("suspicion_score", 0.0), reverse=True)
        for w in sorted_wallets:
            pats = w.get("patterns_flagged") or w.get("flagged_patterns") or []
            tkns = w.get("tokens_traded") or w.get("associated_tokens") or []
            writer.writerow({
                "wallet_address": w.get("wallet_address", ""),
                "chain": w.get("chain", "sol"),
                "suspicion_score": round(float(w.get("suspicion_score", 0.0)), 2),
                "patterns_flagged": "|".join(pats),
                "associated_tokens": "|".join(tkns),
                "estimated_profit_usd": round(float(w.get("estimated_profit_usd", 0.0)), 2),
            })
    return path


def _write_json(clusters: List[Any], output_dir: str) -> str:
    path = os.path.join(output_dir, "clusters.json")
    serialized = [_cluster_to_dict(c) for c in (clusters or [])]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2, default=str)
    return path


def _build_graph_data(wallets: List[Dict[str, Any]], clusters: List[Any]) -> Dict[str, Any]:
    wallet_to_cluster: Dict[str, str] = {}
    for c in (clusters or []):
        cdict = _cluster_to_dict(c)
        cid = cdict.get("cluster_id", "unclustered")
        wlist = cdict.get("wallets") or cdict.get("members") or []
        for w in wlist:
            wallet_to_cluster[w] = cid

    nodes = [
        {
            "id": w.get("wallet_address", ""),
            "score": float(w.get("suspicion_score", 0.0)),
            "patterns": list(w.get("patterns_flagged") or w.get("flagged_patterns") or []),
            "chain": w.get("chain", "sol"),
            "cluster": wallet_to_cluster.get(w.get("wallet_address", ""), "unclustered"),
            "profit": float(w.get("estimated_profit_usd", 0.0)),
        }
        for w in (wallets or [])
        if w.get("wallet_address")
    ]

    token_to_wallets: Dict[str, List[str]] = {}
    for w in (wallets or []):
        tokens = w.get("tokens_traded") or w.get("associated_tokens") or []
        for t in tokens:
            token_to_wallets.setdefault(t, []).append(w.get("wallet_address", ""))

    links = []
    seen: Set = set()
    for t, wlist in token_to_wallets.items():
        for i in range(len(wlist)):
            for j in range(i + 1, min(i + 5, len(wlist))):
                a, b = wlist[i], wlist[j]
                if a == b:
                    continue
                key = tuple(sorted([a, b]))
                if key not in seen:
                    seen.add(key)
                    links.append({"source": a, "target": b, "type": "co_buy"})

    return {"nodes": nodes, "links": links}


def _write_html(wallets: List[Dict[str, Any]], clusters: List[Any], html_path: str) -> str:
    d3_src = _fetch_d3()
    graph_data = _build_graph_data(wallets, clusters)
    top_clusters = sorted(
        [_cluster_to_dict(c) for c in (clusters or [])],
        key=lambda x: float(x.get("suspicion_score", 0.0)),
        reverse=True,
    )[:20]

    table_rows = ""
    for i, c in enumerate(top_clusters):
        wlist = list(c.get("wallets") or c.get("members") or [])
        preview = ", ".join(addr[:10] + "..." for addr in wlist[:3])
        if len(wlist) > 3:
            preview += "..."
        pats = c.get("flagged_patterns") or c.get("patterns_flagged") or []
        table_rows += (
            f'<tr><td>{i+1}</td>'
            f'<td style="font-family:monospace;font-size:11px">{c.get("cluster_id","")[:24]}</td>'
            f'<td><b>{float(c.get("suspicion_score", 0.0)):.1f}</b></td>'
            f'<td>{len(wlist)}</td>'
            f'<td>{", ".join(pats)}</td>'
            f'<td style="font-family:monospace;font-size:10px">{preview}</td>'
            f'<td>${float(c.get("estimated_profit_usd", 0.0)):,.0f}</td></tr>\n'
        )

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    graph_json = json.dumps(graph_data)

    js_viz = r"""
const width = document.getElementById("graph-container").clientWidth || 900;
const height = 600;
const color = d3.scaleOrdinal(d3.schemeTableau10);
const clusterIds = [...new Set(graphData.nodes.map(d => d.cluster))];

const legend = document.getElementById("legend");
if (legend) {
  clusterIds.slice(0, 10).forEach((cid, i) => {
    const el = document.createElement("div"); el.className = "legend-item";
    const dot = document.createElement("div"); dot.className = "legend-dot";
    dot.style.background = color(i);
    const span = document.createElement("span"); span.textContent = cid.slice(0, 20);
    el.appendChild(dot); el.appendChild(span); legend.appendChild(el);
  });
}

const svg = d3.select("#graph-container").append("svg").attr("width","100%").attr("height", height);
const simulation = d3.forceSimulation(graphData.nodes)
  .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(80))
  .force("charge", d3.forceManyBody().strength(-120))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => Math.max(6, d.score / 10 + 4)));

const link = svg.append("g").selectAll("line").data(graphData.links).join("line")
  .attr("stroke", d => d.type === "funding" ? "#f0a050" : "#5580aa")
  .attr("stroke-opacity", 0.5).attr("stroke-width", d => d.type === "funding" ? 2 : 1);

const node = svg.append("g").selectAll("circle").data(graphData.nodes).join("circle")
  .attr("r", d => Math.max(5, d.score / 10 + 3))
  .attr("fill", d => color(clusterIds.indexOf(d.cluster)))
  .attr("stroke", "#fff").attr("stroke-width", 0.5)
  .call(d3.drag()
    .on("start", (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
    .on("end", (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

const tooltip = document.getElementById("tooltip");
node.on("mouseover", (event, d) => {
  if (!tooltip) return;
  tooltip.style.display = "block";
  tooltip.innerHTML = "<b>" + d.id.slice(0,16) + "...</b><br>Score: " + d.score.toFixed(1)
    + "<br>Chain: " + d.chain + "<br>Patterns: " + (d.patterns.join(", ") || "none")
    + "<br>Cluster: " + d.cluster.slice(0,20)
    + "<br>Est. Profit: $" + d.profit.toLocaleString();
}).on("mousemove", event => {
  if (!tooltip) return;
  tooltip.style.left = (event.pageX + 12) + "px"; tooltip.style.top = (event.pageY - 10) + "px";
}).on("mouseout", () => { if (tooltip) tooltip.style.display = "none"; });

simulation.on("tick", () => {
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("cx", d => d.x).attr("cy", d => d.y);
});
"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Crypto Syndicate Research Report</title>
<style>
  body {{font-family:-apple-system,sans-serif;background:#0f0f14;color:#e0e0e0;margin:0;padding:20px}}
  h1{{color:#7eb8f7}}h2{{color:#a0c8ff;border-bottom:1px solid #333;padding-bottom:8px}}
  #graph-container{{width:100%;height:600px;border:1px solid #333;border-radius:8px;background:#1a1a24;margin:20px 0}}
  .tooltip{{position:absolute;background:rgba(0,0,0,.85);color:#fff;padding:10px 14px;border-radius:6px;
            font-size:12px;pointer-events:none;border:1px solid #444;max-width:300px}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  th{{background:#1e2030;padding:10px 8px;text-align:left;color:#7eb8f7;border-bottom:2px solid #333}}
  td{{padding:8px;border-bottom:1px solid #222}}tr:hover td{{background:#1a1a28}}
  .stat{{display:inline-block;background:#1e2030;border-radius:8px;padding:14px 24px;margin:8px;text-align:center}}
  .stat-num{{font-size:28px;font-weight:bold;color:#7eb8f7}}.stat-label{{font-size:12px;color:#888}}
  #legend{{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}}
  .legend-item{{display:flex;align-items:center;gap:6px;font-size:12px}}
  .legend-dot{{width:12px;height:12px;border-radius:50%}}
</style></head><body>
<h1>🔍 Crypto Syndicate Research Report</h1>
<p style="color:#888">Generated: {ts}</p>
<div>
  <div class="stat"><div class="stat-num">{len(wallets or [])}</div><div class="stat-label">Suspicious Wallets</div></div>
  <div class="stat"><div class="stat-num">{len(clusters or [])}</div><div class="stat-label">Syndicates Found</div></div>
  <div class="stat"><div class="stat-num">{len(graph_data["nodes"])}</div><div class="stat-label">Graph Nodes</div></div>
  <div class="stat"><div class="stat-num">{len(graph_data["links"])}</div><div class="stat-label">Relationships</div></div>
</div>
<h2>Wallet Relationship Graph</h2>
<div id="legend"></div>
<div id="graph-container"></div>
<div class="tooltip" id="tooltip" style="display:none"></div>
<h2>Top Clusters (Suspicious Syndicates)</h2>
<table><thead><tr><th>#</th><th>Cluster ID</th><th>Score</th><th>Wallets</th><th>Patterns</th><th>Members</th><th>Est. Profit</th></tr></thead>
<tbody>{table_rows}</tbody></table>
<script>{d3_src}</script>
<script>const graphData = {graph_json};\n{js_viz}</script>
</body></html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("HTML report written: %s", html_path)
    return html_path
