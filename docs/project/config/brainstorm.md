# Brainstorm — MultiTerm

> Generated through brainstorming dialogue on 2026-04-28
> Status: GO

---

## 0. Freeform Input

### Raw Thoughts
Today using CLAUDE.md / agent workflows in VS Code or Cursor isn't intuitive — once you're running multiple agents on multiple terminals, it gets out of hand fast. The idea is a Mac app for managing multiple Claude Code projects at once. Each project drills into a unified view: file explorer + multiple terminals + status awareness. Project pills "light up" when terminals need attention, with a high-level recap of what each terminal is doing so you can quickly understand which functionality is being worked on. Goal: enable productive multi-project / multi-terminal Claude Code workflows without losing track of agents, projects, or ports. Should also serve as a follow-up tracker so projects don't get lost on disk over time — including a separate "prod" mode for apps you're using but no longer actively building.

### Notes & Context
- Personal, single-user, local-only Mac app
- Pain is concrete and recurring: status awareness across multiple Claude sessions, port conflicts between dev servers, "I keep losing projects"
- Reference for the menu bar tray widget: a Mac top-bar popover (ClaudeMate-style screenshot the user shared) — project pills with statuses + content preview
- Project folders live under `~/Claude/`

---

## 1. The One-Liner

**MultiTerm** is a Mac desktop app (Electron + DMG) that hosts multi-project, multi-terminal Claude Code workflows with status-aware visual indicators, port management, and a per-project lifecycle (dev → prod → archived).

---

## 2. The Problem

- **Who has this problem?** Claude Code power users running multiple agents/terminals across multiple projects in parallel.
- **How are they solving it today?** VS Code / Cursor terminal panes. The UI doesn't expose Claude state, doesn't surface "this terminal needs you," and doesn't help with port conflicts or project tracking. Memory, sticky notes, and Cmd-Tab are doing too much work.
- **Why is the current solution inadequate?**
  - No glance-able way to see which terminal needs attention right now
  - Can't tell at a glance which agent / skill is running in which terminal
  - Port conflicts when multiple frontend dev servers want the same port
  - Old projects fade from memory and rot on disk
  - No clean separation between "I'm building this" and "I'm using this" modes
- **How often does this problem occur?** Constantly during active Claude development — daily friction.

---

## 3. The Solution

### Core Workflow (User's Journey)

**Daily dev work:**
1. Open MultiTerm; left sidebar shows DEV projects with status pills (status dot + name + last-active time)
2. Click into a project; see file tree + terminal tabs
3. Open 2–3 terminals — one runs `claude` (e.g. Plan agent for refactoring), one runs `npm dev`, one runs tests
4. Switch to another project to review code
5. While away, an agent in the first project finishes and asks a question → that project's pill lights up red, the menu bar tray shows a "1" badge
6. Click back, pick the lit-up tab, answer

**Lifecycle management:**
1. Once a project is functional and you stop building on it, click "Switch to PROD"
2. App runs validation: run command defined? target script exists? declared ports don't conflict? URL set?
3. On pass, project moves to PROD; the global toggle flips too. PROD view shows Open / Stop / Restart + status + URL list + run command + note
4. Later, when development resumes, "Switch to DEV" restores the full toolkit — no data loss

**Port management:**
1. Run `npm dev` in a new project; app polls `lsof` and detects bound port 3000
2. Another project tries to bind 3000 → app warns "in use by zemaster, suggest 3001?" → accept → no conflict

### What Makes This Different
- **Built specifically for the Claude Code multi-agent workflow** — not a generic terminal app retrofitted
- **Visual status awareness at every level**: terminal tab, project pill, sidebar group, macOS menu bar tray
- **Lifecycle-aware**: dev → prod transition with validation prevents "ship and find it broken later"
- **Port management built-in**: solves the persistent multi-project port conflict pain
- **Personal-scale**: doesn't compete with Cursor/VS Code as an editor; complements them by managing the *agent layer* and the *project portfolio*

---

## 4. Assumptions & Risks

