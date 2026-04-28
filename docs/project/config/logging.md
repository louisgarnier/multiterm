# Logging — MultiTerm

> **Status:** `Draft` — 2026-04-28
> Logging conventions for MultiTerm. The implementation lives in EPIC-1 (Tasks 1.11–1.12 in `docs/plans/2026-04-28-multiterm-mvp.md`); this doc is the source of truth for *what* to log, *how* to format it, and *where* it goes.
> Status flips to `Locked` after EPIC-1's logger module ships and the smoke test in §7 below passes.

---

## 1. Overview

MultiTerm is an Electron desktop app. There is no HTTP API, no separate frontend/backend, and no database. The logging surface is therefore much simpler than the generic template:

- **One process owns the logger** — Electron main (Node.js).
- **Renderer forwards** any log lines via a typed IPC channel (`log.forward`); main writes them to disk.
- **Single log file per day**, in the OS's standard app-data directory.
- **Plain text format**, ANSI-free, structured for `grep`-ability rather than parsing.

Goals:
- Every meaningful event is captured (terminal spawn/exit, lifecycle change, port conflict, validation pass/fail, IPC error).
- No PII, no Claude transcript content, no `~/.claude` internal paths leak into logs (per PRD NFR-10, NFR-11).
- Errors include stack traces.
- Level filter via env var so verbose modes are opt-in.

Non-goals:
- No log shipping to a remote service (single-user, local-only).
- No structured-JSON logs in v1 (plain text is fine for `grep` + manual review; v2 may add JSON output if a log viewer is wanted).
- No log rotation by size — daily files are enough for personal-scale volume.

---

## 2. Log File Layout

| Mode | Location |
|---|---|
| **Production (built app)** | `~/Library/Application Support/MultiTerm/logs/multiterm_YYYY-MM-DD.log` |
| **Development (`npm run dev`)** | same path — uses Electron's `app.getPath('userData')` which defaults to `~/Library/Application Support/<productName>/` |
| **Tests (`npm test`)** | a temporary directory created per test (see Task 1.11 in plan); never writes to the production location |

One file per UTC date. New file auto-created on first write of the day. Files older than ~30 days are NOT auto-pruned in v1; user can delete manually.

**No separate files per component.** A single log file with `[Module]` prefixes is sufficient and matches the project's scale. For filtering, use:
```bash
tail -f ~/Library/Application\ Support/MultiTerm/logs/multiterm_$(date +%F).log | grep '\[PtyManager\]'
```

---

## 3. Line Format

```
[<ISO-8601-timestamp>] [<LEVEL>] [<Module>] <emoji-verb>: <detail>
```

Examples:

```
[2026-04-28T14:23:11.420Z] [INFO] [App] 🚀 startup: version=0.1.0 platform=darwin electron=30.0.0
[2026-04-28T14:23:14.012Z] [INFO] [PtyManager] 📥 spawn: terminalId=t-abc projectId=p1 cwd=/Users/x/Claude/zemaster
[2026-04-28T14:23:18.755Z] [INFO] [Lifecycle] 📤 persist: schema=1 projects=4 size=2.1KB
[2026-04-28T14:23:21.901Z] [INFO] [Promotion] ✅ validate: passed projectId=p1 (4 checks)
[2026-04-28T14:23:25.244Z] [WARN] [TranscriptParser] ⚠️ malformed: line skipped reason=invalid-json projectId=p1
[2026-04-28T14:23:31.881Z] [ERROR] [PortPoller] ❌ poll: lsof exited with code 1
Error: Command failed: lsof -iTCP -sTCP:LISTEN
    at ChildProcess.exithandler (node:child_process:...)
```

