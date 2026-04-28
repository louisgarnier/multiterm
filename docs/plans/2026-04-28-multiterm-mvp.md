# MultiTerm MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship MultiTerm v1.0 — a Mac DMG Electron app providing status-aware multi-project / multi-terminal Claude Code workflows, with port management and a per-project DEV/PROD/ARCHIVED lifecycle.

**Architecture:** Strict main/renderer split with typed IPC and `contextIsolation: true`. Bite-sized epics, just-in-time spikes, transcript-based Claude awareness as the always-on baseline (hooks-based as opt-in upgrade later).

**Tech Stack:** Electron 30 · TypeScript 5 · React 18 · Vite 5 · Tailwind 3 · Zustand 4 · node-pty · xterm.js · chokidar · Vitest · ESLint · Prettier · electron-builder.

---

## How this plan is organized

This is the **Step 3 master plan**. It covers the entire MVP roadmap because the project's methodology has multiple downstream stages that depend on this:

- **Part A — Master Roadmap** (below): all 11 epics with goals, dependencies, milestones, definition-of-done. Used for sequencing decisions and tracking high-level progress.
- **Part B — Detailed EPIC-1 Plan** (below): bite-sized TDD tasks for the Shell foundation. Coding starts here immediately after this plan is approved.
- **Epics 2–11** get their own bite-sized plans during **Step 6 (Build)**, story by story, using the writing-plans skill again. They are *not* expanded here because:
  1. Step 5 (Epics & Stories) hasn't run yet — story granularity is decided there.
  2. Bite-sized plans for work weeks away will be stale by the time we get there.

---

## Conventions (apply to every task)

- **Git wrapper:** all git operations go through `python3 scripts/git_ops.py …` per project rules. The wrapper exposes: `status`, `commit "<msg>"` (stages all + commits), `push`, `pull`, `log`, `branch <name>`, `checkout <branch>`, `diff`.
- **Commit message format:** `[EPIC-N] type: short description` where `type` is one of `feat | fix | chore | refactor | test | docs`. Example: `[EPIC-1] feat: bootstrap Electron + Vite skeleton`.
- **TDD discipline:** for any module with logic, write the failing test → run it (red) → minimal implementation → run it (green) → refactor if needed → commit.
- **One task ≈ one focused commit.** Tasks may have several steps internally but produce a single coherent change.
- **File paths in this plan are relative to the repo root** `/Users/louisgarnier/Claude/MultiTerm/`.
- **No package added without justification.** Every new dependency must be in §1 of `architecture.md` first; if not, edit that section, document the reason, then run install.
- **Logger before features.** EPIC-1 ships the logger; every subsequent module logs through it from line one.

---

# Part A — Master Roadmap

## Sequencing

```
EPIC-1 (Shell)
   ↓
EPIC-2 (Projects + Lifecycle) ──→ EPIC-9 (File tree)
   ↓
EPIC-3 (Terminals)            ──→ EPIC-6 (Ports)
   ↓
EPIC-4 (Claude awareness)     ──→ EPIC-7 (Tray)
   ↓                          ──→ EPIC-8 (PROD ops)
EPIC-5 (Hooks opt-in)
   ↓
EPIC-10 (Packaging + signing)
   ↓
EPIC-11 (Polish)
```

Linear order: **1 → 2 → 3 → 4 → 6 → 7 → 8 → 9 → 5 → 10 → 11**.

**Why this order:**
- EPIC-1 unblocks everything (shell + IPC + logger).
- EPIC-2 (projects) is needed before any per-project feature.
- EPIC-3 (terminals) is the user-facing core; gives a usable DEV experience at minimum viable level.
- EPIC-4 (Claude awareness via transcripts) is when the app actually delivers on the value prop.
- EPIC-6 (ports) and EPIC-7 (tray) give the at-a-glance polish, but only after we have terminals to observe.
- EPIC-8 (PROD ops) and EPIC-9 (file tree) are scoped per-project features that don't gate each other.
- EPIC-5 (hooks) is the latency upgrade — best done after the transcript-based version proves itself.
- EPIC-10 (packaging) is intentionally late so we don't burn time on signing/notarization friction during iteration.
- EPIC-11 (polish) is last; everything has shipped, now make it pleasant.

## Milestones

| Milestone | After | What it proves |
|---|---|---|
| **M1** | EPIC-1 | App launches, IPC roundtrip works, tests run, logger writes to disk |
| **M2** | EPIC-3 | User can add a project, open a shell tab in it, run `npm dev` — no Claude awareness yet |
| **M3** | EPIC-4 | Claude awareness works: 6 states, project pill aggregates, agent/skill/model panel shows |
| **M4** | EPIC-6 + 7 + 8 + 9 | Full feature set: ports, tray, PROD operations, file tree |
| **M5** | EPIC-5 | Hook-based latency upgrade live for opt-in users |
| **M6** | EPIC-10 | Signed + notarized DMG built by CI on tag push |
| **M7** | EPIC-11 | v1.0 release-ready: shortcuts catalogue, About/Help, preferences UI |

---

## EPIC-1 — Shell foundation

**Goal:** Electron app boots; one main + one renderer + preload bridge; typed IPC roundtrip; React + Tailwind UI shell; Vitest test runner; logger writes to disk; window bounds restored across launches; CI runs lint + test.

**Key files (created):** `package.json`, `tsconfig.json`, `vite.config.ts`, `electron-builder.yml`, `lefthook.yml`, `.eslintrc.cjs`, `.prettierrc`, `src/main/index.ts`, `src/main/window.ts`, `src/main/ipc.ts`, `src/main/logger.ts`, `src/preload/index.ts`, `src/renderer/main.tsx`, `src/renderer/App.tsx`, `src/renderer/index.html`, `src/renderer/styles/globals.css`, `src/renderer/ipc/client.ts`, `src/shared/types.ts`, `src/shared/ipc-channels.ts`, `tests/main/logger.test.ts`, `tests/main/ipc.test.ts`, `tests/shared/states.test.ts`, `.github/workflows/ci.yml`.

**Spike included:** **S6 — IPC subscription pattern** (handled within Tasks 1.7–1.9 below).

**Dependencies:** none.

**Definition of done:**
- `npm run dev` launches a window showing "MultiTerm — hello".
- Click a button in the renderer, see a log line written to `~/Library/Application Support/MultiTerm/logs/multiterm_YYYY-MM-DD.log` proving an IPC roundtrip happened.
- `npm test` runs the test suite via Vitest, all green.
- Resize/move the window, quit the app, relaunch — window opens in the same place at the same size.
- Lint + format clean.
- CI workflow green on push to a feature branch.

