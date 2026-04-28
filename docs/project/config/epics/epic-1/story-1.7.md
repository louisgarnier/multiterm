# Story 1.7 — Build skeleton + acceptance smoke (M1)

## Goal
Production build works end-to-end. Manual launch of the built app passes the EPIC-1 acceptance smoke test. Docs (README + CONTRIBUTING + build-log + codebase) are updated. **Milestone M1 reached.**

## Maps to PRD / Architecture
- PRD §1 platform (DMG distribution preview)
- Architecture §1 distribution (electron-builder skeleton; full signing in EPIC-10)

## Acceptance Criteria
- [ ] `electron-builder.yml` skeleton present (no signing yet)
- [ ] `npm run build` produces `dist/main/index.js`, `dist/preload/index.js`, `dist/renderer/index.html` + assets, no errors
- [ ] `npx electron dist/main/index.js` launches the built app — same behavior as dev mode
- [ ] `README.md` written with quickstart, build, test, methodology pointers
- [ ] `CONTRIBUTING.md` written with workflow + git wrapper usage
- [ ] `docs/project/config/build-log.md` updated with EPIC-1 completion entry
- [ ] `docs/project/config/codebase.md` updated with module inventory
- [ ] All Story 1.1–1.6 user-test checkpoints pass when re-run on the fresh build

## Tasks (from plan)
- [ ] Task 1.17 — Skeleton `electron-builder.yml`
- [ ] Task 1.18 — Smoke build verification
- [ ] Task 1.19 — README + CONTRIBUTING
- [ ] Task 1.20 — Update build-log + codebase; M1 acceptance smoke

## Dev Tests to write
None new — final task is run-the-full-suite to confirm zero failures.

## 🧪 User-Test Checkpoint — M1 Acceptance Smoke

This is the formal sign-off for EPIC-1. Run it end-to-end:

```bash
# 1. Build clean
rm -rf dist
npm run build
# Expect: produces dist/main, dist/preload, dist/renderer, no errors

# 2. Launch the built app
npx electron dist/main/index.js
# Expect:
#  • Window opens within 3 seconds
#  • Title: "MultiTerm"
#  • Dark slate background, "MultiTerm — hello" heading
#  • "app.ready: yes" line appears
#  • Click Ping: RTT shown
#  • No errors in the terminal that ran electron

# 3. Verify logs
tail -n 20 "$HOME/Library/Application Support/MultiTerm/logs/multiterm_$(date -u +%Y-%m-%d).log"
# Expect: [App] 🚀 startup line + ping forwarding line

# 4. Verify window state
# Resize the window, quit (Cmd-Q), relaunch via npx electron dist/main/index.js
# Expect: same size + position

# 5. Run full test suite
npm test
# Expect: states + logger + window-state tests all green, zero failures

# 6. Lint + format clean
npm run lint
npm run format -- --check
# Expect: clean

# 7. CI on most recent push to GitHub is green
# Expect: green checkmark on https://github.com/louisgarnier/multiterm/actions
```

When all 7 above pass → EPIC-1 closed, M1 reached. Status flips to `[x] Done` for stories 1.1–1.7. ACTIVE.md advances to EPIC-2 / Story 2.1.

If anything fails → stop, report symptom, do not advance.

## Status

**[ ] Pending**