| Assumption | Risk if Wrong | Mitigation |
|---|---|---|
| Claude Code emits enough state via hooks + transcripts to drive L2 awareness (active agent, skill, idle/working/awaiting) | Lights/recap unreliable; the core value prop weakens | Spike on Claude Code's `settings.json` hooks + `~/.claude/projects/` transcripts during architecture step; confirm the data is reachable before committing the design |
| `node-pty` + `xterm.js` handle multi-terminal in Electron without major issues | Terminal performance/stability problems at scale | Standard stack used by VS Code, Cursor, Hyper — mature; defer concern |
| Port detection via `lsof` polling is fast enough at 1–2s intervals | UI lag or stale port info | Poll on demand + on terminal lifecycle events; cache between |
| Single-user, local-only Mac app — no sync or remote needs for v1 | Future demand for multi-machine sync | Defer; refactor when actually needed |
| Manual project addition is enough — auto-import not desired | Onboarding friction if user changes mind | User explicitly chose manual; folder picker defaults to `~/Claude/` |
| DEV→PROD validation check engine stays simple enough to ship in MVP | Validation complexity grows; promotion becomes brittle | Start with 3 hard checks + soft warnings; expand only based on real friction |

---

## 5. Feasibility Check

| Dimension | Assessment | Notes |
|---|---|---|
| **Technical complexity** | Medium-High | Standard Electron stack but many integrated subsystems: PTY, file watcher, hooks listener, port poller, transcript parser, tray app, IPC, lifecycle engine |
| **Time estimate (MVP)** | 4–6 weeks part-time | Covers: shell, projects sidebar, terminals + tabs, L2 Claude detection, dev/prod lifecycle + promotion, port management, tray widget |
| **Dependencies / blockers** | None hard | Electron, `node-pty`, `xterm.js`, `chokidar`, `lsof` CLI — all mature or built-in |
| **Skills gap** | Minimal | Familiar TypeScript/Electron territory |
| **Maintenance burden** | Low-Medium | Single-user app, no server, no DB; local config files only |

---

## 6. Go / No-Go Decision

**Success criteria:**
- **Minimum (MVP done):** Can manage 3+ DEV projects with multiple Claude + generic terminals each, see aggregated status across all, switch a project to PROD with validation checks, and use the menu bar tray to glance at state from any other app.
- **Full success:** Daily-driver app that genuinely reduces multi-project chaos. User stops losing track of projects, port conflicts, and agent statuses. Reaches a point where opening VS Code's terminal feels worse than opening MultiTerm.
- **Failure looks like:** App is unstable; lights/recap don't accurately reflect Claude state; performance degrades with 5+ terminals; port detection has false positives; user reverts to VS Code terminals.

**Decision:** GO

**Rationale:** Real personal pain (multi-terminal/multi-project Claude chaos), well-scoped feature set, mature underlying stack, single-user means no infrastructure burden, and the lifecycle + port features genuinely differentiate it from any generic terminal app.

---

## 📤 Outputs for 2-PRD.md

| Brainstorm | → PRD input |
|---|---|
| Name + one-liner (§1) | Project Summary |
| Problem + solution (§2-3) | Context & user story seeds |
| Assumptions & risks (§4) | Open Questions & Constraints |
| Feasibility (§5) | Non-functional requirements, constraints |
| Go/No-Go rationale (§6) | Goals framing |

### Locked design decisions (carry forward to PRD / architecture)

**Platform & stack**
- Mac desktop app, Electron, distributed as `.dmg` (Mac-only for v1)
- Stack: Electron + `node-pty` + `xterm.js` + `chokidar` + Claude Code hooks/transcripts + `lsof`

**Layout**
- Top-of-app Dev/Prod mode toggle; sidebar filters by mode
- Left projects sidebar collapsible to icon strip
- Per-project: collapsible/pinnable file tree + browser-tab terminals (one terminal at a time, status dot per tab, "+" to add)

**Status taxonomy**
- 6 states per terminal: `idle` / `running` / `awaiting-input` / `needs-permission` / `error` / `done-unacknowledged` (last auto-clears on focus)
- Project pills aggregate to most-urgent state across their terminals

**Claude awareness — Level 2**
- Show active agent, active skill, model, last tool, token usage when `claude` is running
- Generic terminals work normally; Claude UI is conditional
- No transcript-feed (L3) in MVP

**Lifecycle**
- Three stages: DEV / PROD / ARCHIVED
- Top-of-app toggle filters between DEV and PROD only (primary modes)
- "Switch to PROD" / "Switch to DEV" per-project button moves project AND auto-flips global view to follow
- "Archive" available via per-project `…` menu; archived projects accessible via a separate "Archived" filter in the sidebar (hidden by default, no global mode toggle slot)
- DEV→PROD validation ritual: run-command exists, target script exists, declared ports don't conflict with other PROD projects, ≥1 URL set; soft warnings non-blocking
- "Remove from app" action (clears entry, leaves folder on disk untouched)
- A bundled MD help doc ("PROD setup guide") explains the promotion requirements; the validation-failure dialog deep-links to it