**Risks:**
- Native module build for `node-pty` (not yet added in EPIC-1, but install hook for `@electron/rebuild` should be in place so EPIC-3 doesn't trip on it).
- Tailwind + Vite + Electron interplay (Vite needs the right base path for Electron's `file://` loading).
- macOS hardened-runtime defaults — disable for v0 dev builds.

**Detailed plan: see Part B below.**

---

## EPIC-2 — Projects & Lifecycle

**Goal:** User can add/remove/archive projects via the sidebar; persist registry to `projects.json`; toggle DEV/PROD globally; switch a project's stage with the per-project button; promotion ritual runs validation.

**Key files (created):** `src/main/lifecycle/{store,projects,transitions,validation}.ts`, `src/renderer/components/{Sidebar,ProjectPill,DevProdToggle,ArchivedFilter,ProjectView,DevProjectView,ProdProjectView,PromotionDialog,ProdSetupGuide}.tsx`, `src/renderer/store/{projects,ui}.ts`, `resources/prod-setup-guide.md`, related tests.

**Spike included:** none.

**Dependencies:** EPIC-1.

**Definition of done:**
- User clicks "+ Add Project", folder picker opens at `~/Claude/`, selects a folder, project appears in sidebar with status pill, name = folder basename.
- Right-click / `…` menu offers Remove / Archive / Switch to PROD.
- DEV/PROD toggle filters sidebar; archived filter checkbox shows archived overlay.
- Click "Switch to PROD" → validation modal runs (with placeholder run command + URL fields if PROD-specific UI not yet built — flag remaining work).
- Registry persists atomically; relaunch shows projects intact.
- All file paths absolute; no project metadata written into the user's project folders.

**Risks:**
- Schema migration logic untested for v0 — add a "v1 → v1" no-op migration to validate the path.
- Concurrent writes (rare but possible if user rapidly clicks). Use a write queue.

**Acceptance criteria sources:** PRD US-01 to US-06, US-11 to US-15, FR-01 to FR-06, FR-19 to FR-22, FR-39, FR-41.

---

## EPIC-3 — Terminals (basic, generic)

**Goal:** PTY manager spawns shells per project; xterm.js renders them in browser-tab UI; "+" adds a tab; close-with-running-process triggers a confirmation modal. **No Claude awareness yet.**

**Key files (created):** `src/main/pty/{manager,state-machine}.ts` (state machine with simplified 3 states for now: idle / running / exited), `src/renderer/components/{TerminalTabs,Terminal,KillConfirmModal}.tsx`, `src/renderer/store/terminals.ts`, `tests/main/pty-manager.test.ts`.

**Spikes included:** **S3 — node-pty in Electron** + **S5 — xterm.js wiring** (Tasks 3.1 and 3.2).

**Dependencies:** EPIC-1 (IPC, logger), EPIC-2 (projects exist to attach terminals to).

**Definition of done:**
- Click "+" inside a DEV project → new shell tab opens, prompt visible.
- Type `npm dev` (or any command), output renders correctly with ANSI colors, scrollback works.
- Resize window → terminal reflows correctly.
- Click another tab, click back, content persists.
- Close a tab whose foreground is the shell prompt → closes immediately. Close a tab whose foreground is a running process → confirmation modal appears with "Close tab and kill" / "Cancel".
- Tab status dot reflects 3 simplified states (idle / running / exited).
- Aggregated project pill state reflects most-urgent of its tabs.

**Risks:**
- node-pty native binary rebuild — `@electron/rebuild` postinstall must be in place from EPIC-1.
- xterm.js fit-addon resize timing — must wait for monospace font load.
- Closing the app while terminals are running — must SIGHUP cleanly.

**Acceptance criteria sources:** PRD US-06 to US-10 (partial — full 6-state in EPIC-4), US-19 (file tree deferred to EPIC-9 but layout placeholder needed), FR-07 to FR-10, FR-15 (partial: 3 states only here).

---

## EPIC-4 — Claude awareness (L2 via transcripts)

**Goal:** Detect `claude` sessions via foreground process name; watch transcript JSONL files; parse to extract agent / skill / model / last tool / tokens; expand state machine to full 6 states; render the L2 panel above each Claude tab.

**Key files (created):** `src/main/pty/claude-detector.ts`, `src/main/claude/{transcript-watcher,transcript-parser}.ts`, `src/renderer/components/ClaudePanel.tsx`, `src/main/pty/state-machine.ts` upgraded to 6 states, `tests/main/transcript-parser.test.ts`, `tests/main/state-machine.test.ts`, `tests/fixtures/transcript-sample.jsonl`.

**Spike included:** **S1 — transcript schema** (Task 4.1).

**Dependencies:** EPIC-3 (terminals must exist), EPIC-2 (projects must exist for path mapping).

**Definition of done:**
- Run `claude` in a tab → within 1 second, the L2 panel appears showing model + agent (or "session starting").
- As Claude calls tools, "last tool" updates within 1s.
- Token counts update.
- State transitions to `awaiting-input` when Claude finishes a turn (transcript line indicates Claude is awaiting user); to `running` when Claude is processing; to `done-unack` on session end / task complete; to `error` on transcript-emitted error.
- `done-unack` → `idle` the moment that tab gains focus.
- Aggregation priority works: a single tab in `awaiting-input` puts the project pill in `awaiting-input` color even if other tabs are `idle` or `running`.
- Generic terminals (e.g. `npm dev` running) show no L2 panel and use only `idle`/`running`/`exited` (or `error` on non-zero exit).

**Risks:**
- Transcript schema variation across Claude Code versions — pin `schemaVersion` and degrade gracefully.
- Sanitization function for project path → transcript folder name — confirm via S1 with real files.
- Truncated last line during concurrent write — resilience required.

**Acceptance criteria sources:** PRD US-08 to US-10 (full), FR-09 (full taxonomy), FR-11 to FR-18.

---

## EPIC-6 — Ports (live detection + conflict resolution)

**Goal:** Per-project declared ports persisted; `lsof` poller runs every 1–2s; bound ports matched to spawned PIDs (transitively); per-project ports chip on sidebar pill; per-project Ports panel inside project view; conflict modal with auto-suggest next free port; global Ports view via ⌘⇧P.

**Key files (created):** `src/main/ports/{poller,matcher,conflict}.ts`, `src/renderer/components/{PortsPanel,PortChip,GlobalPortsPalette,ConflictModal}.tsx`, `src/renderer/store/ports.ts`, `tests/main/port-matcher.test.ts`, `tests/main/conflict.test.ts`, `tests/fixtures/lsof-sample.txt`.

**Spike included:** **S4 — lsof output parsing** (Task 6.1).

**Dependencies:** EPIC-3 (terminals + spawned PIDs).

**Definition of done:**
- Run `npm dev` in a tab; within 2s the project pill shows `:5173` (or whatever port Vite bound).
- Open Ports panel inside the project; row shows port, PID, process, owning terminal, since.
- Manually launch a process trying to bind 5173 from another project → conflict modal appears with the right info and auto-suggested next free port (`5174`).
- Choose "Use 5174" → app re-spawns with `PORT=5174` env var.
- ⌘⇧P opens global palette listing all bound ports across all tracked projects + flagged orphans.
- Kill button on an orphan row sends SIGTERM (with SIGKILL fallback after 5s) and the row disappears.

**Risks:**
- `lsof` field parsing across macOS versions — use `-F` machine-readable mode.
- PID transitivity — `pgrep -P` recursion may miss children of children if a spawned process forks weirdly. Test with vite (which forks).
- Race condition: process ends mid-poll. Tolerate with eventual consistency.

**Acceptance criteria sources:** PRD US-20 to US-24, US-33 (orphan kill), FR-26 to FR-33.

---

## EPIC-7 — Tray widget

**Goal:** macOS NSStatusBar tray icon; logo + red dot when any DEV project pending + numeric badge of pending DEV projects; click opens popover; popover shows DEV-only horizontal pills; single-click expands inline; double-click focuses main app on project.

**Key files (created):** `src/main/tray.ts`, `src/renderer/tray/{TrayPopover,TrayPill}.tsx`, `resources/tray-icon@2x.png`, related tests.

**Spike included:** **S7 — tray + popover positioning** (Task 7.1).

**Dependencies:** EPIC-2 (projects) + EPIC-4 (Claude awareness — drives "pending" state).

**Definition of done:**
- App launches → tray icon visible in menu bar.
- A DEV project enters `awaiting-input` → red dot appears + badge shows "1".
- Three projects pending → badge shows "3".
- Click tray → popover opens with horizontal scrollable pills for each DEV project.
- Single-click pill → inline expansion shows preview message + tokens + path.
- Double-click pill → main app window focuses + raises + selects that project.
- PROD/ARCHIVED projects do NOT appear.
- Click outside popover → dismisses cleanly.

**Risks:**
- Tray template image — must be single-color PNG with alpha, both 1x and 2x.
- Popover positioning on multi-display setup.
- Window blur event to dismiss popover — must not dismiss when user interacts with popover content.

**Acceptance criteria sources:** PRD US-25 to US-27, FR-34 to FR-38.

---

## EPIC-8 — PROD operations

**Goal:** Open / Stop / Restart buttons functional for PROD projects; URL polling until reachable; Stop with SIGTERM → SIGKILL fallback; URL list editing.

**Key files (created):** `src/main/lifecycle/prod-runner.ts`, updates to `src/renderer/components/ProdProjectView.tsx`, `tests/main/prod-runner.test.ts`.

**Spike included:** none.

**Dependencies:** EPIC-2 (PROD lifecycle UI).

**Definition of done:**
- For a PROD project with `runCommand: "npm run dev"` and a localhost URL:
  - Click "Open in browser" → spawns the run command (visible status spinner: "Starting..."), polls localhost, opens browser when reachable, status flips to "running · uptime 4s".
  - Click "Stop" → SIGTERM, status flips to "stopped" within 1s. If process ignored SIGTERM, SIGKILL after 5s.
  - Click "Restart" → Stop, then Open.
- URL list editable in-place (add / remove URLs).
- Note field editable.
- If "Open in browser" runs and the URL never becomes reachable in 30s → error toast, status reverts to "stopped".

**Risks:**
- Polling interval / give-up logic — keep simple (every 1s, max 30 attempts).
- Stop must clean up child process tree, not just the direct PID.

**Acceptance criteria sources:** PRD US-16 to US-18, FR-19 (PROD view layout), FR-23 to FR-25.

---

## EPIC-9 — File tree

**Goal:** Per-project folder browser inside DEV view; pin/unpin toggle; click a file to open in user's default editor.

**Key files (created):** `src/main/files/tree.ts`, `src/renderer/components/FileTree.tsx`, related tests.

**Spike included:** none.

**Dependencies:** EPIC-2 (project view layout).

**Definition of done:**
- DEV project view shows file tree on the left, populated from project root.
- Folders are expandable; expansion lazy-loads children.
- File icons differentiate folders vs files.
- Click a file → opens in user's default editor via `shell.openPath`.
- Pin/unpin toggle in panel header collapses/expands the tree.
- Pin state persists per project.
- Updates within 1s when files are added/removed externally (chokidar watch).

**Risks:**
- Symlink loops — bound recursion depth.
- Large directories (`node_modules` etc.) — gitignore-aware filtering or hard exclusions for known-noisy folders.

**Acceptance criteria sources:** PRD US-19, FR-39.

---

## EPIC-5 — Hooks (opt-in latency upgrade)

**Goal:** Settings toggle "Enable Claude Code hooks (recommended)"; on opt-in, merge MultiTerm-tagged entries into `~/.claude/settings.json`; open Unix-domain socket listener; receive hook events; lower L2 update latency from ~1s to ~200ms.

**Key files (created):** `src/main/claude/{hooks-merger,hooks-listener}.ts`, settings UI in renderer, `tests/main/hooks-merger.test.ts`.

**Spike included:** **S2 — hooks merge format** (Task 5.1).

**Dependencies:** EPIC-4 (transcript-based awareness must exist as fallback).

**Definition of done:**
- Settings shows toggle "Enable Claude Code hooks". Default OFF.
- Toggle ON → app reads `~/.claude/settings.json`, merges in MultiTerm hook entries (tagged `__multiterm: true`), writes back atomically. Shows "Hooks enabled" confirmation.
- Toggle OFF → reads settings.json, removes only `__multiterm: true` entries, writes back. User's other hooks preserved.
- With hooks enabled, terminal state changes are reflected in UI within 200ms (vs ~1s on transcripts alone).
- Disabling hooks while Claude is running → app falls back to transcripts cleanly without state loss.
- Hook listener handles malformed events gracefully (logs warning, no crash).

**Risks:**
- User's existing hooks may use JSON with comments — must handle / sanitize before parsing.
- Concurrent edit by Claude Code itself — use file lock + retry.
- Unix socket name collisions if multiple MultiTerm instances ever run (defensive: use PID-suffixed socket).

**Acceptance criteria sources:** PRD US-08 to US-10 (latency), FR-13 (hooks path), FR-14a (the entire opt-in flow).

---

## EPIC-10 — Packaging & signing

**Goal:** `electron-builder` produces signed + notarized DMG; CI runs lint + test on every push and builds DMG on tag push.

**Key files (created/edited):** `electron-builder.yml`, `.github/workflows/{ci,release}.yml`, `resources/dmg-background.png`.

**Spike included:** none.

**Dependencies:** all features done (would be premature otherwise).

**Definition of done:**
- `npm run build:mac` produces `MultiTerm-1.0.0.dmg` and `MultiTerm-1.0.0-mac.zip` in `dist/`.
- DMG is code-signed with Apple Developer ID; verify with `codesign --verify --deep --strict --verbose=2 MultiTerm.app`.
- DMG is notarized; verify with `spctl -a -t exec -vv MultiTerm.app`.
- DMG opens, drags to /Applications, opens without Gatekeeper warning.
- CI green on push: lint + test.
- CI on tag `v*` builds + signs + notarizes + uploads DMG to GitHub Releases.

**Risks:**
- Apple Developer ID required (user-provided cert in CI secrets).
- Notarization can fail mysteriously; first attempts often need iteration on entitlements.
- `node-pty` rebuild for distribution must use Electron's exact Node ABI.

**Acceptance criteria sources:** PRD §1 platform, §9 constraints.

---

## EPIC-11 — Polish

**Goal:** Keyboard shortcut catalogue + cheatsheet view; About / Help menu; preferences UI (log level toggle, default folder for "+ Add Project", relative time format); responsive empty states.

**Key files (created):** `src/renderer/components/{ShortcutsCheatsheet,AboutDialog,PreferencesDialog,EmptyState}.tsx`, related tests.

**Spike included:** none.

**Dependencies:** most features done — polishing the existing surface.

**Definition of done:**
- ⌘? opens shortcuts cheatsheet (modal listing every shortcut with description).
- App menu has About → version + acknowledgements.
- Preferences modal: log level, default add-project folder, time format.
- Empty states ("No projects yet") look intentional, not broken.
- All buttons have hover/focus states; keyboard navigation works through sidebar / tabs / modals.

**Risks:** none meaningful.

**Acceptance criteria sources:** PRD §3 Should-Have stories US-30 to US-32, plus general polish.

---

# Part B — Detailed Plan: EPIC-1 (Shell Foundation)

> Bite-sized TDD tasks. Each task ends in one focused commit via `python3 scripts/git_ops.py commit "[EPIC-1] type: message"`. Estimated total time: 2–3 days of focused work.

## Task 1.1: Initialize repo skeleton

**Files:**
- Create: `package.json` (skeleton), `tsconfig.json`, `tsconfig.node.json`
- Create: `src/main/`, `src/renderer/`, `src/preload/`, `src/shared/` (with `.gitkeep` files)
- Create: `tests/main/.gitkeep`, `tests/renderer/.gitkeep`, `tests/shared/.gitkeep`
- Modify: `.gitignore` (add `dist/`, `out/`, `node_modules/`, `coverage/`)

- [ ] **Step 1.1.1 — Write `package.json` skeleton:**

```json
{
  "name": "multiterm",
  "version": "0.1.0",
  "private": true,
  "description": "Multi-project, multi-terminal Claude Code workflow manager for macOS.",
  "author": "Louis Garnier",
  "main": "dist/main/index.js",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .ts,.tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx,css,md}\"",
    "test": "vitest run",
    "test:watch": "vitest",
    "postinstall": "electron-rebuild -f -w node-pty || true"
  }
}
```

- [ ] **Step 1.1.2 — Write `tsconfig.json`:**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM"],
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "allowSyntheticDefaultImports": true,
    "isolatedModules": true,
    "outDir": "dist"
  },
  "include": ["src/**/*", "tests/**/*"]
}
```

- [ ] **Step 1.1.3 — Update `.gitignore`:**

```
# Add to existing .gitignore:
dist/
out/
node_modules/
coverage/
*.tsbuildinfo
```

- [ ] **Step 1.1.4 — Create folder skeleton:**

```bash
mkdir -p src/{main,renderer,preload,shared}
mkdir -p tests/{main,renderer,shared,fixtures}
touch src/main/.gitkeep src/renderer/.gitkeep src/preload/.gitkeep src/shared/.gitkeep
touch tests/main/.gitkeep tests/renderer/.gitkeep tests/shared/.gitkeep tests/fixtures/.gitkeep
```

- [ ] **Step 1.1.5 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] chore: initialize repo skeleton (package.json, tsconfig, folders)"
```

