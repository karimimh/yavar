# Yavar web app

Next.js 16 (App Router) frontend for Yavar. The UI is Persian-only and
right-to-left (`lang="fa"`, `dir="rtl"`). It talks to the Django API at
`NEXT_PUBLIC_API_URL` using session cookies and CSRF.

See the [root README](../../README.md) for the full setup. To work on the
frontend by itself:

```bash
npm ci
npm run dev         # http://localhost:3000 (expects the API on :8000)
npm test            # Vitest
npm run lint        # ESLint
npm run typecheck   # next typegen + tsc --noEmit
npm run format      # Prettier
```

Layout:

- `src/app/`: routes (`/sign-in`, `/onboarding`, `/coverage`, `/ops`, and the
  signed-in area under `/app/*`)
- `src/components/`: shared UI (`AppShell`, `TaskCard`)
- `src/lib/`: API client (`api.ts`) and Jalali/Persian-digit/toman helpers
  (`dates.ts`)
