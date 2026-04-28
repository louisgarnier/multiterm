# Story 1.2 — IPC roundtrip (preload + ping/pong)

## Goal
A typed IPC roundtrip works between renderer and main: clicking "Ping" sends `app.ping`, main responds, renderer displays the round-trip time. Spike S6 (subscription pattern) is folded in.

## Maps to PRD / Architecture
- Architecture §3 M1 (IPC Bus), R1, R8
- Architecture §7 IPC Design — first channels: `app.ready`, `app.ping`, `app.pong`
- Architecture §9 Spike **S6** — IPC subscription pattern resolved here
- Plan Tasks 1.5, 1.6, 1.7, 1.8, 1.9

## Acceptance Criteria
- [ ] `src/shared/types.ts` exports `LifecycleStage`, `TerminalState`, `Project`, `RegistryFile`, `AppPing`, `AppPong`
- [ ] `src/shared/ipc-channels.ts` has the channel registry (`appReady`, `appPing`, `appPong`, `logForward`, `registryGet`, `registryChanged`)
- [ ] `src/shared/states.ts` exports pure `aggregateProjectState(states)` and `isPending(state)`
- [ ] Vitest configured with environment matchers (`tests/main` → node, `tests/renderer` → jsdom, `tests/shared` → node)
- [ ] `tests/shared/states.test.ts` passes — covers happy path + edge case (empty list) + priority order
- [ ] `src/preload/index.ts` exposes typed `multiterm` global with: `ping`, `appReadySignal(cb)`, `on(channel, cb)`, returning unsubscribe functions where applicable
- [ ] `src/main/ipc.ts` registers `app.ping` handler returning `{ ts, receivedAt }`
- [ ] `src/main/index.ts` broadcasts `app.ready` to renderer once `did-finish-load` fires
- [ ] `src/renderer/main.tsx` mounts `<App />`
- [ ] `src/renderer/App.tsx` shows "MultiTerm — hello", a status line that flips to "yes" on app.ready, a Ping button, and an RTT readout
- [ ] `npm test` runs and the states test suite is all green

## Tasks (from plan)
- [ ] Task 1.5 — Define shared types + IPC channel registry + state aggregation logic
- [ ] Task 1.6 — Configure Vitest with environment matchers
- [ ] Task 1.7 — Build preload bridge with subscription pattern (Spike S6 inline)
- [ ] Task 1.8 — Wire main-process IPC handler for ping/pong
- [ ] Task 1.9 — Build minimal React renderer that exercises IPC

## Dev Tests to write (TDD)
- `tests/shared/states.test.ts` — 6 assertions across 3 describe blocks:
  - `aggregateProjectState`: empty list → `idle`; picks max-priority; priority order verified
  - `isPending`: returns true for awaiting/needs-perm/error/done-unack; false for idle/running

## 🧪 User-Test Checkpoint

After all five tasks are committed, the user verifies:

```bash
npm test
# Expect: tests/shared/states.test.ts passes (3 tests, 6 assertions)

npm run dev
# Expect:
#  • Window opens (as in Story 1.1)
#  • Heading "MultiTerm — hello" visible (no styling yet — that's Story 1.3)
#  • A line that says "app.ready: pending" briefly, then "app.ready: yes"
#  • A button labeled "Ping main process"
#  • Click the button: a line appears with "RTT: <small number> ms"
#  • Multiple clicks update the RTT each time
```

If any of those fail → stop, report.

## Status

**[ ] Pending** — starts after 1.1 closes.