---

## Task 1.2: Install Electron + dev dependencies

**Files:** modifies `package.json` (dependencies, devDependencies).

- [ ] **Step 1.2.1 — Install runtime + dev deps:**

```bash
npm install --save \
  react@^18.3.0 \
  react-dom@^18.3.0 \
  zustand@^4.5.0

npm install --save-dev \
  electron@^30.0.0 \
  vite@^5.4.0 \
  vite-plugin-electron@^0.28.0 \
  vite-plugin-electron-renderer@^0.14.0 \
  @vitejs/plugin-react@^4.3.0 \
  typescript@^5.5.0 \
  @types/node@^22.0.0 \
  @types/react@^18.3.0 \
  @types/react-dom@^18.3.0 \
  vitest@^1.6.0 \
  jsdom@^25.0.0 \
  @testing-library/react@^16.0.0 \
  @testing-library/jest-dom@^6.4.0 \
  eslint@^9.9.0 \
  @typescript-eslint/parser@^8.3.0 \
  @typescript-eslint/eslint-plugin@^8.3.0 \
  eslint-plugin-react@^7.35.0 \
  eslint-plugin-react-hooks@^4.6.0 \
  prettier@^3.3.0 \
  tailwindcss@^3.4.0 \
  postcss@^8.4.0 \
  autoprefixer@^10.4.0 \
  @electron/rebuild@^3.7.0 \
  electron-builder@^24.13.0 \
  lefthook@^1.7.0 \
  date-fns@^3.6.0 \
  nanoid@^5.0.0
```

