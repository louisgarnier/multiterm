## Project: MultiTerm
One-liner: A Mac desktop app (Electron + DMG) that hosts multi-project, multi-terminal Claude Code workflows with status-aware visual indicators, port management, and a per-project lifecycle (dev → prod → archived).
Current stage: Step 2 — PRD Locked (2026-04-28). Next: Step 3 — Architecture.

## Non-goals — these are LAW, do not implement
- NG1: Code editing surface (not a VS Code/Cursor replacement; no editor pane)
- NG2: Cloud deployment integration (Vercel, Netlify, AWS) — defer to v2
- NG3: In-app multi-user / team / collaborative features (shared sessions, sync, comments). Single user per installation. Distributing the binary to others is unrelated and unrestricted.
- NG4: Cross-platform (Windows/Linux) — macOS only at start; nothing in stack blocks future port
- NG5: OS-level notifications, banners, sounds, or dock-bouncing — visual indicators only
- NG6: Skills/agents launcher palette — Claude Code's `/` discovery is sufficient
- NG7: L3 transcript activity feed — defer
- NG8: Multi-command per PROD project — one run command per PROD project for v1
- NG9: Auto-launch PROD apps on app startup — manual launch only
- NG10: Terminal templates / saved launch configurations — plain shell only
- NG11: Auto-kill orphan processes without explicit user click — all process termination is user-initiated
- NG12: Auto-import recent Claude projects on first launch — manual addition only
- NG13: *Autonomous* modification of user files by MultiTerm itself. The app never edits CLAUDE.md, project source, transcripts, or other user data on its own. Only writes to its own config (`~/Library/Application Support/MultiTerm/`) and logs. Does NOT restrict the user: editing CLAUDE.md, browsing `~/Claude/`, and Claude Code's normal read/write access in spawned terminals all remain unrestricted. Opt-in hook merge per FR-14a is the one explicit user-consented exception.

## Stack
- Frontend: [fill from architecture]
- Backend: [fill from architecture]
- Database: [fill from architecture]

## Session start — read these files in order before any code
1. `docs/project/config/build-log.md` — current stage + blockers
2. `docs/project/config/codebase.md` — existing modules
3. `workflow/ERRORS.md` — known problem areas
4. `workflow/ADR.md` — architectural decisions already made
5. `docs/project/config/epics/ACTIVE.md` — current story (once epics are defined)

## Sealed files — never read or modify during development
- `docs/project/testing/BLIND_SCENARIOS.md`
