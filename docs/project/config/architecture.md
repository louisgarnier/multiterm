# Architecture — MultiTerm

> **Status:** `Locked` — 2026-04-28
> Defines all technical decisions before coding starts. AI must not deviate from this without updating this doc first.
> Adding a dependency or changing architecture requires editing this doc + an entry in `workflow/ADR.md`.
>
> **Build sequencing decisions confirmed at lock:**
> - Spikes S1–S7 (§9) execute just-in-time at the start of each dependent epic. No upfront research week.
> - EPIC-4 (Claude awareness via transcripts) ships before EPIC-5 (hooks opt-in). Hooks are a latency upgrade, not a correctness requirement.

---

## 1. Tech Stack

### Core

| Layer | Choice | Version | Rationale |
|---|---|---|---|
| Language | **TypeScript** | 5.x | Type safety across main + renderer + shared types; matches Electron community standard |
| Runtime / Framework | **Electron** | 30.x | Mature desktop shell, well-trodden path for PTY + native menus + tray; required by PRD constraint |
| Renderer build tool | **Vite** | 5.x | Fast HMR, native ESM, integrates cleanly with Electron via `vite-plugin-electron` |
| UI library | **React** | 18.x | Component model fits the project; large ecosystem |
| Styling | **Tailwind CSS** | 3.x | Atomic utility classes match the wireframe density; no theme runtime overhead |
| State management | **Zustand** | 4.x | Minimal API; fits a small-medium client cleanly; avoids Redux boilerplate; works with both renderer and main process |
| Testing | **Vitest** | 1.x | Same Vite pipeline; fast watch mode; both main + renderer tested |
| Component testing | **@testing-library/react** | 14.x | Behavioral component tests for renderer |
| Linter | **ESLint** | 9.x | Standard for TS/React |
| Formatter | **Prettier** | 3.x | Standard, integrates with ESLint |
| Pre-commit | **lefthook** | 1.x | Lightweight git hook runner; runs lint + format on staged files |

### Native / Bridge

| Layer | Choice | Rationale |
|---|---|---|
| Pseudo-terminal | **node-pty** | The mature option for spawning real PTYs in Node; required for Claude Code interactivity, ANSI handling, signal delivery |
| Terminal renderer | **xterm.js** + `xterm-addon-fit` + `xterm-addon-web-links` | The browser terminal used by VS Code, Hyper, Cursor — proven against heavy output |
| File watcher | **chokidar** | Cross-platform-safe FS watcher; reliable even with macOS FSEvents quirks |
| Markdown viewer | **react-markdown** + `remark-gfm` | Renders the bundled PROD setup guide |
| ID generator | **nanoid** | URL-safe, small footprint, sufficient entropy for project IDs |

### Build & Distribution

| Layer | Choice | Rationale |
|---|---|---|
| Packager | **electron-builder** | Produces signed, notarized `.dmg` + `.zip`; auto-updater compatible (deferred) |
| Native rebuild | **@electron/rebuild** | Required to compile node-pty against Electron's bundled Node version |
| Code signing | **Apple Developer ID** (user-provided cert) | Required for Gatekeeper; without it users see "unidentified developer" |
| Notarization | **electron-notarize** (via electron-builder) | Required by macOS for distribution outside the Mac App Store |

### Data & Storage

| Layer | Choice | Rationale |
|---|---|---|
| Persistent store | **JSON file** at `~/Library/Application Support/MultiTerm/projects.json` | Single-user, no concurrent writes from multiple processes; simplicity beats SQLite for this volume (5–30 projects) |
| Atomic write | **write-temp-then-rename** pattern | Prevents half-written config on crash; standard FS atomicity guarantee on macOS |
| In-memory state | **Zustand stores** in renderer; mirrored from main via IPC | Renderer never reads disk directly; main is sole owner of disk |

### Auth & External Services

| Layer | Choice | Notes |
|---|---|---|
| Auth | **None** | Single-user local app; PRD non-goal NG3 |
| LLM / API | **None** (consumes Claude Code transcripts; does not call Anthropic API directly) | PRD non-goal NG6 |

### Infrastructure

| Layer | Choice | Notes |
|---|---|---|
| Hosting | **N/A** — desktop app, no server | |
| CI/CD | **GitHub Actions** | Build + test on PR; cut DMG on tag |
| Crash / error reporting | **None for v1** (deferred) | Sentry possible v2; for v1 logs go to local files only |

### Approved external packages

```
PRODUCTION DEPENDENCIES
- electron — desktop runtime (required)
- react, react-dom — UI library
- zustand — state store
- node-pty — PTY spawning
- @xterm/xterm, @xterm/addon-fit, @xterm/addon-web-links — terminal rendering
- chokidar — file watcher
- nanoid — ID generation
- react-markdown, remark-gfm — markdown rendering
- date-fns — relative time formatting ("2m ago", "1h", "3d")

DEV DEPENDENCIES
- typescript
- vite, vite-plugin-electron, vite-plugin-electron-renderer
- @vitejs/plugin-react
- tailwindcss, postcss, autoprefixer
- vitest, @testing-library/react, jsdom
- eslint, @typescript-eslint/parser, eslint-plugin-react
- prettier
- lefthook
- electron-builder, @electron/rebuild
- @types/node, @types/react, @types/react-dom

AI must not add packages outside this list. To add: edit this section, justify, then run install.
```

---