- [ ] **Step 1.2.2 — Verify install:**

```bash
ls node_modules/electron && echo "electron installed"
ls node_modules/vite && echo "vite installed"
```
Expected: both directories exist.

- [ ] **Step 1.2.3 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] chore: install Electron + dev dependencies"
```

---

## Task 1.3: Configure Vite for Electron (main + renderer + preload)

**Files:**
- Create: `vite.config.ts`
- Create: `src/renderer/index.html`

- [ ] **Step 1.3.1 — Write `vite.config.ts`:**

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import electron from 'vite-plugin-electron';
import renderer from 'vite-plugin-electron-renderer';

export default defineConfig({
  plugins: [
    react(),
    electron([
      {
        entry: 'src/main/index.ts',
        vite: {
          build: {
            outDir: 'dist/main',
            rollupOptions: {
              external: ['electron', 'node-pty', 'chokidar'],
            },
          },
        },
      },
      {
        entry: 'src/preload/index.ts',
        vite: {
          build: {
            outDir: 'dist/preload',
            rollupOptions: { external: ['electron'] },
          },
        },
      },
    ]),
    renderer(),
  ],
  build: {
    outDir: 'dist/renderer',
  },
  root: 'src/renderer',
});
```

- [ ] **Step 1.3.2 — Write minimal `src/renderer/index.html`:**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>MultiTerm</title>
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'" />
  </head>
  <body class="bg-slate-900 text-slate-100">
    <div id="root"></div>
    <script type="module" src="./main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 1.3.3 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] chore: configure Vite for Electron (main, preload, renderer)"
