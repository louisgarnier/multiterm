# Product Requirements Document — MultiTerm

> **Status:** `Locked` — 2026-04-28
> Source of truth for goals, scope, and requirements. Read before every coding session.
> ⚠️ Once LOCKED, changes require a dated entry in §11 Amendments Log.

---

## 1. Project Summary

| Field | Value |
|---|---|
| **Project name** | MultiTerm |
| **One-liner** | A Mac desktop app (Electron + DMG) that hosts multi-project, multi-terminal Claude Code workflows with status-aware visual indicators, port management, and a per-project lifecycle (dev → prod → archived). |
| **Owner** | Louis Garnier |
| **Target completion** | MVP 4–6 weeks part-time |
| **Platform** | macOS desktop (`.dmg`) |
| **Tech stack hint** | Electron + `node-pty` + `xterm.js` + `chokidar` + `lsof` (system CLI) + Claude Code hooks/transcripts. Confirm in `architecture.md`. |

---

## 2. Goals & Non-Goals

> This section is LAW for the AI. It will not build non-goals.

### ✅ Goals (In Scope)

- **G1** — Manage multiple Claude Code projects in a unified Mac desktop app, with manual addition (folder picker default `~/Claude/`) and removal that leaves the folder on disk untouched.
- **G2** — Per project, support multiple concurrent terminals organized as browser-style tabs, each running an independent shell in the project folder.
- **G3** — Surface terminal state with 6 distinct visual indicators (`idle` / `running` / `awaiting-input` / `needs-permission` / `error` / `done-unack`) propagated from terminal tab → project pill → tray icon.
- **G4** — Detect Claude Code sessions automatically; when running, expose Level-2 awareness: active agent, active skill, model, last tool, token usage.
- **G5** — Provide three lifecycle stages per project (DEV / PROD / ARCHIVED). Top-of-app DEV/PROD toggle filters the sidebar to one mode; Archived is a separate filter checkbox.
- **G6** — Validate every DEV → PROD promotion via deterministic pre-flight checks (run command exists, target script exists, declared ports don't conflict, ≥1 URL set), blocking on failure with a deep-link to a bundled setup guide.
- **G7** — Manage ports across projects: declared per project, polled live via `lsof`, surfaced as chips on sidebar pills, in a per-project Ports panel, and in a global Ports view (⌘⇧P). On port conflict, auto-suggest the next free port.
- **G8** — Provide a macOS menu bar tray widget (logo + red dot + badge count) with a popover of DEV-only project pills (single-click = inline expand, double-click = focus main app).
- **G9** — Operate single-user, local-only — no server, no sync, no auth, no remote dependencies beyond Claude Code itself.

### ❌ Non-Goals (Out of Scope — AI must not implement these)

- **NG1** — Code editing surface. MultiTerm is not a replacement for VS Code or Cursor; no file editor pane.
- **NG2** — Cloud deployment integration (Vercel, Netlify, AWS, etc.). The PROD lifecycle is a local-vs-not-actively-developing concept, not a deploy dashboard.
- **NG3** — In-app multi-user, team, or collaborative features (shared sessions, sync between users, comments, chat). The app operates single-user-per-installation. Distributing the binary itself for someone else to install on their own Mac is unrelated and unrestricted.
- **NG4** — Cross-platform support (Windows / Linux) for v1. macOS only at start. Nothing in the stack blocks a future port if demand emerges.
- **NG5** — OS-level notifications, banners, sounds, or dock-bouncing. Visual indicators only.
- **NG6** — Skills/agents launcher palette. Claude Code's built-in `/` discovery is sufficient; visibility (already provided by L2) is the only requirement.
- **NG7** — L3 transcript activity feed (per-tool timeline view). Defer until users actually feel the absence.
- **NG8** — Multi-command per PROD project (e.g. backend + frontend + db together). One run command per PROD project for v1.
- **NG9** — Auto-launch PROD apps on app startup. Strictly manual launch per PROD project.
- **NG10** — Terminal templates / saved launch configurations. Plain shell only.
- **NG11** — Auto-kill orphan processes without explicit user click. All process termination is user-initiated.
- **NG12** — Auto-import recent Claude projects on first launch. Manual addition only.
- **NG13** — *Autonomous* modification of user files by MultiTerm itself. The app does not, on its own initiative, edit `CLAUDE.md`, project source files, Claude Code transcripts, or any other user data. The only files MultiTerm writes to are its own config (`~/Library/Application Support/MultiTerm/`) and its log files. **This does NOT restrict the user**: the user can edit `CLAUDE.md`, browse and modify any file in `~/Claude/` and its sub-projects, and Claude Code running inside a MultiTerm-spawned terminal retains full read/write access to user files exactly as it does today. The opt-in hook merge into `~/.claude/settings.json` (FR-14a) is the one explicit user-consented exception.

---

## 3. User Stories

> Format: "As a [user], I want to [action], so that [outcome]." Each story is independently testable.

### Must Have (MVP)

#### Project shell & navigation

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-01 | As a developer, I want to add a project folder to MultiTerm via "+ Add Project" | - [ ] Folder picker opens defaulting to `~/Claude/` <br>- [ ] Selected folder appears in sidebar with name = folder name <br>- [ ] Project persists across app restarts |
| US-02 | As a developer, I want to remove a project from MultiTerm without affecting the folder | - [ ] "Remove from app" action available per project <br>- [ ] Confirmation required <br>- [ ] Project disappears from sidebar; folder on disk is untouched |
| US-03 | As a developer, I want my DEV projects listed in a left sidebar with status pills | - [ ] Each pill shows: status dot + project name + relative timestamp ("2m", "1h", "3d") <br>- [ ] Active project is highlighted <br>- [ ] Sidebar can scroll if many projects |
| US-04 | As a developer, I want to collapse the projects sidebar to a 48px icon strip | - [ ] Sidebar header has collapse toggle <br>- [ ] Collapsed state shows project initial + status dot <br>- [ ] Collapse state persists across restarts |
| US-05 | As a developer, I want to toggle between DEV and PROD modes at the top of the app | - [ ] Top toggle has two segments: DEV (default), PROD <br>- [ ] Sidebar updates immediately to show only matching projects <br>- [ ] Selected mode persists across restarts |

#### Terminals (DEV mode)

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-06 | As a developer, I want to open a new shell terminal in the project folder via "+" | - [ ] Click "+" tab → spawns a fresh PTY in the project's working directory <br>- [ ] No command is pre-run; user types whatever <br>- [ ] New tab is auto-focused |
| US-07 | As a developer, I want multiple terminals per project organized as browser-style tabs | - [ ] One terminal visible at a time <br>- [ ] Tab shows status dot + terminal name <br>- [ ] Click switches active terminal <br>- [ ] Tab can be closed (with confirmation if process is running) |
| US-08 | As a developer, when a terminal is running `claude`, I want to see active agent / skill / model / last tool / tokens | - [ ] App detects `claude` process by inspecting child process command line <br>- [ ] Above the terminal output, an L2 panel renders agent · skill · model · last tool · tokens <br>- [ ] Generic terminals (npm dev, etc.) show no L2 panel |
| US-09 | As a developer, I want each terminal to be in one of 6 states reflecting reality | - [ ] States: `idle` / `running` / `awaiting-input` / `needs-permission` / `error` / `done-unack` <br>- [ ] State transitions occur within 1s of underlying event <br>- [ ] `done-unack` clears to `idle` the moment that tab gains focus |
| US-10 | As a developer, I want the project pill to aggregate to the most-urgent state across its terminals | - [ ] Aggregation priority: error > needs-permission > awaiting-input > done-unack > running > idle <br>- [ ] Project pill color matches the most-urgent state |

#### Lifecycle (DEV ↔ PROD ↔ ARCHIVED)

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-11 | As a developer, I want to switch a DEV project to PROD via a button | - [ ] "Switch to PROD" button visible on DEV project view <br>- [ ] On click, validation checks run (see US-12) <br>- [ ] On pass, project moves to PROD and global toggle flips to PROD so the project remains visible |
| US-12 | As a developer, the DEV→PROD transition runs deterministic pre-flight checks | - [ ] Checks: run-command non-empty; target script (if relative path) exists; declared ports don't overlap any other PROD project's declared ports; ≥1 URL set <br>- [ ] Soft warnings (e.g. no note) shown but non-blocking <br>- [ ] Failures shown as ✗ rows in red and block the transition |
| US-13 | As a developer, if pre-flight checks fail, I want a blocker dialog with clear next steps | - [ ] Dialog lists each failed check with the specific reason <br>- [ ] Dialog includes a deep-link to `docs/prod-setup-guide.md` (bundled with the app) <br>- [ ] Promote button is disabled until issues are resolved |
| US-14 | As a developer, I want to switch a PROD project back to DEV anytime without data loss | - [ ] "Switch to DEV" button on PROD project view <br>- [ ] No validation needed for PROD → DEV (it's a soft transition) <br>- [ ] Project returns to DEV with all previous state (terminals, file tree, declared ports) intact |
| US-15 | As a developer, I want to archive a project to hide it without losing it | - [ ] "Archive" available via per-project `…` menu <br>- [ ] Archived projects do not appear in DEV or PROD sidebar by default <br>- [ ] Sidebar has an "▢ Archived" filter checkbox; checking it overlays archived projects on the current mode |
| US-16 | As a developer, when a project is in PROD, I want a minimal UI focused on launching it | - [ ] PROD view shows: header (name, path, "Switch to DEV", `…` menu); Status panel (current state + Open / Stop / Restart buttons); Run command field; URLs list; Note field <br>- [ ] No terminal multiplexer or file tree on PROD view |
| US-17 | As a developer, I want one-click launch of a PROD project's local instance | - [ ] "Open in browser" button starts the run command if not running <br>- [ ] App polls localhost URL until reachable, then opens default browser <br>- [ ] Status indicator updates to "running" with uptime |
| US-18 | As a developer, I want Stop and Restart controls for a running PROD project | - [ ] Stop sends SIGTERM, falls back to SIGKILL after 5s <br>- [ ] Restart = stop + start in sequence <br>- [ ] Status updates promptly |

#### Files panel (DEV mode)

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-19 | As a developer, I want a file tree per project that I can pin or unpin | - [ ] File tree shows project root contents (folders expandable) <br>- [ ] Pin/unpin toggle in panel header <br>- [ ] State persists per project across restarts |

#### Port management

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-20 | As a developer, I want to declare expected ports per project (e.g. frontend=3000, backend=8000) | - [ ] Project settings panel allows adding/removing port→label entries <br>- [ ] Persisted across restarts |
| US-21 | As a developer, I want live detection of ports actually bound by my project's processes | - [ ] App polls `lsof -iTCP -sTCP:LISTEN` at 1–2s intervals <br>- [ ] Bound ports are matched to PIDs of terminals MultiTerm spawned <br>- [ ] Surfaced as a chip on the sidebar project pill (e.g. `:3000 :8000`) |
| US-22 | As a developer, I want a Ports panel inside each project showing live state | - [ ] Columns: port, PID, process name, owning terminal, since (uptime) <br>- [ ] Orphan rows (port still bound but spawned terminal is gone) flagged visually with a "Kill" button |
| US-23 | As a developer, when a process tries to bind a port already in use, I want auto-suggestion of the next free port | - [ ] Conflict modal shows: which port, which project owns it, suggested next free port <br>- [ ] Buttons: "Use \<suggested\>", "Pick another", "Cancel launch" <br>- [ ] On accept, app injects the new port into the launch (env var `PORT=<n>` or equivalent) |
| US-24 | As a developer, I want a global Ports view across all projects via ⌘⇧P | - [ ] Palette/overlay opens via ⌘⇧P <br>- [ ] Lists every bound port across all projects with: port, project, process, declared/actual match flag, orphan flag <br>- [ ] Closable via Esc |

#### Mac menu bar tray widget

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-25 | As a Mac user, I want a tray icon showing whether anything in MultiTerm needs me | - [ ] Tray icon appears on app launch <br>- [ ] Icon: app logo + red dot when any DEV project has pending state (`awaiting-input` / `needs-permission` / `error` / `done-unack`) + numeric badge of pending DEV projects |
| US-26 | As a developer, clicking the tray icon opens a popover with my DEV projects | - [ ] Popover shows horizontal pills for DEV projects only (no PROD or ARCHIVED) <br>- [ ] Each pill: status dot + name + relative time <br>- [ ] Popover dismisses on outside click or Esc |
| US-27 | As a developer, single-click expands a tray pill inline; double-click opens the main app | - [ ] Single-click: pill expands inline within popover, showing last preview message + token usage + project path <br>- [ ] Double-click: focuses the MultiTerm main window onto that project (open if not already running) |

### Should Have

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-30 | As a developer, I want a "PROD setup guide" doc shipped with the app | - [ ] `docs/prod-setup-guide.md` bundled with app resources <br>- [ ] Explains every check in DEV→PROD validation <br>- [ ] Deep-linked from the failure dialog (US-13) |
| US-31 | As a developer, I want the app to remember window size, position, and last-active project | - [ ] On relaunch, window restores to last bounds <br>- [ ] Last-active project is reopened |
| US-32 | As a developer, I want a "last activity" timestamp per terminal tab | - [ ] Tab tooltip or label shows "2m ago" etc. when hovering / inspecting <br>- [ ] Updates as state transitions occur |
| US-33 | As a developer, I want orphan port processes to be killable with one click from the Ports panel | - [ ] "Kill" button per orphan row <br>- [ ] Confirmation modal before SIGKILL <br>- [ ] Row disappears once port is released |

### Nice to Have (v2 — do NOT build in v1)

| ID | Story | Notes |
|---|---|---|
| US-50 | Multi-command PROD projects (backend + frontend together) | Defer — adds orchestration scope |
| US-51 | Auto-launch opted-in PROD apps on app startup | Defer — silent background processes need explicit user model |
| US-52 | Vercel API integration for PROD project deploy status | Defer — auth + API surface is its own project |
| US-53 | L3 transcript activity feed (per-tool timeline view per terminal) | Defer until L2 visibility is shown insufficient |
| US-54 | OS-level notifications (banners + sound) | Explicit non-goal for v1; revisit only on user request |
| US-55 | Cross-platform support (Windows, Linux) | Defer to v2 — Mac-first; nothing in stack blocks port |
| US-56 | Terminal templates / saved launch configs per project | Defer — power-user feature |
| US-57 | Skills/agents launcher palette | Explicit non-goal for v1; visibility (L2) is sufficient |
| US-58 | Auto-import recent Claude projects from `~/.claude/projects/` on first launch | Explicit non-goal for v1; user prefers manual control |

---

## 4. Functional Requirements

> What the system MUST do. All statements are testable.

### Project lifecycle

- **FR-01** — System shall persist project metadata (path, lifecycle stage, declared ports, run command, URLs, note) in a local config store, atomically (no half-written state).
- **FR-02** — System shall accept new projects via a folder picker that opens defaulting to `~/Claude/`.
- **FR-03** — System shall accept new projects via drag-and-drop of a folder onto the app window.
- **FR-04** — System shall provide a "Remove from app" action that deletes the project entry and never modifies the folder on disk.
- **FR-05** — System shall provide an Archive action per project, independent of the DEV/PROD toggle.
- **FR-06** — System shall expose an "▢ Archived" filter checkbox in the sidebar that, when checked, overlays archived projects onto the current DEV or PROD view.

### Terminals

- **FR-07** — System shall spawn a new pseudo-terminal (PTY) on click of "+" with: cwd = project folder, shell = user's `$SHELL`, no pre-run command.
- **FR-08** — System shall organize a project's terminals as browser-style tabs, exactly one visible at a time.
- **FR-09** — System shall close a tab on user request. If the foreground process is still running (not at shell prompt), system shall present a confirmation modal with two options: "Close tab and kill process" (sends SIGTERM, then SIGKILL after 5s), or "Cancel". If the tab is at an idle shell prompt, close immediately without confirmation, sending SIGHUP.
- **FR-10** — System shall preserve scrollback per terminal until the tab is closed.

### Claude awareness

- **FR-11** — System shall detect a `claude` session in a terminal by inspecting the PTY's foreground process command line for the `claude` binary.
- **FR-12** — System shall read Claude Code transcripts from `~/.claude/projects/<sanitized-path>/<session>.jsonl` to derive: active agent name, active skill name, model identifier, last tool used, cumulative token usage. Transcripts are read-only.
- **FR-13** — System shall update the L2 awareness panel within 1s of a new transcript line being written (transcript-watcher path) or within 200ms of a hook event (hook-listener path, when enabled — see FR-14a).
- **FR-14** — System shall fall back to "generic terminal" mode (no L2 panel) if Claude transcripts are absent, malformed, or unreadable.
- **FR-14a** — System shall expose a Settings toggle "Enable Claude Code hooks (recommended)". Default: off. On opt-in, system shall merge MultiTerm's hook handlers into the user's `~/.claude/settings.json` non-destructively (preserving existing hooks), and present a one-click "Disable" that reverts the merge. Without hook enablement, the app operates entirely on transcript polling.

### Status taxonomy

- **FR-15** — System shall classify each terminal into exactly one of: `idle` / `running` / `awaiting-input` / `needs-permission` / `error` / `done-unack`.
- **FR-16** — System shall transition `done-unack` to `idle` the moment the user focuses that tab.
- **FR-17** — System shall aggregate per-terminal state to a per-project state using priority: `error` > `needs-permission` > `awaiting-input` > `done-unack` > `running` > `idle`.
- **FR-18** — System shall reflect aggregated project state identically in: sidebar pill color, tray icon (red dot + count), and tray popover pill color.

### DEV→PROD promotion

- **FR-19** — On user-initiated DEV → PROD transition, system shall run validation checks before completing the transition:
  - run command field is non-empty
  - if run command is or contains a relative path (e.g. `./start.sh`), the file at that path exists and is executable
  - none of the project's declared ports overlap with another PROD project's declared ports
  - at least one URL is set
- **FR-20** — System shall present validation results in a modal: passes shown as ✓, soft warnings as ⚠ (non-blocking), failures as ✗ (blocking).
- **FR-21** — Validation failure modal shall include a deep link to `docs/prod-setup-guide.md`.
- **FR-22** — On successful promotion, system shall persist the new lifecycle stage and flip the global Dev/Prod toggle to PROD.

### PROD operations

- **FR-23** — On click of "Open in browser" for a PROD project, system shall: (a) ensure the run command process is alive, starting it if not; (b) poll the configured local URL until reachable (max 30s); (c) open the URL in the user's default browser.
- **FR-24** — Stop button shall send SIGTERM to the run-command process; if not exited within 5s, send SIGKILL. Status updates within 1s of process exit.
- **FR-25** — Restart shall execute Stop then Open in sequence.

### Port management

- **FR-26** — System shall poll `lsof -iTCP -sTCP:LISTEN -n -P` at 1–2 second intervals (adaptive to CPU pressure).
- **FR-27** — System shall match each bound port's PID to PIDs of processes spawned by MultiTerm (transitively), labeling each port with its owning terminal.
- **FR-28** — System shall expose the per-project bound-port set as a chip on the sidebar pill (e.g. `:3000 :8000`).
- **FR-29** — System shall provide a per-project Ports panel showing: port, PID, process name, owning terminal, uptime, with orphan rows flagged.
- **FR-30** — On port-bind conflict (a launching process attempts to bind a port already in use), system shall present a modal showing: conflicting port, current owner, suggested next free port.
- **FR-31** — Conflict modal shall offer "Use <suggested>", "Pick another", "Cancel launch". On "Use suggested", the new port is propagated via `PORT=<n>` env var to the spawning process.
- **FR-32** — System shall provide a global Ports view via the keyboard shortcut ⌘⇧P, listing every bound port across all tracked projects with: port, project, process, declared/actual match flag, orphan flag.
- **FR-33** — System shall provide a "Kill" action for orphan port rows. Click is sufficient — no confirmation modal (the click is the confirmation). Action sends SIGTERM with SIGKILL fallback after 5s.

### Tray widget

- **FR-34** — System shall create a macOS menu bar tray icon on app launch.
- **FR-35** — Tray icon shall display: app logo (always); red dot (when any DEV project has aggregated state in `awaiting-input` / `needs-permission` / `error` / `done-unack`); numeric badge (count of pending DEV projects).
- **FR-36** — On tray icon click, system shall display a popover with horizontal project pills for DEV projects only; PROD and ARCHIVED projects shall not appear.
- **FR-37** — Tray popover pill click handlers: single-click expands the pill inline showing last preview message, token usage, and project path; double-click focuses the main app window onto that project (opening it if not running).
- **FR-38** — System shall not produce any native macOS notifications, banners, or sounds.

### Persistence & startup

- **FR-39** — System shall restore on relaunch: window bounds, last-active mode (DEV/PROD), last-active project, sidebar collapse state, file-tree pin state per project.
- **FR-40** — System shall not persist running terminal processes or empty tab structures across restarts. Each app launch starts with no terminals open per project; the user opens fresh terminals as needed.
- **FR-41** — System shall persist its project registry and per-project metadata to `~/Library/Application Support/MultiTerm/projects.json`. No files are written into project folders themselves.

---

## 5. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| **NFR-01** | Performance | Cold app startup must complete in under 3 seconds on a 2020+ Mac. |
| **NFR-02** | Performance | Spawning a new terminal must produce visible feedback within 200ms. |
| **NFR-03** | Performance | Terminal output rendering (xterm.js) must keep up with 50,000 lines/min without UI lag. |
| **NFR-04** | Performance | Port poll cycle must complete within 1.5s on a system with up to 50 listening ports. |
| **NFR-05** | Performance | UI must remain responsive (interaction frames ≥ 30fps) with 5+ concurrent active terminals. |
| **NFR-06** | Reliability | App must not crash if Claude transcripts are absent, malformed, or being concurrently written — fall back to generic-terminal mode and log warning. |
| **NFR-07** | Reliability | App must not crash if `lsof` is unavailable, denied, or fails — show a degraded "ports unavailable" state and log error. |
| **NFR-08** | Reliability | Project metadata writes must be atomic (write-temp-then-rename or equivalent) — never leave half-written config on disk. |
| **NFR-09** | Reliability | App must survive system sleep/wake without orphaning child processes or losing terminal state. |
| **NFR-10** | Security | App must not log or persist Claude transcript content outside Claude Code's own files. |
| **NFR-11** | Security | App must not log absolute paths containing `~/.claude` or other Claude Code internal paths in user-visible logs. |
| **NFR-12** | Observability | All major operations (project add/remove, terminal spawn/exit, lifecycle transition, port conflict, validation pass/fail) shall be logged in the format `[Module] verb: detail` with the project's emoji conventions (📥 in, 📤 out, ✅ success, ❌ error, ⚠️ warning, 🚀 startup). |
| **NFR-13** | Observability | Errors shall be logged with the ❌ prefix and stack trace. |
| **NFR-14** | Usability | Destructive actions that risk losing work ("Remove from app", closing a tab with a running process, lifecycle change with running processes) require an explicit confirmation modal. Direct buttons that are themselves the confirmation ("Stop", "Kill" on an orphan port row) do not require an additional modal. |
| **NFR-15** | Usability | All keyboard shortcuts (⌘⇧P for global Ports, etc.) shall be discoverable via a help/cheatsheet view. |

---

## 6. Data Requirements

| Dataset | Source | Format | Volume | Notes |
|---|---|---|---|---|
| Project registry | User actions | JSON | 5–30 projects | `~/Library/Application Support/MultiTerm/projects.json` |
| Per-project metadata | User actions | nested JSON | One entry per project | Lifecycle stage, declared ports, run command, URLs, note, file-tree pin state — stored within the same registry JSON |
| Terminal session state | App runtime | In-memory | 5–20 terminals | NOT persisted across restarts (FR-40 — cold start each launch) |
| Claude transcript files | Claude Code | JSONL | varies | Read-only consumption from `~/.claude/projects/` |
| Application logs | App | Plain text | rotating per day | `logs/multiterm_YYYY-MM-DD.log` |

**Data constraints:**
- Claude Code transcripts are READ-ONLY; MultiTerm never modifies, copies, or persists them.
- No PII, credentials, or API keys are persisted by MultiTerm.
- Project folders on disk are NEVER modified by MultiTerm (no auto-edits, no `.multiterm/` files inside project folders unless Q4 resolves that way).

---

## 7. Interfaces & Integrations

| System | Direction | Method | Auth |
|---|---|---|---|
| `claude` CLI | Outbound (spawned child) | `node-pty` PTY | None (inherits user shell env) |
| Claude Code transcripts (`~/.claude/projects/`) | Read | filesystem read + `chokidar` watch | None |
| Claude Code hooks (`~/.claude/settings.json`) | Read + opt-in merge | Filesystem read; merge MultiTerm-owned hook entries when user enables (FR-14a) | None |
| User shell (`$SHELL`) | Outbound (spawned child) | `node-pty` PTY | None |
| `lsof` (system CLI) | Outbound | child process | None |
| Default browser | Outbound | macOS `open` URL | None |

---

## 8. Error Handling Policy

- All errors must be caught and logged — no silent failures.
- Failed terminal spawn (PTY error) → display error message in tab content; do not crash app.
- Claude transcript file unreadable or malformed → fall back to generic-terminal mode for that tab; log warning; do not crash.
- `lsof` unavailable or fails → show degraded "ports unavailable" state in panels; log error; do not retry destructively.
- Port-bind conflict during launch → show conflict modal; do NOT auto-launch on a conflicting port without user choice.
- Failed PROD validation → block transition; show clear blocker dialog; do NOT silently degrade.
- User-facing errors must show a clear human-readable message with a suggested action; never a stack trace.
- App must survive system sleep/wake without orphaning child processes or causing zombie state.

---

## 9. Constraints

- macOS only for v1 (`.dmg` distribution); no Windows or Linux support.
- Single-user, local-only — no auth, no server, no remote sync.
- MVP target: 4–6 weeks part-time.
- Must operate against the current public release of Claude Code without requiring patches to Claude Code itself.
- Must not require user-installed dependencies beyond those bundled with the app and macOS itself (`lsof` is standard on macOS).
- Must work offline for status detection. (Claude Code itself may need internet, but MultiTerm's awareness layer must function locally.)
- Project folders on disk are immutable from MultiTerm's perspective.

---

## 10. Resolved Questions

> All resolved at lock time (2026-04-28). Future changes go through Amendments Log §11.

| # | Question | Resolution |
|---|---|---|
| **Q1** | Persist running terminals across restarts? | **(a) Cold start each time.** No terminal state survives app close. Reflected in FR-40. |
| **Q2** | How does MultiTerm receive Claude Code state events? | **(b) One-click "Enable hooks" in Settings.** Default off; transcript polling is the always-on baseline. Hooks add lower latency when user opts in. Reflected in FR-13, FR-14a. |
| **Q3** | Orphan port "Kill" — confirmation or one-click? | **One-click, no modal.** The Kill button is itself the confirmation. Reflected in FR-33, NFR-14. |
| **Q4** | Project metadata storage location? | **Single JSON in `~/Library/Application Support/MultiTerm/projects.json`.** No files written into user project folders. Reflected in FR-41, §6. |
| **Q5** | Closing a tab mid-process — behavior? | **(a) Confirmation modal** with "Close tab and kill process" (SIGTERM → SIGKILL after 5s) and "Cancel". Idle shell closes immediately without modal. Reflected in FR-09, NFR-14. |

---

## 11. Amendments Log

> Add entries here once status is `Locked`. Never delete history.

| Date | Change | Reason |
|---|---|---|
| | | |

---

## 📤 Outputs for 3-ARCHITECTURE.md

| PRD section | → Architecture input |
|---|---|
| Tech stack hints (§1) | Stack decisions — confirm Electron + node-pty + xterm.js + chokidar + lsof |
| Functional requirements (§4) | Component breakdown — PTY manager, lifecycle store, port poller, hooks listener / transcript watcher, tray manager |
| Non-functional requirements (§5) | Performance budgets, reliability strategy, observability/logging conventions |
| Data requirements (§6) | Storage layout, file vs DB, serialization |
| Interfaces & integrations (§7) | Claude Code IPC strategy (Q2), browser open, lsof spawn pattern |
| Error handling (§8) | Boundary definitions, recovery flows |
| Constraints (§9) | Stack limits, distribution model |
| User stories (§3) | System overview / user flows |

---

*→ Once locked, proceed to `3-ARCHITECTURE.md`.*
*→ Also write blind scenarios in `../testing/BLIND_SCENARIOS.md` while requirements are fresh.*
