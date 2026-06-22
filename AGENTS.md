# AGENTS.md — sunsponge-capture

<!-- RHOBEAR-CANON:OPERATING-DISCIPLINE v1 — source of truth: rhobear-app/docs/canon/OPERATING-DISCIPLINE.md -->
## OPERATING DISCIPLINE — RHOBEAR CANON v1 (every agent, every spawn)
Binds you whether spun up as worker, crew agent, Pi step, or courier. Read first.

1. CODEGRAPH FIRST. Before grep/glob/find/read-to-locate, query CodeGraph
   (code-graph-mcp) — it has the symbol/dependency/route answer at a fraction of the
   tokens. Grep/glob are the FALLBACK. If CodeGraph is unreachable, say so in one
   line, then fall back.
2. ONE AGENT. ONE THREAD. ONE STEP. Never spawn subagents. No Agent/Task fan-out, no
   parallel instances in-thread. Work like Pi: smallest next step toward the goal,
   finish it, then the next. No speculative scaffolding. If the job is bigger than
   one agent should hold, STOP and hand back a note — don't recruit.
3. LEAN TOKENS. Let RTK-G (rtk) compress noisy tool output. Speak caveman-terse by
   default; keep every path/command/error string exact. (Exception: reporting to the
   owner in a planning thread — stay readable.)
4. KNOW WHERE YOU ARE. You are one of many agents across local + 3 VMs (GCP
   chat-brain-1, Hetzner rhobear-vps, Azure rhobear-bld-01). Consult docs/canon/
   before assuming where anything lives. One project = one repo.
5. STAY IN YOUR LANE. Do only the lane you were given. Out-of-lane → flag, don't absorb.
<!-- /RHOBEAR-CANON -->

This repo = rested-state bulk website screenshot capture tool (Playwright) (one lane).