```

---

## Task 1.4: Implement minimal Electron main process

**Files:**
- Create: `src/main/index.ts`
- Create: `src/main/window.ts`

- [ ] **Step 1.4.1 — Write `src/main/window.ts`:**

```ts
import { BrowserWindow, screen } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export function createMainWindow(): BrowserWindow {
  const display = screen.getPrimaryDisplay();
  const { width, height } = display.workAreaSize;

  const win = new BrowserWindow({
    width: Math.min(1440, width - 60),
    height: Math.min(900, height - 60),
    minWidth: 900,
    minHeight: 600,
    title: 'MultiTerm',
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  if (process.env.NODE_ENV === 'development' && process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL);
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    win.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  return win;
}
```

- [ ] **Step 1.4.2 — Write `src/main/index.ts`:**

```ts
import { app, BrowserWindow } from 'electron';
import { createMainWindow } from './window.js';

let mainWindow: BrowserWindow | null = null;

app.whenReady().then(() => {
  mainWindow = createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
```

- [ ] **Step 1.4.3 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] feat: minimal Electron main process opens BrowserWindow"
```

---

## Task 1.5: Define shared types and IPC channel registry

**Files:**
- Create: `src/shared/types.ts`
- Create: `src/shared/ipc-channels.ts`
- Create: `src/shared/states.ts`
- Create: `tests/shared/states.test.ts`

- [ ] **Step 1.5.1 — Write `src/shared/types.ts`:**

```ts
export type LifecycleStage = 'dev' | 'prod' | 'archived';

export type TerminalState =
  | 'idle'
  | 'running'
  | 'awaiting-input'
  | 'needs-permission'
  | 'error'
  | 'done-unack';

export type Project = {
  id: string;
  name: string;
  path: string;
  stage: LifecycleStage;
  addedAt: string;
  lastActiveAt: string;
  fileTreePinned: boolean;
  declaredPorts: Array<{ port: number; label: string }>;
  runCommand?: string;
  urls: Array<{ url: string; label: string; kind: 'dev' | 'prod' | 'staging' | 'other' }>;
  note?: string;
};

export type RegistryFile = {
  schemaVersion: 1;
  settings: {
    lastActiveMode: 'dev' | 'prod';
    lastActiveProjectId: string | null;
    sidebarCollapsed: boolean;
    showArchived: boolean;
    windowBounds: { x: number; y: number; width: number; height: number } | null;
    hooksEnabled: boolean;
  };
  projects: Project[];
};

export type AppPing = { ts: number };
export type AppPong = { ts: number; receivedAt: number };
```

- [ ] **Step 1.5.2 — Write `src/shared/ipc-channels.ts`:**

```ts
export const IPC = {
  // App lifecycle
  appReady: 'app.ready',
  appPing: 'app.ping',          // renderer → main
  appPong: 'app.pong',          // main → renderer (response to ping)

  // Future-stub (just declared so type imports work elsewhere; handlers added in later epics)
  registryGet: 'registry.get',
  registryChanged: 'registry.changed',
} as const;

export type IpcChannel = (typeof IPC)[keyof typeof IPC];
```

- [ ] **Step 1.5.3 — Write `src/shared/states.ts` with aggregation logic:**

```ts
import type { TerminalState } from './types.js';

const PRIORITY: Record<TerminalState, number> = {
  error: 6,
  'needs-permission': 5,
  'awaiting-input': 4,
  'done-unack': 3,
  running: 2,
  idle: 1,
};

export function aggregateProjectState(states: TerminalState[]): TerminalState {
  if (states.length === 0) return 'idle';
  return states.reduce((acc, s) => (PRIORITY[s] > PRIORITY[acc] ? s : acc), states[0]);
}

export function isPending(s: TerminalState): boolean {
  return s === 'awaiting-input' || s === 'needs-permission' || s === 'error' || s === 'done-unack';
}
```

- [ ] **Step 1.5.4 — Write the failing test `tests/shared/states.test.ts`:**

```ts
import { describe, it, expect } from 'vitest';
import { aggregateProjectState, isPending } from '../../src/shared/states.js';

describe('aggregateProjectState', () => {
  it('returns idle for empty list', () => {
    expect(aggregateProjectState([])).toBe('idle');
  });

  it('picks the most urgent state by priority', () => {
    expect(aggregateProjectState(['idle', 'running', 'error'])).toBe('error');
    expect(aggregateProjectState(['idle', 'awaiting-input', 'running'])).toBe('awaiting-input');
    expect(aggregateProjectState(['done-unack', 'running'])).toBe('done-unack');
    expect(aggregateProjectState(['running', 'idle'])).toBe('running');
  });

  it('respects priority order: error > needs-perm > awaiting > done-unack > running > idle', () => {
    expect(aggregateProjectState(['needs-permission', 'awaiting-input'])).toBe('needs-permission');
    expect(aggregateProjectState(['running', 'done-unack'])).toBe('done-unack');
  });
});

describe('isPending', () => {
  it('returns true for awaiting-input, needs-permission, error, done-unack', () => {
    expect(isPending('awaiting-input')).toBe(true);
    expect(isPending('needs-permission')).toBe(true);
    expect(isPending('error')).toBe(true);
    expect(isPending('done-unack')).toBe(true);
  });

  it('returns false for idle and running', () => {
    expect(isPending('idle')).toBe(false);
    expect(isPending('running')).toBe(false);
  });
});
```

- [ ] **Step 1.5.5 — Run tests:**

```bash
npx vitest run tests/shared/states.test.ts
```
Expected: 3 tests pass (after vitest config in Task 1.7). For now, expect either no test runner yet or a pass once vitest is configured.

- [ ] **Step 1.5.6 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] feat: shared types, IPC channel registry, state aggregation logic"
```

---

## Task 1.6: Configure Vitest

**Files:**
- Create: `vitest.config.ts`

- [ ] **Step 1.6.1 — Write `vitest.config.ts`:**

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/**/*.test.{ts,tsx}'],
    globals: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      exclude: ['dist/**', 'tests/**'],
    },
    environmentMatchGlobs: [
      ['tests/renderer/**', 'jsdom'],
      ['tests/main/**', 'node'],
      ['tests/shared/**', 'node'],
    ],
  },
});
```

- [ ] **Step 1.6.2 — Verify by running the states test from Task 1.5:**

```bash
npm test -- tests/shared/states.test.ts
```
Expected: 6 tests pass.

- [ ] **Step 1.6.3 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] test: configure Vitest with environment matchers per test folder"
```

---

## Task 1.7: Build the preload bridge with subscription pattern (Spike S6 inline)

**Files:**
- Create: `src/preload/index.ts`

- [ ] **Step 1.7.1 — Write `src/preload/index.ts` exposing typed bridge:**

```ts
import { contextBridge, ipcRenderer } from 'electron';
import type { AppPing, AppPong } from '../shared/types.js';
import { IPC } from '../shared/ipc-channels.js';

type Unsubscribe = () => void;

const api = {
  ping: (payload: AppPing): Promise<AppPong> =>
    ipcRenderer.invoke(IPC.appPing, payload),

  // Subscription pattern (Spike S6): renderer subscribes to a streamed channel,
  // receives an unsubscribe fn that detaches the listener cleanly.
  on: (channel: string, cb: (payload: unknown) => void): Unsubscribe => {
    const handler = (_e: Electron.IpcRendererEvent, payload: unknown) => cb(payload);
    ipcRenderer.on(channel, handler);
    return () => ipcRenderer.off(channel, handler);
  },

  appReadySignal: (cb: () => void): Unsubscribe => {
    const handler = () => cb();
    ipcRenderer.on(IPC.appReady, handler);
    return () => ipcRenderer.off(IPC.appReady, handler);
  },
};

export type MultiTermAPI = typeof api;

contextBridge.exposeInMainWorld('multiterm', api);
```

- [ ] **Step 1.7.2 — Add typing for renderer:** create `src/renderer/global.d.ts`:

```ts
import type { MultiTermAPI } from '../preload/index.js';

declare global {
  interface Window {
    multiterm: MultiTermAPI;
  }
}
```

- [ ] **Step 1.7.3 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] feat: preload bridge with typed IPC + subscription pattern (S6)"
```

---

## Task 1.8: Wire main-process IPC handler for ping/pong

**Files:**
- Create: `src/main/ipc.ts`
- Modify: `src/main/index.ts` (register IPC, broadcast app.ready)

- [ ] **Step 1.8.1 — Write `src/main/ipc.ts`:**

```ts
import { ipcMain, BrowserWindow } from 'electron';
import { IPC } from '../shared/ipc-channels.js';
import type { AppPing, AppPong } from '../shared/types.js';

export function registerIpc(getWin: () => BrowserWindow | null): void {
  ipcMain.handle(IPC.appPing, async (_e, payload: AppPing): Promise<AppPong> => {
    return { ts: payload.ts, receivedAt: Date.now() };
  });
}

export function broadcastAppReady(win: BrowserWindow): void {
  win.webContents.send(IPC.appReady);
}
```

- [ ] **Step 1.8.2 — Update `src/main/index.ts`:**

```ts
import { app, BrowserWindow } from 'electron';
import { createMainWindow } from './window.js';
import { registerIpc, broadcastAppReady } from './ipc.js';

let mainWindow: BrowserWindow | null = null;

app.whenReady().then(() => {
  registerIpc(() => mainWindow);
  mainWindow = createMainWindow();
  mainWindow.webContents.once('did-finish-load', () => {
    if (mainWindow) broadcastAppReady(mainWindow);
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
```

- [ ] **Step 1.8.3 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] feat: main-process IPC ping/pong handler + app.ready broadcast"
```

---

## Task 1.9: Build minimal React renderer that exercises IPC

**Files:**
- Create: `src/renderer/main.tsx`
- Create: `src/renderer/App.tsx`
- Create: `src/renderer/styles/globals.css`

- [ ] **Step 1.9.1 — Write `src/renderer/styles/globals.css`:**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root {
  margin: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
}
```

- [ ] **Step 1.9.2 — Write `src/renderer/main.tsx`:**

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App.js';
import './styles/globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 1.9.3 — Write `src/renderer/App.tsx`:**

```tsx
import { useEffect, useState } from 'react';

export function App() {
  const [appReady, setAppReady] = useState(false);
  const [pongRtt, setPongRtt] = useState<number | null>(null);

  useEffect(() => {
    const off = window.multiterm.appReadySignal(() => setAppReady(true));
    return off;
  }, []);

  async function handlePing() {
    const sentAt = Date.now();
    const result = await window.multiterm.ping({ ts: sentAt });
    setPongRtt(Date.now() - sentAt);
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 text-slate-100 gap-4">
      <h1 className="text-3xl font-semibold">MultiTerm — hello</h1>
      <p className="text-slate-400 text-sm">
        app.ready: <span className={appReady ? 'text-green-400' : 'text-slate-500'}>{appReady ? 'yes' : 'pending'}</span>
      </p>
      <button
        type="button"
        onClick={handlePing}
        className="px-5 py-2 rounded bg-blue-500 hover:bg-blue-600 text-white text-sm"
      >
        Ping main process
      </button>
      {pongRtt !== null && (
        <p className="text-slate-400 text-sm">RTT: {pongRtt} ms</p>
      )}
    </div>
  );
}
```

- [ ] **Step 1.9.4 — Run dev mode end-to-end:**

```bash
npm run dev
```
Expected: a window opens with the heading "MultiTerm — hello", "app.ready: yes" appears within 1 second, clicking "Ping main process" displays an RTT in ms.

- [ ] **Step 1.9.5 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] feat: minimal React renderer exercises IPC ping/pong"
```

---

## Task 1.10: Configure Tailwind

**Files:**
- Create: `tailwind.config.cjs`
- Create: `postcss.config.cjs`

- [ ] **Step 1.10.1 — Write `tailwind.config.cjs`:**

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/renderer/index.html', './src/renderer/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['SF Mono', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};
```