## 2. System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  ELECTRON MAIN PROCESS  (Node.js context)                │
│                                                                          │
│   ┌─────────────────┐  ┌────────────────┐  ┌──────────────────┐          │
│   │  PTY Manager    │  │ Lifecycle      │  │   Port Poller    │          │
│   │  (node-pty)     │  │ Store          │  │   (lsof loop)    │          │
│   │  spawns shells  │  │ projects.json  │  │   1–2s interval  │          │
│   └────────┬────────┘  └───────┬────────┘  └────────┬─────────┘          │
│            ↕                   ↕                    ↕                    │
│   ┌─────────────────┐  ┌────────────────┐  ┌──────────────────┐          │
│   │  Transcript     │  │ Hooks          │  │  Tray Manager    │          │
│   │  Watcher        │  │ Listener       │  │  (NSStatusBar    │          │
│   │  (chokidar)     │  │ (opt-in)       │  │   + popover)     │          │
│   └────────┬────────┘  └───────┬────────┘  └────────┬─────────┘          │
│            ↕                   ↕                    ↕                    │
│   ┌────────────────────────────────────────────────────────────┐         │
│   │       State Aggregator + Logger (logs/multiterm_*.log)     │         │
│   └────────────────────────────────────────────────────────────┘         │
│                                  ↕                                       │
│   ┌────────────────────────────────────────────────────────────┐         │
│   │         IPC Bus  (typed channels via contextBridge)        │         │
│   └────────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────┬────────────────────────────────────┘
                                      │ Electron IPC
                                      ↓
┌──────────────────────────────────────────────────────────────────────────┐
│              ELECTRON RENDERER PROCESS  (browser context, React UI)      │
│                                                                          │
│   ┌─────────────────┐   ┌──────────────────────────────────┐             │
│   │   Sidebar       │   │       Project View               │             │
│   │   (projects     │   │   (DEV layout OR PROD layout)    │             │
│   │    + filters)   │   │                                  │             │
│   └─────────────────┘   │  ┌──────────┐ ┌──────────────┐   │             │
│                         │  │ Files    │ │ Terminal     │   │             │
│   ┌─────────────────┐   │  │ Tree     │ │ Tabs         │   │             │
│   │   Tray Popover  │   │  │ (DEV)    │ │ (xterm.js +  │   │             │
│   │   (separate     │   │  │          │ │  L2 panel)   │   │             │
│   │   BrowserWin)   │   │  └──────────┘ └──────────────┘   │             │
│   └─────────────────┘   └──────────────────────────────────┘             │
│            ↕                              ↕                              │
│   ┌────────────────────────────────────────────────────────────┐         │
│   │       Zustand stores (projects, terminals, ports, ui)      │         │
│   └────────────────────────────────────────────────────────────┘         │
└──────────────────────────────────────┬───────────────────────────────────┘
                                       │ Filesystem reads (read-only)
                                       ↓
        ┌──────────────────────────────────────────────────────────────┐
        │ ~/.claude/projects/<sanitized>/<session>.jsonl   (R-only)    │
        │ ~/.claude/settings.json                          (R-only or  │
        │                                                   opt-in     │
        │                                                   merge)     │
        └──────────────────────────────────────────────────────────────┘
                                       ↕
        ┌──────────────────────────────────────────────────────────────┐
        │ APP CONFIG: ~/Library/Application Support/MultiTerm/         │
        │   • projects.json   (registry — atomic writes)               │
        │   • logs/multiterm_YYYY-MM-DD.log                            │
        └──────────────────────────────────────────────────────────────┘
