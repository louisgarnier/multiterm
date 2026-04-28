# Story 1.6 — Lint, format, hooks, CI

## Goal
Code quality tooling configured: ESLint + Prettier + lefthook pre-commit hooks + GitHub Actions CI workflow on push/PR.

## Maps to PRD / Architecture
- Architecture §1 stack (ESLint, Prettier, lefthook)
- Project conventions (CLAUDE.md): "Tests written same session as code, never after"

## Acceptance Criteria
- [ ] `.eslintrc.cjs` configured for TypeScript + React + react-hooks
- [ ] `.prettierrc` with project conventions (single-quote, trailing-comma-all, printWidth 100, semi true, 2-space tabs)
- [ ] `.prettierignore` excludes `dist/`, `node_modules/`, `coverage/`, `package-lock.json`
- [ ] `npm run lint` clean on the current src tree
- [ ] `npm run format` rewrites only changed files
- [ ] `lefthook.yml` configures pre-commit: lint, format-check, test --bail
- [ ] `npx lefthook install` succeeds and writes hooks under `.git/hooks/`
- [ ] `.github/workflows/ci.yml` runs on push to any branch + PR to main: lint + prettier --check + tests
- [ ] CI workflow uses `macos-14` runner and Node 20

## Tasks (from plan)
- [ ] Task 1.14 — ESLint + Prettier config; clean lint pass on existing code
- [ ] Task 1.15 — lefthook pre-commit hooks installed
- [ ] Task 1.16 — GitHub Actions CI workflow

## Dev Tests to write
None (tooling story).

## 🧪 User-Test Checkpoint

```bash
npm run lint
# Expect: zero errors, zero warnings on a clean tree

npm run format -- --check
# Expect: no formatting issues

# Try a deliberate violation to verify the pre-commit hook works:
printf '\nlet __unused__ = 1\n' >> src/renderer/App.tsx
git add src/renderer/App.tsx
git commit -m "test: should be blocked"
# Expect: lefthook blocks commit, complains about unused var

# Restore:
git checkout -- src/renderer/App.tsx
```

After pushing the story's commits to GitHub:
- The CI workflow at `.github/workflows/ci.yml` runs
- Build is green within ~3 minutes (lint + format + tests)

If the pre-commit doesn't fire, or CI fails on a clean push → stop, report.

## Status

**[ ] Pending**
