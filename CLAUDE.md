# CLAUDE.md (AIOS Workspace Guide)

## Core Development Commands
- **Install dependencies:** `pip install -e .` or `./.venv/bin/pip install -e .`
- **Run Workflow Engine:** `python3 -m runtime.cli -w workflows/<pipeline>.yaml -s .`
- **Verify test suites:** `./.venv/bin/pytest` or python3 unit-testing command.

## Quality & Style Guidelines
- Keep critical computational loops (like DSP filtering) 100% allocation-free to prevent GC pauses.
- Never let `NaN` or `Infinity` propagate through digital feedback systems (always reset/clamp states).
- Flush subnormal numbers smaller than $10^{-30}$ to cleanly protect CPU latency.

## Recent Technical Decisions
- Completed stage document_filter_api using agent technical_writer
- Completed stage design_dsp_filter using agent dsp_engineer
- Completed stage define_requirements using agent product_owner

## Active Plugins
- **Context Mode:** Enabled (raw tool output sandbox filtering).
- **Claude Mem:** Enabled (local SQLite persistence of decisions & lifecycle triggers).
- **GSD Orchestrator:** Enabled (autonomous task decomposition & sub-agent validation).

*Last updated: 2026-05-30 14:35:40*
