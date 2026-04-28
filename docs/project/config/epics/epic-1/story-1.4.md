# Story 1.4 — Logger module + IPC log forwarding

## Goal
A daily-rotated file logger lives in main; renderer can forward log lines via IPC. Both startup and ping events show up in the log file.

## Maps to PRD / Architecture
- PRD NFR-12 (logging conventions), NFR-13 (errors with stack traces)
- PRD NFR-10, NFR-11 (privacy — no transcript content, no `~/.claude` paths)
- Logging conventions: `docs/project/config/logging.md`
- Plan Tasks 1.11, 1.12

## Acceptance Criteria
- [ ] `src/main/logger.ts` exports `createLogger({ dir, level })` returning `{ debug, info, warn, error }`
- [ ] Log lines format `[ISO ts] [LEVEL] [Module] verb: detail`
- [ ] `error()` prefixes verb with `❌` automatically and appends stack trace if `Error` passed
- [ ] Daily rotation by date (UTC); file `multiterm_YYYY-MM-DD.log`
- [ ] Level filter respected (`debug` suppressed at `info`)
- [ ] `MULTITERM_LOG_LEVEL` env var override (default `info`)
- [ ] `tests/main/logger.test.ts` passes (3 tests: file write, level suppression, error stack)
- [ ] `IPC` constants include `logForward`
- [ ] `src/main/ipc.ts` exposes `initLogger()` returning the singleton; registers `log.forward` listener that calls `logger[level](module, verb, ...detail)`
- [ ] `src/main/index.ts` initializes the logger before window creation; logs `[App] 🚀 startup` line
- [ ] `src/preload/index.ts` exposes `multiterm.log(level, module, verb, ...detail)` (fire-and-forget `ipcRenderer.send`)
- [ ] Manual smoke: running `npm run dev` then clicking Ping produces an `[IPC] 📥 app.ping` line in the log file

## Tasks (from plan)
- [ ] Task 1.11 — Implement logger module (TDD: write failing test, then `createLogger`)
- [ ] Task 1.12 — Wire logger into main + add `log.forward` IPC channel + preload helper

## Dev Tests to write (TDD)
- `tests/main/logger.test.ts` — 3 tests:
  - **happy path:** writes daily-rotated file with formatted line
  - **level filter:** `debug` suppressed when level=`info`
  - **error path:** `❌` prefix + stack trace appears in output

## 🧪 User-Test Checkpoint

```bash
npm test -- tests/main/logger.test.ts
# Expect: 3 tests pass

npm run dev
# Click "Ping main process" once

# Then in another terminal:
tail -f "$HOME/Library/Application Support/MultiTerm/logs/multiterm_$(date -u +%Y-%m-%d).log"
# Expect to see (timestamps will vary):
#   [...] [INFO] [App] 🚀 startup: version=0.1.0 ...
#   [...] [DEBUG] [IPC] app.ping received: ...
# (DEBUG line only if MULTITERM_LOG_LEVEL=debug — at default INFO it won't show.)
# Click Ping multiple times — verify each click appears as a new line.
```

If the log file isn't created or lines are missing → stop, report.

## Status

**[ ] Pending**
