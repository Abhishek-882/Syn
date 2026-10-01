# Rule: Mandatory Persistence of Agent Work, Reports & Audit Records

1. **Persistent Output Mandate**: Every agent, subagent, and orchestrator must save all intermediate and final outputs (research dossiers, strategy specifications, code implementations, reasoning traces, and QA audit certificates) directly to persistent files on disk. Never leave work only in ephemeral chat messages or temporary buffers.
2. **Continuous Milestone Updates**: As work progresses, status files (such as `progress.md`, `plan.md`, `BRIEFING.md`, or wave dispatch dossiers) must be updated in real time at every milestone, not just at final completion.
3. **Structured Directory Organization**:
   - Strategy definitions, quantitative research, and mathematical models belong in `research/`.
   - Subagent logs, execution plans, handoffs, and swarm transcripts belong in `.agents/`.
   - Verification reports, backtest logs, and compiler validation receipts belong in `results/`.
4. **Historical Record Preservation**: Never overwrite previous milestone records without archiving or maintaining versioned sections. Future agent sessions and human operators must be able to trace the exact rationale, defects found, and solutions applied at each stage.
5. **Doubt & Decision Logging**: Any doubts raised, user clarifications received, and multi-agent debate resolutions must be formally recorded in a dedicated audit or decision log file for future reference.