- [ ] **Step 1.10.2 — Write `postcss.config.cjs`:**

```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 1.10.3 — Restart `npm run dev` and verify Tailwind classes work** (they should already, since we used them in App.tsx).

- [ ] **Step 1.10.4 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] chore: add Tailwind + PostCSS configuration"
```

---

## Task 1.11: Implement the logger module (TDD)

**Files:**
- Create: `src/main/logger.ts`
- Create: `tests/main/logger.test.ts`

- [ ] **Step 1.11.1 — Write the failing test `tests/main/logger.test.ts`:**

```ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createLogger } from '../../src/main/logger.js';

describe('logger', () => {
  let tmpDir: string;
  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'multiterm-log-'));
  });
  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('writes to a daily-rotated log file in the configured dir', () => {
    const logger = createLogger({ dir: tmpDir, level: 'info' });
    logger.info('App', '🚀 startup', 'version=0.1.0');

    const today = new Date().toISOString().slice(0, 10);
    const expected = path.join(tmpDir, `multiterm_${today}.log`);
    expect(fs.existsSync(expected)).toBe(true);
    const contents = fs.readFileSync(expected, 'utf-8');
    expect(contents).toContain('[App] 🚀 startup: version=0.1.0');
  });

  it('respects log level (debug suppressed at info)', () => {
    const logger = createLogger({ dir: tmpDir, level: 'info' });
    logger.debug('Module', 'detail', 'data');
    const today = new Date().toISOString().slice(0, 10);
    const expected = path.join(tmpDir, `multiterm_${today}.log`);
    if (fs.existsSync(expected)) {
      expect(fs.readFileSync(expected, 'utf-8')).not.toContain('Module');
    }
  });

  it('logs errors with ❌ prefix and stack trace if Error is passed', () => {
    const logger = createLogger({ dir: tmpDir, level: 'info' });
    const err = new Error('boom');
    logger.error('Module', 'failed', err);
    const today = new Date().toISOString().slice(0, 10);
    const contents = fs.readFileSync(path.join(tmpDir, `multiterm_${today}.log`), 'utf-8');
    expect(contents).toContain('[Module] ❌ failed');
    expect(contents).toContain('Error: boom');
  });
});
```

- [ ] **Step 1.11.2 — Run test, expect FAIL:**

```bash
npm test -- tests/main/logger.test.ts
```
Expected: failures because `createLogger` is not yet defined.

- [ ] **Step 1.11.3 — Write `src/main/logger.ts`:**

```ts
import fs from 'node:fs';
import path from 'node:path';

type Level = 'debug' | 'info' | 'warn' | 'error';
const LEVEL_ORDER: Record<Level, number> = { debug: 0, info: 1, warn: 2, error: 3 };

export type Logger = {
  debug(module: string, verb: string, ...detail: unknown[]): void;
  info(module: string, verb: string, ...detail: unknown[]): void;
  warn(module: string, verb: string, ...detail: unknown[]): void;
  error(module: string, verb: string, ...detail: unknown[]): void;
};

export type LoggerOptions = { dir: string; level: Level };

export function createLogger(opts: LoggerOptions): Logger {
  fs.mkdirSync(opts.dir, { recursive: true });
  const minOrder = LEVEL_ORDER[opts.level];

  function write(level: Level, module: string, verb: string, detail: unknown[]): void {
    if (LEVEL_ORDER[level] < minOrder) return;

    const today = new Date().toISOString().slice(0, 10);
    const filePath = path.join(opts.dir, `multiterm_${today}.log`);

    const ts = new Date().toISOString();
    const detailParts: string[] = [];
    let extraNewline = '';

    for (const d of detail) {
      if (d instanceof Error) {
        extraNewline += `\n${d.stack ?? d.message}`;
      } else if (typeof d === 'string') {
        detailParts.push(d);
      } else {
        detailParts.push(JSON.stringify(d));
      }
    }

    const line = `[${ts}] [${level.toUpperCase()}] [${module}] ${verb}: ${detailParts.join(' ')}${extraNewline}\n`;
    fs.appendFileSync(filePath, line);
  }

  return {
    debug: (m, v, ...d) => write('debug', m, v, d),
    info: (m, v, ...d) => write('info', m, v, d),
    warn: (m, v, ...d) => write('warn', m, v, d),
    error: (m, v, ...d) => write('error', m, `❌ ${v}`, d),
  };
}
```

- [ ] **Step 1.11.4 — Run test, expect PASS:**

```bash
npm test -- tests/main/logger.test.ts
```
Expected: 3 tests pass.

- [ ] **Step 1.11.5 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] feat: file-based logger with daily rotation, level filtering, error stack traces"
```

---

## Task 1.12: Wire logger into main process and bridge for renderer log forwarding

**Files:**
- Modify: `src/main/index.ts` (instantiate logger, pass to ipc)
- Modify: `src/main/ipc.ts` (add `log.forward` channel; renderer can forward log lines)
- Modify: `src/shared/ipc-channels.ts` (add `logForward` channel name)
- Modify: `src/preload/index.ts` (expose `log(level, module, verb, ...detail)` helper)

- [ ] **Step 1.12.1 — Add channel constant in `src/shared/ipc-channels.ts`:**

```ts
export const IPC = {
  appReady: 'app.ready',
  appPing: 'app.ping',
  appPong: 'app.pong',
  logForward: 'log.forward',
  registryGet: 'registry.get',
  registryChanged: 'registry.changed',
} as const;
```

- [ ] **Step 1.12.2 — Add log forwarding handler in `src/main/ipc.ts`:**

```ts
import { ipcMain, BrowserWindow, app } from 'electron';
import path from 'node:path';
import { IPC } from '../shared/ipc-channels.js';
import type { AppPing, AppPong } from '../shared/types.js';
import { createLogger, type Logger } from './logger.js';

let logger: Logger | null = null;

export function initLogger(): Logger {
  const dir = path.join(app.getPath('userData'), 'logs');
  const level = (process.env.MULTITERM_LOG_LEVEL as 'debug' | 'info' | 'warn' | 'error') ?? 'info';
  logger = createLogger({ dir, level });
  return logger;
}

export function registerIpc(getWin: () => BrowserWindow | null): void {
  ipcMain.handle(IPC.appPing, async (_e, payload: AppPing): Promise<AppPong> => {
    logger?.debug('IPC', 'app.ping received', { ts: payload.ts });
    return { ts: payload.ts, receivedAt: Date.now() };
  });

  ipcMain.on(IPC.logForward, (_e, level: 'debug' | 'info' | 'warn' | 'error', module: string, verb: string, ...detail: unknown[]) => {
    if (!logger) return;
    logger[level](module, verb, ...detail);
  });
}