Rules:
- **Timestamp** is ISO 8601 in UTC, millisecond precision.
- **Level** is uppercase: `DEBUG` / `INFO` / `WARN` / `ERROR`.
- **Module** is the originating component (see §4 catalogue).
- **emoji-verb** is the standard emoji prefix + a short verb. The emoji conveys at-a-glance what kind of event it is; the verb is what happened.
- **Detail** is a free-form key-value-ish string. Prefer `key=value` pairs for greppability.
- **Errors** are passed as the last argument and produce an extra newline + the full stack trace.

The error level always prefixes verb with `❌` automatically (the logger does this — callers don't need to add it).

---

## 4. Module Catalogue

Use the exact `Module` token from this list. New modules added to this catalogue first.

| Module | Used by | Typical log lines |
|---|---|---|
| `App` | `src/main/index.ts` | `🚀 startup`, `📤 shutdown`, `🔄 activate` |
| `IPC` | `src/main/ipc.ts` | `📥 <channel>`, `❌ handler-error` |
| `Logger` | `src/main/logger.ts` | (rare — only its own initialization) `🚀 init` |
| `Window` | `src/main/window.ts` + `window-state.ts` | `📥 createMainWindow`, `📤 saveBounds`, `📥 loadBounds` |
| `PtyManager` | `src/main/pty/manager.ts` | `📥 spawn`, `📤 exit`, `🔄 resize`, `❌ spawn-failed` |
| `ClaudeDetector` | `src/main/pty/claude-detector.ts` | `📥 detect`, `🔄 reclassify` |
| `StateMachine` | `src/main/pty/state-machine.ts` | `🔄 transition` |
| `Lifecycle` | `src/main/lifecycle/store.ts` + `projects.ts` + `transitions.ts` | `📥 add`, `📤 remove`, `📤 persist`, `🔄 archive`, `🔄 stage-change` |
| `Promotion` | `src/main/lifecycle/validation.ts` | `✅ validate`, `❌ blocked` |
| `PortPoller` | `src/main/ports/poller.ts` | `🔄 poll`, `📥 bind-detected`, `📤 unbind`, `❌ poll` |
| `PortMatcher` | `src/main/ports/matcher.ts` | `🔄 match`, `⚠️ unmatched` |
| `PortConflict` | `src/main/ports/conflict.ts` | `⚠️ conflict`, `📤 suggest` |
| `TranscriptWatcher` | `src/main/claude/transcript-watcher.ts` | `📥 watch`, `🔄 update`, `⚠️ malformed`, `❌ read` |
| `TranscriptParser` | `src/main/claude/transcript-parser.ts` | `🔄 parse`, `⚠️ malformed` |
| `HooksMerger` | `src/main/claude/hooks-merger.ts` | `📥 merge`, `📤 unmerge`, `⚠️ user-edit-conflict` |
| `HooksListener` | `src/main/claude/hooks-listener.ts` | `🚀 socket-open`, `📥 event`, `📤 socket-close`, `❌ socket-error` |
| `Tray` | `src/main/tray.ts` | `🚀 init`, `🔄 badge-update`, `📥 click` |
| `FileTree` | `src/main/files/tree.ts` | `📥 list`, `🔄 watch-update` |
| `ProdRunner` | `src/main/lifecycle/prod-runner.ts` | `📥 start`, `📤 stop`, `🔄 url-poll`, `❌ unreachable` |
| `Renderer/<ComponentName>` | renderer-side via IPC forwarding | E.g. `[Renderer/Sidebar] 📥 click: projectId=p1` — used sparingly, mostly for debugging UX |

---

## 5. Standard Emojis & Verbs

| Emoji | Use case | Sample verbs |
|---|---|---|
| 📥 | Incoming / starting an action | `spawn`, `add`, `start`, `event`, `list`, `click` |
| 📤 | Outgoing / completed action | `exit`, `remove`, `stop`, `persist`, `unmerge` |
| ✅ | Success / passed check | `validate`, `merged`, `connected` |
| ❌ | Error (auto-prefixed by logger.error) | (any verb) |
| ⚠️ | Warning / unexpected-but-handled | `malformed`, `unmatched`, `user-edit-conflict`, `degraded` |
| 🔄 | In-progress / state transition / refresh | `transition`, `poll`, `reclassify`, `watch-update`, `url-poll` |
| 🚀 | Startup / initialization | `startup`, `init`, `socket-open` |

**No other emojis** — keep the set small and consistent so `grep '🚀'` / `grep '⚠️'` is meaningful.

---

## 6. Levels

| Level | When to use | Examples |
|---|---|---|
| `DEBUG` | Per-frame / per-tick noise; verbose only on demand | Every port poll cycle, every IPC ping, every state-machine evaluation |
| `INFO` | Normal events worth seeing in real-time | Project add/remove, terminal spawn/exit, lifecycle transition, validation pass, hook merge |
| `WARN` | Abnormal-but-handled situations | Malformed transcript line skipped, lsof permission-denied for some ports, unknown hook event |
| `ERROR` | Errors that need attention; always include stack | Spawn failure, transcript file unreadable, lsof crashed, IPC handler threw |

Default level: `INFO`.
Override: `MULTITERM_LOG_LEVEL=debug npm run dev` (or set in app preferences in EPIC-11).

---

## 7. Privacy Constraints (PRD NFR-10, NFR-11)

The logger MUST refuse to record:

- **Claude transcript content** — message bodies, tool inputs, tool outputs. Token *counts* are fine; content is not.
- **Absolute paths into `~/.claude/`** — log only the project relative-id (e.g. `projectId=p1`) or a sanitized basename. The transcript path computation happens in main; the path itself is not logged.
- **Any value that could contain user secrets** — `.env` contents, API keys, OAuth tokens, etc. None of these are read by MultiTerm anyway, but the rule is explicit.

The logger is dumb (it logs whatever it receives). The discipline is at the call site:

```ts
// ❌ BAD — leaks transcript content
logger.info('TranscriptParser', '🔄 parse', { content: line });

// ✅ GOOD — logs only metadata
logger.info('TranscriptParser', '🔄 parse', `terminalId=${tid} bytes=${line.length}`);

// ❌ BAD — leaks Claude internal path
logger.info('TranscriptWatcher', '📥 watch', `path=${claudePath}`);

// ✅ GOOD — logs only the project id
logger.info('TranscriptWatcher', '📥 watch', `projectId=${pid}`);
```

A unit test in `tests/main/logger-privacy.test.ts` (added during EPIC-4) asserts that transcripts never appear in log output for a sample session.

---

## 8. Environment Configuration

| Variable | Effect | Default |
|---|---|---|
| `MULTITERM_LOG_LEVEL` | Min level written to file. One of `debug`, `info`, `warn`, `error`. | `info` |
| `MULTITERM_LOG_DIR` | Override log directory (testing only). | `<userData>/logs` |
| `NODE_ENV` | When `development`, `console.log` mirrors of every line are also emitted to stdout for live tailing. | `production` in built app |

In production builds, log lines are NOT mirrored to stdout (the user has no terminal attached). In dev, they are mirrored so `npm run dev` shows live activity.

---

## 9. Example: End-to-End Flow

User clicks "+ new terminal" inside DEV project `zemaster`, then types `claude` in the new shell.

```
[2026-04-28T14:50:01.120Z] [INFO] [Renderer/TerminalTabs] 📥 click: action=newTerminal projectId=p1
[2026-04-28T14:50:01.135Z] [INFO] [IPC] 📥 pty.spawn: projectId=p1
[2026-04-28T14:50:01.142Z] [INFO] [PtyManager] 📥 spawn: terminalId=t-abc projectId=p1 cwd=<sanitized> shell=/bin/zsh pid=14012
[2026-04-28T14:50:01.144Z] [INFO] [StateMachine] 🔄 transition: terminalId=t-abc from=initial to=idle
[2026-04-28T14:50:04.812Z] [INFO] [ClaudeDetector] 🔄 reclassify: terminalId=t-abc isClaude=true
[2026-04-28T14:50:04.815Z] [INFO] [TranscriptWatcher] 📥 watch: terminalId=t-abc projectId=p1
[2026-04-28T14:50:04.819Z] [INFO] [StateMachine] 🔄 transition: terminalId=t-abc from=idle to=running
[2026-04-28T14:50:07.224Z] [INFO] [TranscriptParser] 🔄 parse: terminalId=t-abc bytes=412 type=tool_use
[2026-04-28T14:50:07.228Z] [INFO] [StateMachine] 🔄 transition: terminalId=t-abc from=running to=needs-permission
[2026-04-28T14:50:09.502Z] [INFO] [Renderer/Modal] 📥 click: action=approve toolName=Bash
[2026-04-28T14:50:09.514Z] [INFO] [StateMachine] 🔄 transition: terminalId=t-abc from=needs-permission to=running
```

This sequence proves: tab click → IPC → spawn → state machine → Claude detected → transcript watcher attached → tool needs permission → user approves → back to running.

---

## 10. Implementation Checklist

Mapped to plan tasks. Flips to `Locked` once all are done and §11 smoke passes.

- [ ] **EPIC-1 Task 1.11** — `createLogger` module with daily-rotated file output, level filter, error stack trace
- [ ] **EPIC-1 Task 1.12** — `initLogger` in main; `log.forward` IPC channel; preload bridge `multiterm.log(level, module, verb, ...detail)`; renderer log helper used in App.tsx
- [ ] **EPIC-1 Task 1.20** — verify a log file is written under `~/Library/Application Support/MultiTerm/logs/` after running `npm run dev`
- [ ] **EPIC-2** — every Lifecycle action logs `[Lifecycle]` lines per §4
- [ ] **EPIC-3** — PtyManager + StateMachine log spawn/exit/transition
- [ ] **EPIC-4** — TranscriptWatcher + Parser log per §4. Add `tests/main/logger-privacy.test.ts` asserting no transcript content leaks
- [ ] **EPIC-5** — HooksMerger + Listener log
- [ ] **EPIC-6** — PortPoller + Matcher + Conflict log; downgrade per-poll lines to `DEBUG`
- [ ] **EPIC-7** — Tray init, badge-update, click events log
- [ ] **EPIC-8** — ProdRunner start/stop/url-poll log
- [ ] **EPIC-9** — FileTree list/watch-update log

---

## 11. Smoke Test (run when EPIC-1 ships)

1. `npm run dev` — app launches; check `~/Library/Application Support/MultiTerm/logs/multiterm_$(date +%F).log` has `[App] 🚀 startup` line.
2. Click "Ping main process" in renderer — verify `[IPC] 📥 app.ping` line written.
3. Quit app, relaunch — verify a NEW startup line appended (not overwritten).
4. Set `MULTITERM_LOG_LEVEL=debug` and relaunch — verify DEBUG-level lines now present.
5. Set `MULTITERM_LOG_LEVEL=warn` and relaunch — verify INFO lines suppressed.
6. Trigger an error (e.g. throw inside an IPC handler) — verify `[ERROR]` line includes stack trace.

When all 6 pass: flip status to `Locked`.

---

## 📤 Outputs for 5-EPICS.md

- **Logger module + IPC bridge** are part of EPIC-1's Definition of Done. Any subsequent epic that adds a new module MUST register it in §4 above before the first log line is written.
- **Privacy unit test** is acceptance criteria for EPIC-4 (Claude awareness).
- **Per-poll DEBUG vs INFO downgrade** is acceptance criteria for EPIC-6 (Ports).
- **Hooks event logging** is acceptance criteria for EPIC-5 (opt-in hooks).

---

*→ Once `Locked` (after EPIC-1 smoke passes), proceed to `5-EPICS.md`.*