**Ports**
- Declared expected ports per project (frontend=3000, backend=8000) + live `lsof` polling matched against tracked PIDs
- Per-project ports chip on sidebar pill + Ports panel inside project (port → PID → process → owning terminal → since)
- Stale-process detection + one-click cleanup
- Conflict UX: auto-suggest next free port
- Global Ports view (palette / overlay) showing all bound ports + flagged orphans

**Terminals**
- New terminal = bare shell in project folder; user runs whatever (`claude`, `npm dev`, etc.)
- App auto-detects Claude vs generic and updates tab UI accordingly

**Project discovery**
- Manual only; "+ Add Project" folder picker defaults to `~/Claude/`
- Add/remove anytime, no auto-import, no auto-watch

**Menu bar tray (Mac)**
- Tray icon: logo + red dot when any DEV project has pending state + badge count
- Click → popover with horizontal pills of DEV projects only (status + name + time)
- Single-click pill = inline expand (preview message, tokens, path); double-click = focus main app on project

**Notifications**
- Visual only. No OS banners, no sounds.

**Out of scope for MVP (deferred to v2+)**
- Vercel / cloud deployment integration
- Multi-command per PROD project (backend + frontend together)
- Auto-launch PROD apps on startup
- Skills/agents launcher palette
- L3 activity feed (transcript timeline view)
- OS notifications
- Cross-platform (Windows/Linux)
- Terminal templates / saved launch configs

---

## 🎨 Visual References

Self-contained design mockup — open in any browser to see all locked views in one page:

📁 **[docs/project/config/mockups/design-reference-v1.html](mockups/design-reference-v1.html)**

The reference covers 9 sections, each capturing decisions aligned during brainstorm dialogue:

| § | View | What's locked |
|---|---|---|
| 1 | Terminal state taxonomy | 6 colors: gray idle, green running, blue awaiting-input, yellow needs-permission, red error, purple done-unack (auto-clears on focus). Aggregation priority: error → needs-perm → awaiting → done → running → idle |
| 2 | Overall app layout | Layout C — projects sidebar (collapsible to 48px icon strip) · file tree (pin/unpin) · terminal area dominant. Both side panels have pin/unpin toggles; terminals always remain primary |
| 3 | Project sidebar pills | Pill content: status dot + name + relative timestamp + optional ports chip (`:3000 :8000`). Active project highlighted. 3-position selector at top of sidebar: DEV / PROD / ▢ Archived (Archived is a checkbox filter, not a third mode) |
| 4 | DEV/PROD top toggle | Top-of-app segmented control. Per-project "Switch to X" button moves the project AND auto-flips the global toggle to follow |
| 5 | Terminal tabs | Browser-tab style, one terminal at a time. Tab shows status dot + name + "+" to add. Claude awareness header (L2) appears when `claude` is detected: agent · skill · model · last tool · tokens |
| 6 | PROD project view | Header (name, path, "Switch to DEV" btn, ⋯) + Status panel (Open/Stop/Restart) + Run command + URLs + Note. Minimal, no terminal multiplexer |
| 7 | DEV→PROD promotion dialog | Pass: ✓ rows + soft warnings + Promote button. Block: ✗ rows in red + deep-link to `docs/prod-setup-guide.md`, Promote button disabled |
| 8 | Port management | (a) ports chip on sidebar pill, (b) Ports panel inside project (port → PID → process → owning terminal → since, with "Kill" for orphans), (c) conflict modal with auto-suggested next free port, (d) global Ports view via ⌘⇧P |
| 9 | Mac tray widget | Tray icon: logo + red dot + badge count. Popover: DEV-only horizontal pills (ClaudeMate-style). Single-click pill = inline expand (preview, tokens, path). Double-click = focus main app on project |

**Versioning:** When future steps (PRD, architecture, build) introduce design changes, bump to `design-reference-v2.html` rather than mutating v1 — keeps the brainstorm-locked design as a stable reference point.

---

✅ Brainstorm complete. Proceed to `docs/project/requirements/2-PRD.md` after user review.