export function broadcastAppReady(win: BrowserWindow): void {
  win.webContents.send(IPC.appReady);
}
```

- [ ] **Step 1.12.3 — Init logger in `src/main/index.ts`:**

```ts
import { app, BrowserWindow } from 'electron';
import { createMainWindow } from './window.js';
import { registerIpc, broadcastAppReady, initLogger } from './ipc.js';

let mainWindow: BrowserWindow | null = null;

app.whenReady().then(() => {
  const logger = initLogger();
  logger.info('App', '🚀 startup', `version=${app.getVersion()} platform=darwin`);

  registerIpc(() => mainWindow);
  mainWindow = createMainWindow();
  mainWindow.webContents.once('did-finish-load', () => {
    if (mainWindow) broadcastAppReady(mainWindow);
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
```

- [ ] **Step 1.12.4 — Add log helper to preload `src/preload/index.ts`:**

```ts
import { contextBridge, ipcRenderer } from 'electron';
import type { AppPing, AppPong } from '../shared/types.js';
import { IPC } from '../shared/ipc-channels.js';

type Unsubscribe = () => void;
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const api = {
  ping: (payload: AppPing): Promise<AppPong> =>
    ipcRenderer.invoke(IPC.appPing, payload),

  log: (level: LogLevel, module: string, verb: string, ...detail: unknown[]) =>
    ipcRenderer.send(IPC.logForward, level, module, verb, ...detail),

  appReadySignal: (cb: () => void): Unsubscribe => {
    const handler = () => cb();
    ipcRenderer.on(IPC.appReady, handler);
    return () => ipcRenderer.off(IPC.appReady, handler);
  },

  on: (channel: string, cb: (payload: unknown) => void): Unsubscribe => {
    const handler = (_e: Electron.IpcRendererEvent, payload: unknown) => cb(payload);
    ipcRenderer.on(channel, handler);
    return () => ipcRenderer.off(channel, handler);
  },
};

export type MultiTermAPI = typeof api;
contextBridge.exposeInMainWorld('multiterm', api);
```

- [ ] **Step 1.12.5 — Manually verify by running `npm run dev`, clicking Ping**, then checking that `~/Library/Application Support/MultiTerm/logs/multiterm_<today>.log` contains both the startup line and the IPC ping line.

- [ ] **Step 1.12.6 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] feat: wire logger into main + renderer log forwarding via IPC"
```

---

## Task 1.13: Window state restoration

**Files:**
- Create: `src/main/window-state.ts`
- Modify: `src/main/window.ts` (use saved bounds if any)
- Modify: `src/main/index.ts` (persist bounds on close)

- [ ] **Step 1.13.1 — Write the failing test `tests/main/window-state.test.ts`:**

```ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { loadBounds, saveBounds, type WindowBounds } from '../../src/main/window-state.js';

describe('window-state', () => {
  let tmpDir: string;
  beforeEach(() => { tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'multiterm-ws-')); });
  afterEach(() => { fs.rmSync(tmpDir, { recursive: true, force: true }); });

  it('returns null when no state file exists', () => {
    expect(loadBounds(tmpDir)).toBeNull();
  });

  it('saves and loads window bounds', () => {
    const bounds: WindowBounds = { x: 100, y: 200, width: 1280, height: 800 };
    saveBounds(tmpDir, bounds);
    expect(loadBounds(tmpDir)).toEqual(bounds);
  });

  it('returns null on malformed state file', () => {
    fs.writeFileSync(path.join(tmpDir, 'window-state.json'), 'not json');
    expect(loadBounds(tmpDir)).toBeNull();
  });
});
```

- [ ] **Step 1.13.2 — Run test, expect FAIL:**

```bash
npm test -- tests/main/window-state.test.ts
```

- [ ] **Step 1.13.3 — Write `src/main/window-state.ts`:**

```ts
import fs from 'node:fs';
import path from 'node:path';

export type WindowBounds = { x: number; y: number; width: number; height: number };

const FILE = 'window-state.json';

export function loadBounds(dir: string): WindowBounds | null {
  const p = path.join(dir, FILE);
  if (!fs.existsSync(p)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(p, 'utf-8'));
    if (
      typeof data?.x === 'number' &&
      typeof data?.y === 'number' &&
      typeof data?.width === 'number' &&
      typeof data?.height === 'number'
    ) {
      return data;
    }
    return null;
  } catch {
    return null;
  }
}

export function saveBounds(dir: string, bounds: WindowBounds): void {
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, FILE);
  const tmp = `${p}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(bounds));
  fs.renameSync(tmp, p);
}
```

- [ ] **Step 1.13.4 — Run test, expect PASS:**

```bash
npm test -- tests/main/window-state.test.ts
```

- [ ] **Step 1.13.5 — Wire into `src/main/window.ts`:**

```ts
import { BrowserWindow, screen, app } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadBounds, saveBounds } from './window-state.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export function createMainWindow(): BrowserWindow {
  const userData = app.getPath('userData');
  const saved = loadBounds(userData);
  const display = screen.getPrimaryDisplay();
  const { width, height } = display.workAreaSize;

  const bounds = saved ?? {
    x: Math.round((width - Math.min(1440, width - 60)) / 2),
    y: Math.round((height - Math.min(900, height - 60)) / 2),
    width: Math.min(1440, width - 60),
    height: Math.min(900, height - 60),
  };

  const win = new BrowserWindow({
    ...bounds,
    minWidth: 900,
    minHeight: 600,
    title: 'MultiTerm',
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  const persist = () => saveBounds(userData, win.getBounds());
  win.on('close', persist);
  win.on('moved', persist);
  win.on('resized', persist);

  if (process.env.NODE_ENV === 'development' && process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL);
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    win.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  return win;
}
```

- [ ] **Step 1.13.6 — Manual smoke test:** run `npm run dev`, resize and move window, quit, relaunch — bounds should be preserved.

- [ ] **Step 1.13.7 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] feat: persist + restore main window bounds across launches"
```

---

## Task 1.14: ESLint + Prettier configuration

**Files:**
- Create: `.eslintrc.cjs`
- Create: `.prettierrc`
- Create: `.prettierignore`

- [ ] **Step 1.14.1 — Write `.eslintrc.cjs`:**

```js
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaVersion: 2022, sourceType: 'module', project: './tsconfig.json' },
  plugins: ['@typescript-eslint', 'react', 'react-hooks'],
  extends: ['eslint:recommended', 'plugin:@typescript-eslint/recommended', 'plugin:react/recommended', 'plugin:react-hooks/recommended'],
  settings: { react: { version: 'detect' } },
  ignorePatterns: ['dist/', 'node_modules/', 'coverage/'],
  rules: {
    'react/react-in-jsx-scope': 'off',
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
  },
};
```

- [ ] **Step 1.14.2 — Write `.prettierrc`:**

```json
{
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "semi": true
}
```

- [ ] **Step 1.14.3 — Write `.prettierignore`:**

```
dist/
node_modules/
coverage/
package-lock.json
```

- [ ] **Step 1.14.4 — Run `npm run lint`** — fix any reported issues in our code.

- [ ] **Step 1.14.5 — Run `npm run format`.**

- [ ] **Step 1.14.6 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] chore: ESLint + Prettier configuration; clean lint pass"
```

---

## Task 1.15: lefthook pre-commit setup

**Files:**
- Create: `lefthook.yml`

- [ ] **Step 1.15.1 — Write `lefthook.yml`:**

```yaml
pre-commit:
  parallel: true
  commands:
    lint:
      glob: '*.{ts,tsx}'
      run: npx eslint {staged_files}
    format:
      glob: '*.{ts,tsx,css,md,json}'
      run: npx prettier --check {staged_files}
    test:
      run: npm test -- --run --bail
```

- [ ] **Step 1.15.2 — Install hooks:**

```bash
npx lefthook install
```

- [ ] **Step 1.15.3 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] chore: lefthook pre-commit hooks (lint, format, tests)"
```

---

## Task 1.16: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1.16.1 — Write `.github/workflows/ci.yml`:**

```yaml
name: CI
on:
  push:
    branches: [main, '**']
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npx prettier --check "src/**/*.{ts,tsx,css,md}"
      - run: npm test -- --run
```

- [ ] **Step 1.16.2 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] ci: macOS GitHub Actions workflow (lint, format, tests)"
```

---

## Task 1.17: Skeleton `electron-builder.yml`

**Files:**
- Create: `electron-builder.yml`

- [ ] **Step 1.17.1 — Write `electron-builder.yml` (skeleton — full signing in EPIC-10):**

```yaml
appId: com.louisgarnier.multiterm
productName: MultiTerm
directories:
  output: out
  buildResources: resources
