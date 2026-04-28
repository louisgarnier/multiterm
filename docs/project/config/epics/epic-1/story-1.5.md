# Story 1.5 — Window state restoration

## Goal
Window bounds (x, y, width, height) persist across app restarts. First-launch defaults to centered ~1440×900 (or screen-fit).

## Maps to PRD / Architecture
- PRD FR-39 (window state restore), NFR-09 (atomic writes)
- Plan Task 1.13

## Acceptance Criteria
- [ ] `src/main/window-state.ts` exports `loadBounds(dir): WindowBounds | null` and `saveBounds(dir, bounds)`
- [ ] `saveBounds` uses write-temp-then-rename for atomicity
- [ ] `loadBounds` returns `null` if file missing or malformed (does not throw)
- [ ] `src/main/window.ts` reads saved bounds, falls back to centered defaults
- [ ] Persists on `close`, `moved`, `resized` events
- [ ] `tests/main/window-state.test.ts` passes (3 tests: missing file, save+load round-trip, malformed file)

## Tasks (from plan)
- [ ] Task 1.13 — Window state restoration (TDD: write tests first)

## Dev Tests to write (TDD)
- `tests/main/window-state.test.ts` — 3 tests:
  - **edge case:** returns `null` when no state file exists
  - **happy path:** save then load round-trip preserves all four fields
  - **failure case:** malformed JSON returns `null` (no throw)

## 🧪 User-Test Checkpoint

```bash
npm test -- tests/main/window-state.test.ts
# Expect: 3 tests pass

npm run dev
# In the app: resize window to a noticeable size (e.g. 1000×600), drag it to a corner
# Quit with Cmd-Q
# Relaunch:
npm run dev
# Expect: window opens at the same size and corner

# Then test the empty-state path:
rm "$HOME/Library/Application Support/MultiTerm/window-state.json"
npm run dev
# Expect: window opens centered at default ~1440×900
```

If bounds aren't restored or the rm-then-relaunch doesn't center properly → stop, report.

## Status

**[ ] Pending**