```

**Process model:** one main process (privileged, Node.js APIs, owns all FS + child processes), one main `BrowserWindow` for the app UI, one separate small `BrowserWindow` for the tray popover. Renderer processes have **`contextIsolation: true`** and **`nodeIntegration: false`**; all main/renderer communication is through a typed `contextBridge` API in `src/preload/index.ts`.

**Data flow:**
1. User clicks "+" → renderer dispatches IPC `pty.spawn` → main creates a node-pty session → emits `pty.ready` back → renderer mounts xterm.js → forwards keystrokes via IPC.
2. PTY output → main streams it to renderer via IPC; PTY Manager simultaneously inspects the tail for known patterns (Claude prompt, awaiting input, etc.) → updates state machine.
3. Transcript Watcher (or Hooks Listener if enabled) detects Claude state change → enriches the terminal's L2 metadata (agent, skill, model, last tool, tokens) → IPC push to renderer.
4. Port Poller runs `lsof` → diff against last cycle → if a tracked terminal binds a new port, IPC push to renderer; on conflict, surface conflict modal.
5. Lifecycle Store persists every project mutation atomically → on relaunch, hydrates renderer with the registry.

---

## 3. Component Breakdown

### Main process

#### M1 — IPC Bus (`src/main/ipc.ts` + channel registry)
- **Responsibility:** Define typed IPC channels; route requests to handlers; broadcast state events to renderer.
- **Channels:** see §7 IPC Design.
- **Logging:** `[IPC] <channel> <verb>: <detail>` for every call.

#### M2 — PTY Manager (`src/main/pty/`)
- **Responsibility:** Spawn/destroy PTYs, route I/O to renderer, detect Claude sessions, drive the 6-state machine, emit state transitions.
- **Files:**
  - `manager.ts` — owns the `Map<terminalId, IPty>`, lifecycle hooks
  - `claude-detector.ts` — inspects PTY's foreground process command line via `ps -o command= -p <pid>`; classifies as `claude` vs other
  - `state-machine.ts` — formal FSM: 6 states + transitions + aggregation rules (see §8)
- **Inputs:** IPC `pty.spawn`, `pty.input`, `pty.resize`, `pty.close`; transcript/hook events for Claude-aware transitions.
- **Outputs:** IPC `pty.output`, `pty.state`, `pty.exit`.

#### M3 — Lifecycle Store (`src/main/lifecycle/`)
- **Responsibility:** Sole owner of `projects.json`; atomic writes; broadcast registry mutations.
- **Files:**
  - `store.ts` — load/save with `write-temp-then-rename`; schema version + migrations
  - `projects.ts` — `addProject`, `removeProject`, `archiveProject`, `unarchiveProject`
  - `transitions.ts` — `switchToProd`, `switchToDev` (orchestrates validation + persistence + view flip)
  - `validation.ts` — pure functions implementing FR-19 promotion checks
- **Inputs:** IPC project commands.
- **Outputs:** IPC `registry.changed` push; validation result objects.

#### M4 — Port Poller (`src/main/ports/`)
- **Responsibility:** Run `lsof -iTCP -sTCP:LISTEN -n -P -F pPLn` at adaptive interval; build PID→port map; reconcile against tracked terminal PIDs (transitively, since shells fork children).
- **Files:**
  - `poller.ts` — interval loop with backoff on failure; pauses when no projects loaded
  - `matcher.ts` — `getPidTree(pid: number): number[]` using `pgrep -P` recursively; matches each bound port to nearest known terminal owner
  - `conflict.ts` — given a project's declared ports + a launching PID, computes conflict + next-free-port suggestion
- **Inputs:** PTY Manager exposes spawned PIDs.
- **Outputs:** IPC `ports.update`, `ports.conflict`.

#### M5 — Transcript Watcher (`src/main/claude/transcript-watcher.ts` + `transcript-parser.ts`)
- **Responsibility:** Watch `~/.claude/projects/<sanitized>/` (sanitized = absolute path with `/` → `-`) for `.jsonl` mutations; tail new lines; parse to derive L2 awareness.
- **Detection:** for each tracked Claude PTY, compute its session's `.jsonl` path from the project's cwd; subscribe to that file via chokidar.
- **Outputs:** IPC `claude.l2update` per terminal (debounced 200ms).
- **Resilience:** if file is absent or malformed → fall back to "generic terminal" mode for that tab; log warning; never crash.

#### M6 — Hooks Listener (`src/main/claude/hooks-merger.ts` + `hooks-listener.ts`)
- **Responsibility:** When user opts in, merge MultiTerm-owned entries into `~/.claude/settings.json` non-destructively. Listen on a local Unix domain socket at `~/Library/Application Support/MultiTerm/hooks.sock` for hook event POSTs.
- **Merge format:** appends entries under `hooks.SessionStart`, `hooks.UserPromptSubmit`, `hooks.PreToolUse`, `hooks.PostToolUse`, `hooks.Stop` whose command writes a JSON event to the socket. Each entry tagged `__multiterm: true` for identification on disable/uninstall.
- **Disable path:** removes only entries marked `__multiterm: true`; preserves user's other hooks.
- **Outputs:** IPC `claude.hookevent` per terminal — much lower latency than transcript watching.

#### M7 — Tray Manager (`src/main/tray.ts`)
- **Responsibility:** Create NSStatusBar tray icon; manage badge state derived from State Aggregator; create the popover `BrowserWindow`; show/hide on click.
- **Icon:** template image (single-color PNG with alpha) so macOS auto-handles light/dark mode.
- **Badge:** updated whenever any DEV project's aggregated state enters/leaves `awaiting-input` / `needs-permission` / `error` / `done-unack`.

#### M8 — Logger (`src/main/logger.ts`)
- **Responsibility:** Daily-rotated log file at `~/Library/Application Support/MultiTerm/logs/multiterm_YYYY-MM-DD.log`. Format `[Module] verb: detail` per CLAUDE.md conventions. Emojis: 📥 in, 📤 out, ✅ success, ❌ error, ⚠️ warning, 🚀 startup, 🗄️ db.
- **Levels:** debug / info / warn / error. Default `info`. Override via `MULTITERM_LOG_LEVEL` env var.
- **Constraints:** must not log Claude transcript content or absolute paths into `~/.claude/`.

### Renderer process

#### R1 — Layout + Sidebar (`src/renderer/components/Sidebar.tsx`, `ProjectPill.tsx`, `DevProdToggle.tsx`)
- DEV/PROD top toggle drives a Zustand `mode` selector. Sidebar filters from the projects store accordingly.
- Pin/unpin sidebar collapse to icon strip is local UI state, persisted via IPC `settings.set('sidebarCollapsed', …)`.

#### R2 — Project View (`src/renderer/components/ProjectView.tsx` + `DevProjectView.tsx` + `ProdProjectView.tsx`)
- One component selects DEV vs PROD layout based on the active project's `stage`.
- DEV: `FileTree` + `TerminalTabs`. PROD: status panel + run command + URLs + note.

#### R3 — Terminal Tabs + xterm.js Wrapper (`src/renderer/components/TerminalTabs.tsx`, `Terminal.tsx`, `ClaudePanel.tsx`)
- One xterm.js instance per tab; only the active tab's element is mounted to the DOM (others are virtualized).
- `Terminal.tsx` listens to `pty.output` IPC events and writes to its xterm instance; sends user keystrokes via `pty.input`.
- `ClaudePanel.tsx` shows L2 fields when present.

#### R4 — Files Tree (`src/renderer/components/FileTree.tsx`)
- Renders folder tree from main-process IPC `files.list` (which uses `fs.readdir` + chokidar in main). Read-only display in v1; clicking a file opens it in user's default editor via `shell.openPath`.

#### R5 — Tray Popover (`src/renderer/tray/TrayPopover.tsx`, `TrayPill.tsx`)
- Separate React entry mounted in the popover `BrowserWindow`.
- Single-click expands inline (selected pill fills the lower half of popover with preview message + tokens + path).
- Double-click sends IPC `app.focusProject(id)` to main; main raises the main window and dispatches.

#### R6 — Modals & Dialogs (`src/renderer/components/PromotionDialog.tsx`, `ConflictModal.tsx`, `KillConfirmModal.tsx`, `ProdSetupGuide.tsx`)
- Promotion dialog: receives a `ValidationResult` from main, renders pass/warn/fail rows; "Open setup guide" opens an in-app markdown viewer.
- Conflict modal: fed by `ports.conflict` IPC; enacts choice via `pty.spawn(envExtras: { PORT: '<n>' })`.
- Kill confirmation modal: only shown when closing a tab whose foreground process is non-shell (per FR-09).

#### R7 — Global Ports Palette (`src/renderer/components/GlobalPortsPalette.tsx`)
- ⌘⇧P shortcut; full-screen overlay; lists every bound port with project, process, declared/actual flag, orphan flag.

#### R8 — State stores (`src/renderer/store/`)
- `projects.ts` — registry slice; mirrors main via IPC `registry.changed`.
- `terminals.ts` — per-terminal state, output buffer (small ring), L2 awareness data.
- `ports.ts` — current port map; refreshed on `ports.update`.
- `ui.ts` — view mode, sidebar collapse, modals open, etc.

### Shared

#### S1 — Types (`src/shared/types.ts`)
- All cross-process types live here: `Project`, `LifecycleStage`, `Terminal`, `TerminalState`, `L2Awareness`, `PortBinding`, `ValidationResult`, `IPCEvents`. Imported by both main and renderer.

#### S2 — IPC channels (`src/shared/ipc-channels.ts`)
- Const string registry of all channel names; prevents typos and orphaned listeners.

#### S3 — State logic (`src/shared/states.ts`)
- Pure functions: `aggregateProjectState(terminals)`, `priority`, `isPending(state)`. Used by both processes for consistency.

---

## 4. Data Model

### Persistent: `projects.json`

```typescript
// ~/Library/Application Support/MultiTerm/projects.json
type RegistryFile = {
  schemaVersion: 1;                  // bump on breaking change; main runs migrations
  settings: {
    lastActiveMode: 'dev' | 'prod';
    lastActiveProjectId: string | null;
    sidebarCollapsed: boolean;
    showArchived: boolean;
    windowBounds: { x: number; y: number; width: number; height: number } | null;
    hooksEnabled: boolean;           // Q2 resolution — opt-in
  };
  projects: Project[];
};

