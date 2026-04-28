# Story 1.1 — Repo skeleton + Electron boots

## Goal
`npm run dev` launches an empty Electron window titled "MultiTerm". This unblocks every subsequent story.

## Maps to PRD / Architecture
- PRD §1 platform (macOS Electron DMG)
- Architecture §1 stack, §5 folder structure
- Plan Tasks 1.1, 1.2, 1.3, 1.4

## Acceptance Criteria
- [ ] `package.json` + `tsconfig.json` exist with the agreed scripts and config
- [ ] Folder skeleton present: `src/{main,renderer,preload,shared}/`, `tests/{main,renderer,shared,fixtures}/`
- [ ] `.gitignore` excludes `dist/`, `out/`, `node_modules/`, `coverage/`, `*.tsbuildinfo`
- [ ] All approved dependencies installed via `npm install` (matches architecture §1 list)
- [ ] `vite.config.ts` configured for Electron main + preload + renderer
- [ ] `src/renderer/index.html` minimal page with `#root` div
- [ ] `src/main/index.ts` opens a `BrowserWindow` on `app.whenReady`
- [ ] `src/main/window.ts` factories the window with `contextIsolation: true`, `nodeIntegration: false`
- [ ] `npm run dev` opens a window, no errors in main-process console
- [ ] Window title reads "MultiTerm"
- [ ] Quitting the app via Cmd-Q closes the window cleanly (no orphan processes)

## Tasks (from `docs/plans/2026-04-28-multiterm-mvp.md`)
- [ ] Task 1.1 — Initialize repo skeleton (package.json, tsconfig, folders, gitignore)
- [ ] Task 1.2 — Install Electron + dev dependencies
- [ ] Task 1.3 — Configure Vite for Electron (main + preload + renderer)
- [ ] Task 1.4 — Implement minimal Electron main process (window.ts + index.ts)

## Dev Tests to write
None for this story — there's no business logic yet. The first dev tests appear in Story 1.2 (`tests/shared/states.test.ts`) and Story 1.4 (`tests/main/logger.test.ts`).

## 🧪 User-Test Checkpoint

After all four tasks above are committed, the user verifies:

```bash
npm run dev
```

**Expect:**
- A new Electron window opens within ~3 seconds
- Window title in the menu bar reads **MultiTerm**
- Window is roughly 1440×900 (or screen-fit if smaller display) and centered
- Window is empty — a placeholder element should appear in Story 1.2; for now any blank or default Electron content is acceptable
- DevTools panel may appear detached (development-mode default)
- Cmd-Q quits the app cleanly with no error in the terminal that ran `npm run dev`

If anything looks wrong → stop, report symptom, do not advance to Story 1.2.

## Status

**[→] In progress** — execution started 2026-04-28.
