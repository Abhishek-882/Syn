# ⚡ Crypto Syndicate Sentinel Platform

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Abhishek-882/Syn)
![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Anti-Vibe Design](https://img.shields.io/badge/UI-Anti--Vibe%202D-purple)

An autonomous on-chain syndicate research and real-time meme token creation sentry platform on Solana. Built with a high-density, Bloomberg/Arkham-style 2D live terminal adhering strictly to `/anti-vibe-design` principles (zero 3D WebGL overhead, instantaneous `< 200ms` rendering).

---

## 🚀 1-Click Cloud Deployment (Render)

Deploy this application directly to Render with zero configuration:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Abhishek-882/Syn)

Render automatically detects `render.yaml`, provisions the Python web service, builds runtime dependencies from `requirements.txt`, and binds to `0.0.0.0:$PORT` with health probe monitoring on `/healthz`.

---

## 🎯 Key Architectural Capabilities

```
┌────────────────────────────────────────────────────────────────────────┐
│               RECURSIVE FUND LINEAGE & SENTRY ENGINE                   │
└────────────────────────────────────────────────────────────────────────┘
          │
          ▼
   [Root Treasury] (150 SOL)
          │  Outgoing transfer (5.0 SOL)
          ▼
   [Member Wallet 1] (Hop 1)
          │  Outgoing transfer (0.5 SOL)
          ▼
   [Child Deployer] (Hop 2)
          │  Outgoing transfer (25.0 SOL)
          ▼
   [⚡ Dynamic Treasury Anchor] (≥20 SOL / ~$3,000 USD)
          │  Promoted to Primary Anchor! Resets descent to Hop 0
          ▼
   [Child Deployer Under Whale Anchor] (Hop 1)
          │
          ├── Balance ≥ $5.00 USD (e.g. 0.08 SOL = $12) ──► [READY DEPLOYER WATCHLIST]
          │                                                            │
          │                                                            ▼
          │                                                  [TOKEN CREATION SENTINEL]
          │                                                  - Intercepts Pump.fun / Raydium
          │                                                  - 1-Click DexScreener & GMGN
          │                                                            │
          │                                                            ▼
          │                                                [STICKY GOLDEN SPOTLIGHT BANNER]
          │                                                [DUAL-TONE WEB AUDIO CHIME]
          │                                                [HTML5 DESKTOP PUSH NOTIFICATION]
          │
          └── Balance < $5.00 USD (e.g. 0.01 SOL = $1.50) ──► [DUST MONITOR]
```

### 1. Multi-Hop Ingress & Dynamic Treasury Anchor Engine
* **5-Hop Recursive Descent**: Automatically tracks outgoing transfers from known syndicate wallets up to 5 hops deep, seamlessly adopting funded recipient wallets into the syndicate connectome.
* **Dynamic Treasury Anchor Rule**: Any intermediate or child wallet accumulating $\ge 20\text{ SOL}$ ($\sim \$3,000\text{ USD}$) is dynamically promoted to a primary treasury anchor, re-centering a fresh 5-hop descent tree.
* **Deployer Watchlist Gate ($\ge \$5.00\text{ USD}$)**: Gated monitoring segregates qualified deployers with sufficient creation fees ($\sim 0.03\text{ SOL}$) into active watchlists (`READY`), while smaller accounts remain in passive `DUST`.

### 2. Real-Time Meme Token Creation Sentinel
* **Protocol Interception**: Actively monitors transaction streams for Pump.fun `Create`, Raydium Pool v4/CPMM, and SPL Token `InitializeMint` instructions originating from watched syndicate deployers.
* **Multi-Gateway 1-Click Execution**:
  * **📈 DexScreener**: Direct links to verified pumpswap pairs with active liquidity (e.g. `$ZLONG`).
  * **🪐 GMGN**: Direct 1-click execution to `https://gmgn.ai/sol/token/{mint_address}`.
  * **⚡ Photon**: Instant LP routing via `https://photon-sol.tinyastro.io/en/lp/{mint_address}`.
  * **💊 Pump.fun**: Native bonding curve execution on `https://pump.fun/{mint_address}`.

### 3. Clean 2D Live Terminal Platform (`web/syndicate_terminal.html`)
* **Anti-Vibe Design**: High-density 3-column layout (Deployers, Live Activity Tape, 2D SVG Lineage DAG + Node Inspector) with zero WebGL/Three.js bloat.
* **Persistent Notification Controls**: Top-header toggleable `[🔔 NOTIFICATIONS: ACTIVE / 🔕 MUTED]` backed by `localStorage`.
* **Acoustic Feedback**: Web Audio API dual-tone synthetic chime (880Hz $\to$ 1320Hz) alerting whenever any syndicate member creates a meme token.

---

## 🛠 Local Setup & Running

### Option A: Direct Python Execution

```bash
# Clone the repository
git clone https://github.com/Abhishek-882/Syn.git
cd Syn

# Install dependencies
pip install -r requirements.txt

# Start the live terminal server
python src/crypto_syndicate/server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### Option B: Docker Container

```bash
# Build the production image
docker build -t crypto-syndicate .

# Run the container
docker run -p 8000:8000 -e PORT=8000 crypto-syndicate
```

---

## 🌐 API & Endpoint Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the Clean 2D Syndicate Live Terminal (`web/syndicate_terminal.html`) |
| `GET` | `/healthz` | Health check probe endpoint for cloud runtimes (Render, Docker, K8s) |
| `GET` | `/api/syndicates` | Complete JSON snapshot of active clusters, deployer watchlist, and launches |
| `GET` | `/events/stream` | Server-Sent Events (SSE) real-time event stream pushing live deltas |

---

## 📁 Repository Structure

```
├── .env.example                     <- Environment template
├── Dockerfile                       <- Production container build
├── Procfile                         <- PaaS process runner
├── README.md                        <- Documentation
├── render.yaml                      <- Render Blueprint specification
├── requirements.txt                 <- Production dependencies
├── pyproject.toml                   <- Package configuration
├── src/crypto_syndicate/
│   ├── server.py                    <- Threaded HTTP + SSE live streaming server
│   ├── ground_truth_loader.py       <- Authoritative syndicate wallet/token loader
│   ├── lineage_sentry.py            <- 5-hop descent & 20 SOL anchor engine
│   ├── token_sentinel.py            <- Meme token creation interceptor & DEX links
│   ├── scanner.py                   <- Live syndicate scanner loop
│   └── api/
│       ├── fixtures.py              <- Offline test fixtures
│       └── models.py                <- Core dataclass data models
├── results/                         <- Ground-truth syndicate databases & state
│   ├── syndicate_identities.json    <- 94 syndicates, 805 wallets, 67 tokens
│   ├── wallets.csv                  <- Qualified deployers list
│   └── live_alerts.json             <- Active meme token alerts
└── web/
    └── syndicate_terminal.html      <- Clean 2D live terminal web app
```

---

## 🛡 Security & Best Practices

* Sensitive keys and credentials (`.env`, `GMGN_API_KEY`, `SOLSCAN_API_KEY`) are excluded via `.gitignore`.
* Zero 3D canvas overhead guarantees accessibility and instant loading on all mobile and desktop devices.
* Health check probes on `/healthz` allow continuous zero-downtime rolling deploys.

---

## 📄 License
MIT License.
