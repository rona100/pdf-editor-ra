---
paths:
  - "frontend/**"
---

# Frontend (React + Vite + Vitest)

- Each operation is one component in `frontend/src/operations/`. It builds a `FormData` and calls `execute(endpoint, formData, outputFilename)` from `hooks/useOperation.ts`, which handles loading and error state and triggers the download. Follow that pattern for a new operation, and add it to `App.tsx`.
- Tests live in `frontend/src/test/` and run under jsdom. `URL.createObjectURL` and `revokeObjectURL` don't exist in jsdom, so they are stubbed in `src/test/setup.ts`.
- Run `npm --prefix frontend test` for the tests and `npx --prefix frontend tsc --noEmit -p frontend` for types. A hook already runs `tsc` after each `.ts`/`.tsx` edit.
- Node 18+ is required.
