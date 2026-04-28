# Epics & Stories — MultiTerm

> **Status:** Drafted at architecture/PRD lock; individual story details written when each epic begins.
> Status indicators: `[ ] Pending` · `[→] In Progress` · `[x] Done` · `[~] Blocked`
> The active story pointer lives in `ACTIVE.md`.

---

## Epic Overview

| ID | Epic | Goal | Status | Stories | Source |
|---|---|---|---|---|---|
| EPIC-1 | Shell foundation | Electron + IPC + logger + tests + window restore | [→] | 7 | architecture §3 M1, M8; plan Tasks 1.1–1.20 |
| EPIC-2 | Projects & Lifecycle | Project sidebar, add/remove/archive, DEV/PROD toggle, promotion ritual | [ ] | 5 | PRD US-01–05, US-11–15; FR-01–06, FR-19–22 |
| EPIC-3 | Terminals (basic) | PTY manager + xterm tabs + 3-state machine + close-confirm | [ ] | 4 | PRD US-06–10 (partial), FR-07–10 |
| EPIC-4 | Claude awareness (L2 via transcripts) | Detect claude, watch transcripts, full 6-state machine, L2 panel | [ ] | 5 | PRD US-08–10 (full), FR-11–18 |
| EPIC-6 | Ports | Live lsof poller, per-project chip + panel, conflict UX, global ⌘⇧P | [ ] | 5 | PRD US-20–24, US-33; FR-26–33 |
| EPIC-7 | Tray | NSStatusBar icon, badge, popover with DEV pills, click handlers | [ ] | 3 | PRD US-25–27, FR-34–38 |
| EPIC-8 | PROD operations | Run command spawn, URL polling, Open/Stop/Restart | [ ] | 3 | PRD US-16–18, FR-23–25 |
| EPIC-9 | File tree | Per-project folder browser, pin/unpin, open externally | [ ] | 2 | PRD US-19, FR-39 |
| EPIC-5 | Hooks (opt-in latency upgrade) | Settings toggle, settings.json merge, Unix-socket listener | [ ] | 3 | PRD US-08–10 (latency), FR-13, FR-14a |
| EPIC-10 | Packaging & signing | electron-builder DMG, Apple Dev ID signing, notarization, release CI | [ ] | 3 | PRD §1 platform, §9 constraints |
| EPIC-11 | Polish | Keyboard shortcuts, About/Help, preferences, empty states | [ ] | 4 | PRD US-30–32, general polish |

**Linear sequencing:** 1 → 2 → 3 → 4 → 6 → 7 → 8 → 9 → 5 → 10 → 11. Total stories: 44.

---

## Stories per epic

### EPIC-1 — Shell foundation (detailed in `epic-1/story-X.Y.md`)

| ID | Story | User-test checkpoint |
|---|---|---|
| 1.1 | Repo skeleton + Electron boots | `npm run dev` opens a window titled "MultiTerm" |
| 1.2 | IPC roundtrip (preload + ping/pong) | Renderer shows "MultiTerm — hello"; click Ping shows RTT in ms |
| 1.3 | Tailwind + dark theme | UI is styled (dark bg, blue button, slate text); no FOUC |
| 1.4 | Logger module + IPC log forwarding | `tail` log file shows startup + ping forwarded lines |
| 1.5 | Window state restoration | Resize / move / quit / relaunch — bounds preserved |
| 1.6 | Lint, format, hooks, CI | `npm run lint` clean; pre-commit triggers; CI workflow file present |
| 1.7 | Build skeleton + acceptance smoke (M1) | `npm run build` then `npx electron dist/main/index.js` launches app; ping works; log writes |

### EPIC-2 — Projects & Lifecycle

| ID | Story | User-test checkpoint |
|---|---|---|
| 2.1 | Project registry persistence (atomic JSON store) | `projects.json` written atomically; restart preserves state |
| 2.2 | Sidebar with project pills (read-only render) | Sidebar shows pills with name + status dot + relative time |
| 2.3 | Add / Remove project (folder picker + remove action) | `+ Add Project` opens picker at `~/Claude/`; remove deletes from app, leaves folder |
| 2.4 | DEV/PROD top toggle (mode filter) | Toggle filters sidebar to one mode; survives restart |
| 2.5 | Switch to PROD with promotion ritual + Archive | "Switch to PROD" runs validation; Archive hides project; "▢ Archived" filter overlays |

### EPIC-3 — Terminals (basic)

| ID | Story | User-test checkpoint |
|---|---|---|
| 3.1 | Spike S3+S5: node-pty in Electron + xterm wiring | Single shell tab opens; ANSI colors render; resize works |
| 3.2 | Multiple tab management | "+" adds tabs; click switches; content persists |
| 3.3 | Close tab with confirm-when-running | Idle shell closes immediately; running process triggers confirm modal |
| 3.4 | Basic 3-state machine (idle/running/exited) | Tab status dot updates; project pill aggregates |

### EPIC-4 — Claude awareness (L2 via transcripts)

| ID | Story | User-test checkpoint |
|---|---|---|
| 4.1 | Spike S1: transcript schema | Sample transcript parsed; field shapes documented in ADR.md |
| 4.2 | Claude detector | Running `claude` → tab marked Claude; running `npm dev` → not marked |
| 4.3 | Transcript watcher + parser | New transcript line → L2 fields update within 1s |
| 4.4 | Full 6-state machine + aggregation | All 6 states observable; project pill aggregates correctly |
| 4.5 | L2 panel UI | Panel above Claude tab shows agent/skill/model/last tool/tokens; updates live |

