---
trigger: always_on
---

# Agent Quota Recovery Rules

## When Any Subagent Hits RESOURCE_EXHAUSTED (429)

1. **Kill immediately** — use `manage_subagents kill` on all errored agents. Do not leave them in the list.
2. **Do NOT wait idle** — quota resets take 4+ hours. Continue working directly or with a different agent type.
3. **Try a fresh spawn** of the same type — a new session sometimes avoids the per-session quota.
4. **teamwork_preview and DeepCoder have separate quotas** — if one is exhausted, try the other.
5. **Build directly** using `write_to_file` and `run_command` tools if both agent types are quota-limited.
6. **Always update** `.agents/skills/crypto-syndicate-resume/SKILL.md` milestone checklist after significant progress so the next session resumes without re-reading conversation history.

## When an Agent Fails With "unknown model key MODEL_PLACEHOLDER_*"

This means the agent session's internal model config is permanently corrupted.
- Kill it immediately — it cannot be restarted.
- Spawn a fresh agent of the same type instead.

## When Any Agent Stops, Drops Idle, or Fails (Give an Immediate Retry)

If any subagent, worker, or orchestrator stops, drops into idle prematurely, encounters a stream interruption, or pauses unexpectedly:
1. **Immediate Retry**: Send a revival message via `send_message` to resume the agent's work.
2. **Never leave it stalled**: If an agent died or cannot be revived, cleanly terminate it and immediately spawn a fresh replacement with the resume context.
3. **Maintain Continuous Execution**: Never let tasks remain blocked or abandoned when an interruption occurs.

## Crypto Syndicate Project — Session Context

This project builds an on-chain syndicate research system.
Full resume context is in: `.agents/skills/crypto-syndicate-resume/SKILL.md`

Read that file at the START of any session involving this project.