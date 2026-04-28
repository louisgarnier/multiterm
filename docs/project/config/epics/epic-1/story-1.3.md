# Story 1.3 — Tailwind + dark theme

## Goal
Tailwind utility classes render correctly; the app uses a dark slate theme matching the design reference. No flash of unstyled content.

## Maps to PRD / Architecture
- Architecture §1 stack (Tailwind 3.x)
- `docs/project/config/mockups/design-reference-v1.html` — visual baseline

## Acceptance Criteria
- [ ] `tailwind.config.cjs` content globs cover `src/renderer/index.html` + `src/renderer/**/*.{ts,tsx}`
- [ ] `postcss.config.cjs` has `tailwindcss` and `autoprefixer` plugins
- [ ] `src/renderer/styles/globals.css` includes `@tailwind base/components/utilities`
- [ ] App renders with dark slate-900 background, slate-100 text, blue-500 button
- [ ] No FOUC — first paint is already styled
- [ ] No console warnings about missing Tailwind classes

## Tasks (from plan)
- [ ] Task 1.10 — Configure Tailwind + PostCSS

## Dev Tests to write
None — visual story.

## 🧪 User-Test Checkpoint

```bash
npm run dev
```

**Expect:**
- Window opens with dark slate background
- "MultiTerm — hello" heading rendered in white at center, large, bold
- "Ping main process" button is solid blue, white text, hover darkens
- Status line "app.ready: yes" in green when ready, gray when pending
- RTT line "RTT: N ms" in muted slate after first click
- No visible flash of unstyled content on window open

If the page renders unstyled or with fallback fonts only → stop, report.

## Status

**[ ] Pending**