type Project = {
  id: string;                        // nanoid, immutable
  name: string;                      // = basename(path) by default; user-editable
  path: string;                      // absolute path on disk; folder must exist
  stage: 'dev' | 'prod' | 'archived';
  addedAt: string;                   // ISO 8601
  lastActiveAt: string;              // ISO 8601 — updated on focus
  fileTreePinned: boolean;           // DEV mode only
  declaredPorts: Array<{ port: number; label: string }>;
  runCommand?: string;               // PROD only — required for promotion
  urls: Array<{ url: string; label: string; kind: 'dev' | 'prod' | 'staging' | 'other' }>;
  note?: string;
};
```

### In-memory only (not persisted)

```typescript
type Terminal = {
  id: string;                        // nanoid, fresh per spawn
  projectId: string;
  pid: number;
  cwd: string;
  shellPath: string;
  state: TerminalState;
  createdAt: number;                 // epoch ms
  lastStateChangeAt: number;
  isClaude: boolean;
  l2?: L2Awareness;
};

type TerminalState =
  | 'idle' | 'running' | 'awaiting-input'
  | 'needs-permission' | 'error' | 'done-unack';

type L2Awareness = {
  agent?: string;
  skill?: string;
  model?: string;
  lastTool?: string;
  tokens?: { input: number; output: number; cacheHit?: number };
  sessionPath?: string;              // path to .jsonl
};

type PortBinding = {
  port: number;
  pid: number;
  process: string;                   // command basename
  ownerTerminalId: string | null;    // null = orphan
  ownerProjectId: string | null;
  declared: boolean;                 // matches a Project.declaredPorts entry
  since: number;                     // epoch ms first detected
};
```

**Invariants:**
- Project IDs are immutable for the project's lifetime; renaming changes `name` only.
- A terminal cannot exist without a parent project; closing a project closes all its terminals first.
- `runCommand` is optional but must be set before DEV→PROD promotion succeeds (FR-19).
- Schema version bump → main writes a backup as `projects.<old>.bak.json` before migrating.

---

## 5. Folder Structure

```
MultiTerm/
├── CLAUDE.md
├── README.md
├── package.json
├── tsconfig.json
├── vite.config.ts
├── electron-builder.yml
├── lefthook.yml
├── .eslintrc.cjs
├── .prettierrc
├── .gitignore
│
├── src/
│   ├── main/                       # Main process — Node.js context
│   │   ├── index.ts                # app entry, lifecycle hooks
│   │   ├── window.ts               # main BrowserWindow + dock icon
│   │   ├── tray.ts                 # NSStatusBar tray + popover window
│   │   ├── ipc.ts                  # channel registry + handlers
│   │   ├── logger.ts
│   │   ├── pty/
│   │   │   ├── manager.ts
│   │   │   ├── claude-detector.ts
│   │   │   └── state-machine.ts
│   │   ├── lifecycle/
│   │   │   ├── store.ts
│   │   │   ├── projects.ts
│   │   │   ├── transitions.ts
│   │   │   └── validation.ts
│   │   ├── ports/
│   │   │   ├── poller.ts
│   │   │   ├── matcher.ts
│   │   │   └── conflict.ts
│   │   ├── claude/
│   │   │   ├── transcript-watcher.ts
│   │   │   ├── transcript-parser.ts
│   │   │   ├── hooks-merger.ts
│   │   │   └── hooks-listener.ts
│   │   └── files/
│   │       └── tree.ts             # fs.readdir + chokidar wrapper
│   │
│   ├── preload/
│   │   └── index.ts                # contextBridge — typed bridge
│   │
│   ├── renderer/                   # Renderer — browser context
│   │   ├── index.html
│   │   ├── main.tsx                # React entry
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ProjectPill.tsx
│   │   │   ├── DevProdToggle.tsx
│   │   │   ├── ArchivedFilter.tsx
│   │   │   ├── ProjectView.tsx
│   │   │   ├── DevProjectView.tsx
│   │   │   ├── ProdProjectView.tsx
│   │   │   ├── FileTree.tsx
│   │   │   ├── TerminalTabs.tsx
│   │   │   ├── Terminal.tsx
│   │   │   ├── ClaudePanel.tsx
│   │   │   ├── PortsPanel.tsx
│   │   │   ├── PortChip.tsx
│   │   │   ├── GlobalPortsPalette.tsx
│   │   │   ├── PromotionDialog.tsx
│   │   │   ├── ConflictModal.tsx
│   │   │   ├── KillConfirmModal.tsx
│   │   │   └── ProdSetupGuide.tsx
│   │   ├── tray/
│   │   │   ├── TrayPopover.tsx
│   │   │   └── TrayPill.tsx
│   │   ├── store/
│   │   │   ├── projects.ts
│   │   │   ├── terminals.ts
│   │   │   ├── ports.ts
│   │   │   └── ui.ts
│   │   ├── ipc/
│   │   │   └── client.ts
│   │   └── styles/
│   │       └── globals.css
│   │
│   └── shared/
│       ├── types.ts
│       ├── ipc-channels.ts
│       └── states.ts
│
├── resources/
│   ├── icon.icns                   # app icon
│   ├── tray-icon@2x.png            # template image (Mac auto light/dark)
│   ├── dmg-background.png
│   └── prod-setup-guide.md         # bundled help doc
│
├── tests/
│   ├── main/
│   │   ├── pty-manager.test.ts
│   │   ├── port-matcher.test.ts
│   │   ├── transcript-parser.test.ts
│   │   ├── lifecycle-store.test.ts
│   │   ├── promotion-validation.test.ts
│   │   └── hooks-merger.test.ts
│   ├── renderer/
│   │   ├── ProjectPill.test.tsx
│   │   ├── DevProdToggle.test.tsx
│   │   ├── PromotionDialog.test.tsx
│   │   └── TerminalTabs.test.tsx
│   ├── shared/
│   │   └── states.test.ts
│   └── fixtures/
│       ├── transcript-sample.jsonl
│       └── lsof-sample.txt
│
├── docs/
│   ├── project/
│   │   ├── requirements/           # read-only templates
│   │   ├── config/                 # generated outputs
│   │   │   ├── brainstorm.md
│   │   │   ├── prd.md
│   │   │   ├── architecture.md     ← THIS FILE
│   │   │   ├── logging.md
│   │   │   ├── build-log.md
│   │   │   ├── codebase.md
│   │   │   ├── mockups/
│   │   │   │   └── design-reference-v1.html
│   │   │   └── epics/
│   │   └── testing/
│   │       └── BLIND_SCENARIOS.md  ← SEALED
│   └── plans/                      # implementation plans (Step 3 + Step 6)
│
├── workflow/
│   ├── ADR.md
│   └── ERRORS.md
│
├── scripts/
│   ├── git_ops.py
│   ├── brainstorm.py
│   └── new_project.py
│
└── logs/                           # gitignored — dev-time logs only
                                    # production logs live in user data dir
