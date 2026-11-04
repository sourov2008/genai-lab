# ClauseDesk - 3 User Flows Demo

Live URL: [https://clausedesk-api.onrender.com](https://clausedesk-api.onrender.com)

- UI: [https://clausedesk-api.onrender.com/ui](https://clausedesk-api.onrender.com/ui)
- API Docs: [https://clausedesk-api.onrender.com/docs](https://clausedesk-api.onrender.com/docs)

---

## Flow 1: Upload & Extract (The Happy Path)

1. Go to `/ui`.
2. Upload a sample contract (PDF or TXT).
3. Click "Run Extraction".
4. Verify that extracted clauses appear with a green "auto_accepted" badge.

Use a clean contract whose quotes match the source and include type keywords (for example `terminate`, `liability`, `governed by`). High confidence plus an exact quote match is what produces `auto_accepted`.

---

## Flow 2: Human Review Queue (The Review Path)

1. Upload a contract containing a typo (e.g., "This agreement may be termanated...").
2. Click "Run Extraction".
3. Verify that the clause appears with a yellow "review" badge.
4. Click "Accept" or "Reject" to see the status change.

The LLM may “fix” `termanated` to `terminated`. Exact substring match then fails, so the clause stays in review instead of auto-accepting. Accept sets `verified`; Reject sets `rejected`.

---

## Flow 3: API Testing (Swagger UI)

1. Go to `/docs`.
2. Expand the `POST /contracts/` endpoint.
3. Use the Swagger UI to upload a file.
4. Verify the JSON response returns the created contract.

Expect HTTP 200/201 and a JSON body with `id`, `filename`, and `status` (typically `pending`).
