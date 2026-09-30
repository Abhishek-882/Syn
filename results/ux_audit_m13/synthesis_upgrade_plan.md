# Synthesis & Upgrade Plan — M13 (Vector Store & Semantic Wallet Memory)

## Executive Synthesis of Phase 1 (Three-Agent Browser Audit)

Across 3 independent browser audit agents executing live on the station (`http://localhost:8000/web/syndicate_3d_visualizer.html`), a total of **105 discrete interaction steps** were executed and **108 full-resolution screenshots** were captured across viewports:
- **Agent 1 (Power User & Shortcuts)**: 35 / 35 PASS (100%), 38 screenshots in `results/ux_audit_m13/agent_1/`
- **Agent 2 (Dossier & Cross-Referencing)**: 35 / 35 PASS (100%), 35 screenshots in `results/ux_audit_m13/agent_2/`
- **Agent 3 (3D Graph & Search Specialist)**: 35 / 35 PASS (100%), 35 screenshots in `results/ux_audit_m13/agent_3/`

### Visual Benchmark Grounding
The upgrades are directly modeled on the two high-density concept artworks:
- **`syndicate_vector_ui`**: Multi-cluster 3D connectome with luminous dashed vector arcs, top telemetry HUD chip `[VECTOR DATABASE: N STORED]`, and dense monospace telemetry.
- **`similar_wallets_dossier`**: Glassmorphic curatorial plaque with circular SVG cosine similarity gauge (`91.4% MATCH`), discrete tactile slider `[Show: 3 | 5 | 10 | 20]`, pattern badges, and micro sparklines.

---

## Top 5 Prioritized Upgrades for M13

### 1. Glassmorphic "Similar Wallets" Section in Dossier
- **Insertion Location**: In `#entity-view`, immediately following the Jito metrics grid (`#dossier-jito-signals`) and directly preceding `.plaque-actions`.
- **Visual Design**: Obsidian frosted card with glowing cyan border, circular cosine similarity score badge (`[91% MATCH]` with color thresholding: green >80%, yellow >50%, red <50%), syndicate badge (`SYND-0042`), and behavioral pattern tags.
- **Kinetic Interaction**: Clicking any similar wallet immediately invokes `focusOnEntity(targetAddr)` with a smooth 800ms kinetic camera glide.

### 2. User-Configurable Tactile Result Slider (`3 | 5 | 10 | 20`)
- **Location**: In the header of the "Similar Wallets" dossier section.
- **Specification**: Range slider with discrete step snapping to values `[3, 5, 10, 20]` and live count badge.
- **Behavior**: Re-renders visible similar wallet cards dynamically without page reload.

### 3. Telemetry HUD `[VECTORS: N STORED]` Counter
- **Location**: In `.telemetry-hud` alongside `JITO BUNDLES` and `SYNDICATES`.
- **Display**: `[VECTORS: N STORED]` in luminous cyan (`#00f0ff`) representing total vectors stored in the Qdrant database.

### 4. 3D Inter-Cluster Dashed Similarity Spline Arcs
- **Visual Affordance**: When an entity is selected in the dossier, draw dynamic dashed spline arcs (`THREE.LineDashedMaterial` with color `#00f0ff`) connecting the focused neuron to its top-k similar neurons across other clusters.
- **Pulsing Halo**: Render subtle arrival pulse sprites on the target similar neurons.

### 5. Similarity Search Prefix in Command Deck (`~0x...` / `similar:...`)
- **Functionality**: When an investigator types `~` or `similar:` followed by a wallet address or symbol into `#radar-search-input`, the visualizer filters and highlights the most behaviorally similar entities in both the radar feed and 3D space.

---

## Zero-Regression Verification Gate
- All 349 existing repository unit, E2E, and adversarial tests must continue to pass 100%.
- New module `src/crypto_syndicate/vector_store.py` will have comprehensive tests in `tests/unit/test_vector_store.py`.
