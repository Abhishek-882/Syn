# Production MQL Engineering Skill (Local Snapshot)
Refer to: C:\Users\Asus\.gemini\config\skills\production-mql-engineering\SKILL.md
Core methodology:
- MQL5 EA Architecture & Bar access semantics (ArraySetAsSeries, shift >= 1)
- Handle management: Global initialization in OnInit, release in OnDeinit, limit < 60 handles (<12% MT5 limit)
- Strategy brain voting contract (+1, -1, 0)
- Execution microstructure, stop level guards, pip normalization for XAUUSD (_Digits == 2, _Point == 0.01)
- Zero-lookahead bias prevention, elimination of repainting indicators
