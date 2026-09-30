# Task Assignment: Suspicious Wallet Discovery Heuristics & Cluster Algorithms

## Identity
- Archetype: teamwork_preview_explorer
- Working Directory: C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_heuristics_1

## Objective
Investigate, design, and formulate the detection algorithms, heuristics, graph clustering methodologies, and suspicion scoring model for Automated Suspicious Wallet Discovery (R1) across multi-chain launches without seed wallets.

## Authoritative Requirements
You MUST read: C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md

## Scope & Focus
1. Non-seed discovery mechanics: How to ingest new token launch pools (from GMGN/Solscan) across chains, pull initial trade history and transfer logs, and discover candidate wallets.
2. The 4 Mandatory Pattern Types:
   - Coordinated early entry: wallets buying the same new token within minutes of launch.
   - Common funding source: wallets funded by the same source wallet before coordinated buys.
   - Shared deployers: wallets connected to the same deployer wallet across multiple tokens.
   - Coordinated sells/dumps: wallets dumping tokens within the same time window.
3. Graph clustering algorithms:
   - Community detection / connected components / Louvain / DBSCAN to cluster related wallets into suspected syndicates.
   - Acceptance criteria: at least 5 clusters discovered, each with >= 3 wallets, each with >= 2 pattern types flagged.
4. Suspicion scoring and evidence formatting:
   - Multi-factor suspicion score (0-100 or 0.0-1.0) with weighted contributions.
   - Evidence metadata dictionary for each wallet and cluster.
   - Estimated coordinated profit calculation methodology (buys vs sells vs remaining holdings).

## Scope Boundaries
- Do NOT write implementation source code files in the project workspace.
- Do NOT run build/test commands.
- Focus on algorithmic analysis, mathematical/heuristic formulation, edge cases, and producing the report.

## Output Requirements
Write your detailed algorithmic analysis to:
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_heuristics_1\heuristics_report.md`
Write your completion handoff report to:
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_heuristics_1\handoff.md`

## Completion Criteria
When your reports are written, send a completion message back to the orchestrator referencing the file paths.

## 2026-09-20T12:58:30Z
You are survey_explorer_heuristics_1. Your working directory is C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_heuristics_1. Read your assignment at C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_heuristics_1\DISPATCH.md and the authoritative requirements at C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md. Formulate the non-seed discovery heuristics, the 4 mandatory pattern types, graph clustering algorithms, suspicion scoring, and profit calculation models. Output your findings to heuristics_report.md and handoff.md in your working directory. Send a message to the caller when done.