files:
  - dist/**
  - package.json
mac:
  category: public.app-category.developer-tools
  target:
    - dmg
    - zip
  hardenedRuntime: false
  gatekeeperAssess: false
  artifactName: ${productName}-${version}-${arch}.${ext}
dmg:
  title: ${productName} ${version}
```

- [ ] **Step 1.17.2 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] chore: electron-builder skeleton config (no signing yet)"
```

---

## Task 1.18: Smoke build verification

**Files:** none added; this is a verification step.

- [ ] **Step 1.18.1 — Build:**

```bash
npm run build
```
Expected: produces `dist/main/index.js`, `dist/preload/index.js`, `dist/renderer/index.html` + assets, no errors.

- [ ] **Step 1.18.2 — Manual launch:**

```bash
npx electron dist/main/index.js
```
Expected: app window opens, shows "MultiTerm — hello", Ping button works, log file written to `~/Library/Application Support/MultiTerm/logs/`.

- [ ] **Step 1.18.3 — No commit** (verification only). If issues are found, return to the relevant task.

---

## Task 1.19: README + CONTRIBUTING

**Files:**
- Create: `README.md` (project overview + quickstart)
- Create: `CONTRIBUTING.md` (dev workflow per project methodology)

- [ ] **Step 1.19.1 — Write `README.md`:**

```markdown
# MultiTerm

A Mac desktop app for managing multiple Claude Code projects with status-aware visual indicators, port management, and a per-project DEV/PROD lifecycle.

**Status:** in development (v0.1.0 — EPIC-1 shell foundation).

## Quickstart

\`\`\`bash
npm install
npm run dev
\`\`\`

## Build

\`\`\`bash
npm run build
\`\`\`

## Tests

\`\`\`bash
npm test
\`\`\`

## Project methodology

This project follows a staged spec-first methodology — see `docs/project/requirements/REQUIREMENTS_WORKFLOW.md`.

Source-of-truth docs:
- [docs/project/config/brainstorm.md](docs/project/config/brainstorm.md)
- [docs/project/config/prd.md](docs/project/config/prd.md)
- [docs/project/config/architecture.md](docs/project/config/architecture.md)
- [docs/plans/2026-04-28-multiterm-mvp.md](docs/plans/2026-04-28-multiterm-mvp.md)
```

- [ ] **Step 1.19.2 — Write `CONTRIBUTING.md`:**

```markdown
# Contributing

Read CLAUDE.md first. Stack and conventions live there.

## Workflow

1. Read \`docs/project/config/build-log.md\` to know the current stage and blockers.
2. Read \`docs/project/config/codebase.md\` for module map.
3. Check \`workflow/ERRORS.md\` for known issues in your area.
4. Follow the implementation plan at \`docs/plans/2026-04-28-multiterm-mvp.md\`.

## Git

Use the wrapper:

\`\`\`bash
python3 scripts/git_ops.py status
python3 scripts/git_ops.py commit "[EPIC-N] type: short description"
python3 scripts/git_ops.py push
\`\`\`

## Tests

Write tests with the same change. Run via \`npm test\`. Pre-commit hooks run lint + format + tests on staged files.
```

- [ ] **Step 1.19.3 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] docs: README + CONTRIBUTING with project workflow pointers"
```

---

## Task 1.20: EPIC-1 acceptance smoke test (Definition of Done)

**Files:** none added; verification only.

- [ ] **Step 1.20.1 — Run `npm run dev`:** verify window opens, "MultiTerm — hello" displayed.

- [ ] **Step 1.20.2 — Click "Ping main process":** verify RTT shown.

- [ ] **Step 1.20.3 — Open `~/Library/Application Support/MultiTerm/logs/multiterm_<today>.log`:** verify startup line + ping forwarding line written.

- [ ] **Step 1.20.4 — Resize/move window, quit, relaunch:** verify window opens at same place + size.

- [ ] **Step 1.20.5 — `npm test`:** verify all tests pass (logger, window-state, states aggregation).

- [ ] **Step 1.20.6 — `npm run lint && npx prettier --check "src/**/*.{ts,tsx,css}"`:** verify clean.

- [ ] **Step 1.20.7 — Update `docs/project/config/build-log.md`** with an EPIC-1 completion entry (date, what was built, smoke test passed).

- [ ] **Step 1.20.8 — Update `docs/project/config/codebase.md`** with an inventory of modules added (logger, window, ipc, states, types, ipc-channels, App, main.tsx).

- [ ] **Step 1.20.9 — Commit:**

```bash
python3 scripts/git_ops.py commit "[EPIC-1] docs: build-log + codebase.md updated; EPIC-1 acceptance passed (M1)"
```

**M1 reached.** EPIC-1 done. Stop and confirm with user before starting EPIC-2.

---

# Self-Review

**Spec coverage check (Part B → PRD/Architecture):**
- ✅ FR-39 (window bounds restore) → Task 1.13
- ✅ NFR-12, NFR-13 (logging conventions) → Task 1.11–1.12
- ✅ FR-13 (200ms latency goal — for hooks; not exercised in EPIC-1)
- ✅ Architecture §1 (stack pinned) → Task 1.2
- ✅ Architecture §3 (M1, M8, S1, S2, S3 modules introduced) → Tasks 1.4, 1.5, 1.7, 1.8, 1.11
- ✅ Architecture §5 (folder structure) → Task 1.1
- ✅ Architecture §7 (IPC design — first channels) → Task 1.5, 1.7, 1.8
- ✅ Architecture §9 spike S6 (IPC subscription pattern) → Task 1.7

**Placeholder scan:** none. All tasks contain executable code, exact file paths, and concrete commands.

**Type consistency check:**
- `Logger` interface in `src/main/logger.ts` ↔ `Logger` returned from `createLogger` ↔ used in `src/main/ipc.ts` — consistent.
- `MultiTermAPI` exported from `src/preload/index.ts` ↔ declared on `window.multiterm` in `src/renderer/global.d.ts` — consistent.
- `IPC` constant in `src/shared/ipc-channels.ts` is referenced by both main, preload, and (transitively) renderer — same source.
- `AppPing`/`AppPong` types defined once in `src/shared/types.ts`, used by all three processes — consistent.

**Scope check:** Part A is roadmap-level only; Part B (EPIC-1) is fully executable. Epics 2–11 deliberately deferred to Step 6 per project methodology, with goals and DoD captured in Part A.

---

# Execution Handoff

Plan complete and saved to `docs/plans/2026-04-28-multiterm-mvp.md`.

**Two execution options for Part B (EPIC-1):**

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration with safety checkpoints.

**2. Inline Execution** — execute tasks in this session using `superpowers:executing-plans`, batch execution with manual checkpoints for review.

User's call after this plan is approved.