### EPIC-6 — Ports

| ID | Story | User-test checkpoint |
|---|---|---|
| 6.1 | Spike S4: lsof parsing | Sample lsof output parsed; tested against real macOS output |
| 6.2 | Port poller + matcher | Run `npm dev` in a tab → port appears in store within 2s |
| 6.3 | Per-project chip + Ports panel | Sidebar pill shows `:5173`; Ports panel lists port → PID → process → owning terminal |
| 6.4 | Conflict modal + auto-suggest | Two projects competing for 3000 → modal shows "Use 3001" |
| 6.5 | Global Ports view (⌘⇧P) | Shortcut opens palette listing all bound ports + flagged orphans |

### EPIC-7 — Tray

| ID | Story | User-test checkpoint |
|---|---|---|
| 7.1 | Spike S7: tray + popover positioning | Tray icon visible; popover opens on click in correct position |
| 7.2 | Tray icon with badge + DEV pills | Pending DEV project → red dot + count; popover lists DEV only |
| 7.3 | Single/double-click | Single = inline expand; double = focus main app |

### EPIC-8 — PROD operations

| ID | Story | User-test checkpoint |
|---|---|---|
| 8.1 | Run command spawn + URL polling | "Open in browser" spawns command, polls localhost, opens browser when reachable |
| 8.2 | Stop / Restart | Stop = SIGTERM → SIGKILL fallback. Restart = stop + start |
| 8.3 | URLs + note editing | Add/remove URLs; edit note inline |

### EPIC-9 — File tree

| ID | Story | User-test checkpoint |
|---|---|---|
| 9.1 | Folder browser + watch | Tree shows project root; expand works; updates on external file changes |
| 9.2 | Pin/unpin + open externally | Pin/unpin persists; click file → opens in default editor |

### EPIC-5 — Hooks (opt-in latency upgrade)

| ID | Story | User-test checkpoint |
|---|---|---|
| 5.1 | Spike S2: hooks merge | Sample settings.json round-trips correctly; user's hooks preserved |
| 5.2 | Settings toggle + merge logic | Toggle ON merges hooks; toggle OFF removes only MultiTerm-tagged entries |
| 5.3 | Unix socket listener + low-latency events | With hooks ON, terminal state updates within 200ms |

### EPIC-10 — Packaging & signing

| ID | Story | User-test checkpoint |
|---|---|---|
| 10.1 | electron-builder DMG (unsigned dev build) | `npm run build:mac` produces a DMG; opens locally |
| 10.2 | Apple Dev ID signing + notarization | DMG passes `codesign --verify` + `spctl -a -t exec`; opens without Gatekeeper warning |
| 10.3 | Release CI workflow | Tag push triggers CI build + signs + uploads DMG to GitHub Releases |

### EPIC-11 — Polish

| ID | Story | User-test checkpoint |
|---|---|---|
| 11.1 | Keyboard shortcuts cheatsheet (⌘?) | Modal lists every shortcut |
| 11.2 | About / Help menu | App menu has About showing version + acknowledgements |
| 11.3 | Preferences UI | Log level, default add-project folder, time format — all persist |
| 11.4 | Empty states + accessibility pass | Empty state copy visible; keyboard nav works through sidebar/tabs/modals |

---

## Test Design Rules — apply to every story (per template §🧪)

**Mocking:**
- Same DB/API mock called more than once → use `side_effect=[r1, r2, ...]`, never reused `return_value` (silent false-positive risk).
- Mock external services (HTTP, DB client). Never mock internal business logic.

**Assertions:**
- Never wrap an assertion in a conditional guard (`if rows: assert rows[0] == x` silently passes when rows is empty).
- Always assert exact value, not just presence (`assert "synced" in response` passes when `synced=0`).
- Every story's tests must cover: happy path, ≥1 edge case, ≥1 failure case.

**Structure:**
- Tests written in the same session as the code. Never deferred.
- Each story's final task: run the full test suite. Not just new tests.
- Blind scenarios in `testing/BLIND_SCENARIOS.md` are sealed — user's responsibility, run after dev tests pass.

---

## Backlog (post-v1)

- [ ] Auto-update (`electron-updater`)
- [ ] Crash reporting (Sentry or local crash dumps)
- [ ] Localization
- [ ] L3 transcript activity feed
- [ ] OS-level notifications (banner + sound)
- [ ] Cross-platform (Windows/Linux)
- [ ] Skills/agents launcher palette
- [ ] Multi-command per PROD project
- [ ] Auto-launch PROD apps on startup
- [ ] Terminal templates / saved launch configs
- [ ] Vercel API integration for PROD deploy status
- [ ] Auto-import recent Claude projects on first launch

---

## 📤 Outputs for 6-BUILD.md

- Epic structure → BUILD session organization (epics in linear order)
- Story breakdown → one BUILD session per story
- User-test checkpoints → story sign-off requirements (user verifies before close)
- Test requirements → dev tests written same session as code
- Status tracking → updates flow back to `ACTIVE.md`

*→ See `ACTIVE.md` for current pointer; `epic-1/story-1.1.md` for execution detail.*