```

**Key principles:**
- Strict main/renderer separation. The renderer never imports `node-pty`, `chokidar`, `fs`, or `child_process`. All system calls go through IPC.
- `src/shared/` types are imported by both processes — no runtime code, type-only or pure-function only.
- `resources/` is bundled into the app via electron-builder; `prod-setup-guide.md` is read at runtime via `app.getAppPath()`.
- `scripts/` are the user's existing project utilities (Python); not part of the app build.

---

## 6. Environment Variables

| Variable | Description | Default | Where |
|---|---|---|---|
| `MULTITERM_LOG_LEVEL` | Logger verbosity: `debug` / `info` / `warn` / `error` | `info` | dev + production |
| `MULTITERM_HOOK_SOCKET` | Override Unix-domain socket path for hook events (testing only) | `~/Library/Application Support/MultiTerm/hooks.sock` | dev only |
| `MULTITERM_DATA_DIR` | Override app user-data directory (testing only) | `~/Library/Application Support/MultiTerm/` | dev only |
| `MULTITERM_DEV_TOOLS` | Open Chrome DevTools on launch | unset | dev only |
| `NODE_ENV` | `development` / `production` | `production` in built app | both |

There is no `.env.example` — the app has no required env vars at runtime.

---

## 7. IPC Design

> *Replaces "API Design" since this is a desktop app with no HTTP surface.*

All channels defined in `src/shared/ipc-channels.ts`. Renderer calls go through preload-bridged typed methods. Naming: `<domain>.<verb>`.

| Channel | Direction | Payload | Returns | Notes |
|---|---|---|---|---|
| `app.ready` | main→renderer | `{}` | — | Renderer hydrates initial state |
| `app.focusProject` | renderer→main | `{ projectId }` | `void` | Used by tray double-click |
| `registry.get` | renderer→main | `{}` | `RegistryFile` | Initial load |
| `registry.changed` | main→renderer | `RegistryFile` (full snapshot) | — | After every mutation |
| `project.add` | renderer→main | `{ path }` | `Project` | |
| `project.remove` | renderer→main | `{ projectId }` | `void` | Confirms in main first? No — renderer shows confirm modal, main trusts the call |
| `project.update` | renderer→main | `{ projectId, partial }` | `Project` | name, declaredPorts, runCommand, urls, note |
| `project.archive` | renderer→main | `{ projectId }` | `Project` | |
| `project.unarchive` | renderer→main | `{ projectId }` | `Project` | |
| `project.switchToProd` | renderer→main | `{ projectId }` | `ValidationResult` | Promotion ritual |
| `project.switchToDev` | renderer→main | `{ projectId }` | `void` | No validation |
| `pty.spawn` | renderer→main | `{ projectId, envExtras? }` | `{ terminalId, pid }` | |
| `pty.input` | renderer→main | `{ terminalId, data }` | — | |
| `pty.resize` | renderer→main | `{ terminalId, cols, rows }` | — | |
| `pty.close` | renderer→main | `{ terminalId, force? }` | — | force=true → SIGKILL |
| `pty.output` | main→renderer | `{ terminalId, data }` | — | Streamed |
| `pty.state` | main→renderer | `{ terminalId, state, l2? }` | — | |
| `pty.exit` | main→renderer | `{ terminalId, exitCode }` | — | |
| `ports.snapshot` | renderer→main | `{}` | `PortBinding[]` | Used by global palette |
| `ports.update` | main→renderer | `{ projectId, bindings }` | — | Per-project diff |
| `ports.conflict` | main→renderer | `{ pid, requestedPort, owner, suggestedPort }` | — | Renderer shows ConflictModal |
| `files.list` | renderer→main | `{ projectId, relPath }` | `FileNode[]` | |
| `files.openExternal` | renderer→main | `{ absPath }` | — | shell.openPath |
| `claude.l2update` | main→renderer | `{ terminalId, l2 }` | — | Debounced 200ms |
| `claude.hookevent` | main→renderer | `{ terminalId, event, payload }` | — | When hooks enabled |
| `settings.set` | renderer→main | `{ key, value }` | — | Atomic persisted update |
| `tray.openMain` | main→main | (internal) | — | |
| `prod.open` | renderer→main | `{ projectId }` | — | Spawn run command, poll URL, open browser |
| `prod.stop` | renderer→main | `{ projectId }` | — | |
| `prod.restart` | renderer→main | `{ projectId }` | — | |

**Security:** preload exposes only the listed channels via `contextBridge.exposeInMainWorld('multiterm', {...})`. No `ipcRenderer` is exposed directly.

---

## 8. Key Technical Decisions

| Decision | Options Considered | Choice | Rationale |
|---|---|---|---|
| **Desktop shell** | Electron · Tauri · native SwiftUI | **Electron** | Mature PTY/terminal stack (xterm + node-pty); same path as VS Code/Cursor; lower risk than Tauri for the riskiest piece. PRD-confirmed in §1. |
| **Terminal spawning** | `child_process.spawn` · `node-pty` | **node-pty** | Real PTY needed for ANSI/cursor handling, signal delivery, and `claude` interactive prompts; `child_process` lacks job control. |
| **Terminal rendering** | xterm.js · custom canvas · ink | **xterm.js** | Battle-tested at scale, handles 50k lines/min, maintained by Microsoft. |
| **State management** | Redux · Zustand · Context only | **Zustand** | Smallest API surface, no boilerplate, supports selective subscriptions; appropriate for ~5 stores of moderate size. |
| **Persistent storage** | SQLite · JSON file · electron-store | **JSON file with hand-rolled atomic write** | Volume is small (5–30 projects); SQLite is overkill; `electron-store` lacks the schema-migration + backup-on-version-bump pattern we want. |
| **Port detection** | `lsof` polling · `netstat` · OS kqueue · `ss` | **lsof polling** | Universally available on macOS, well-documented format, no extra deps; native kqueue is overkill for 1–2s freshness. |
| **PID-to-terminal matching** | `pgrep -P` recursion · `proc` parsing · `ps -o ppid=` | **`pgrep -P` recursion** | macOS-portable, simple, avoids parsing `/proc` (which doesn't exist on macOS anyway). |
| **Claude state inference** | Transcript polling · Hooks · Both | **Both, hybrid: transcripts always-on, hooks opt-in for low latency** | Per Q2 resolution. Transcript watcher is the always-on baseline; hooks reduce update lag from ~1s to ~200ms when enabled. |
| **Hook injection mechanism** | Auto-merge on first launch · Opt-in toggle · Don't use hooks | **Opt-in toggle in Settings (FR-14a)** | Per Q2; respects user's `~/.claude/settings.json` ownership. |
| **State machine** | Ad-hoc booleans · XState · custom FSM | **Custom FSM in `src/shared/states.ts`** | XState is over-engineered for 6 states + 1 priority function. Pure-function FSM is testable and shared between main and renderer. |
| **IPC contract** | `ipcMain.handle` + invocations · `EventEmitter`-style · tRPC-electron | **Plain `ipcMain.handle` + typed channel registry** | tRPC-electron adds abstraction; we have ~30 channels, easy to maintain a hand-rolled registry. |
| **Window for tray popover** | Native popover (NSPopover bridge) · Frameless `BrowserWindow` | **Frameless BrowserWindow with `vibrancy: 'sidebar'`** | NSPopover requires native code; frameless window with positioning is the standard Electron tray pattern. |
| **Tab virtualization** | All tabs mounted · Active-only mounted · Suspended | **Active-only mounted; xterm instances destroyed on tab close** | Keeps memory bounded with many tabs; backbuffers are kept in main-process scrollback ring (small). |
| **Code signing** | Apple Developer ID · Self-signed · Unsigned | **Apple Developer ID + notarize** | Required for Gatekeeper without users having to right-click → Open. |

---

## 9. Integration Seams — Verify Before Coding

> *Spike each one before writing production code in that area.*

| Dependency | Format contract | Known edge cases | How to validate before coding |
|---|---|---|---|
| **Claude Code transcript JSONL** (`~/.claude/projects/<sanitized>/<session>.jsonl`) | One JSON object per line. Each line has at minimum `{ role, content, timestamp }`; assistant lines may include `tool_use`, `tool_result`, `model`, `usage`. Schema is owned by Anthropic and may change. | (1) Sanitization function for project path is non-trivial — must match Claude Code's exact algorithm. (2) Files may be partially written when read mid-stream — handle truncated last line. (3) Multiple `.jsonl` per project (one per session). (4) "Active" session detection: most-recently-modified file in project's dir. | **Spike S1:** Open user's actual `~/.claude/projects/-Users-louisgarnier-Claude-MultiTerm/`, list files, parse first 50 + last 50 lines of an active session, document field shapes. Confirm sanitization rule. Time-box: 1 day. |
| **Claude Code hooks** (`~/.claude/settings.json`) | JSON5-tolerant in some Claude versions; schema for `hooks.<EventName>` is a list of `{ matcher, hooks: [{ type, command }] }`. MultiTerm hooks must run a tiny shell command that POSTs JSON to our Unix socket. | (1) User may already have hooks → must merge non-destructively. (2) JSON5 with comments → `JSON.parse` fails. (3) Settings file may not exist yet. (4) Concurrent edit by Claude Code itself. (5) Removing our hooks must leave user's untouched. | **Spike S2:** Write a sample merger that takes a real settings.json (with comments) → adds tagged entries → idempotently removes them. Tag identification: `__multiterm: true` field. Time-box: 1 day. |
| **node-pty** | API: `spawn(shell, args, opts) → IPty`; `.onData(cb)`, `.write(data)`, `.resize(cols, rows)`, `.kill(signal)`, `.pid`. | (1) Native binary must match Electron's Node ABI — `electron-rebuild` post-install. (2) macOS Big Sur+ may prompt for terminal access on first PTY spawn. (3) `IPty.kill()` defaults to SIGHUP — explicit SIGTERM/SIGKILL needed for clean process tree shutdown. (4) `process.title` of shell may differ from `process.argv[0]`. | **Spike S3:** Build smallest Electron app that spawns zsh, displays output via xterm.js, handles resize and Ctrl-C. Confirm no permissions issues on developer Mac. Time-box: 1 day. |
| **lsof** (system CLI) | `lsof -iTCP -sTCP:LISTEN -n -P -F pPLn` returns one record per file descriptor; we need machine-parseable `-F` mode. Each record has fields prefixed (`p<pid>`, `P<protocol>`, `L<login>`, `n<host:port>`). | (1) Records can span multiple lines per record (one field per line). (2) Some processes appear under multiple PIDs (forks). (3) macOS truncates long process names to 16 chars; cross-reference with `ps -o command=` if needed. (4) `lsof` returns nonzero exit on permission denials but still emits partial output. (5) Hostname may be IPv4 or IPv6 (e.g. `*:3000` vs `[::1]:3000`). | **Spike S4:** Run `lsof -F` on dev Mac with 5+ listening processes; write parser; verify against `netstat -an -p tcp \| grep LISTEN`. Time-box: 0.5 day. |
| **xterm.js + addon-fit** | API: `new Terminal({ ... })`, `.open(elem)`, `.write(data)`, `.onData(cb)`, `.dispose()`. fit-addon: `.proposeDimensions()` + `.fit()` for resize. | (1) Webfont loading: need to wait for monospace font before `.open()` or first render is wrong size. (2) Pasting bracketed paste mode requires terminal config. (3) DevicePixelRatio changes on display switch — must re-fit. (4) Must dispose properly to free memory on tab close. | **Spike S5:** Build minimal renderer page with one xterm + node-pty wired through IPC. Verify resize, paste, scrollback. Done as part of S3. |
| **Electron contextBridge typed IPC** | `contextBridge.exposeInMainWorld('multiterm', { ... })`. Renderer types come from `src/shared/`. | (1) Cannot expose functions returning `EventEmitter` directly — must wrap in callback registration. (2) Promise-based `invoke` is one-shot; subscriptions need a `subscribe(channel, cb) → unsubscribe` pattern. (3) Large payloads (e.g. full PTY output buffer) should be streamed, not single-shot. | **Spike S6:** Implement `subscribe`/`unsubscribe` pattern in preload + verify with a test channel. Done early in implementation. |
| **macOS NSStatusBar tray + frameless popover** | Electron `Tray` API + custom `BrowserWindow` for popover. Position popover with `Tray.getBounds()` + screen offset. | (1) Template image must be ≤22pt height + 2x retina version. (2) Popover window dismisses on blur — listen for `blur` event. (3) Re-positioning after Mac display change. (4) Multiple displays — popover must align to the screen the tray icon is on. | **Spike S7:** Build minimal tray with click → popover behavior. Confirm light + dark mode rendering. Time-box: 0.5 day. |

**Rule:** any spike that produces an unanswered "unknown" must be resolved before its dependent epic ships.

---

## 10. Performance & Scalability Assumptions

- **Expected load:** 5–10 projects, 3–5 active terminals at peak, 10–50 listening ports system-wide.
- **This architecture breaks at:**
  - 30+ active xterm.js terminals open at once (DOM/canvas pressure)
  - 500+ listening ports system-wide (`lsof` parse time exceeds 1s)
  - 1000+ projects in registry (sidebar scroll, JSON parse on startup)
  - Transcript files > 100MB (line-by-line tail becomes slow)
- **Scaling path if needed:**
  - Sidebar: virtualize with `react-window` (no work in v1)
  - Terminals: defer xterm instantiation until tab is focused (already designed); aggressive scrollback trimming
  - Ports: move `lsof` polling + parsing to a worker thread; back off to 5s when window is unfocused
  - Transcript: skip-to-end on first read; only tail recent additions

**Performance budgets (per NFRs):**
- Cold launch: < 3s on 2020+ Mac (NFR-01)
- Spawn terminal feedback: < 200ms (NFR-02)
- xterm rendering: keeps up with 50k lines/min (NFR-03)
- Port poll cycle: < 1.5s (NFR-04)
- UI interaction: ≥ 30fps with 5+ terminals (NFR-05)

---

## 11. Platform-Specific Gotchas (macOS)

> Only macOS gotchas apply (PRD constraint: macOS only for v1).

### App distribution & signing

- **Apple Developer ID is required for signing** — without it, users see "unidentified developer" and must right-click → Open on first launch. Acceptable for early personal use; required for any distribution.
- **Notarization is required for Gatekeeper** — `electron-builder` runs `electron-notarize` automatically when given Apple ID credentials. Notarization can take 5–30 minutes; first failure usually means an unsigned binary inside.
- **DMG background image** must be 540×380 retina (i.e. 1080×760 PNG); other sizes render distorted.
- **`hardened-runtime` entitlements** must include `com.apple.security.cs.allow-unsigned-executable-memory` for V8/Electron, plus `com.apple.security.cs.allow-jit`.

### node-pty + native modules

- **node-pty must be rebuilt against Electron's Node version** — run `electron-rebuild` after every install or version bump. Cache locally; CI rebuilds on every install.
- **Universal (Apple Silicon + Intel) binaries** require `--arch=universal` build; node-pty publishes prebuilds for both, but `electron-rebuild` may need explicit flags.
- **First PTY spawn may prompt for "Terminal access"** under macOS TCC if Electron is sandboxed. We do NOT sandbox in v1 — confirm `hardenedRuntime: false` in `electron-builder.yml` is acceptable for our distribution model. If we sandbox later, must add Terminal access entitlement.

### Tray icon

- **Template image only** — single-color PNG with alpha channel and transparent black pixels. Anything else looks wrong in dark mode or under macOS Sonoma's "Reduce transparency" accessibility setting.
- **Tray height ≤ 22pt** — provide both `tray-icon.png` (22×22) and `tray-icon@2x.png` (44×44).
- **Title text on tray** is allowed but eats menu bar space — use icon-only with badge.

### Filesystem watch

- **chokidar uses FSEvents on macOS** which can miss events under heavy load — fall back to `usePolling: true` if we observe missed transcript lines. Default off (FSEvents is fine for our load).
- **Symlinks in `~/.claude/projects/`** — projects can be symlinked. Resolve with `fs.realpath`.
- **Permission for `~/Library/Application Support/`** — always writable for the current user, but `~/.claude/` may have stricter perms set by Claude Code; read-only access is what we need anyway.

### lsof permissions

- **lsof for the current user's processes does not require sudo** — what we need.
- **lsof on system-level processes will show `(unknown)` or skip entirely without sudo** — these are not our problem; we only care about user-spawned processes.

### Window restoration

- **`BrowserWindow.setBounds` after multi-display unplug** can place the window off-screen — always validate against `screen.getDisplayMatching()` and clamp.

### IPC + contextIsolation

- **Renderer crashes do not kill main** — wrap renderer-bound errors in a logger that surfaces them; otherwise silent renderer crashes leave a blank window.
- **Large payloads on IPC** can stall the renderer — chunked streaming for PTY output is required.

---

## 12. Logging Foundation (preview for Step 4)

Per NFR-12, the logger writes `[Module] verb: detail` lines using:
- 📥 `[PtyManager] spawn: terminalId=tab-abc projectId=p1 cwd=/Users/x/Claude/zemaster`
- 📤 `[Lifecycle] persist: schema=1 projects=4 size=2.1KB`
- ✅ `[Promotion] validate: passed projectId=p1 (4 checks)`
- ❌ `[PortPoller] error: lsof exited with code 1`
- ⚠️ `[TranscriptParser] warn: malformed JSONL line skipped path=...`
- 🚀 `[App] startup: version=0.1.0 macOS=14.4 electron=30.0.0`

Step 4 will fully define `logging.md`.

---

## 13. Known Limitations & Technical Debt (v1)

- [ ] No auto-update mechanism (`electron-updater` deferred to v2). Updates are manual `.dmg` installs.
- [ ] No crash reporting (Sentry/etc deferred). Crashes surface only in local logs.
- [ ] No localization (English only).
- [ ] No accessibility audit (basic keyboard nav and focus rings only).
- [ ] No persistence of terminal scrollback across restarts (per Q1 resolution).
- [ ] Tray popover is a frameless window, not a true NSPopover — minor visual differences from native Mac apps.
- [ ] `lsof` polling fixed at 1–2s; no dynamic backoff based on system load (could move to v2 if perf complaints).

---

## 📤 Outputs for 4-LOGGING.md and 5-EPICS.md

**To 4-LOGGING.md:**
- Logger module: `src/main/logger.ts` (single source); renderer logs forward via IPC `log.<level>`
- Log destination: `~/Library/Application Support/MultiTerm/logs/multiterm_YYYY-MM-DD.log` (production); `logs/` in repo root (dev mode)
- Format: `[ISO8601] [Level] [Module] emoji-verb: detail`
- Rotation: daily by date; no built-in size cap (filesize concern is minor — can prune manually)
- Level: `MULTITERM_LOG_LEVEL` env var, default `info`
- Emojis per CLAUDE.md conventions: 📥 in, 📤 out, ✅ success, ❌ error, ⚠️ warning, 🗄️ db, 🚀 startup

**To 5-EPICS.md (proposed epic decomposition):**
- **EPIC-1 — Shell** — Electron + React + Vite skeleton; main↔renderer IPC bus; logger; window restore
- **EPIC-2 — Projects & Lifecycle** — sidebar; add/remove/archive; DEV/PROD toggle + per-project switch; promotion validation; bundled PROD setup guide
- **EPIC-3 — Terminals** — PTY manager; xterm.js wrapper; tabs; close-with-running confirm; basic state machine (3 states first)
- **EPIC-4 — Claude Awareness (L2)** — transcript watcher + parser; classify Claude vs generic; L2 panel UI; full 6-state transitions
- **EPIC-5 — Hooks (opt-in)** — settings toggle; merge/disable into `~/.claude/settings.json`; hook event listener; lower-latency state updates
- **EPIC-6 — Ports** — lsof poller; PID matcher; per-project chip; Ports panel; conflict modal + auto-suggest; global palette ⌘⇧P
- **EPIC-7 — Tray** — NSStatusBar icon; popover window; DEV-only pills; single/double-click behavior; badge count
- **EPIC-8 — PROD operations** — Open/Stop/Restart; URL polling; stop-with-fallback; URL list editing
- **EPIC-9 — File tree** — folder browser; pin/unpin; open in external editor
- **EPIC-10 — Packaging & signing** — electron-builder config; DMG branding; signing + notarization pipeline; CI build
- **EPIC-11 — Polish** — keyboard shortcuts catalog; about/help; relative time formatting; preferences UI

Sequencing: 1 → 2 → 3 → 4 → 6 → 7 → 8 → 9 → 5 → 10 → 11 (5 sequenced after 4 because hooks are an optimization, not a blocker; 10 late to avoid signing/notarization friction during iteration; 11 last).

---

*→ Once locked, proceed to `4-LOGGING.md`, then `5-EPICS.md`.*
*→ Spike S1–S7 (§9) are pre-flight investigations to be done early in their dependent epics.*
